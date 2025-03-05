from rest_framework import serializers
from .models import Receipt, CostItem

# Custom DocumentSerializer for MongoEngine Documents 
class DocumentSerializer(serializers.Serializer):
    """
    Base serializer for MongoEngine documents that makes them 
    compatible with DRF.
    """
    id = serializers.CharField(read_only=True)
    
    def create(self, validated_data):
        instance = self.Meta.model(**validated_data)
        instance.save()
        return instance
        
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
        
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
    
    def custom_representation(self, instance, data):
        """
        Override this to add custom fields to the representation
        """
        return data

# Model Serializers 
class CostItemSerializer(DocumentSerializer):
    item_name = serializers.CharField()
    unit_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    quantity = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        model = CostItem

class ReceiptSerializer(DocumentSerializer):
    merchant_name = serializers.CharField()
    transaction_time = serializers.DateTimeField()
    merchant_address = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    reference_number = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    tax_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    category = serializers.CharField()
    description = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    subtotal_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    currency = serializers.CharField(default='GBP')
    status = serializers.CharField(default='pending')
    upload_date = serializers.DateTimeField(read_only=True)
    file_type = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    latitude = serializers.FloatField(required=False, allow_null=True)
    longitude = serializers.FloatField(required=False, allow_null=True)
    location_name = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    
    class Meta:
        model = Receipt
    
    def custom_representation(self, instance, data):
        """Add cost items to the representation"""
        # Find all cost items for this receipt
        from .models import CostItem
        cost_items = CostItem.objects(receipt=instance)
        
        # Serialize each cost item
        serializer = CostItemSerializer(cost_items, many=True)
        data['cost_items'] = serializer.data
        
        return data
