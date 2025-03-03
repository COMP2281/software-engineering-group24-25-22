import json
from rest_framework import status
from rest_framework.fields import empty
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from .services import ParserService, ParserServiceError
from .serializers import ReceiptUploadSerializer, ReceiptDataSerializer

class ReceiptUploadView(APIView):
    """
    API endpoint for uploading receipts for processing
    """
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Validate the uploaded file
        serializer = ReceiptUploadSerializer(data=request.data)
        if (not serializer.is_valid()) or (serializer.validated_data is None) or (not isinstance(serializer.validated_data, empty)):
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        file_obj = serializer.validated_data['file']

        if not file_obj: 
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Prepare metadata for the File Parsing Server
        metadata = {
            'user_id': request.user.id,
            'original_filename': file_obj.name,
            'file_size': file_obj.size,
            'content_type': file_obj.content_type,
        }
        
        # Add user profile information if available
        if hasattr(request.user, 'profile'):
            metadata.update({
                'employee_id': request.user.profile.employee_id,
                'department': request.user.profile.department,
                'name': request.user.profile.full_name
            })
            
        try:
            parser_service = ParserService()
            result = parser_service.upload_receipt(file_obj, metadata)
            return Response(result, status=status.HTTP_202_ACCEPTED)
        except ParserServiceError as e:
            return Response(
                {'error': str(e), 'detail': e.detail}, 
                status=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class JobStatusView(APIView):
    """
    API endpoint for checking the status of a processing job
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, job_id):
        try:
            parser_service = ParserService()
            result = parser_service.get_job_status(job_id)
            return Response(result)
        except ParserServiceError as e:
            return Response(
                {'error': str(e), 'detail': e.detail}, 
                status=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ConfirmJobView(APIView):
    """
    API endpoint for confirming processed receipt data
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, job_id):
        try:
            parser_service = ParserService()
            result = parser_service.confirm_job(job_id, request.user.id)
            
            # If confirmation successful, create a Receipt record in our database
            # (This would typically be done in a service layer)
            from apps.receipts.models import Receipt, CostItem

            # Ensure result is properly decoded
            if isinstance(result, bytes):
                try:
                    result = json.loads(result.decode('utf-8'))
                except json.JSONDecodeError:
                    # TODO: Improve the error handling.
                    # If we can't decode as JSON, return as is
                    return Response({"message": "Receipt confirmed", "data": result})
            
            receipt_data = result.get('receipt_data', {})
            
            # Create and return the formatted response
            return Response(result)
        except ParserServiceError as e:
            return Response(
                {'error': str(e), 'detail': e.detail}, 
                status=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class DiscardJobView(APIView):
    """
    API endpoint for discarding a processing job
    """
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, job_id):
        try:
            parser_service = ParserService()
            parser_service.discard_job(job_id)
            return Response({'success': True})
        except ParserServiceError as e:
            return Response(
                {'error': str(e), 'detail': e.detail}, 
                status=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class EditJobDataView(APIView):
    """
    API endpoint for editing processed receipt data
    """
    parser_classes = (JSONParser,)
    permission_classes = [IsAuthenticated]
    
    def post(self, request, job_id):
        # Validate input data
        serializer = ReceiptDataSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            parser_service = ParserService()
            result = parser_service.edit_job_data(job_id, serializer.validated_data)
            return Response(result)
        except ParserServiceError as e:
            return Response(
                {'error': str(e), 'detail': e.detail}, 
                status=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR
            )
