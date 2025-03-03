import uuid
import os
from django.db import models
from django.utils import timezone

def job_directory_path(instance, filename):
    """Generate file path for job files"""
    # File will be uploaded to MEDIA_ROOT/jobs/<job_id>/<filename>
    return f'jobs/{instance.job_id}/{filename}'

class ProcessingJob(models.Model):
    """Model for tracking OCR processing jobs"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )
    
    job_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.IntegerField(help_text="ID of the user who initiated the job")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50)
    uploaded_file = models.FileField(upload_to=job_directory_path)
    
    # Metadata (stored as JSON)
    metadata = models.JSONField(default=dict)
    
    # Processing details
    processed_data = models.JSONField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    ocr_confidence = models.FloatField(default=0.0)
    needs_review = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Job {self.job_id} - {self.status}"
    
    @property
    def duration(self):
        """Calculate job duration"""
        if self.status in ('completed', 'failed'):
            return self.updated_at - self.created_at
        return None
