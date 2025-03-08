from django.core.management.base import BaseCommand
from apps.optics.models import ReceiptTemplate
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Creates a generic receipt template that serves as a fallback'

    def handle(self, *args, **options):
        # Check if generic template already exists
        if ReceiptTemplate.objects(merchant_name='Generic').count() > 0:
            self.stdout.write(self.style.WARNING('Generic template already exists'))
            return
        
        # Create a generic template with common patterns
        generic_template = ReceiptTemplate(
            merchant_name='Generic',
            currency_info={
                "iso_code": "GBP",
                "symbol": "£",
            },
            field_extractors={
                "merchant_name": {
                    "expected_present": True,
                    "patterns": [
                        "^([A-Z][A-Za-z0-9\\s&.']+)$",  # Capitalized name at start of line
                        "^(.{5,50})$"  # Any reasonable length text at start of line
                    ],
                    "line_hints": [0, 1, 2]  # Usually in first 3 lines
                },
                "transaction_time": {
                    "expected_present": True,
                    "patterns": [
                        "Date[:\\s]*(\\d{1,2}[/\\-]\\d{1,2}[/\\-]\\d{2,4})",  # Date: MM/DD/YYYY
                        "(\\d{1,2}[/\\-]\\d{1,2}[/\\-]\\d{2,4})[\\s]*\\d{1,2}:\\d{2}",  # MM/DD/YYYY HH:MM
                        "\\b(\\d{1,2}[/\\-]\\d{1,2}[/\\-]\\d{2,4})\\b"  # Just the date anywhere
                    ],
                    "line_hints": [2, 3, 4, 5, 6]  # Usually in first few lines
                },
                "merchant_address": {
                    "expected_present": True,
                    "patterns": [
                        "([A-Za-z0-9\\s,.']+,\\s*[A-Z]{1,2}\\d{1,2}\\s*\\d[A-Z]{2})",  # UK postcode format
                        "([A-Za-z0-9\\s,.']+,\\s*[A-Z]{2}\\s*\\d{5})"  # US ZIP code format
                    ],
                    "line_hints": [1, 2, 3, 4]  # Usually after merchant name
                },
                "reference_number": {
                    "expected_present": False,
                    "patterns": [
                        "(?:receipt|order|ref|invoice)[\\s#:]*([A-Za-z0-9\\-]+)",  # After keywords
                        "\\b(\\d{5,})\\b"  # Any 5+ digit number as fallback
                    ],
                    "line_hints": [2, 3, 4, 5, 6, 7, 8, 9, 10]  # Can be anywhere in header
                },
                "total_amount": {
                    "expected_present": True,
                    "patterns": [
                        "total\\s*[:\\s]*[£$€]?(\\d+\\.\\d{2})",  # After "total" with currency
                        "amount\\s*[:\\s]*[£$€]?(\\d+\\.\\d{2})",  # After "amount" with currency
                        "(?:sum|due|pay)[\\s:]*[£$€]?(\\d+\\.\\d{2})",  # Other keywords
                        "[£$€]?\\s*(\\d+\\.\\d{2})\\s*$"  # Currency amount at end of line
                    ],
                    "offset_from_last_item": 3  # Usually a few lines after last line item
                },
                "tax_amount": {
                    "expected_present": False,
                    "patterns": [
                        "(?:tax|vat|gst)[\\s:]*[£$€]?(\\d+\\.\\d{2})",  # Tax keywords
                        "(?:tax|vat|gst)[\\s:]*\\d+%[\\s:]*[£$€]?(\\d+\\.\\d{2})"  # Tax with percentage
                    ],
                    "offset_from_last_item": 2  # Usually before total amount
                }
            },
            item_patterns=[
                {
                    "pattern": "(\\d+)[xX\\s]+(.*?)\\s+[£$€]?(\\d+\\.\\d{2})",
                    "groups": {
                        "quantity": 1,
                        "item_name": 2,
                        "total_price": 3
                    }
                },
                {
                    "pattern": "([\\d.]+)\\s+(.*?)\\s+[£$€]?(\\d+\\.\\d{2})\\s+[£$€]?(\\d+\\.\\d{2})",
                    "groups": {
                        "quantity": 1,
                        "item_name": 2,
                        "unit_price": 3,
                        "total_price": 4
                    }
                },
                {
                    "pattern": "(.*?)\\s+[£$€]?(\\d+\\.\\d{2})",
                    "groups": {
                        "item_name": 1,
                        "total_price": 2
                    }
                }
            ],
            field_accuracy={
                "merchant_name": 80.0,
                "transaction_time": 75.0,
                "merchant_address": 60.0,
                "reference_number": 50.0,
                "total_amount": 80.0,
                "tax_amount": 60.0
            },
            usage_count=0,
            success_rate=70.0  # Initial success rate
        )
        
        generic_template.save()
        self.stdout.write(self.style.SUCCESS('Successfully created generic template'))
