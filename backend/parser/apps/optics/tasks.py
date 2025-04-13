import logging
from django.utils import timezone
from datetime import datetime
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def run_template_maintenance():
    """
    Scheduled task to run template maintenance operations.
    This should be run daily via Celery scheduler.
    """
    from .services import TemplateSuite

    logger.info("Starting template maintenance job")
    start_time = timezone.now()

    # Archive templates that meet archiving criteria
    try:
        TemplateSuite.evaluate_templates_for_archiving()
        logger.info("Template archiving completed successfully")
    except Exception as e:
        logger.error(f"Error during template archiving: {e}")

    # Clean up old archived templates
    try:
        TemplateSuite.cleanup_archived_templates()
        logger.info("Template cleanup completed successfully")
    except Exception as e:
        logger.error(f"Error during template cleanup: {e}")

    # Log completion
    duration = timezone.now() - start_time
    logger.info(
        f"Template maintenance completed in {duration.total_seconds():.2f} seconds"
    )

    return {
        "status": "completed",
        "duration_seconds": duration.total_seconds(),
        "timestamp": timezone.now().isoformat(),
    }


@shared_task(bind=True, max_retries=3)
def process_receipt_ocr(self, job_id):
    """
    Celery task for processing receipt using the OCR processor

    Args:
        job_id: UUID of the ProcessingJob to process

    Returns:
        dict: Processing results
    """
    from apps.jobs.models import ProcessingJob
    from .ocr_processor import OCRProcessor, OCRProcessorError

    logger.info(f"Starting OCR processing for job {job_id}")
    start_time = timezone.now()

    try:
        job = ProcessingJob.objects.get(id=job_id)

        # Update job status
        job.update_status("processing")

        # Create processor and process
        processor = OCRProcessor(job)
        result = processor.process_file()

        # Update job status
        job.update_status("completed")

        # Calculate duration
        duration = timezone.now() - start_time
        logger.info(
            f"OCR processing completed in {duration.total_seconds():.2f} seconds"
        )
        return {
            "status": "success",
            "job_id": str(job_id),
            "duration_seconds": duration.total_seconds(),
        }
    except Exception as e:
        logger.error(f"Error in Celery task for job {job_id}: {str(e)}")
        raise

    # try:
    #     # Get the job
    #     print("I'm here")
    #     job = ProcessingJob.objects.get(id=job_id)
    #     print(job)
    #
    #     # Update job status
    #     job.update_status('processing')
    #
    #     # Create processor and process
    #     processor = OCRProcessor(job)
    #     result = processor.process_file()
    #
    #     # Update job status
    #     job.update_status('completed')
    #
    #     # Calculate duration
    #     duration = timezone.now() - start_time
    #     logger.info(f"OCR processing completed in {duration.total_seconds():.2f} seconds")
    #
    #     return {
    #         'status': 'success',
    #         'job_id': str(job_id),
    #         'needs_review': job.needs_review,
    #         'duration_seconds': duration.total_seconds()
    #     }
    #
    # except ProcessingJob.DoesNotExist:
    #     logger.error(f"Job {job_id} not found")
    #     return {'status': 'error', 'error': f"Job {job_id} not found"}
    #
    # except OCRProcessorError as e:
    #     logger.error(f"OCR processing error for job {job_id}: {str(e)}")
    #
    #     # Update job status
    #     try:
    #         print("EEWW")
    #         job = ProcessingJob.objects.get(id=job_id)
    #         print("YAH")
    #         job.update_status('failed', error_message=str(e))
    #     except Exception:
    #         pass
    #
    #     return {
    #         'status': 'error',
    #         'job_id': str(job_id),
    #         'error': str(e)
    #     }
    #
    # except Exception as e:
    #     logger.error(f"Unexpected error processing job {job_id}: {str(e)}")
    #
    #     # Update job status
    #     try:
    #         job = ProcessingJob.objects.get(job_id=job_id)
    #         job.update_status('failed', error_message=f"Unexpected error: {str(e)}")
    #     except Exception:
    #         pass
    #
    #     # Retry with backoff
    #     retry_count = self.request.retries
    #     backoff = 60 * (2 ** retry_count)  # Exponential backoff: 60s, 120s, 240s
    #     self.retry(exc=e, countdown=backoff)
    #
    #     return {
    #         'status': 'retry',
    #         'job_id': str(job_id),
    #         'error': str(e),
    #         'retry_count': retry_count
    #     }
