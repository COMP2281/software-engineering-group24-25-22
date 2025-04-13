from django.urls import path
from .views import (
    ParseReceiptView,
    JobStatusView,
    ConfirmJobView,
    DiscardJobView,
    GetAllJobs,
)

app_name = "jobs"

urlpatterns = [
    path("parse/", ParseReceiptView.as_view(), name="parse-receipt"),
    path("status/<str:id>/", JobStatusView.as_view(), name="job-status"),
    path("confirm/<str:id>/", ConfirmJobView.as_view(), name="confirm-job"),
    path("discard/<str:id>/", DiscardJobView.as_view(), name="discard-job"),
    path("all/", GetAllJobs.as_view(), name="list-jobs"),
]
