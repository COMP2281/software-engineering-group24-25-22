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
        list_display = ('get_id', 'get_user', 'get_status', 'get_filename', 'get_confidence', 'get_date', 'get_template')
        # Remove list_filter for now as it causes issues with proxy models
        list_filter = ()
        search_fields = ('user_id', 'original_filename')
        
        def get_user(self, obj):
            # Just display the user ID since it's not a reference we can easily link to
            return obj.user_id
        get_user.short_description = 'User'
        
        def get_status(self, obj):
            status_colors = {
                'pending': '#FFC107',  # Amber
                'queued': '#03A9F4',   # Blue
                'processing': '#9C27B0', # Purple
                'completed': '#4CAF50', # Green
                'confirmed': '#8BC34A', # Light Green
                'failed': '#F44336',   # Red
                'discarded': '#9E9E9E' # Gray
            }
            color = status_colors.get(obj.status, '#000000')
            return f'<span style="color:{color};font-weight:bold;">{obj.status}</span>'
        get_status.short_description = 'Status'
        get_status.allow_tags = True
        
        def get_filename(self, obj):
            return obj.original_filename
        get_filename.short_description = 'Filename'
        
        def get_confidence(self, obj):
            if not obj.ocr_confidence:
                return 'N/A'
            
            confidence = obj.ocr_confidence
            color = '#F44336'  # Red for low confidence
            if confidence >= 80:
                color = '#4CAF50'  # Green for high confidence
            elif confidence >= 50:
                color = '#FFC107'  # Amber for medium confidence
                
            return f'<span style="color:{color};font-weight:bold;">{confidence:.2f}%</span>'
        get_confidence.short_description = 'OCR Confidence'
        get_confidence.allow_tags = True
        
        def get_date(self, obj):
            return obj.created_at.strftime('%Y-%m-%d %H:%M') if obj.created_at else 'N/A'
        get_date.short_description = 'Created'
        
        @MongoDBAdmin.reference_field(app='parser', model='receipttemplateproxy')
        def get_template(self, obj):
            # If the template_used field is a string ID, we need to look up the template
            if obj.template_used and isinstance(obj.template_used, str):
                try:
                    template = ReceiptTemplate.objects.get(id=obj.template_used)
                    return template
                except:
                    return None
            return None
        get_template.short_description = 'Template'

    class ReceiptTemplateAdmin(MongoDBAdmin):
        mongo_model = ReceiptTemplate
        list_display = ('get_id', 'get_merchant', 'get_usage', 'get_success_rate', 'get_status', 'get_last_used')
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
            if not obj.success_rate:
                return '0%'
                
            success_rate = obj.success_rate
            color = '#F44336'  # Red for low success rate
            if success_rate >= 80:
                color = '#4CAF50'  # Green for high success rate
            elif success_rate >= 50:
                color = '#FFC107'  # Amber for medium success rate
                
            return f'<span style="color:{color};font-weight:bold;">{success_rate:.2f}%</span>'
        get_success_rate.short_description = 'Success Rate'
        get_success_rate.allow_tags = True
        
        def get_status(self, obj):
            if obj.is_archived:
                return '<span style="color:#9E9E9E;font-weight:bold;">Archived</span>'
            else:
                return '<span style="color:#4CAF50;font-weight:bold;">Active</span>'
        get_status.short_description = 'Status'
        get_status.allow_tags = True
        
        def get_last_used(self, obj):
            return obj.last_used_at.strftime('%Y-%m-%d %H:%M') if obj.last_used_at else 'Never'
        get_last_used.short_description = 'Last Used'
    
    # Register the proxy models with their admin classes
    admin.site.register(ProcessingJobProxy, ProcessingJobAdmin)
    admin.site.register(ReceiptTemplateProxy, ReceiptTemplateAdmin)
    
except ImportError as e:
    print(f"Error importing parser models: {e}")
    # Don't register models if import fails
    pass
