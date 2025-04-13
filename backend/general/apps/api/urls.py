from django.urls import path, include

urlpatterns = [
    path("auth/", include("apps.accounts.urls")),
    path("", include("apps.receipts.urls")),
    path("parser/", include("apps.parser.urls")),
]
