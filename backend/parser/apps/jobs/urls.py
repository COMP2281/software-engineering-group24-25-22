from django.urls import path
from .views import (
    UploadReceiptView,
    JobStatusView,
    ConfirmJobView,
    DiscardJobView,
    EditJobDataView
)

app_name = 'jobs'

urlpatterns = [
    path('upload/', UploadReceiptView.as_view(), name='upload-receipt'),
    path('status/<str:job_id>/', JobStatusView.as_view(), name='job-status'),
    path('confirm/<str:job_id>/', ConfirmJobView.as_view(), name='confirm-job'),
    path('discard/<str:job_id>/', DiscardJobView.as_view(), name='discard-job'),
    path('edit/<str:job_id>/', EditJobDataView.as_view(), name='edit-job-data'),
]