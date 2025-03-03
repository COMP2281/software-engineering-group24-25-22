from django.urls import path, include

urlpatterns = [
    # Authentication endpoints
    path('auth/', include('apps.accounts.urls')),
    # You'll add other API endpoints here later
]
