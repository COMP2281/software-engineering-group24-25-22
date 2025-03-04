from django.urls import path
from .views import ReceiptParseView, ReceiptCorrectionView, TemplateMaintenanceView

app_name = 'optics'

urlpatterns = [
    path('parse/', ReceiptParseView.as_view(), name='receipt-parse'),
    path('correct/', ReceiptCorrectionView.as_view(), name='receipt-correction'),
    path('maintenance/', TemplateMaintenanceView.as_view(), name='template-maintenance'),
]