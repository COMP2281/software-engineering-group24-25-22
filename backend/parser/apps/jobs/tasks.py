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
    Task to clean up old temporary files from the TEMP_UPLOAD_DIR
    Runs daily and removes files older than 7 days that aren't related to active jobs
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
    
    # Get list of active job IDs 
    active_jobs = [str(job.job_id) for job in ProcessingJob.objects(
        status__in=['pending', 'processing']
    )]
    
    # Get all job directories
    job_dirs = [d for d in temp_dir.iterdir() if d.is_dir()]
    
    # Set cutoff date (7 days ago)
    cutoff_date = datetime.now() - timedelta(days=7)
    
    removed_count = 0
    
    # Check each directory
    for job_dir in job_dirs:
        job_id = job_dir.name
        
        # Skip if this is an active job
        if job_id in active_jobs:
            logger.debug(f"Skipping cleanup of active job: {job_id}")
            continue
        
        # Check directory modification time
        try:
            mod_time = datetime.fromtimestamp(job_dir.stat().st_mtime)
            
            # Remove if older than cutoff date
            if mod_time < cutoff_date:
                logger.info(f"Removing old job directory: {job_id}")
                shutil.rmtree(job_dir)
                removed_count += 1
        except Exception as e:
            logger.error(f"Error cleaning up job directory {job_id}: {e}")
    
    # Calculate duration
    duration = timezone.now() - start_time
    
    # Log results
    logger.info(
        f"Temporary file cleanup completed in {duration.total_seconds():.2f} seconds. "
        f"Removed {removed_count} directories."
    )
    
    return {
        'status': 'completed',
        'removed_count': removed_count,
        'duration_seconds': duration.total_seconds(),
        'timestamp': timezone.now().isoformat()
    }

@shared_task
def transfer_to_gridfs(job_id):
    """
    Task to transfer a completed job's files to MongoDB GridFS
    
    Args:
        job_id: The UUID of the ProcessingJob to transfer
        
    Returns:
        dict: Transfer results
    """
    # This would implement the transfer logic to move files from 
    # temporary storage to GridFS when a job is confirmed
    # In a real implementation, this would:
    # 1. Connect to MongoDB
    # 2. Create a GridFS bucket
    # 3. Read the file from temp storage
    # 4. Store it in GridFS with metadata
    # 5. Update job with the GridFS file ID
    # 6. Delete the temp file
    
    # For now, just log that we would do this
    logger.info(f"Would transfer job {job_id} to GridFS")
    
    return {
        'status': 'completed',
        'job_id': str(job_id),
        'gridfs_id': f"simulated_gridfs_id_{job_id}",
        'timestamp': timezone.now().isoformat()
    }
    
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