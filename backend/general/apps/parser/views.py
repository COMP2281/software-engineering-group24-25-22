import json
from rest_framework import status
from rest_framework.fields import empty
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from .services import ParserService, ParserServiceError
from .serializers import ReceiptUploadSerializer, ConfirmJobSerializer
from bson import ObjectId

class ReceiptParseView(APIView):
    """
    API endpoint for parsing receipts (blocking until processing completes)
    """
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Validate the uploaded file
        serializer = ReceiptUploadSerializer(data=request.data)
        if (not serializer.is_valid()) or (serializer.validated_data is None) or (isinstance(serializer.validated_data, empty)):
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        file_obj = serializer.validated_data['file']

        if not file_obj: 
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Prepare metadata for the File Parsing Server
        metadata = {
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
        
        # Get user's JWT token to forward to parser service
        auth_header = request.headers.get('Authorization')
        user_token = None
        
        if auth_header and auth_header.startswith('Bearer '):
            user_token = auth_header.split(' ')[1]
            
        try:
            parser_service = ParserService()
            # This will block until processing is complete
            result = parser_service.parse_receipt(file_obj, metadata, user_token)
            
            # Return the complete processed data
            return Response(result, status=status.HTTP_200_OK)
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
        auth_header = request.headers.get('Authorization')
        user_token = None
        
        if auth_header and auth_header.startswith('Bearer '):
            user_token = auth_header.split(' ')[1]

        try:

            parser_service = ParserService()
            result = parser_service.get_job_status(job_id, user_token)
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
    parser_classes = (JSONParser,)
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, job_id):
        # Validate the request data
        serializer = ConfirmJobSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid data format', 'details': serializer.errors}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Get the validated data
        valid_data = serializer.validated_data
        
        try:
            # Get corrections from request if any
            corrections = valid_data.get('corrections', {})
            descriptions = valid_data.get('descriptions', {})
            
            # Get user's JWT token
            auth_header = request.headers.get('Authorization')
            user_token = None
            
            if auth_header and auth_header.startswith('Bearer '):
                user_token = auth_header.split(' ')[1]
                
            parser_service = ParserService()
            result = parser_service.confirm_job(
                job_id, 
                corrections,
                user_token
            )
            
            # If confirmation successful, create a Receipt record in our database
            from apps.receipts.models import Receipt
            from datetime import datetime
            from decimal import Decimal
            from django.utils import timezone

            # Ensure result is properly decoded
            if isinstance(result, bytes):
                try:
                    result = json.loads(result.decode('utf-8'))
                except json.JSONDecodeError:
                    # If we can't decode as JSON, return as is
                    return Response({"message": "Receipt confirmed", "data": result})
            
            # Extract data from the parser response
            extracted_data = result.get('extracted_data', {})
            user_corrections = result.get('user_corrections', {})

            print(json.dumps(result, indent=3))

            gridfs_id = result.get('gridfs_id', False)
            gridfs_ext = result.get('gridfs_ext', False)

            print("gridfs_ext", gridfs_ext)

            if not gridfs_id or not gridfs_ext: 
                raise ParserServiceError("No file data found in response", status_code=500)

            print("extracted_data", extracted_data)
            print("user_corrections", user_corrections)
            
            # Combine extracted data with user corrections to get final data
            final_data = {**extracted_data}
            if descriptions:
                final_data.update(descriptions)
            if user_corrections:
                final_data.update(user_corrections)
            
            # Parse date string to datetime object
            transaction_time = None
            date_str = final_data.get('transaction_time')
            if date_str:
                try:
                    # Try different date formats
                    date_formats = [
                        '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', 
                        '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S'
                    ]
                    
                    for fmt in date_formats:
                        try:
                            transaction_time = datetime.strptime(date_str, fmt)
                            break
                        except ValueError:
                            continue
                except Exception as e:
                    # Fallback to current time if date parsing fails
                    transaction_time = timezone.now()
            else:
                transaction_time = timezone.now()

            # Convert decimal strings to Decimal objects
            total_amount = Decimal(str(final_data.get('total_amount', '0.00') or '0.00'))
            tax_amount = Decimal(str(final_data.get('tax_amount', '0.00') or '0.00'))
            subtotal_amount = Decimal(str(final_data.get('subtotal_amount', '0.00') or '0.00'))
            
            # Create the Receipt instance
            receipt = Receipt(
                merchant_name=final_data.get('merchant_name', 'Unknown Merchant'),
                transaction_time=transaction_time,
                merchant_address=final_data.get('merchant_address', ''),
                reference_number=final_data.get('reference_number', ''),
                tax_amount=tax_amount,
                category=final_data.get('category', 'Uncategorized'),
                description=final_data.get('description', ''),
                total_amount=total_amount,
                subtotal_amount=subtotal_amount,
                currency=final_data.get('currency', 'GBP'),
                employee=request.user,
                status="pending",
                upload_date=timezone.now(),
                file_ext=gridfs_ext,
                template_correspondence=final_data.get('template_correspondence', 0.0),
                updated_at=timezone.now()
            )

            print("gridfs_ext", gridfs_ext)
            receipt.file.grid_id = ObjectId(gridfs_id)

            # Use whichever has items
            items_to_process = final_data.get("cost_items", [])           
            print(items_to_process)
            # Create embedded cost items
            for item in items_to_process:
                # Handle both API and internal format field names
                item_name = item.get('item_name', "Unknown Item")
                unit_price = item.get('unit_price', '0.00')
                # API format uses 'total', internal format uses 'total_price'
                total_price = item.get('total_price', item.get('total', '0.00'))
                # Handle different quantity field names and formats
                quantity = item.get('quantity', '1')
                
                # Add item to receipt using helper method
                receipt.add_cost_item(
                    item_name=item_name,
                    unit_price=Decimal(str(unit_price or '0.00')),
                    quantity=Decimal(str(quantity or '1')),
                    total_price=Decimal(str(total_price or '0.00'))
                )

            receipt.save()
            
            # Add receipt to the result
            result['receipt_id'] = str(receipt.pk)
            
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
            # Get user's JWT token
            auth_header = request.headers.get('Authorization')
            user_token = None
            
            if auth_header and auth_header.startswith('Bearer '):
                user_token = auth_header.split(' ')[1]
                
            parser_service = ParserService()
            parser_service.discard_job(job_id, user_token=user_token)
            return Response({'success': True})
        except ParserServiceError as e:
            return Response(
                {'error': str(e), 'detail': e.detail}, 
                status=e.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR
            )
