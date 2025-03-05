import json
import os
import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings
from django.http import Http404
from django.utils import timezone
from typing import Dict, Any

from .models import ProcessingJob

logger = logging.getLogger(__name__)

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
        job = ProcessingJob(
            user_id=user_id,
            original_filename=metadata.get('original_filename', file_obj.name),
            file_type=metadata.get('content_type', file_obj.content_type),
            uploaded_file=file_obj,
            metadata=metadata,
            status='pending'
        )
        job.save()
        
        # Queue job for asynchronous processing
        from apps.optics.tasks import process_receipt_ocr
        try:
            # Direct function call since it's a shared_task function
            task_result = process_receipt_ocr(str(job.job_id))
            
            # Update job status directly since we called the task synchronously
            job.update_status('completed')  # The task will have already completed
            
            # Return job ID
            return Response({
                'job_id': str(job.job_id),
                'status': job.status
            }, status=status.HTTP_202_ACCEPTED)
            
        except Exception as e:
            # Handle processing error
            job.update_status('failed', error_message=f"Failed to process job: {str(e)}")
            
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
        
        # Transfer to permanent storage and create records
        from .tasks import transfer_to_gridfs
        
        # Queue file transfer to GridFS in the background
        # Direct function call since it's a shared_task function
        transfer_task = transfer_to_gridfs(str(job.job_id))
        
        # Update job with confirmation details
        if not hasattr(job, 'metadata') or job.metadata is None:
            job.metadata = {}
        
        job.metadata['confirmed_at'] = timezone.now().isoformat()
        job.update_status('confirmed')
        
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
        try:
            if job.uploaded_file and hasattr(job.uploaded_file, 'path'):
                job_dir = os.path.dirname(job.uploaded_file.path)
                if os.path.exists(job_dir):
                    for filename in os.listdir(job_dir):
                        if filename.startswith(str(job.job_id)):
                            file_path = os.path.join(job_dir, filename)
                            if os.path.exists(file_path):
                                os.remove(file_path)
        except Exception as e:
            logger.warning(f"Failed to clean up job files: {str(e)}")
        
        # Mark job as discarded (instead of deleting - for audit purposes)
        job.update_status('discarded')
        
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
        
        # Store original data for template feedback
        original_data = job.processed_data.copy() if job.processed_data else {}
        
        # Merge edited data with existing data
        processed_data: Dict[str, Any] = {} if job.processed_data is None else dict(job.processed_data)
            
        # Create a new dictionary with updated values
        for key, value in edited_data.items():
            if value is not None:  # Only update fields that were provided
                processed_data[key] = value
        
        # Assign the new dictionary to processed_data
        job.processed_data = processed_data
        
        # Save the updated job
        job.save()
        
        # Count number of fields that were corrected
        corrected_fields = {}
        for key, value in edited_data.items():
            if key in original_data and original_data[key] != value:
                corrected_fields[key] = {
                    'original': original_data[key],
                    'corrected': value
                }
        
        # If fields were corrected, trigger template learning through TemplateSuite
        if corrected_fields and job.template_used:
            try:
                from django.core.cache import cache
                from apps.optics.services import TemplateSuite
                
                cache_key = f"template_improvement_{job.job_id}"
                
                # Only proceed if we haven't processed this job's corrections already
                if not cache.get(cache_key):
                    # Set flag to prevent duplicate processing
                    cache.set(cache_key, True, timeout=3600)  # 1 hour timeout
                    
                    # Get the original OCR text from job metadata or use a placeholder
                    ocr_text = job.metadata.get('ocr_text', 'No OCR text available')
                    
                    # Log the correction details
                    logger.info(
                        f"User corrected {len(corrected_fields)} fields for job {job.job_id}. "
                        f"Sending corrections to template system."
                    )
                    
                    # Convert to API format using the service helpers
                    # Original data in API format
                    original_api_data = TemplateSuite.convert_to_api_format(original_data)
                    
                    # Ensure processed_data is not None
                    processed_data = job.processed_data if job.processed_data is not None else {}
                    
                    # Corrected data in API format
                    corrected_api_data = TemplateSuite.convert_to_api_format(processed_data)
                    
                    # Process the correction through TemplateSuite
                    result = TemplateSuite.process_correction(
                        ocr_text=ocr_text,
                        template_id=job.template_used,
                        original_data=original_api_data,
                        corrected_data=corrected_api_data
                    )
                    
                    # Check if the template was updated successfully
                    if result.get('success'):
                        logger.info(
                            f"Template {result.get('template_action')} successfully: "
                            f"{result.get('template_id')}"
                        )
                    else:
                        logger.error(f"Template update failed: {result.get('error', 'Unknown error')}")
                        
            except Exception as e:
                logger.error(f"Error during template improvement: {e}", exc_info=True)
        
        return Response(job.processed_data or {})
