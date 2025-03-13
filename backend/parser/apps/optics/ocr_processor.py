import os
import logging
import tempfile
from typing import Optional
from PIL import Image
from pathlib import Path
from django.utils import timezone
from django.conf import settings
import json

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
        self.temp_file_path = temp_file_path(job)
    
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
            print("------------------------- PROCESSED DATA -----------------------")
            print(json.dumps(result))
            print("------------------------- PROCESSED DATA END -------------------")
            self.job.extracted_data = result
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
    
    def _process_image(self, image_path: Optional[str] = None, image_pil: Optional[Image.Image] = None):
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
                image: Image.Image

                if image_path and isinstance(image_path, str):
                    image = Image.open(image_path)
                elif image_pil and isinstance(image_pil, Image.Image):
                    image = image_pil
                else: 
                    OCRProcessorError("No image provided")
                
                # Run OCR on the image (using pytesseract in a real implementation)
                ocr_text = pytesseract.image_to_string(image)
                
                # For demo purposes, simulate OCR text
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
            template_correspondence = result.get('correspondence', 0) / 100  # Convert percentage to decimal
            template_id = result.get('template_id')
            
            # Store results in job if available
            if self.job:
                self.job.template_correspondence = template_correspondence
                if template_id:
                    self.job.template_used = str(template_id)
                
                # Store the OCR text in job metadata for template learning
                if 'metadata' in dir(self.job) and hasattr(self.job, 'metadata'):
                    self.job.metadata['ocr_text'] = ocr_text
                    self.job.metadata['ocr_text_preprocessed'] = TemplateSuite.preprocess_ocr_text(ocr_text)
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"Image processing error: {str(e)}")
            
            # If we have a job, mark it for review since extraction failed
            if self.job:
                self.job.template_correspondence = 0.0
            
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
        from pdf2image import convert_from_path
        logger.info(f"Processing PDF: {pdf_path}")
        
        return self._process_image(image_pil=convert_from_path(pdf_path)[0])
    
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
        
        # Set correspondence to 1.0 (perfect) for JSON
        if self.job:
            self.job.template_correspondence = 2.0
        
        return data
