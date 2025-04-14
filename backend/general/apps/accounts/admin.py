from django.contrib import admin
from django.contrib.auth.models import AnonymousUser
from django.db import models
from django.http import HttpResponse
from django.utils.html import format_html
from rest_framework import status
from rest_framework.response import Response
from .models import User, EmployeeProfile, ExpenseSettings, BlacklistedToken


# Create proxy models for MongoDB documents
class UserProxy(models.Model):
    """Proxy model for MongoDB User documents"""

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        app_label = "accounts"


class EmployeeProfileProxy(models.Model):
    """Proxy model for MongoDB EmployeeProfile documents"""

    class Meta:
        verbose_name = "Employee Profile"
        verbose_name_plural = "Employee Profiles"
        app_label = "accounts"


class ExpenseSettingsProxy(models.Model):
    """Proxy model for MongoDB ExpenseSettings documents"""

    class Meta:
        verbose_name = "Expense Settings"
        verbose_name_plural = "Expense Settings"
        app_label = "accounts"


# Base admin class for MongoDB documents
class MongoDBAdmin(admin.ModelAdmin):
    """Admin class for MongoDB documents using Django proxy models"""

    list_display = ("get_id", "get_display_data")
    search_fields = ()
    list_filter = ()
    change_list_template = "admin/mongodb_change_list.html"

    # Store the real MongoDB model class
    mongo_model = None

    def changelist_view(self, request, extra_context=None):
        """Override changelist view to directly handle MongoDB objects"""

        # Check if user is authenticated and has permission
        if not request.user.is_authenticated:
            from django.contrib.admin.views.decorators import staff_member_required

            return staff_member_required(lambda _: None)(request)

        # Get basic admin data
        app_label = self.model._meta.app_label
        model_name = self.model._meta.model_name
        title = f"{self.model._meta.verbose_name_plural}"
        # Fetch MongoDB data

        if self.mongo_model is None:
            raise Exception("This should not happen!")

        mongo_objects = list(self.mongo_model.objects.all())

        # Create a simple HTML table display
        header_html = "".join(
            [
                f"<th scope='col' class='column-{field}'>{self.get_header_for_field(field)}</th>"
                for field in self.list_display
            ]
        )

        # Build table rows
        rows_html = ""
        for i, obj in enumerate(mongo_objects):
            row_class = "row1" if i % 2 == 0 else "row2"  # Alternating row colors
            object_url = f"/admin/{app_label}/{model_name}/{obj.id}/"
            row_cells = []

            # Process all fields
            for field_index, field_name in enumerate(self.list_display):
                if not isinstance(field_name, str):
                    continue

                if hasattr(self, field_name) and callable(getattr(self, field_name)):
                    method = getattr(self, field_name)
                    value = method(obj)
                    # Check if this is a reference field that should be linked
                    if hasattr(method, "is_reference") and method.is_reference:
                        # For relationship fields, provide a link to the related object
                        ref_obj = value
                        if ref_obj:
                            ref_value = (
                                method.reference_display_func(ref_obj)
                                if hasattr(method, "reference_display_func")
                                else str(ref_obj)
                            )
                            if hasattr(ref_obj, "id"):
                                ref_app = getattr(method, "reference_app", app_label)
                                ref_model = getattr(
                                    method,
                                    "reference_model",
                                    ref_obj.__class__.__name__.lower() + "proxy",
                                )
                                row_cells.append(
                                    f"<td><a href='/admin/{ref_app}/{ref_model}/{ref_obj.id}/'>{ref_value}</a></td>"
                                )
                            else:
                                row_cells.append(f"<td>{ref_value}</td>")
                        else:
                            row_cells.append("<td>—</td>")
                    elif hasattr(method, "allow_tags") and method.allow_tags:
                        row_cells.append(f"<td>{value}</td>")
                    else:
                        # For first column, make it a primary link to the object
                        if field_index == 0:
                            row_cells.append(
                                f'<td><a href="{object_url}">{value}</a></td>'
                            )
                        else:
                            row_cells.append(f"<td>{value}</td>")
                else:
                    value = getattr(obj, field_name, "—")
                    # For first column, make it a primary link to the object
                    if field_index == 0:
                        row_cells.append(f'<td><a href="{object_url}">{value}</a></td>')
                    else:
                        row_cells.append(f"<td>{value}</td>")

            # Add a JavaScript onclick event to make the entire row clickable
            rows_html += f"""<tr class='{row_class}' onclick="window.location='{object_url}'" style="cursor:pointer;">{"".join(row_cells)}</tr>"""

        # Handle case when there are no objects
        if not mongo_objects:
            cols_count = len(self.list_display)
            rows_html = f"<tr><td colspan='{cols_count}' style='text-align:center;padding:20px;'>No {self.model._meta.verbose_name_plural} found</td></tr>"

        # Create the admin HTML with proper Django admin styling
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>{title} | Django site admin</title>
            <link rel="stylesheet" href="/static/admin/css/base.css">
            <link rel="stylesheet" href="/static/admin/css/dashboard.css">
            <link rel="stylesheet" href="/static/admin/css/changelists.css">
            <link rel="stylesheet" href="/static/admin/css/responsive.css">
            <script src="/static/admin/js/nav_sidebar.js" defer></script>
            <style>
                /* Custom styles for MongoDB admin */
                #result_list {{
                    width: 100%;
                    border-spacing: 0;
                    border-collapse: collapse;
                }}
                #result_list th {{
                    background: #f8f8f8;
                    padding: 8px;
                    font-weight: bold;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }}
                #result_list td {{
                    padding: 8px;
                    border-bottom: 1px solid #eee;
                    vertical-align: top;
                }}
                #result_list .row1 {{
                    background: #fff;
                }}
                #result_list .row2 {{
                    background: #f9f9f9;
                }}
                #result_list tr:hover {{
                    background: #f5f5f5;
                }}
                /* Make ID column narrower */
                .column-get_id {{
                    width: 150px;
                }}
                /* Limit height of large text content */
                pre {{
                    max-height: 100px;
                    overflow-y: auto;
                    padding: 5px;
                    background: #f5f5f5;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    white-space: pre-wrap;
                    word-break: break-all;
                }}
                /* For reference fields */
                a {{
                    color: #447e9b;
                    text-decoration: none;
                }}
                a:hover {{
                    color: #036;
                }}
                .breadcrumbs {{
                    background: #f8f8f8;
                    padding: 10px;
                    border-bottom: 1px solid #eee;
                    margin-bottom: 15px;
                }}
                .breadcrumbs a {{
                    margin: 0 5px;
                }}
            </style>
        </head>
        <body class="app-{app_label} model-{model_name} change-list" data-admin-utc-offset="0">
            <div id="container">
                <!-- Header -->
                <div id="header">
                    <div id="branding">
                        <h1 id="site-name"><a href="/admin/">Django administration</a></h1>
                    </div>
                    <div id="user-tools">
                        Welcome, <strong>{request.user.username if isinstance(request.user, AnonymousUser) else ""}</strong>.
                        <a href="/admin/password_change/">Change password</a> /
                        <a href="/admin/logout/">Log out</a>
                    </div>
                </div>
                
                <!-- Breadcrumbs -->
                <div class="breadcrumbs">
                    <a href="/admin/">Home</a> &rsaquo;
                    <a href="/admin/{app_label}/">{app_label.title()}</a> &rsaquo;
                    {title}
                </div>
                
                <!-- Main content -->
                <div id="content" class="flex">
                    <h1>{title}</h1>
                    <div id="changelist" class="module filtered">
                        <div class="results">
                            <table id="result_list">
                                <thead>
                                    <tr>{header_html}</tr>
                                </thead>
                                <tbody>
                                    {rows_html}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        from django.http import HttpResponse

        return HttpResponse(html)

    def get_header_for_field(self, field_name):
        """Get the header label for a field"""
        if hasattr(self, field_name) and hasattr(
            getattr(self, field_name), "short_description"
        ):
            return getattr(self, field_name).short_description
        return field_name.replace("_", " ").title()

    @classmethod
    def reference_field(
        cls, field_func=None, *, app=None, model=None, display_func=None
    ):
        """
        Decorator to mark a method as returning a reference to another object

        Args:
            field_func: The method that returns the reference object
            app: The app name for the referenced model (defaults to current app)
            model: The model name for the referenced model (defaults to class name + 'proxy')
            display_func: Function to get display value from reference (defaults to str)
        """

        def decorator(func):
            func.is_reference = True
            if app:
                func.reference_app = app
            if model:
                func.reference_model = model
            if display_func:
                func.reference_display_func = display_func
            return func

        if field_func is None:
            return decorator
        return decorator(field_func)

    def get_id(self, obj):
        """Get the MongoDB document ID"""
        return str(obj.id)

    get_id.short_description = "ID"

    def get_display_data(self, obj):
        """Display MongoDB document as formatted HTML"""
        return format_html("<pre>{}</pre>", str(obj))

    get_display_data.short_description = "Data"

    def has_add_permission(self, request):
        """Disable adding through admin (for now)"""
        return False

    def has_change_permission(self, request, obj=None):
        """Disable editing through admin (for now)"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Disable deletion through admin (for now)"""
        return False

    def detail_view(self, request, object_id):
        """Show detailed information about a MongoDB object"""
        # Get basic admin data
        app_label = self.model._meta.app_label
        model_name = self.model._meta.model_name

        # Get the object
        obj = self.get_object(request, object_id)
        if not obj:
            from django.http import Http404

            raise Http404(f"Object with ID {object_id} not found")

        # Title
        title = f"{self.model._meta.verbose_name}: {str(obj)}"

        # Build a table with all field values
        fields_html = ""

        # Get all fields from the MongoDB document
        all_fields = {}

        # First add special fields from list_display methods
        for field_name in self.list_display:
            if not isinstance(field_name, str):
                continue

            if hasattr(self, field_name) and callable(getattr(self, field_name)):
                method = getattr(self, field_name)
                if field_name != "get_display_data":  # Skip the raw data display
                    label = getattr(
                        method,
                        "short_description",
                        field_name.replace("get_", "").replace("_", " ").title(),
                    )
                    value = method(obj)

                    # Handle references
                    if hasattr(method, "is_reference") and method.is_reference:
                        ref_obj = value
                        if ref_obj:
                            ref_value = (
                                method.reference_display_func(ref_obj)
                                if hasattr(method, "reference_display_func")
                                else str(ref_obj)
                            )
                            if hasattr(ref_obj, "id"):
                                ref_app = getattr(method, "reference_app", app_label)
                                ref_model = getattr(
                                    method,
                                    "reference_model",
                                    ref_obj.__class__.__name__.lower() + "proxy",
                                )
                                all_fields[label] = (
                                    f"<a href='/admin/{ref_app}/{ref_model}/{ref_obj.id}/'>{ref_value}</a>"
                                )
                            else:
                                all_fields[label] = ref_value
                        else:
                            all_fields[label] = "—"
                    elif hasattr(method, "allow_tags") and method.allow_tags:
                        all_fields[label] = value
                    elif hasattr(method, "boolean") and method.boolean:
                        icon = "✓" if value else "✗"
                        all_fields[label] = (
                            f"<span style='color:{'green' if value else 'red'}'>{icon}</span>"
                        )
                    else:
                        all_fields[label] = str(value)

        # Then add all document fields
        for field_name in dir(obj):
            # Skip private attributes, methods, and already displayed fields
            if (
                field_name.startswith("_")
                or field_name in ("objects", "DoesNotExist", "MultipleObjectsReturned")
                or callable(getattr(obj, field_name))
            ):
                continue

            value = getattr(obj, field_name)

            # Skip metadata and special attribute groups
            if field_name in ("meta", "id"):
                continue

            # Format the value based on its type
            if value is None:
                formatted_value = "—"
            elif hasattr(value, "id") and hasattr(value, "__class__"):
                # This is likely a reference to another document
                ref_class_name = value.__class__.__name__.lower() + "proxy"
                ref_app = app_label  # Default to same app
                formatted_value = f"<a href='/admin/{ref_app}/{ref_class_name}/{value.id}/'>{str(value)}</a>"
            elif isinstance(value, (list, dict)):
                import json

                try:
                    formatted_value = (
                        f"<pre>{json.dumps(value, default=str, indent=2)}</pre>"
                    )
                except Exception:
                    formatted_value = f"<pre>{str(value)}</pre>"
            elif isinstance(value, bool):
                icon = "✓" if value else "✗"
                formatted_value = (
                    f"<span style='color:{'green' if value else 'red'}'>{icon}</span>"
                )
            else:
                formatted_value = str(value)

            # Add to fields dict if not already present
            label = field_name.replace("_", " ").title()
            if label not in all_fields:
                all_fields[label] = formatted_value

        # Convert fields dict to HTML table rows
        for label, value in all_fields.items():
            fields_html += f"""
            <tr>
                <th style="text-align:left; padding:8px; background:#f8f8f8; width:150px;">{label}</th>
                <td style="padding:8px;">{value}</td>
            </tr>
            """

        # Create HTML for the detail view
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>{title} | Django site admin</title>
            <link rel="stylesheet" href="/static/admin/css/base.css">
            <link rel="stylesheet" href="/static/admin/css/responsive.css">
            <style>
                pre {{
                    max-height: 200px;
                    overflow-y: auto;
                    padding: 8px;
                    background: #f5f5f5;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    white-space: pre-wrap;
                    word-break: break-all;
                }}
                table.data-table {{
                    width: 100%;
                    border-spacing: 0;
                    border-collapse: collapse;
                    margin-top: 20px;
                }}
                table.data-table td, table.data-table th {{
                    padding: 8px;
                    border-bottom: 1px solid #eee;
                    vertical-align: top;
                }}
                a {{
                    color: #447e9b;
                    text-decoration: none;
                }}
                a:hover {{
                    color: #036;
                }}
                .breadcrumbs {{
                    background: #f8f8f8;
                    padding: 10px;
                    border-bottom: 1px solid #eee;
                    margin-bottom: 15px;
                }}
                .breadcrumbs a {{
                    margin: 0 5px;
                }}
                .object-tools {{
                    float: right;
                    margin-top: -40px;
                }}
                .object-tools a {{
                    display: inline-block;
                    padding: 4px 12px;
                    background: #79aec8;
                    color: #fff;
                    border-radius: 4px;
                    margin-left: 8px;
                }}
                .object-tools a:hover {{
                    background: #417690;
                }}
            </style>
        </head>
        <body class="app-{app_label} model-{model_name} change-form" data-admin-utc-offset="0">
            <div id="container">
                <!-- Header -->
                <div id="header">
                    <div id="branding">
                        <h1 id="site-name"><a href="/admin/">Django administration</a></h1>
                    </div>
                    <div id="user-tools">
                        Welcome, <strong>{request.user.username}</strong>.
                        <a href="/admin/password_change/">Change password</a> /
                        <a href="/admin/logout/">Log out</a>
                    </div>
                </div>
                
                <!-- Breadcrumbs -->
                <div class="breadcrumbs">
                    <a href="/admin/">Home</a> &rsaquo;
                    <a href="/admin/{app_label}/">{app_label.title()}</a> &rsaquo;
                    <a href="/admin/{app_label}/{model_name}/">{self.model._meta.verbose_name_plural}</a> &rsaquo;
                    {str(obj)}
                </div>
                
                <!-- Main content -->
                <div id="content" class="flex">
                    <h1>{title}</h1>
                    
                    <div class="module aligned">
                        <table class="data-table">
                            {fields_html}
                        </table>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        from django.http import HttpResponse

        return HttpResponse(html)

    def get_object(self, request, object_id, from_field=None):
        """Get the MongoDB object by ID"""
        if self.mongo_model is None:
            return None

        try:
            # Direct MongoDB query
            return self.mongo_model.objects.get(id=object_id)
        except Exception:
            return None

    def get_urls(self):
        """Override URLs to handle our custom detail view"""
        from django.urls import path

        # Get the default admin URLs
        urls = super().get_urls()

        # Add our custom detail view URL
        custom_urls = [
            path(
                "<path:object_id>/",
                self.admin_site.admin_view(self.detail_view),
                name=f"{self.model._meta.app_label}_{self.model._meta.model_name}_change",
            ),
        ]

        return custom_urls + urls


# Admin classes for MongoDB documents
class UserAdmin(MongoDBAdmin):
    mongo_model = User
    list_display = (
        "get_id",
        "get_email",
        "get_is_active",
        "get_is_staff",
        "get_date_joined",
    )
    search_fields = ("email",)
    # Remove list_filter for now as it causes issues with proxy models
    list_filter = ()

    def changelist_view(self, request, extra_context=None):
        """Override changelist view to make email clickable"""
        response = super().changelist_view(request, extra_context)

        # If this is a direct HttpResponse (our custom HTML), we need to modify it
        if hasattr(response, "content") and response is not None and isinstance(response.content, bytes):
            html_content = response.content.decode("utf-8")

            # Make the email cells clickable - find td cells containing the email
            import re

            # Update the email cells to include links to the user detail page
            # Find all table rows in the result table with the specific class 'row1' or 'row2'
            pattern = r'<tr class=[\'"](?:row1|row2)[\'"]>(.*?)</tr>'
            rows = re.findall(pattern, html_content, re.DOTALL)

            for row_html in rows:
                # Extract the user ID from the first cell
                id_match = re.search(r"<td>(.*?)</td>", row_html)
                if not id_match:
                    continue

                user_id = id_match.group(1).strip()

                # Find the email cell (second cell)
                email_match = re.search(r"<td>(.*?)</td>.*?<td>", row_html, re.DOTALL)
                if not email_match:
                    continue

                email = email_match.group(1).strip()

                # Create a link for the email cell
                email_link = (
                    f'<a href="/admin/accounts/userproxy/{user_id}/">{email}</a>'
                )

                # Replace the plain email with the link in the row HTML
                new_row_html = row_html.replace(
                    f"<td>{email}</td>", f"<td>{email_link}</td>", 1
                )

                # Replace the original row in the full HTML
                html_content = html_content.replace(row_html, new_row_html)

        if response is None:
            return Response(                                                  
                {"error": "Response is none" },                        
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
)                                                                 
        new_response = HttpResponse(
                content=html_content.encode('utf-8'),
                content_type=response.get("Content-Type", 'text/html')
        )

        for key, value in response.items():
            new_response[key] = value

        return new_response

    def get_email(self, obj):
        return obj.email

    get_email.short_description = "Email"

    def get_is_active(self, obj):
        icon = "✓" if obj.is_active else "✗"
        color = "green" if obj.is_active else "red"
        return f'<span style="color:{color};font-weight:bold;">{icon}</span>'

    get_is_active.short_description = "Active"
    get_is_active.allow_tags = True

    def get_is_staff(self, obj):
        icon = "✓" if obj.is_staff else "✗"
        color = "green" if obj.is_staff else "red"
        return f'<span style="color:{color};font-weight:bold;">{icon}</span>'

    get_is_staff.short_description = "Staff"
    get_is_staff.allow_tags = True

    def get_date_joined(self, obj):
        return obj.date_joined.strftime("%Y-%m-%d %H:%M") if obj.date_joined else "N/A"

    get_date_joined.short_description = "Date Joined"


class EmployeeProfileAdmin(MongoDBAdmin):
    mongo_model = EmployeeProfile
    list_display = (
        "get_id",
        "get_employee_id",
        "get_name",
        "get_department",
        "get_position",
        "get_user",
        "get_manager",
    )
    search_fields = ("employee_id", "first_name", "last_name")
    # Remove list_filter for now as it causes issues with proxy models
    list_filter = ()

    def get_employee_id(self, obj):
        return obj.employee_id

    get_employee_id.short_description = "Employee ID"

    def get_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    get_name.short_description = "Name"

    def get_department(self, obj):
        return obj.department

    get_department.short_description = "Department"

    def get_position(self, obj):
        return obj.position

    get_position.short_description = "Position"

    @MongoDBAdmin.reference_field(app="accounts", model="userproxy")
    def get_user(self, obj):
        return obj.user

    get_user.short_description = "User"

    @MongoDBAdmin.reference_field(app="accounts", model="employeeprofileproxy")
    def get_manager(self, obj):
        return obj.manager

    get_manager.short_description = "Manager"


class ExpenseSettingsAdmin(MongoDBAdmin):
    mongo_model = ExpenseSettings
    list_display = (
        "get_id",
        "get_user",
        "get_currency",
        "get_expense_limit",
        "get_approver",
    )
    # Remove list_filter for now as it causes issues with proxy models
    list_filter = ()

    @MongoDBAdmin.reference_field(app="accounts", model="userproxy")
    def get_user(self, obj):
        return obj.user

    get_user.short_description = "User"

    @MongoDBAdmin.reference_field(app="accounts", model="userproxy")
    def get_approver(self, obj):
        return obj.expense_approver

    get_approver.short_description = "Approver"

    def get_currency(self, obj):
        return obj.default_currency

    get_currency.short_description = "Currency"

    def get_expense_limit(self, obj):
        return obj.monthly_expense_limit

    get_expense_limit.short_description = "Monthly Limit"


# Register the proxy models with their admin classes
admin.site.register(UserProxy, UserAdmin)
admin.site.register(EmployeeProfileProxy, EmployeeProfileAdmin)
admin.site.register(ExpenseSettingsProxy, ExpenseSettingsAdmin)


# Register the BlacklistedToken model with Django's default admin
@admin.register(BlacklistedToken)
class BlacklistedTokenAdmin(admin.ModelAdmin):
    """Admin class for BlacklistedToken model"""

    list_display = ("token_jti", "user_id", "blacklisted_at", "expires_at")
    list_filter = ("blacklisted_at", "expires_at")
    search_fields = ("token_jti", "user_id")
    date_hierarchy = "blacklisted_at"

    actions = ["clean_expired_tokens"]

    def clean_expired_tokens(self, request, queryset):
        """Admin action to clean expired tokens"""
        from django.utils import timezone

        expired_count = BlacklistedToken.objects.filter(
            expires_at__lt=timezone.now()
        ).count()
        BlacklistedToken.clean_expired_tokens()

        self.message_user(
            request, f"Successfully removed {expired_count} expired tokens."
        )

    clean_expired_tokens.short_description = "Remove expired tokens"
