import os
import logging
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from django.db.models import Q
from celery import shared_task

logger = logging.getLogger(__name__)

@shared_task
def cleanup_temporary_files():
    """
    Task to clean up temporary files from the TEMP_UPLOAD_DIR:
    1. For jobs with expiration timestamp: delete if expired (4 hours)
    2. For jobs without expiration timestamp: delete if older than 7 days (legacy fallback)
    """
    from .models import ProcessingJob
    
    logger.info("Starting temporary file cleanup task")
    start_time = timezone.now()
    
    # Get the path to the temporary upload directory
    temp_dir = Path(settings.TEMP_UPLOAD_DIR)
    
    # Skip if directory doesn't exist
    if not temp_dir.exists():
        logger.warning(f"Temporary directory {temp_dir} does not exist")
        return
    
    # Get all jobs with temporary files that haven't been confirmed or discarded
    all_jobs = ProcessingJob.objects(
        status__nin=['confirmed', 'discarded'],
        uploaded_file__ne=None
    )
    
    # Track results
    expired_count = 0
    active_count = 0
    error_count = 0
    orphaned_count = 0
    
    # Get current time for comparisons
    now = timezone.now()
    
    # First check jobs with expiration timestamps
    for job in all_jobs:
        try:
            # Skip jobs that don't have a file anymore
            if not hasattr(job.uploaded_file, 'path') or not job.uploaded_file.path:
                continue
                
            # Get file path
            file_path = Path(job.uploaded_file.path)
            
            # Check if the file exists
            if not file_path.exists():
                continue
                
            # Check if job has expiration timestamp
            if job.metadata and 'temp_expiration' in job.metadata:
                try:
                    # Parse expiration timestamp
                    expiration_time = datetime.fromisoformat(job.metadata['temp_expiration'])
                    
                    # Check if expired
                    if now > expiration_time:
                        # Remove the file
                        try:
                            os.remove(file_path)
                            
                            # Mark job as abandoned
                            if job.status not in ['confirmed', 'discarded', 'failed']:
                                if not job.metadata:
                                    job.metadata = {}
                                job.metadata['abandoned_at'] = now.isoformat()
                                job.update_status('abandoned', error_message="Temporary file expired")
                                
                            expired_count += 1
                            logger.info(f"Removed expired file for job {job.id}")
                        except Exception as e:
                            logger.error(f"Error removing file for job {job.id}: {e}")
                            error_count += 1
                    else:
                        # File not expired yet
                        active_count += 1
                        
                except (ValueError, TypeError):
                    # Invalid timestamp format, fall back to modification time check
                    logger.warning(f"Invalid expiration timestamp for job {job.id}")
                    check_file_modification_time(file_path, job)
            else:
                # No expiration timestamp, fall back to modification time check
                check_file_modification_time(file_path, job)
                
        except Exception as e:
            logger.error(f"Error processing job {job.id}: {e}")
            error_count += 1
    
    # Now check for orphaned files/directories (files without associated jobs)
    # Get job directories
    jobs_dir = temp_dir / 'jobs'
    if jobs_dir.exists():
        job_dirs = [d for d in jobs_dir.iterdir() if d.is_dir()]
        valid_job_ids = [str(job.id) for job in all_jobs]
        
        for job_dir in job_dirs:
            job_id = job_dir.name
            
            # If no active job with this ID, remove the directory
            if job_id not in valid_job_ids:
                try:
                    shutil.rmtree(job_dir)
                    orphaned_count += 1
                    logger.info(f"Removed orphaned directory for job {job_id}")
                except Exception as e:
                    logger.error(f"Error removing orphaned directory {job_id}: {e}")
                    error_count += 1
    
    # Calculate duration
    duration = timezone.now() - start_time
    
    # Log results
    logger.info(
        f"Temporary file cleanup completed in {duration.total_seconds():.2f} seconds. "
        f"Expired: {expired_count}, Active: {active_count}, Orphaned: {orphaned_count}, Errors: {error_count}"
    )
    
    return {
        'status': 'completed',
        'expired_count': expired_count,
        'active_count': active_count,
        'orphaned_count': orphaned_count,
        'error_count': error_count,
        'duration_seconds': duration.total_seconds(),
        'timestamp': timezone.now().isoformat()
    }

def check_file_modification_time(file_path, job):
    """Helper function to check file modification time and cleanup if needed"""
    # Set cutoff date (7 days ago) - legacy fallback
    cutoff_date = datetime.now() - timedelta(days=7)
    
    # Check file modification time
    try:
        mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
        
        # Remove if older than cutoff date
        if mod_time < cutoff_date:
            os.remove(file_path)
            
            # Mark job as abandoned
            if job.status not in ['confirmed', 'discarded', 'failed']:
                if not job.metadata:
                    job.metadata = {}
                job.metadata['abandoned_at'] = timezone.now().isoformat()
                job.update_status('abandoned', error_message="Temporary file expired (7-day fallback)")
            
            logger.info(f"Removed old file for job {job.id} based on modification time")
            return True
    except Exception as e:
        logger.error(f"Error checking modification time for job {job.id}: {e}")
    
    return False

@shared_task
def transfer_to_gridfs(job_id):
    """
    Task to transfer a completed job's files to MongoDB GridFS
    
    Args:
        job_id: The UUID of the ProcessingJob to transfer
        
    Returns:
        dict: Transfer results
    """
    from .models import ProcessingJob
    import gridfs
    from pymongo import MongoClient
    from django.conf import settings
    
    try:
        # Get the job
        job = ProcessingJob.objects.get(id=job_id)
        
        # Get file path
        file_path = job.uploaded_file.path
        
        # Check if file exists
        if not os.path.exists(file_path):
            error_msg = f"File not found for job {job_id}"
            logger.error(error_msg)
            job.update_status('failed', error_message=error_msg)
            return {'status': 'failed', 'error': error_msg}
        
        # Connect to MongoDB
        client = MongoClient(settings.MONGO_CONNECTION_STRING)
        db = client['receipt_scanner_db']
        
        # Create GridFS bucket
        fs = gridfs.GridFS(db, collection='receipt_files')
        
        # Prepare metadata
        metadata = {
            'job_id': str(job.id),
            'user_id': str(job.user_id),
            'original_filename': job.original_filename,
            'file_type': job.file_type,
            'upload_date': job.created_at,
            'confirmed_date': timezone.now()
        }
        
        # Read the file from temp storage
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        # Store it in GridFS with metadata
        gridfs_id = fs.put(
            file_data, 
            filename=job.original_filename,
            content_type=job.file_type,
            metadata=metadata
        )
        
        # Update job with the GridFS file ID
        job.gridfs_id = str(gridfs_id)
        job.storage_path = f"gridfs:{gridfs_id}"
        
        # Delete the temp file
        os.remove(file_path)
        
        job.uploaded_file = None
        job.save()

        # Log success
        logger.info(f"Successfully transferred job {job_id} to GridFS (id: {gridfs_id})")
        
        return {
            'status': 'completed',
            'job_id': str(job_id),
            'gridfs_id': str(gridfs_id),
            'timestamp': timezone.now().isoformat()
        }
        
    except ProcessingJob.DoesNotExist:
        error_msg = f"Job not found: {job_id}"
        logger.error(error_msg)
        return {'status': 'failed', 'error': error_msg}
        
    except Exception as e:
        error_msg = f"Error transferring to GridFS: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # Try to update job status if we have a reference to it
        try:
            if 'job' in locals():
                job.update_status('failed', error_message=error_msg)
        except Exception:
            pass
            
        return {'status': 'failed', 'error': error_msg}
    
@shared_task
def cleanup_old_jobs():
    """
    Task to permanently delete old job records after 90 days.
    Only deletes jobs in terminal states (completed, confirmed, failed, discarded).
    """
    from .models import ProcessingJob
    
    logger.info("Starting old job cleanup task")
    start_time = timezone.now()
    
    # Calculate cutoff date (90 days ago)
    cutoff_date = timezone.now() - timedelta(days=90)
    
    # Get jobs in terminal states older than cutoff date
    old_jobs = ProcessingJob.objects(
        status__in=['completed', 'confirmed', 'failed', 'discarded'],
        created_at__lt=cutoff_date
    )
    
    # Count jobs to be deleted
    count = old_jobs.count()
    logger.info(f"Found {count} old jobs to clean up")
    
    # Only proceed if there are jobs to delete
    if count > 0:
        # Delete the jobs
        deletion_result = old_jobs.delete()
        logger.info(f"Deleted {count} job records")
    
    # Calculate duration
    duration = timezone.now() - start_time
    
    # Log completion
    logger.info(f"Job record cleanup completed in {duration.total_seconds():.2f} seconds")
    
    return {
        'status': 'completed',
        'deleted_count': count,
        'duration_seconds': duration.total_seconds(),
        'timestamp': timezone.now().isoformat()
    }
