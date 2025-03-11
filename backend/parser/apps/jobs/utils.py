from django.conf import settings
import os
from .models import ProcessingJob

def temp_file_path(instance: ProcessingJob, filename: str):
    return os.path.join(settings.TEMP_UPLOAD_DIR, str(instance.id)+os.path.splitext(filename)[1])
