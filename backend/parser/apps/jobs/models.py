import uuid
import os
from pathlib import Path
from mongoengine import Document, StringField, DateTimeField, IntField, FloatField
from mongoengine import BooleanField, FileField, DictField, UUIDField, CASCADE, NULLIFY
from django.utils import timezone
from django.conf import settings


def job_directory_path(instance, filename):
    """Generate file path for job files"""
    # File will be uploaded to TEMP_UPLOAD_DIR/jobs/<id>/<filename>
    return f"jobs/{instance.id}/{filename}"


class ProcessingJob(Document):
    """Model for tracking OCR processing jobs"""

    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("queued", "Queued"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("confirmed", "Confirmed"),  # User has confirmed the data
        ("failed", "Failed"),
        ("discarded", "Discarded"),  # User discarded the job
        ("abandoned", "Abandoned"),  # Job was never confirmed/discarded and expired
    )

    id = UUIDField(primary_key=True, default=uuid.uuid4)
    user_id = StringField(help_text="ID of the user who initiated the job")
    status = StringField(max_length=20, choices=STATUS_CHOICES, default="pending")
    original_filename = StringField(max_length=255)
    file_type = StringField(max_length=50)
    uploaded_file = FileField(
        default=None,
        cascade_delete=False,
    )

    # Celery task tracking
    task_id = StringField(
        max_length=50,
        required=False,
        help_text="ID of the Celery task processing this job",
    )

    # Metadata (stored as JSON)
    metadata = DictField(default=dict)

    # Processing details
    extracted_data = DictField(
        required=False, help_text="Original data extracted by the OCR system"
    )
    user_corrections = DictField(
        required=False, help_text="Corrections made by the user"
    )
    error_message = StringField(required=False)
    template_correspondence = FloatField(default=0.0)
    template_used = StringField(
        max_length=50, required=False, help_text="ID of the template used for parsing"
    )

    # Timestamps
    created_at = DateTimeField(default=timezone.now)
    updated_at = DateTimeField(default=timezone.now)
    processing_started = DateTimeField(required=False)
    processing_completed = DateTimeField(required=False)

    meta = {
        "collection": "processing_jobs",
        "ordering": ["-created_at"],
        "indexes": [
            "user_id",
            "status",
            "task_id",
            "created_at",
        ],
    }

    def __str__(self):
        return f"Job {self.id} - {self.status}"

    @property
    def duration(self):
        """Calculate job processing duration"""
        if self.processing_started and self.processing_completed:
            return self.processing_completed - self.processing_started
        if (
            self.status in ("completed", "confirmed", "failed")
            and not self.processing_completed
        ):
            # Fallback for jobs processed before this field was added
            return self.updated_at - self.created_at
        return None

    @property
    def temporary_directory(self):
        """Get the temporary directory path for this job"""
        return Path(settings.TEMP_UPLOAD_DIR) / str(self.id)

    def update_status(self, new_status, error_message=None):
        """Update job status and related fields"""
        # With mongoengine directly, we modify attributes and save
        self.status = new_status

        # Set timestamps based on status
        now = timezone.now()
        # Always update the updated_at field
        self.updated_at = now

        if new_status == "processing" and not self.processing_started:
            self.processing_started = now
        elif new_status in ("completed", "failed"):
            self.processing_completed = now

        # Store error message if provided
        if error_message:
            self.error_message = error_message

        # Save changes
        self.save()
