from rest_framework import serializers
from .models import Receipt, CostItem

# Model Serialiser
class CostItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CostItem
        fields = ('id', 'item_name', 'unit_price', 'quantity', 'total_price')
        read_only_fields = ('id',)

class ReceiptSerializer(serializers.ModelSerializer):
    cost_items = CostItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Receipt
        fields = (
            'id', 'merchant_name', 'transaction_time', 'merchant_address',
            'reference_number', 'tax_amount', 'category', 'description',
            'total_amount', 'subtotal_amount', 'currency', 'status',
            'upload_date', 'cost_items', 'file_type', 'latitude', 'longitude',
            'location_name'
        )
        read_only_fields = ('id', 'upload_date', 'employee')
