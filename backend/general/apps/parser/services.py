import json
import requests
from django.conf import settings
from rest_framework import status

class ParserServiceError(Exception):
    """Custom exception for parser service errors"""
    def __init__(self, message, status_code=None, detail=None):
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.message)

class ParserService:
    """Service for communicating with the File Parsing Server"""
    
    def __init__(self):
        self.base_url = settings.FILE_PARSER_SERVER_URL
    
    def _handle_response(self, response):
        """Process the response from the File Parsing Server"""
        if 200 <= response.status_code < 300:
            try:
                return response.json()
            except json.JSONDecodeError:
                return response.content
        
        error_detail = None
        try:
            error_detail = response.json()
        except:
            error_detail = response.text
            
        raise ParserServiceError(
            f"Parser service error: {response.status_code}",
            status_code=response.status_code,
            detail=error_detail
        )
    
    def parse_receipt(self, file_obj, metadata, user_token=None):
        """Parse a receipt using the File Parsing Server (blocking request)"""
        url = f"{self.base_url}/api/parser/parse/"
        
        # Prepare multipart form data
        files = {'file': file_obj}
        
        # Prepare headers
        from common.json_utils import MongoJSONEncoder
        
        headers = {}

        # Add metadata
        headers['X-Receipt-Metadata'] = json.dumps(metadata, cls=MongoJSONEncoder)
        
        # Forward the user's JWT token if provided
        if user_token:
            headers['Authorization'] = f'Bearer {user_token}'
        
        # Make the request (blocks until processing is complete)
        response = requests.post(url, files=files, headers=headers)
        return self._handle_response(response)
    
    def get_job_status(self, job_id, user_token):
        """Get the status of a processing job"""
        url = f"{self.base_url}/api/parser/status/{job_id}/"
        headers = {}

        if user_token:
            headers['Authorization'] = f'Bearer {user_token}'
        else:
            raise ParserServiceError("User token required to confirm job")

        response = requests.get(url, headers=headers)
        return self._handle_response(response)
    
    def confirm_job(self, job_id, corrections, user_token):
        """Confirm a processed receipt with optional corrections"""
        url = f"{self.base_url}/api/parser/confirm/{job_id}/"
        
        # Use MongoJSONEncoder to handle ObjectId and Decimal
        from common.json_utils import MongoJSONEncoder
        
        # Add corrections if provided
        data = {}
        if corrections:
            data['corrections'] = corrections
            
        # Prepare headers
        headers = {}
        headers['Content-Type'] = 'application/json'
        
        # Forward the user's JWT token if provided
        if user_token:
            headers['Authorization'] = f'Bearer {user_token}'
        else:
            raise ParserServiceError("User token required to confirm job")
        
        # Convert to JSON-safe format
        data_str = json.dumps(data, cls=MongoJSONEncoder)
        
        response = requests.post(url, data=data_str, headers=headers)
        return self._handle_response(response)
    
    def discard_job(self, job_id, user_token):
        """Discard a processing job"""
        url = f"{self.base_url}/api/parser/discard/{job_id}/"
        
        # Prepare headers
        headers = {}
        
        # Forward the user's JWT token if provided
        if user_token:
            headers['Authorization'] = f'Bearer {user_token}'
        else:
            raise ParserServiceError("User token required to discard job")
        
        response = requests.delete(url, headers=headers)
        return self._handle_response(response)
