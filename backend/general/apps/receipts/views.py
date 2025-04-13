from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
import csv
from .serializers import ReceiptSerializer
from .models import Receipt


class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of a receipt to view or edit it
    """

    def has_object_permission(self, request, view, obj):
        return obj.employee == request.user


class ReceiptViewSet(viewsets.ModelViewSet):
    serializer_class = ReceiptSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        """
        This view returns a list of all receipts for the currently authenticated user.
        """
        # mongoengine syntax for querying
        queryset = Receipt.objects(employee=self.request.user)
        queryset.model = Receipt
        return queryset

    def get_object(self):
        """Override get_object to handle permissions properly"""
        # Get the object ID from the URL
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        obj_id = self.kwargs[lookup_url_kwarg]

        # Get the specific object
        obj = Receipt.objects.get(id=obj_id)

        # Check permissions
        self.check_object_permissions(self.request, obj)

        return obj

    def perform_create(self, serializer):
        """
        Override to set the employee automatically to the current user
        """
        serializer.save(employee=self.request.user)

    @action(detail=False, methods=["get"])
    def export(self, request):
        """
        Export receipts to CSV or JSON format with filtering options
        """
        format_type = request.query_params.get("format", "csv")

        # Start with all receipts for the current user
        queryset = Receipt.objects(employee=self.request.user)

        # Date range filtering
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        if start_date:
            queryset = queryset(transaction_time__gte=start_date)
        if end_date:
            queryset = queryset(transaction_time__lte=end_date)

        # Category filtering
        category = request.query_params.get("category")
        if category:
            queryset = queryset(category=category)

        # Status filtering
        status = request.query_params.get("status")
        if status:
            queryset = queryset(status=status)

        # Limit results
        limit = request.query_params.get("limit")
        if limit and limit.isdigit():
            queryset = queryset[: int(limit)]

        if format_type.lower() == "json":
            # JSON export
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        else:
            # CSV export (default)
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = (
                'attachment; filename="receipts_export.csv"'
            )

            writer = csv.writer(response)
            # Write header
            writer.writerow(
                [
                    "ID",
                    "Merchant",
                    "Date",
                    "Category",
                    "Description",
                    "Total Amount",
                    "Currency",
                    "Tax Amount",
                    "Status",
                ]
            )

            # Write data
            for receipt in queryset:
                writer.writerow(
                    [
                        receipt.pk,
                        receipt.merchant_name,
                        receipt.transaction_time.strftime("%Y-%m-%d %H:%M"),
                        receipt.category,
                        receipt.description,
                        receipt.total_amount,
                        receipt.currency,
                        receipt.tax_amount or "",
                        receipt.status,
                    ]
                )

            return response
