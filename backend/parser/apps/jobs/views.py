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
from .utils import temp_file_path

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

class ParseReceiptView(APIView):
    """
    API endpoint for parsing receipts (blocking until processing completes)
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
                metadata['extension_filename'] = os.path.splitext(metadata['original_filename'])[1]
                del metadata['original_filename']
            except json.JSONDecodeError:
                return Response(
                    {'error': 'Invalid metadata format'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Extract user_id from JWT token if available
        user_id = None
        
        # Check Authorization header for JWT token
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            import jwt
            from django.conf import settings
            
            token = auth_header.split(' ')[1]
            try:
                # Verify the token and extract user_id in one step
                decoded_token = jwt.decode(
                    token,
                    settings.SECRET_KEY,
                    algorithms=['HS256']
                )
                user_id = decoded_token.get('user_id')
                if user_id:
                    logger.info(f"Authenticated request with JWT for user_id: {user_id}")
            except jwt.InvalidTokenError as e:
                logger.warning(f"Invalid JWT token: {str(e)}")
            except Exception as e:
                logger.warning(f"Failed to decode JWT token: {str(e)}")

        # Fallback to metadata if JWT extraction failed
        if not user_id:
            user_id = metadata.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'User ID is required in either JWT token or metadata'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            

        print("METADATA")
        print(json.dumps(metadata, indent=2))
        # Create a new processing job
        job = ProcessingJob(
            user_id=user_id,
            original_filename=metadata.get('original_filename', file_obj.name),
            file_type=metadata.get('content_type', file_obj.content_type),
            metadata=metadata,
            status='pending'
        )

        # Add expiration time (4 hours from now) for temporary file
        if not job.metadata:
            job.metadata = {}
        job.metadata['temp_expiration'] = (timezone.now() + timezone.timedelta(hours=4)).isoformat()
        job.save()

        # Save the uploaded file to a temporary location
        with open(temp_file_path(job), "wb") as tmp:
            for chunk in file_obj.chunks():
                tmp.write(chunk)

        # Process receipt using Celery task asynchronously but wait for result
        from apps.optics.tasks import process_receipt_ocr
        try:
            import time
            from celery.exceptions import TimeoutError
            
            # Start the task
            start_time = time.time()
            print(f"Starting Celery task for job {job.id}")
            
            # Launch the task
            task = process_receipt_ocr.delay(str(job.id))
            
            # Wait for task completion with timeout
            try:
                task_result = task.get(timeout=30)  # 30 seconds timeout
                print(f"Task result: {task_result}")
            except TimeoutError:
                # If it times out, that's okay - we'll return a pending status
                print(f"Task {task.id} is still processing (timeout reached)")
                job.update_status('processing')
                
                return Response({
                    'id': str(job.id),
                    'status': 'processing',
                    'message': 'Receipt processing started'
                }, status=status.HTTP_202_ACCEPTED)
            except Exception as e:
                # Handle other exceptions
                error_msg = f"Processing task failed: {str(e)}"
                print(error_msg)
                job.update_status('failed', error_message=error_msg)
                return Response(
                    {'error': error_msg}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
            # If we get here, the task completed within the timeout
            # Refresh job from database to get latest state
            job = ProcessingJob.objects.get(id=job.id)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Return job data immediately
            return Response({
                'id': str(job.id),
                'status': job.status,
                'extracted_data': job.extracted_data,
                'ocr_confidence': job.ocr_confidence,
                'needs_review': job.needs_review,
                'processing_time': processing_time
            }, status=status.HTTP_200_OK)
            
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
    def get_object(self,id):
        try:
            return ProcessingJob.objects.get(id=id)
        except ProcessingJob.DoesNotExist:
            raise Http404("Processing job not found")
    
    def get(self, request, id):
        job = self.get_object(id)
        
        # Extract user_id from JWT token if available and verify ownership
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            import jwt
            from django.conf import settings
            
            token = auth_header.split(' ')[1]
            try:
                # Verify the token and extract user_id in one step
                decoded_token = jwt.decode(
                    token,
                    settings.SECRET_KEY,
                    algorithms=['HS256']
                )
                user_id = decoded_token.get('user_id')
                
                # Verify the user owns this job
                if user_id and str(job.id) != str(user_id):
                    return Response(
                        {'error': 'User ID does not match job owner'}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
                    
                if user_id:
                    logger.info(f"Authenticated request with JWT for job status: {id}")
            except jwt.InvalidTokenError as e:
                logger.warning(f"Invalid JWT token for job status: {str(e)}")
            except Exception as e:
                logger.warning(f"Failed to decode JWT token: {str(e)}")
        
        response_data = {
            'id': str(job.id),
            'status': job.status,
            'created_at': job.created_at.isoformat(),
            'updated_at': job.updated_at.isoformat(),
            'original_filename': job.original_filename,
            'ocr_confidence': job.ocr_confidence,
            'needs_review': job.needs_review,
        }
        
        # Include extracted data and user corrections if available
        if job.status == 'completed':
            if job.extracted_data:
                response_data['extracted_data'] = job.extracted_data
            if job.user_corrections:
                response_data['user_corrections'] = job.user_corrections
        
        # Include error message if failed
        if job.status == 'failed' and job.error_message:
            response_data['error_message'] = job.error_message
            
        return Response(response_data)

class ConfirmJobView(APIView):
    """
    API endpoint for confirming processed receipt data
    """
    def get_object(self, id):
        try:
            return ProcessingJob.objects.get(id=id)
        except ProcessingJob.DoesNotExist:
            raise Http404("Processing job not found")
    
    def post(self, request, id):
        job = self.get_object(id)
        
        # Verify job status
        if job.status != 'completed':
            return Response(
                {'error': 'Can only confirm completed jobs'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Extract user_id from JWT token if available
        user_id = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header and auth_header.startswith('Bearer '):
            import jwt
            from django.conf import settings
            
            token = auth_header.split(' ')[1]
            try:
                # Verify the token and extract user_id in one step
                decoded_token = jwt.decode(
                    token,
                    settings.SECRET_KEY,
                    algorithms=['HS256']
                )
                user_id = decoded_token.get('user_id')
                if user_id:
                    logger.info(f"Authenticated request with JWT for confirm job: {id}")
            except jwt.InvalidTokenError as e:
                logger.warning(f"Invalid JWT token for confirm job: {str(e)}")
            except Exception as e:
                logger.warning(f"Failed to decode JWT token: {str(e)}")
                
        # Fallback to request body
        if not user_id:
            try:
                request_data = json.loads(request.body)
                user_id = request_data.get('user_id')
            except json.JSONDecodeError:
                user_id = None
        
        # Verify user ID matches
        if not user_id or str(job.user_id) != str(user_id):
            return Response(
                {'error': 'User ID does not match job owner'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get any corrections from the request body
        corrections = {}
        try:
            request_data = json.loads(request.body)
            corrections = request_data.get('corrections', {})
        except json.JSONDecodeError:
            pass
        
        # Apply corrections if provided
        if corrections:
            # Store original data for template feedback
            original_data = job.extracted_data.copy() if job.extracted_data else {}

            # Store the user corrections
            job.user_corrections = corrections
            
            job.save()
            
            # Process template improvements with the corrections
            self.process_template_improvements(job, original_data, corrections)
        
        # Transfer to permanent storage and create records
        from .tasks import transfer_to_gridfs
        
        # Transfer file to GridFS
        transfer_result = transfer_to_gridfs(str(job.id))
        
        # Check if transfer was successful
        if transfer_result.get('status') != 'completed':
            return Response(
                {'error': f"Failed to transfer file to permanent storage: {transfer_result.get('error')}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Update job with confirmation details
        if not hasattr(job, 'metadata') or job.metadata is None:
            job.metadata = {}
        
        job.metadata['confirmed_at'] = timezone.now().isoformat()
        job.update_status('confirmed')

        print(job.uploaded_file.grid_id)
        
        # Return the final receipt data
        return Response({
            'id': str(job.id),
            'gridfs_id': transfer_result.get('gridfs_id', None),
            'extracted_data': job.extracted_data,
            'user_corrections': job.user_corrections
        })
    
    def process_template_improvements(self, job, original_data, corrections):
        """Process template improvements based on user corrections"""
        # Only proceed if there are corrections
        if not corrections:
            return
            
        try:
            from django.core.cache import cache
            from apps.optics.services import TemplateSuite
            
            cache_key = f"template_improvement_{job.id}"
            
            # Only proceed if we haven't processed this job's corrections already
            if not cache.get(cache_key):
                # Set flag to prevent duplicate processing
                cache.set(cache_key, True, timeout=3600)  # 1 hour timeout
                
                # Get the original OCR text from job metadata or use a placeholder
                ocr_text = job.metadata.get('ocr_text_preprocessed', 'No OCR text available')
                
                # Count corrected fields
                corrected_fields = {}
                for key, value in corrections.items():
                    if key in original_data and original_data[key] != value:
                        corrected_fields[key] = {
                            'original': original_data[key],
                            'corrected': value
                        }
                
                # Log the correction details
                logger.info(
                    f"User corrected {len(corrected_fields)} fields for job {job.id}. "
                    f"Sending corrections to template system."
                )
                
                # Only proceed if there's a template to improve and corrections were made
                if job.template_used and corrected_fields:
                    # Convert to API format using the service helpers
                    original_api_data = TemplateSuite.convert_to_api_format(original_data)
                    
                    # Combine extracted data with user corrections to get the final data
                    final_data = job.extracted_data.copy() if job.extracted_data else {}
                    for key, value in job.user_corrections.items():
                        if value is not None:
                            final_data[key] = value
                    
                    # Corrected data in API format
                    corrected_api_data = TemplateSuite.convert_to_api_format(final_data)
                    
                    # Process the correction through TemplateSuite
                    result = TemplateSuite.process_correction(
                        ocr_text=ocr_text,
                        template_id=job.template_used,
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

class DiscardJobView(APIView):
    """
    API endpoint for discarding a processing job
    """
    def get_object(self, id):
        try:
            return ProcessingJob.objects.get(id=id)
        except ProcessingJob.DoesNotExist:
            raise Http404("Processing job not found")
    
    def delete(self, request, id):
        job = self.get_object(id)
        
        # Extract user_id from JWT token if available and verify ownership
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            import jwt
            from django.conf import settings
            
            token = auth_header.split(' ')[1]
            try:
                # Verify the token and extract user_id in one step
                decoded_token = jwt.decode(
                    token,
                    settings.SECRET_KEY,
                    algorithms=['HS256']
                )
                user_id = decoded_token.get('user_id')
                
                # Verify the user owns this job
                if user_id and str(job.user_id) != str(user_id):
                    return Response(
                        {'error': 'User ID does not match job owner'}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
                    
                if user_id:
                    logger.info(f"Authenticated request with JWT for discard job: {id}")
            except jwt.InvalidTokenError as e:
                logger.warning(f"Invalid JWT token for discard job: {str(e)}")
                # Continue without user verification in this case
            except Exception as e:
                logger.warning(f"Failed to decode JWT token: {str(e)}")
        
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
                        if filename.startswith(str(job.id)):
                            file_path = os.path.join(job_dir, filename)
                            if os.path.exists(file_path):
                                os.remove(file_path)
        except Exception as e:
            logger.warning(f"Failed to clean up job files: {str(e)}")
        
        # Update job with discard details
        if not hasattr(job, 'metadata') or job.metadata is None:
            job.metadata = {}
        
        job.metadata['discarded_at'] = timezone.now().isoformat()
        
        # Mark job as discarded (instead of deleting - for audit purposes)
        job.update_status('discarded')
        
        return Response(status=status.HTTP_204_NO_CONTENT)

class EditJobDataView(APIView):
    """
    API endpoint for editing processed receipt data
    """
    def get_object(self, id):
        try:
            return ProcessingJob.objects.get(id=id)
        except ProcessingJob.DoesNotExist:
            raise Http404("Processing job not found")
    
    def post(self, request, id):
        job = self.get_object(id)
        
        # Verify job status
        if job.status != 'completed':
            return Response(
                {'error': 'Can only edit completed jobs'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Extract user_id from JWT token if available and verify ownership
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            import jwt
            from django.conf import settings
            
            token = auth_header.split(' ')[1]
            try:
                # Verify the token and extract user_id in one step
                decoded_token = jwt.decode(
                    token,
                    settings.SECRET_KEY,
                    algorithms=['HS256']
                )
                user_id = decoded_token.get('user_id')
                
                # Verify the user owns this job
                if user_id and str(job.user_id) != str(user_id):
                    return Response(
                        {'error': 'User ID does not match job owner'}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
                    
                if user_id:
                    logger.info(f"Authenticated request with JWT for edit job: {id}")
            except jwt.InvalidTokenError as e:
                logger.warning(f"Invalid JWT token for edit job: {str(e)}")
            except Exception as e:
                logger.warning(f"Failed to decode JWT token: {str(e)}")
        
        # Get the edited data (already validated by General Server)
        edited_data = json.loads(request.body)
        
        # Store original data for template feedback
        original_data = job.extracted_data.copy() if job.extracted_data else {}
        
        # Update user corrections
        user_corrections = {} if job.user_corrections is None else dict(job.user_corrections)
            
        # Add the edited data to user corrections
        for key, value in edited_data.items():
            if value is not None:  # Only update fields that were provided
                user_corrections[key] = value
        
        # Assign the new corrections
        job.user_corrections = user_corrections
        
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
                
                cache_key = f"template_improvement_{job.id}"
                
                # Only proceed if we haven't processed this job's corrections already
                if not cache.get(cache_key):
                    # Set flag to prevent duplicate processing
                    cache.set(cache_key, True, timeout=3600)  # 1 hour timeout
                    
                    # Get the original OCR text from job metadata or use a placeholder
                    ocr_text = job.metadata.get('ocr_text', 'No OCR text available')
                    
                    # Log the correction details
                    logger.info(
                        f"User corrected {len(corrected_fields)} fields for job {job.id}. "
                        f"Sending corrections to template system."
                    )
                    
                    # Convert to API format using the service helpers
                    # Original data in API format
                    original_api_data = TemplateSuite.convert_to_api_format(original_data)
                    
                    # Combine extracted data with user corrections to get the final data
                    final_data = job.extracted_data.copy() if job.extracted_data else {}
                    for key, value in job.user_corrections.items():
                        if value is not None:
                            final_data[key] = value
                    
                    # Corrected data in API format
                    corrected_api_data = TemplateSuite.convert_to_api_format(final_data)
                    
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
        
        # Combine extracted data with user corrections to get the final data
        final_data = job.extracted_data.copy() if job.extracted_data else {}
        for key, value in job.user_corrections.items():
            if value is not None:
                final_data[key] = value
                
        return Response({
            'extracted_data': job.extracted_data,
            'user_corrections': job.user_corrections,
            'final_data': final_data
        })
