from mongoengine import Document, StringField, DateTimeField, FloatField, BooleanField
from mongoengine import DecimalField, ReferenceField, CASCADE, NULLIFY
import mongoengine
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class Receipt(Document):
    """Receipt model for storing extracted data from uploaded receipts"""
    
    STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    # Required form fields
    merchant_name = StringField(max_length=255)
    transaction_time = DateTimeField()
    merchant_address = StringField(required=False)
    reference_number = StringField(max_length=100, required=False)
    tax_amount = DecimalField(precision=2, required=False)
    category = StringField(max_length=100)
    description = StringField(required=False)
    
    # Calculated fields
    total_amount = DecimalField(precision=2)
    subtotal_amount = DecimalField(precision=2, required=False)
    currency = StringField(max_length=3, default='GBP')
    
    # Ownership and workflow

    # Workflow for approving the encoded receipts for reimbursement.
    # MongoEngine uses references instead of ForeignKey
    employee = ReferenceField(
        'User',  # Use string reference to avoid circular imports
        reverse_delete_rule=CASCADE
    )
    status = StringField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    approver = ReferenceField(
        'User',
        reverse_delete_rule=NULLIFY,
        required=False
    )
    
    # File metadata
    upload_date = DateTimeField(default=timezone.now)
    original_filename = StringField(max_length=255, required=False)
    file_type = StringField(max_length=10, required=False)  # PDF, JPG, etc.
    file_id = StringField(max_length=50, required=False)    # GridFS ID reference
    
    # OCR processing details
    ocr_confidence = FloatField(default=0.0)  # 0-100
    needs_review = BooleanField(default=False)
    
    # Location data (optional)
    latitude = FloatField(required=False)
    longitude = FloatField(required=False)
    location_name = StringField(max_length=255, required=False)
    
    # Timestamps
    created_at = DateTimeField(default=timezone.now)
    updated_at = DateTimeField()
    
    def __str__(self):
        return f"{self.merchant_name} - {self.transaction_time.date()} - {self.total_amount} {self.currency}"
    
    meta = {
        'collection': 'receipts',
        'ordering': ['-transaction_time'],
        'indexes': [
            'employee',
            'status',
            'transaction_time',
        ]
    }


class CostItem(Document):
    """Individual line items on a receipt"""
    
    receipt = ReferenceField(
        Receipt, 
        reverse_delete_rule=CASCADE
    )
    item_name = StringField(max_length=255)
    unit_price = DecimalField(precision=2)
    quantity = DecimalField(precision=2, default=Decimal('1.00'))
    total_price = DecimalField(precision=2)
    
    def save(self, *args, **kwargs):
        # Auto-calculate total_price if not provided
        if not self.total_price:
            self.total_price = self.unit_price * self.quantity
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.item_name} - {self.quantity} x {self.unit_price} = {self.total_price}"
        
    meta = {
        'collection': 'cost_items',
        'indexes': [
            'receipt'
        ]
    }
