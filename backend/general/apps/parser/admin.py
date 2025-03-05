from django.contrib import admin
from django.db import models
import sys
import os
from apps.accounts.admin import MongoDBAdmin

# Add parser app path to Python path
parser_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'parser')
if parser_path not in sys.path:
    sys.path.append(parser_path)

# Import parser models
try:
    from apps.jobs.models import ProcessingJob
    from apps.optics.models import ReceiptTemplate
    
    # Create proxy models for MongoDB documents
    class ProcessingJobProxy(models.Model):
        """Proxy model for MongoDB ProcessingJob documents"""
        class Meta:
            verbose_name = 'Processing Job'
            verbose_name_plural = 'Processing Jobs'
            app_label = 'parser'

    class ReceiptTemplateProxy(models.Model):
        """Proxy model for MongoDB ReceiptTemplate documents"""
        class Meta:
            verbose_name = 'Receipt Template'
            verbose_name_plural = 'Receipt Templates'
            app_label = 'parser'
    
    # Admin classes for MongoDB documents
    class ProcessingJobAdmin(MongoDBAdmin):
        mongo_model = ProcessingJob
        list_display = ('get_id', 'get_user', 'get_status', 'get_filename', 'get_confidence', 'get_date')
        # Remove list_filter for now as it causes issues with proxy models
        list_filter = ()
        search_fields = ('user_id', 'original_filename')
        
        def get_user(self, obj):
            return obj.user_id
        get_user.short_description = 'User'
        
        def get_status(self, obj):
            return obj.status
        get_status.short_description = 'Status'
        
        def get_filename(self, obj):
            return obj.original_filename
        get_filename.short_description = 'Filename'
        
        def get_confidence(self, obj):
            return f"{obj.ocr_confidence:.2f}%" if obj.ocr_confidence else 'N/A'
        get_confidence.short_description = 'OCR Confidence'
        
        def get_date(self, obj):
            return obj.created_at.strftime('%Y-%m-%d %H:%M') if obj.created_at else 'N/A'
        get_date.short_description = 'Created'
    
    class ReceiptTemplateAdmin(MongoDBAdmin):
        mongo_model = ReceiptTemplate
        list_display = ('get_id', 'get_merchant', 'get_usage', 'get_success_rate', 'get_status')
        # Remove list_filter for now as it causes issues with proxy models
        list_filter = ()
        search_fields = ('merchant_name',)
        
        def get_merchant(self, obj):
            return obj.merchant_name
        get_merchant.short_description = 'Merchant'
        
        def get_usage(self, obj):
            return obj.usage_count
        get_usage.short_description = 'Usage Count'
        
        def get_success_rate(self, obj):
            return f"{obj.success_rate:.2f}%" if obj.success_rate else '0%'
        get_success_rate.short_description = 'Success Rate'
        
        def get_status(self, obj):
            return 'Archived' if obj.is_archived else 'Active'
        get_status.short_description = 'Status'
    
    # Register the proxy models with their admin classes
    admin.site.register(ProcessingJobProxy, ProcessingJobAdmin)
    admin.site.register(ReceiptTemplateProxy, ReceiptTemplateAdmin)
    
except ImportError as e:
    print(f"Error importing parser models: {e}")
    # Don't register models if import fails
    pass
