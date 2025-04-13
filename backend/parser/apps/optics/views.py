"""
This file contains API views for the optics app.
The functionality has been moved to the TemplateSuite class in services.py
and is directly used by the jobs app. These view stubs are kept for future
API needs if required.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
import logging

from .services import TemplateSuite

logger = logging.getLogger(__name__)


class ReceiptParseView(APIView):
    """API endpoint for parsing receipts using templates."""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """Parse receipt using the best template."""
        # Implementation moved to TemplateSuite.parse_receipt
        pass


class ReceiptCorrectionView(APIView):
    """API endpoint for handling user corrections and improving templates."""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """Submit corrected receipt data to improve templates."""
        # Implementation moved to TemplateSuite.process_correction
        pass


class TemplateMaintenanceView(APIView):
    """Admin endpoint for template maintenance operations."""

    permission_classes = [IsAuthenticated]  # Should use admin permission in production

    def post(self, request, *args, **kwargs):
        """Run template maintenance tasks."""
        # Implementation moved to TemplateSuite maintenance methods
        pass
