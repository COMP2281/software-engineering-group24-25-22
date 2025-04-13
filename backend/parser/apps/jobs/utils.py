from django.conf import settings
import os
from .models import ProcessingJob


def temp_file_path(instance: ProcessingJob):
    return os.path.join(settings.TEMP_UPLOAD_DIR, str(instance.id) + ".temp")
