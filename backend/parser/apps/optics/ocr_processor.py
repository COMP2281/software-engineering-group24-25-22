import os
import logging
import tempfile
from PIL import Image
from pathlib import Path
from django.utils import timezone
from django.conf import settings

from apps.jobs.models import ProcessingJob
from apps.jobs.utils import temp_file_path

logger = logging.getLogger(__name__)

class OCRProcessorError(Exception):
    """Custom exception for OCR processor errors"""
    pass

class OCRProcessor:
    """
    Class for OCR processing of receipt images using the template system.
    Handles different file types and extracts structured data.
    """

    job:ProcessingJob
    
    def __init__(self, job: ProcessingJob):
        """
        Initialize processor with an optional job instance.
        
        Args:
            job: Optional ProcessingJob instance. If provided, results will be
                 stored in the job record.
        """
        self.job = job
        self.temp_file_path = temp_file_path(job, job.original_filename)
    
    def process_file(self):
        """
        Main processing method that delegates to appropriate handler
        based on file type.
        
        Args:
            file_path: Optional path to file (if not using job)
            file_type: Optional file MIME type (if not using job)
            
        Returns:
            dict: Extracted data from the receipt
        """

        # Process based on file type
        if 'image' in self.job.file_type:
            result = self._process_image(self.temp_file_path)
        elif 'pdf' in self.job.file_type:
            result = self._process_pdf(self.temp_file_path)
        elif 'json' in self.job.file_type:
            result = self._process_json(self.temp_file_path)
        else:
            raise OCRProcessorError(f"Unsupported file type: {self.job.file_type}")
        
        # Store results in job if available
        if self.job:
            self.job.processed_data = result
            self.job.save()
        
        return result
        # try:
        #     # If using a job, get file details from there
        #     if self.job:
        #         file_path = self.job.uploaded_file.path
        #         file_type = self.job.file_type.lower()
        #     elif not file_path or not file_type:
        #         raise OCRProcessorError("Either job or file_path and file_type must be provided")
        #     else:
        #         file_type = file_type.lower()
        #
        #     # Process based on file type
        #     if 'image' in file_type:
        #         result = self._process_image(file_path)
        #     elif 'pdf' in file_type:
        #         result = self._process_pdf(file_path)
        #     elif 'json' in file_type:
        #         result = self._process_json(file_path)
        #     else:
        #         raise OCRProcessorError(f"Unsupported file type: {file_type}")
        #
        #     # Store results in job if available
        #     if self.job:
        #         self.job.processed_data = result
        #         self.job.save()
        #
        #     return result
        #
        # except Exception as e:
        #     logger.error(f"Error processing file: {e}")
        #     if self.job:
        #         self.job.error_message = str(e)
        #         self.job.save()
        #     raise OCRProcessorError(f"Processing failed: {str(e)}")
    
    def _process_image(self, image_path):
        """
        Process an image file using OCR and template matching
        
        Args:
            image_path: Path to the image file
            
        Returns:
            dict: Extracted data from the receipt
        """
        import pytesseract
        from PIL import Image
        from .services import TemplateSuite
        
        logger.info(f"Processing image: {image_path}")
        
        try:
            # 1. Preprocess the image (resize, enhance, etc.)
            # This would include image enhancement code in a real implementation
            
            # 2. Run OCR to extract text
            try:
                # Open the image using PIL
                image = Image.open(image_path)
                
                # Run OCR on the image (using pytesseract in a real implementation)
                # ocr_text = pytesseract.image_to_string(image)
                
                # For demo purposes, simulate OCR text
                ocr_text = """Example Store
123 Main St
Date: 02/15/2025
Register: 2
--------------------------
1 Sample Item      $42.99
--------------------------
Subtotal:         $42.99
Tax:               $3.01
Total:            $46.00
"""
            except Exception as e:
                logger.error(f"OCR error: {str(e)}")
                raise OCRProcessorError(f"Failed to extract text from image: {str(e)}")
            
            # 3. Use the TemplateSuite directly to process the extracted text
            # This leverages the existing template matching and data extraction logic
            result = TemplateSuite.parse_receipt(ocr_text)
            
            if 'error' in result:
                raise OCRProcessorError(f"Failed to parse receipt: {result.get('error', 'Unknown error')}")
            
            # Get data from response
            extracted_data = result.get('extracted_data', {})
            confidence = result.get('confidence', 0) / 100  # Convert percentage to decimal
            template_id = result.get('template_id')
            needs_review = result.get('needs_review', True)
            
            # Store results in job if available
            if self.job:
                self.job.ocr_confidence = confidence
                self.job.needs_review = needs_review
                if template_id:
                    self.job.template_used = str(template_id)
                
                # Store the OCR text in job metadata for template learning
                if 'metadata' in dir(self.job) and hasattr(self.job, 'metadata'):
                    self.job.metadata['ocr_text'] = ocr_text
            
            # Convert from API format to internal format
            processed_data = TemplateSuite.convert_to_internal_format(extracted_data)
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Image processing error: {str(e)}")
            
            # If we have a job, mark it for review since extraction failed
            if self.job:
                self.job.needs_review = True
                self.job.ocr_confidence = 0.0
            
            # Return fallback data
            return {
                'merchant_name': "Error extracting data",
                'transaction_time': timezone.now().isoformat(),
                'total_amount': '',
                'currency': '',
                'error': str(e)
            }
    
    def _process_pdf(self, pdf_path):
        """
        Process a PDF file by converting to image and running OCR
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            dict: Extracted data from the receipt
        """
        logger.info(f"Processing PDF: {pdf_path}")
        
        # In a real implementation, this would:
        # 1. Convert PDF to images
        # 2. Process each page as an image
        # 3. Combine results if needed
        
        # For simulation, we'll return placeholder data with lower confidence
        
        # Set confidence level
        confidence = 0.75
        
        # Store confidence if using a job
        if self.job:
            self.job.ocr_confidence = confidence
            self.job.needs_review = True  # Always need review for PDFs
        
        # Return simulated extraction results
        return {
            'merchant_name': 'PDF Example Corp',
            'transaction_time': timezone.now().isoformat(),
            'total_amount': '123.45',
            'currency': 'USD',
            'line_items': [
                {'item_name': 'PDF Item 1', 'quantity': 2, 'unit_price': '50.00', 'total_price': '100.00'},
                {'item_name': 'PDF Item 2', 'quantity': 1, 'unit_price': '23.45', 'total_price': '23.45'}
            ]
        }
    
    def _process_json(self, json_path):
        """
        Process a JSON file containing receipt data
        
        Args:
            json_path: Path to the JSON file
            
        Returns:
            dict: The parsed JSON data
        """
        import json
        logger.info(f"Processing JSON: {json_path}")
        
        # For JSON, we can just load the data directly
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        # Set confidence to 1.0 (perfect) for JSON
        if self.job:
            self.job.ocr_confidence = 1.0
            self.job.needs_review = False
        
        return data
