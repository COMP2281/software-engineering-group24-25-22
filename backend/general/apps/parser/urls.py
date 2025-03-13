from django.urls import path
from .views import (
    ReceiptParseView,
    JobStatusView, 
    ConfirmJobView, 
    DiscardJobView, 
)

urlpatterns = [
    path('parse/', ReceiptParseView.as_view(), name='receipt-parse'),
    path('status/<str:job_id>/', JobStatusView.as_view(), name='job-status'),
    path('confirm/<str:job_id>/', ConfirmJobView.as_view(), name='confirm-job'),
    path('discard/<str:job_id>/', DiscardJobView.as_view(), name='discard-job'),
]
