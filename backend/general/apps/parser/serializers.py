from rest_framework import serializers
from django.core.validators import FileExtensionValidator


class ReceiptUploadSerializer(serializers.Serializer):
    """Serializer for validating receipt upload"""

    file = serializers.FileField(
        validators=[
            FileExtensionValidator(
                allowed_extensions=["jpg", "jpeg", "png", "pdf", "tiff"]
            )
        ]
    )

    def validate_file(self, value):
        """Validate file size and type"""
        # Check file size (limit to 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File size cannot exceed 10MB")

        # Check content type
        valid_types = ["image/jpeg", "image/png", "application/pdf", "image/tiff"]
        if value.content_type not in valid_types:
            raise serializers.ValidationError(
                "Unsupported file type. Please upload a JPG, PNG, PDF, or TIFF file."
            )

        return value


class CostItemSerializer(serializers.Serializer):
    """Serializer for validating cost items"""

    item_name = serializers.CharField(required=True, max_length=255)
    unit_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False
    )
    quantity = serializers.DecimalField(
        max_digits=8, decimal_places=2, required=False, default=1.0
    )
    total_price = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False
    )

    def validate(self, attrs):
        """Ensure either total_price or both unit_price and quantity are provided"""
        if "total_price" not in attrs and (
            "unit_price" not in attrs or "quantity" not in attrs
        ):
            raise serializers.ValidationError(
                "Either total_price or both unit_price and quantity must be provided"
            )

        return attrs


class ReceiptDataSerializer(serializers.Serializer):
    """Serializer for validating receipt data structure"""

    merchant_name = serializers.CharField(
        required=False, allow_blank=True, max_length=255
    )
    transaction_time = serializers.DateTimeField(required=False)
    merchant_address = serializers.CharField(
        required=False, allow_blank=True, max_length=500
    )
    reference_number = serializers.CharField(
        required=False, allow_blank=True, max_length=100
    )
    tax_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True
    )
    category = serializers.CharField(required=False, allow_blank=True, max_length=100)
    description = serializers.CharField(
        required=False, allow_blank=True, max_length=500
    )
    total_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False
    )
    subtotal_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True
    )
    currency = serializers.CharField(max_length=3, required=False, default="GBP")

    # Cost items
    cost_items = serializers.ListField(child=CostItemSerializer(), required=False)


class ConfirmJobSerializer(serializers.Serializer):
    """Serializer for job confirmation request"""

    corrections = ReceiptDataSerializer(required=False)
    descriptions = serializers.DictField(
        required=False,
        help_text="Additional descriptive fields like category and description",
    )
