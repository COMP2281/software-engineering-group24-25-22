from django.contrib import admin
from django.db import models
from django.utils.html import format_html
from .models import User, EmployeeProfile, ExpenseSettings, BlacklistedToken

# Create proxy models for MongoDB documents
class UserProxy(models.Model):
    """Proxy model for MongoDB User documents"""
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        app_label = 'accounts'

class EmployeeProfileProxy(models.Model):
    """Proxy model for MongoDB EmployeeProfile documents"""
    class Meta:
        verbose_name = 'Employee Profile'
        verbose_name_plural = 'Employee Profiles'
        app_label = 'accounts'

class ExpenseSettingsProxy(models.Model):
    """Proxy model for MongoDB ExpenseSettings documents"""
    class Meta:
        verbose_name = 'Expense Settings'
        verbose_name_plural = 'Expense Settings'
        app_label = 'accounts'

# Base admin class for MongoDB documents
class MongoDBAdmin(admin.ModelAdmin):
    """Admin class for MongoDB documents using Django proxy models"""
    list_display = ('get_id', 'get_display_data')
    search_fields = ()
    list_filter = ()
    
    # Store the real MongoDB model class
    mongo_model = None
    
    def get_queryset(self, request):
        """Convert mongoengine queryset to a Django-compatible queryset"""
        from django.db.models.query import QuerySet
        
        # Fetch all objects from MongoDB
        mongo_objects = list(self.mongo_model.objects.all())
        
        # Create a mock queryset
        qs = self.model.objects.none()  # Start with empty QuerySet of proxy model
        
        # Store the MongoDB objects for later retrieval
        self._mongo_objects_dict = {}
        for obj in mongo_objects:
            self._mongo_objects_dict[str(obj.id)] = obj
        
        # Store the original list for reference
        self._mongo_object_list = mongo_objects
        if hasattr(qs, '_clone'):
           # Override the required methods to make it work with admin
           class MongoQuerySet(QuerySet):
               def __init__(self_qs, *args, **kwargs):
                   super().__init__(*args, **kwargs)
                   self_qs._mongo_objects = mongo_objects
                   # Add model reference required by Django admin
                   self_qs.model = self.model
               
               def __iter__(self_qs):
                   return iter(self_qs._mongo_objects)
               
               def __getitem__(self_qs, k):
                   if isinstance(k, slice):
                       return self_qs._mongo_objects[k]
                   return self_qs._mongo_objects[k]
               
               def __len__(self_qs):
                   return len(self_qs._mongo_objects)
               
               def count(self_qs):
                   """Return the count of all objects"""
                   return len(self_qs._mongo_objects)
               
               def order_by(self_qs, *args, **kwargs):
                   """Mock ordering - just return self for compatibility"""
                   return self_qs
               
               def filter(self_qs, *args, **kwargs):
                   """Mock filtering - just return self for compatibility"""
                   return self_qs
           
           # Create a MongoDB-backed queryset
           qs = MongoQuerySet(model=self.model)
           qs._mongo_objects = mongo_objects
  
        return qs
        
    
    def get_id(self, obj):
        """Get the MongoDB document ID"""
        return str(obj.id)
    get_id.short_description = 'ID'
    
    def get_display_data(self, obj):
        """Display MongoDB document as formatted HTML"""
        return format_html('<pre>{}</pre>', str(obj))
    get_display_data.short_description = 'Data'
    
    def has_add_permission(self, request):
        """Disable adding through admin (for now)"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing through admin (for now)"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Disable deletion through admin (for now)"""
        return False
        
    def lookup_allowed(self, lookup, value):
        """Allow all lookups to avoid Django ORM restrictions"""
        return True
        
    def get_ordering(self, request):
        """Override ordering to prevent SQL queries"""
        return []
    
    def get_paginator(self, request, queryset, per_page, orphans=0, allow_empty_first_page=True):
        """Use a custom paginator that works with our queryset"""
        from django.core.paginator import Paginator
        
        # Custom paginator to work with MongoDB objects
        class MongoPaginator(Paginator):
            def _get_count(self):
                return len(queryset)
                
        return MongoPaginator(queryset, per_page, orphans, allow_empty_first_page)
        
    def get_object(self, request, object_id, from_field=None):
        """Get the MongoDB object by ID"""
        try:
            # Use the dictionary of MongoDB objects we created in get_queryset
            if hasattr(self, '_mongo_objects_dict') and object_id in self._mongo_objects_dict:
                return self._mongo_objects_dict[object_id]
            
            # Fallback to direct MongoDB query
            return self.mongo_model.objects.get(id=object_id)
        except:
            return None
        
# Admin classes for MongoDB documents
class UserAdmin(MongoDBAdmin):
    mongo_model = User
    list_display = ('get_id', 'get_email', 'get_is_active', 'get_is_staff', 'get_date_joined')
    search_fields = ('email',)
    # Remove list_filter for now as it causes issues with proxy models
    list_filter = ()
    
    def get_email(self, obj):
        return obj.email
    get_email.short_description = 'Email'
    
    def get_is_active(self, obj):
        return obj.is_active
    get_is_active.short_description = 'Active'
    get_is_active.boolean = True
    
    def get_is_staff(self, obj):
        return obj.is_staff
    get_is_staff.short_description = 'Staff'
    get_is_staff.boolean = True
    
    def get_date_joined(self, obj):
        return obj.date_joined
    get_date_joined.short_description = 'Date Joined'

class EmployeeProfileAdmin(MongoDBAdmin):
    mongo_model = EmployeeProfile
    list_display = ('get_id', 'get_employee_id', 'get_name', 'get_department', 'get_position')
    search_fields = ('employee_id', 'first_name', 'last_name')
    # Remove list_filter for now as it causes issues with proxy models
    list_filter = ()
    
    def get_employee_id(self, obj):
        return obj.employee_id
    get_employee_id.short_description = 'Employee ID'
    
    def get_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    get_name.short_description = 'Name'
    
    def get_department(self, obj):
        return obj.department
    get_department.short_description = 'Department'
    
    def get_position(self, obj):
        return obj.position
    get_position.short_description = 'Position'

class ExpenseSettingsAdmin(MongoDBAdmin):
    mongo_model = ExpenseSettings
    list_display = ('get_id', 'get_user', 'get_currency', 'get_expense_limit')
    # Remove list_filter for now as it causes issues with proxy models
    list_filter = ()
    
    def get_user(self, obj):
        return obj.user.email if obj.user else None
    get_user.short_description = 'User'
    
    def get_currency(self, obj):
        return obj.default_currency
    get_currency.short_description = 'Currency'
    
    def get_expense_limit(self, obj):
        return obj.monthly_expense_limit
    get_expense_limit.short_description = 'Monthly Limit'

# Register the proxy models with their admin classes
admin.site.register(UserProxy, UserAdmin)
admin.site.register(EmployeeProfileProxy, EmployeeProfileAdmin)
admin.site.register(ExpenseSettingsProxy, ExpenseSettingsAdmin)

# Register the BlacklistedToken model with Django's default admin
@admin.register(BlacklistedToken)
class BlacklistedTokenAdmin(admin.ModelAdmin):
    """Admin class for BlacklistedToken model"""
    list_display = ('token_jti', 'user_id', 'blacklisted_at', 'expires_at')
    list_filter = ('blacklisted_at', 'expires_at')
    search_fields = ('token_jti', 'user_id')
    date_hierarchy = 'blacklisted_at'
    
    actions = ['clean_expired_tokens']
    
    def clean_expired_tokens(self, request, queryset):
        """Admin action to clean expired tokens"""
        from django.utils import timezone
        
        expired_count = BlacklistedToken.objects.filter(expires_at__lt=timezone.now()).count()
        BlacklistedToken.clean_expired_tokens()
        
        self.message_user(request, f'Successfully removed {expired_count} expired tokens.')
    clean_expired_tokens.short_description = "Remove expired tokens"
