import uuid
import os
from pathlib import Path
from django.db import models
from django.utils import timezone
from django.conf import settings

def job_directory_path(instance, filename):
    """Generate file path for job files"""
    # File will be uploaded to TEMP_UPLOAD_DIR/jobs/<job_id>/<filename>
    return f'jobs/{instance.job_id}/{filename}'

class ProcessingJob(models.Model):
    """Model for tracking OCR processing jobs"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('queued', 'Queued'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('confirmed', 'Confirmed'),  # User has confirmed the data
        ('failed', 'Failed'),
        ('discarded', 'Discarded'),  # User discarded the job
    )
    
    job_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.IntegerField(help_text="ID of the user who initiated the job")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50)
    uploaded_file = models.FileField(upload_to=job_directory_path)
    
    # GridFS storage details (filled when confirmed and transferred)
    gridfs_id = models.CharField(max_length=50, blank=True, null=True)
    storage_path = models.CharField(max_length=255, blank=True, null=True)
    
    # Celery task tracking
    task_id = models.CharField(max_length=50, blank=True, null=True, 
                              help_text="ID of the Celery task processing this job")
    
    # Metadata (stored as JSON)
    metadata = models.JSONField(default=dict)
    
    # Processing details
    processed_data = models.JSONField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    ocr_confidence = models.FloatField(default=0.0)
    needs_review = models.BooleanField(default=False)
    template_used = models.CharField(max_length=50, blank=True, null=True,
                                    help_text="ID of the template used for parsing")
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    processing_started = models.DateTimeField(null=True, blank=True)
    processing_completed = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['status']),
            models.Index(fields=['task_id']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Job {self.job_id} - {self.status}"
    
    @property
    def duration(self):
        """Calculate job processing duration"""
        if self.processing_started and self.processing_completed:
            return self.processing_completed - self.processing_started
        if self.status in ('completed', 'confirmed', 'failed') and not self.processing_completed:
            # Fallback for jobs processed before this field was added
            return self.updated_at - self.created_at
        return None
    
    @property
    def temporary_directory(self):
        """Get the temporary directory path for this job"""
        return Path(settings.TEMP_UPLOAD_DIR) / str(self.job_id)
    
    def update_status(self, new_status, error_message=None):
        """Update job status and related fields"""
        self.status = new_status
        
        # Set timestamps based on status
        if new_status == 'processing' and not self.processing_started:
            self.processing_started = timezone.now()
        elif new_status in ('completed', 'failed'):
            self.processing_completed = timezone.now()
            
        # Store error message if provided
        if error_message:
            self.error_message = error_message
            
        self.save()
