from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class Receipt(models.Model):
    """Receipt model for storing extracted data from uploaded receipts"""
    
    STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    # Required form fields
    merchant_name = models.CharField(max_length=255)
    transaction_time = models.DateTimeField()
    merchant_address = models.TextField(blank=True)
    reference_number = models.CharField(max_length=100, blank=True)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    category = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Calculated fields
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='GBP')
    
    # Ownership and workflow

    # Workflow for approving the encoded receipts for reimbursement.
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='receipts'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True,
        related_name='receipts_to_approve'
    )
    
    # File metadata
    upload_date = models.DateTimeField(default=timezone.now)
    original_filename = models.CharField(max_length=255, blank=True)
    file_type = models.CharField(max_length=10, blank=True)  # PDF, JPG, etc.
    file_id = models.CharField(max_length=50, blank=True)    # GridFS ID reference
    
    # OCR processing details
    ocr_confidence = models.FloatField(default=0.0)  # 0-100
    needs_review = models.BooleanField(default=False)
    
    # Location data (optional)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    location_name = models.CharField(max_length=255, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.merchant_name} - {self.transaction_time.date()} - {self.total_amount} {self.currency}"
    
    class Meta:
        ordering = ['-transaction_time']
        indexes = [
            models.Index(fields=['employee']),
            models.Index(fields=['status']),
            models.Index(fields=['transaction_time']),
        ]


class CostItem(models.Model):
    """Individual line items on a receipt"""
    
    receipt = models.ForeignKey(
        Receipt, 
        on_delete=models.CASCADE,
        related_name='cost_items'
    )
    item_name = models.CharField(max_length=255)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('1.00'))
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def save(self, *args, **kwargs):
        # Auto-calculate total_price if not provided
        if not self.total_price:
            self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.item_name} - {self.quantity} x {self.unit_price} = {self.total_price}"
