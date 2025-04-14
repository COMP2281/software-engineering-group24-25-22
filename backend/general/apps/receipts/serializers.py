from rest_framework import serializers
from common.serializers import DocumentSerializer
from .models import Receipt 
from bson import ObjectId
import base64


# Custom ReceiptDocumentSerializer for MongoEngine Documents
class ReceiptDocumentSerializer(DocumentSerializer):
    """
    Base serializer for MongoEngine documents that makes them
    compatible with DRF.
    """

    id = serializers.CharField(read_only=True)

    def to_representation(self, instance):
        """
        Custom representation method that bypasses DRF's model-specific features
        """
        ret = {}
        fields = self._readable_fields

        for field in fields:
            attribute = field.get_attribute(instance)
            if attribute is None:
                ret[field.field_name] = None
            else:
                ret[field.field_name] = field.to_representation(attribute)

        # Handle any custom fields
        ret = self.custom_representation(instance, ret)

        return ret

    def custom_representation(self,  data, ret):
        """
        Override this to add custom fields to the representation
        """
        return data


# Model Serializers
class CostItemSerializer(serializers.Serializer):
    item_name = serializers.CharField()
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    quantity = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2)

    def to_representation(self, instance):
        return {
            "item_name": instance.item_name,
            "unit_price": str(instance.unit_price),
            "quantity": str(instance.quantity),
            "total_price": str(instance.total_price),
        }


class ReceiptSerializer(ReceiptDocumentSerializer):
    id = serializers.CharField(read_only=True)
    template_used = serializers.SerializerMethodField(read_only=True)
    merchant_name = serializers.CharField(read_only=True)
    transaction_time = serializers.DateTimeField(read_only=True)
    merchant_address = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )
    reference_number = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )
    tax_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True
    )
    category = serializers.CharField()
    description = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )

    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    subtotal_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True
    )
    currency = serializers.CharField(default="GBP")

    employee = serializers.SerializerMethodField(read_only=True)
    status = serializers.CharField(default="pending")
    approver = serializers.CharField(read_only=True)

    upload_date = serializers.DateTimeField(read_only=True)
    file = serializers.FileField(required=False)
    file_ext = serializers.CharField(required=False)

    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)
    location_name = serializers.CharField(
        required=False, allow_null=True, allow_blank=True
    )

    template_correspondence = serializers.FloatField(read_only=True)

    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Receipt

    def get_employee(self, obj):
        if obj.employee:
            return str(obj.employee.id)  # Convert ObjectId to string
        return None

    def get_approver(self, obj):
        if obj.approver:
            return str(obj.approver.id)  # Convert ObjectId to string
        return None

    def get_template_used(self, obj):
        if obj.template_used:
            return str(obj.template_used.id)
        return None

    def validate(self, data):
        """Validate that receipts have required file-related fields."""
        # First apply the standard model validation
        data = super().validate(data)

        if self.instance:  # This means we're updating an existing instance
            immutable_fields = ["file", "file_ext", "upload_date"]

            for field in immutable_fields:
                if field in data and getattr(self.instance, field) != data[field]:
                    raise serializers.ValidationError(
                        {field: f"The '{field}' cannot be changed after creation."}
                    )
        else:  # For new receipt creation (not updates)
            # Check for required file fields
            required_fields = ["file", "file_ext", "upload_date"]
            missing_fields = [field for field in required_fields if not data.get(field)]

            if missing_fields:
                raise serializers.ValidationError(
                    {
                        "file_error": "Receipt requires a file attachment. "
                        + f"Missing required fields: {', '.join(missing_fields)}",
                        "missing_fields": missing_fields,
                    }
                )

            # Optional: Additional file type validation
            valid_file_types = ["pdf", "jpg", "jpeg", "png", "tiff"]
            if (
                data.get("file_type")
                and data["file_type"].lower() not in valid_file_types
            ):
                raise serializers.ValidationError(
                    {
                        "file_type": f"File type must be one of: {', '.join(valid_file_types)}"
                    }
                )

        return data

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Ensure any missed ObjectIds are converted
        for field in ret:
            if isinstance(ret[field], ObjectId):
                ret[field] = str(ret[field])
        return ret

    def custom_representation(self, instance, data):
        """Handle file and other special person fields"""
        # Find all cost items for this receipt
        data["file"] = base64.b64encode(instance.file.read()).decode("utf-8")
        data["file_ext"] = instance.file_ext

        # Properly serialize the embedded cost_items document list
        if hasattr(instance, "cost_items") and instance.cost_items:
            serializer = CostItemSerializer(instance.cost_items, many=True)
            data["cost_items"] = serializer.data
        else:
            data["cost_items"] = []

        return data
