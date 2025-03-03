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
        self.api_key = settings.FILE_PARSER_API_KEY
        self.headers = {
            'Authorization': f'ApiKey {self.api_key}',
            'Accept': 'application/json',
        }
    
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
    
    def upload_receipt(self, file_obj, metadata):
        """Upload a receipt to the File Parsing Server"""
        url = f"{self.base_url}/api/parser/upload/"
        
        # Prepare multipart form data
        files = {'file': file_obj}
        
        # Send metadata as JSON
        headers = self.headers.copy()
        headers['X-Receipt-Metadata'] = json.dumps(metadata)
        
        response = requests.post(url, files=files, headers=headers)
        return self._handle_response(response)
    
    def get_job_status(self, job_id):
        """Get the status of a processing job"""
        url = f"{self.base_url}/api/parser/status/{job_id}/"
        response = requests.get(url, headers=self.headers)
        return self._handle_response(response)
    
    def confirm_job(self, job_id, user_id):
        """Confirm a processed receipt"""
        url = f"{self.base_url}/api/parser/confirm/{job_id}/"
        data = {'user_id': user_id}
        
        response = requests.post(url, json=data, headers=self.headers)
        return self._handle_response(response)
    
    def discard_job(self, job_id):
        """Discard a processing job"""
        url = f"{self.base_url}/api/parser/discard/{job_id}/"
        
        response = requests.delete(url, headers=self.headers)
        return self._handle_response(response)
    
    def edit_job_data(self, job_id, validated_data):
        """Edit the data extracted from a receipt"""
        url = f"{self.base_url}/api/parser/edit/{job_id}/"
        
        response = requests.post(
            url, 
            json=validated_data,
            headers=self.headers
        )
        return self._handle_response(response)
