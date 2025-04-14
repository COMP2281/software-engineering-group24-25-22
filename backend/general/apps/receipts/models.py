from mongoengine import (
    Document,
    StringField,
    DateTimeField,
    FloatField,
    FileField,
    DecimalField,
    ReferenceField,
    CASCADE,
    NULLIFY,
    EmbeddedDocument,
    EmbeddedDocumentField,
    ListField,
)
from common.models.templates import ReceiptTemplate
from django.utils import timezone
from decimal import Decimal


class CostItem(EmbeddedDocument):
    """Individual line items embedded in a receipt"""

    item_name = StringField(max_length=255)
    unit_price = DecimalField(precision=2)
    quantity = DecimalField(precision=2, default=Decimal("1.00"))
    total_price = DecimalField(precision=2)

    def __str__(self):
        return f"{self.item_name} - {self.quantity} x {self.unit_price} = {self.total_price}"


class Receipt(Document):
    """Receipt model for storing extracted data from uploaded receipts"""

    STATUS_CHOICES = (
        ("pending", "Pending Review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
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
    currency = StringField(max_length=3, default="GBP")

    # Cost Items
    cost_items = ListField(EmbeddedDocumentField(CostItem), default=list)

    template_used = ReferenceField(ReceiptTemplate, reverse_delete_rule=NULLIFY)

    # Ownership and workflow

    # Workflow for approving the encoded receipts for reimbursement.
    # MongoEngine uses references instead of ForeignKey
    employee = ReferenceField(
        "User",  # Use string reference to avoid circular imports
        reverse_delete_rule=CASCADE,
    )
    status = StringField(max_length=10, choices=STATUS_CHOICES, default="pending")
    approver = ReferenceField("User", reverse_delete_rule=NULLIFY, required=False)

    # File metadata
    upload_date = DateTimeField(default=timezone.now)
    file = FileField(required=True, cascade_delete=True)
    file_ext = StringField(max_length=10, required=True)  # PDF, JPG, etc.

    # OCR processing details
    template_correspondence = FloatField(default=0.0)  # 0-100

    # Location data (optional)
    latitude = FloatField(required=False)
    longitude = FloatField(required=False)
    location_name = StringField(max_length=255, required=False)

    # Timestamps
    created_at = DateTimeField(default=timezone.now)
    updated_at = DateTimeField()

    def add_cost_item(
        self, item_name, unit_price, quantity=Decimal("1.00"), total_price=None
    ):
        """Helper method to add a cost item to the receipt"""
        if total_price is None:
            total_price = unit_price * quantity

        item = CostItem(
            item_name=item_name,
            unit_price=unit_price,
            quantity=quantity,
            total_price=total_price,
        )
        self.cost_items.append(item)
        return item

    def __str__(self):
        return f"{self.merchant_name} - {self.transaction_time.date()} - {self.total_amount} {self.currency}"

    meta = {
        "collection": "receipts",
        "ordering": ["-transaction_time"],
        "indexes": [
            "employee",
            "status",
            "transaction_time",
        ],
    }
