import json
import os
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings
from django.http import Http404

from .models import ProcessingJob
from .ocr_processor import OCRProcessor # TODO: Implement this

# API Key Authentication Middleware
class APIKeyAuthentication:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/api/parser/'):
            api_key = request.headers.get('Authorization')
            if not api_key or not api_key.startswith('ApiKey '):
                return Response(
                    {'error': 'Invalid API key'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Extract the key
            key = api_key.split(' ')[1]
            if key != settings.API_KEY:
                return Response(
                    {'error': 'Invalid API key'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
                
        return self.get_response(request)

class UploadReceiptView(APIView):
    """
    API endpoint for uploading receipts for processing
    """
    parser_classes = (MultiPartParser, FormParser)
    
    def post(self, request):
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No file provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        file_obj = request.FILES['file']
        
        # Parse metadata from header
        metadata = {}
        if 'X-Receipt-Metadata' in request.headers:
            try:
                metadata = json.loads(request.headers['X-Receipt-Metadata'])
            except json.JSONDecodeError:
                return Response(
                    {'error': 'Invalid metadata format'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        user_id = metadata.get('user_id')
        if not user_id:
            return Response(
                {'error': 'User ID is required in metadata'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Create a new processing job
        job = ProcessingJob.objects.create(
            user_id=user_id,
            original_filename=metadata.get('original_filename', file_obj.name),
            file_type=metadata.get('content_type', file_obj.content_type),
            uploaded_file=file_obj,
            metadata=metadata,
            status='pending'
        )
        
        # Start processing in background
        # (In a real implementation, this would use Celery or similar)
        try:
            job.status = 'processing'
            job.save()
            
            # Process the receipt
            processor = OCRProcessor(job)
            processor.process()
            
            # Return job ID
            return Response({
                'job_id': str(job.job_id),
                'status': job.status
            }, status=status.HTTP_202_ACCEPTED)
        except Exception as e:
            job.status = 'failed'
            job.error_message = str(e)
            job.save()
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class JobStatusView(APIView):
    """
    API endpoint for checking the status of a processing job
    """
    def get_object(self, job_id):
        try:
            return ProcessingJob.objects.get(job_id=job_id)
        except ProcessingJob.DoesNotExist:
            raise Http404("Processing job not found")
    
    def get(self, request, job_id):
        job = self.get_object(job_id)
        
        response_data = {
            'job_id': str(job.job_id),
            'status': job.status,
            'created_at': job.created_at.isoformat(),
            'updated_at': job.updated_at.isoformat(),
            'original_filename': job.original_filename,
            'ocr_confidence': job.ocr_confidence,
            'needs_review': job.needs_review,
        }
        
        # Include processed data if available
        if job.status == 'completed' and job.processed_data:
            response_data['processed_data'] = job.processed_data
        
        # Include error message if failed
        if job.status == 'failed' and job.error_message:
            response_data['error_message'] = job.error_message
            
        return Response(response_data)

class ConfirmJobView(APIView):
    """
    API endpoint for confirming processed receipt data
    """
    def get_object(self, job_id):
        try:
            return ProcessingJob.objects.get(job_id=job_id)
        except ProcessingJob.DoesNotExist:
            raise Http404("Processing job not found")
    
    def post(self, request, job_id):
        job = self.get_object(job_id)
        
        # Verify job status
        if job.status != 'completed':
            return Response(
                {'error': 'Can only confirm completed jobs'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify user ID matches
        request_data = json.loads(request.body)
        user_id = request_data.get('user_id')
        
        if str(job.user_id) != str(user_id):
            return Response(
                {'error': 'User ID does not match job owner'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # In a real implementation, here we would:
        # 1. Move file from temporary storage to permanent storage (GridFS)
        # 2. Create Receipt and CostItem records in the database
        
        # Return the final receipt data
        return Response({
            'job_id': str(job.job_id),
            'receipt_data': job.processed_data
        })

class DiscardJobView(APIView):
    """
    API endpoint for discarding a processing job
    """
    def get_object(self, job_id):
        try:
            return ProcessingJob.objects.get(job_id=job_id)
        except ProcessingJob.DoesNotExist:
            raise Http404("Processing job not found")
    
    def delete(self, request, job_id):
        job = self.get_object(job_id)
        
        # Delete the uploaded file
        if job.uploaded_file:
            if os.path.exists(job.uploaded_file.path):
                os.remove(job.uploaded_file.path)
        
        # Delete any preprocessed images
        job_dir = os.path.dirname(job.uploaded_file.path)
        for filename in os.listdir(job_dir):
            if filename.startswith(str(job.job_id)):
                os.remove(os.path.join(job_dir, filename))
        
        # Delete the job
        job.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)

class EditJobDataView(APIView):
    """
    API endpoint for editing processed receipt data
    """
    def get_object(self, job_id):
        try:
            return ProcessingJob.objects.get(job_id=job_id)
        except ProcessingJob.DoesNotExist:
            raise Http404("Processing job not found")
    
    def post(self, request, job_id):
        job = self.get_object(job_id)
        
        # Verify job status
        if job.status != 'completed':
            return Response(
                {'error': 'Can only edit completed jobs'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the edited data (already validated by General Server)
        edited_data = json.loads(request.body)
        
        # Merge edited data with existing data
        if job.processed_data is None:
            job.processed_data = {}
            
        for key, value in edited_data.items():
            if value is not None:  # Only update fields that were provided
                job.processed_data[key] = value
        
        job.save()
        
        return Response(job.processed_data)
