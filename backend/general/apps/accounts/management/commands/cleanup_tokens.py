from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.accounts.models import BlacklistedToken
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Cleans up expired blacklisted tokens"

    def handle(self, *args, **options):
        """
        Delete tokens that have passed their expiration date.
        """
        now = timezone.now()
        expired_tokens = BlacklistedToken.objects.filter(expires_at__lt=now)
        count = expired_tokens.count()

        if count:
            expired_tokens.delete()
            self.stdout.write(
                self.style.SUCCESS(f"Successfully deleted {count} expired tokens")
            )
            logger.info(f"Deleted {count} expired tokens")
        else:
            self.stdout.write(self.style.SUCCESS("No expired tokens found"))
            logger.info("No expired tokens found")
