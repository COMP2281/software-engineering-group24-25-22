from django.contrib import admin
from django.db import models
from django.utils.html import format_html
from .models import Receipt, CostItem
from apps.accounts.admin import MongoDBAdmin

# Create proxy models for MongoDB documents
class ReceiptProxy(models.Model):
    """Proxy model for MongoDB Receipt documents"""
    class Meta:
        verbose_name = 'Receipt'
        verbose_name_plural = 'Receipts'
        app_label = 'receipts'

class CostItemProxy(models.Model):
    """Proxy model for MongoDB CostItem documents"""
    class Meta:
        verbose_name = 'Cost Item'
        verbose_name_plural = 'Cost Items'
        app_label = 'receipts'

# Admin classes for MongoDB documents
from apps.accounts.admin import MongoDBAdmin

class ReceiptAdmin(MongoDBAdmin):
    mongo_model = Receipt
    list_display = ('get_id', 'get_merchant', 'get_date', 'get_amount', 'get_status', 'get_employee', 'get_approver')
    search_fields = ('merchant_name', 'reference_number')
    # Remove list_filter for now as it causes issues with proxy models
    list_filter = ()
    
    def get_merchant(self, obj):
        return obj.merchant_name
    get_merchant.short_description = 'Merchant'
    
    def get_date(self, obj):
        return obj.transaction_time.strftime('%Y-%m-%d %H:%M') if obj.transaction_time else 'N/A'
    get_date.short_description = 'Date'
    
    def get_amount(self, obj):
        return f"{obj.total_amount} {obj.currency}"
    get_amount.short_description = 'Amount'
    
    def get_status(self, obj):
        status_colors = {
            'pending': '#FFC107',  # Amber
            'approved': '#4CAF50',  # Green
            'rejected': '#F44336',  # Red
        }
        color = status_colors.get(obj.status, '#000000')
        return f'<span style="color:{color};font-weight:bold;">{obj.status}</span>'
    get_status.short_description = 'Status'
    get_status.allow_tags = True
    
    @MongoDBAdmin.reference_field(app='accounts', model='userproxy')
    def get_employee(self, obj):
        return obj.employee
    get_employee.short_description = 'Employee'
    
    @MongoDBAdmin.reference_field(app='accounts', model='userproxy') 
    def get_approver(self, obj):
        return obj.approver
    get_approver.short_description = 'Approver'

class CostItemAdmin(MongoDBAdmin):
    mongo_model = CostItem
    list_display = ('get_id', 'get_item_name', 'get_receipt', 'get_quantity', 'get_price', 'get_total')
    search_fields = ('item_name',)
    
    def get_item_name(self, obj):
        return obj.item_name
    get_item_name.short_description = 'Item'
    
    @MongoDBAdmin.reference_field(app='receipts', model='receiptproxy')
    def get_receipt(self, obj):
        return obj.receipt
    get_receipt.short_description = 'Receipt'
    
    def get_quantity(self, obj):
        return obj.quantity
    get_quantity.short_description = 'Qty'
    
    def get_price(self, obj):
        return obj.unit_price
    get_price.short_description = 'Unit Price'
    
    def get_total(self, obj):
        return obj.total_price
    get_total.short_description = 'Total'

# Register the proxy models with their admin classes
admin.site.register(ReceiptProxy, ReceiptAdmin)
admin.site.register(CostItemProxy, CostItemAdmin)
