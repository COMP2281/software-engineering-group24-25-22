from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import timedelta
from django.utils import timezone
from django.db.models import Q, Sum

from .models import ReceiptTemplate
from .lib.templates import OCRTemplate, OCRTemplateCorrection

logger = logging.getLogger(__name__)


class TemplateSuite:
    """
    Comprehensive suite for managing receipt templates, including:
    - Template creation from user corrections
    - Finding and applying the best template for a receipt
    - Template lifecycle management (archiving/unarchiving)
    - Template performance tracking
    - Direct interfaces for parsing and correction
    - Data format conversion utilities
    """

    @staticmethod
    def find_template_candidates(merchant_name: str, limit: int = 5) -> List[ReceiptTemplate]:
        """
        Find potential template matches for a given merchant name.
        Uses fuzzy matching to handle variations in merchant names.

        Args:
            merchant_name: The merchant name to match
            limit: Maximum number of templates to return

        Returns:
            List of template objects sorted by relevance
        """
        # First, try exact match on active templates
        exact_matches = ReceiptTemplate.objects.filter(
            merchant_name__iexact=merchant_name,
            is_archived=False
        ).order_by('-usage_count')[:limit]

        if exact_matches.exists():
            return list(exact_matches)

        # If no exact match, try fuzzy match on active templates
        # This is a simplified fuzzy match using contains
        # In production, you would use a more sophisticated approach
        fuzzy_matches = ReceiptTemplate.objects.filter(
            merchant_name__icontains=merchant_name.split(
            )[0] if merchant_name.split() else "",
            is_archived=False
        ).order_by('-usage_count')[:limit]

        if fuzzy_matches.exists():
            return list(fuzzy_matches)

        # If still no matches, check archived templates
        archived_matches = ReceiptTemplate.objects.filter(
            Q(merchant_name__iexact=merchant_name) |
            Q(merchant_name__icontains=merchant_name.split()
              [0] if merchant_name.split() else ""),
            is_archived=True
        ).order_by('-usage_count')[:limit]

        if archived_matches.exists():
            return list(archived_matches)

        # If no matches at all, return generic templates
        # Assuming generic templates have merchant_name = 'Generic'
        generic_templates = ReceiptTemplate.objects.filter(
            merchant_name='Generic'
        ).order_by('-usage_count')[:limit]

        return list(generic_templates)

    @staticmethod
    def create_template_from_correction(ocr_text: str, corrected_values: OCRTemplateCorrection) -> ReceiptTemplate:
        """
        Create a new template based on user corrections.

        Args:
            ocr_text: The original OCR text
            corrected_values: User-corrected values

        Returns:
            Newly created template
        """
        # Create OCR template
        ocr_template = OCRTemplate(ocr_text, corrected_values)

        # Convert to model format
        template_data = ocr_template.to_model_data()

        # Create new template
        template = ReceiptTemplate(
            merchant_name=template_data['merchant_name'],
            currency_info=template_data['currency_info'],
            field_extractors=template_data['field_extractors'],
            item_patterns=template_data['item_patterns'],
            field_accuracy=template_data['field_accuracy'],
            usage_count=1,
            success_rate=80.0  # Initial success rate (optimistic)
        )

        template.save()
        logger.info(
            f"Created new template for {template_data['merchant_name']}")

        return template

    @staticmethod
    def extract_with_template(ocr_text: str, template: ReceiptTemplate) -> Dict[str, Any]:
        """
        Extract data from OCR text using a template.

        Args:
            ocr_text: The OCR text to extract from
            template: The template to use

        Returns:
            Extracted fields
        """
        # Record usage
        template.record_usage()

        # Create OCR template and extract fields
        ocr_template = OCRTemplate(ocr_text)

        # Build template data structure
        template_data = {
            'field_extractors': template.field_extractors,
            'item_patterns': template.item_patterns,
            'has_line_items': template.has_line_items
        }

        # Extract fields using the template
        extracted_data = ocr_template.extract_fields(template_data)

        # Update usage statistics periodically
        if template.usage_count % 10 == 0:  # Every 10 uses
            # Get total uses for this merchant
            total_merchant_uses = ReceiptTemplate.objects.filter(
                merchant_name=template.merchant_name
            ).aggregate(total=Sum('usage_count'))['total'] or 1

            # Update statistics
            template.update_recent_usage_stats(total_merchant_uses)

        return extracted_data

    @staticmethod
    def find_best_template(ocr_text: str, merchant_name: Optional[str] = None) -> Tuple[Optional[ReceiptTemplate], Dict[str, Any]]:
        """
        Find the best template for a receipt and extract fields.

        Args:
            ocr_text: The OCR text to extract from
            merchant_name: Optional merchant name hint

        Returns:
            Tuple of (best template, extracted data)
        """
        # If no merchant name provided, try to extract it
        if not merchant_name:
            ocr_lines = ocr_text.strip().split('\n')
            # Simple heuristic: use first line as merchant name
            merchant_name = ocr_lines[0].strip() if ocr_lines else "Unknown"

        # Find template candidates
        candidates = TemplateSuite.find_template_candidates(merchant_name)

        if not candidates:
            logger.warning(f"No template candidates found for {merchant_name}")
            return None, {}

        # Try each template and keep the one with most fields extracted
        best_template = None
        best_data = {}
        best_score = -1

        for template in candidates:
            extracted_data = TemplateSuite.extract_with_template(
                ocr_text, template)

            # Calculate extraction score (number of fields extracted)
            score = len([k for k, v in extracted_data.items() if v])

            if score > best_score:
                best_template = template
                best_data = extracted_data
                best_score = score

        return best_template, best_data

    @staticmethod
    def update_template_after_correction(template: ReceiptTemplate, ocr_text: str,
                                         extracted_data: Dict[str, Any],
                                         corrected_data: OCRTemplateCorrection) -> ReceiptTemplate:
        """
        Update template performance metrics after user correction.
        If needed, create new patterns based on the correction.

        Args:
            template: Template that was used
            ocr_text: Original OCR text
            extracted_data: Data extracted by the template
            corrected_data: User-corrected data

        Returns:
            Updated template
        """
        # Calculate accuracy for each field
        field_corrections = {}

        # Compare extracted vs corrected values
        for field in template.field_extractors.keys():
            extracted = extracted_data.get(field)
            corrected = None

            # Map field names between systems
            if field == 'merchant_name':
                corrected = corrected_data.get('merchant_name')
            elif field == 'transaction_time':
                corrected = corrected_data.get('date')
            elif field == 'merchant_address':
                corrected = corrected_data.get('address')
            elif field == 'reference_number':
                corrected = corrected_data.get('reference')
            elif field == 'tax_amount':
                corrected = corrected_data.get('tax')
            elif field == 'total_amount':
                corrected = corrected_data.get('total_amount')
            elif field == 'subtotal_amount':
                corrected = corrected_data.get('subtotal_amount')

            # If field was corrected, update accuracy and edit distance
            if corrected is not None and extracted != corrected:
                field_corrections[field] = False
                template.calculate_updated_accuracy(field, False)
                # Track edit distance between extracted and corrected values
                # Convert None to empty string if needed
                extracted_str = str(extracted) if extracted is not None else ""
                corrected_str = str(corrected)
                template.update_edit_distance(field, extracted_str, corrected_str)
            elif extracted is not None:
                field_corrections[field] = True
                template.calculate_updated_accuracy(field, True)
                # Even matching fields contribute to edit distance stats (with 0 distance)
                extracted_str = str(extracted)
                template.update_edit_distance(field, extracted_str, extracted_str)

        # Update overall success rate and override rate
        correct_fields = sum(
            1 for correct in field_corrections.values() if correct)
        total_fields = len(field_corrections)

        if total_fields > 0:
            field_accuracy = (correct_fields / total_fields) * 100
            override_percentage = (
                (total_fields - correct_fields) / total_fields) * 100

            # Update with weighted average: 70% historical, 30% new
            template.success_rate = (
                template.success_rate * 0.7) + (field_accuracy * 0.3)
            template.override_rate = (
                template.override_rate * 0.7) + (override_percentage * 0.3)

            # Make sure we save the updated metrics
            template.save(update_fields=['success_rate', 'override_rate',
                          'avg_edit_distance', 'field_edit_distances', 'field_accuracy'])

        # Count how many fields were corrected
        significant_corrections = sum(
            1 for correct in field_corrections.values() if not correct)

        if significant_corrections > 1:
            # For 2+ corrections, create a new template instead of updating the existing one
            new_template = TemplateSuite.create_template_from_correction(ocr_text, corrected_data)
            logger.info(f"Created new template from correction due to {significant_corrections} fields needing correction")
            
            # Return the new template instead of the updated one
            return new_template
        
        # For single field correction or no corrections, update the existing template
        if significant_corrections == 1:
            # Create a temporary template to extract the corrected pattern
            new_ocr_template = OCRTemplate(ocr_text, corrected_data)
            new_data = new_ocr_template.to_model_data()
            
            # Find which field was corrected
            corrected_field = None
            for field, correct in field_corrections.items():
                if not correct:
                    corrected_field = field
                    break
            
            # Update only the corrected field
            if corrected_field and corrected_field in new_data['field_extractors']:
                template.field_extractors[corrected_field] = new_data['field_extractors'][corrected_field]
                logger.info(f"Updated pattern for field '{corrected_field}' in template {template.pk}")
            
            # Update line item patterns if they were the corrected field
            if 'cost_items' in extracted_data and 'cost_list' in corrected_data:
                extracted_items = extracted_data.get('cost_items', [])
                corrected_items = corrected_data.get('cost_list', [])
                
                if len(extracted_items) != len(corrected_items) or corrected_field == 'cost_items':
                    # Line items were corrected
                    if new_data['item_patterns']:
                        template.item_patterns = new_data['item_patterns']
                        template.has_line_items = new_data['has_line_items']
                        if 'line_items_start_line' in new_data:
                            template.line_items_start_line = new_data['line_items_start_line']
                        logger.info(f"Updated line item patterns in template {template.pk}")

        # Save updated template
        template.save()

        return template

    @staticmethod
    def evaluate_templates_for_archiving():
        """
        Evaluate all templates against archiving criteria.
        Should be run as a scheduled task.
        """
        # Get active templates
        active_templates = ReceiptTemplate.objects.filter(is_archived=False)

        for template in active_templates:
            # Calculate flags using the model method
            flag_data = template.calculate_flags()
            flags = flag_data['flags']
            flag_count = flag_data['flag_count']

            # Use our flag-based decision system
            should_archive = (
                (flag_count >= 3) or
                (flags['age_flag'] and any([flags['usage_flag'], flags['override_flag'], flags['extraction_flag']])) or
                (flags['override_flag'] and flags['extraction_flag'])
            )

            if should_archive:
                template.archive()
                logger.info(
                    f"Archived template: {template.merchant_name} (ID: {template.pk})")

                # Log the reason for archiving
                reasons = [name for name, value in flags.items() if value]
                logger.info(f"Archive reasons: {', '.join(reasons)}")

    @staticmethod
    def cleanup_archived_templates():
        """
        Delete archived templates older than 2 months.
        Should be run as a scheduled task.
        """
        now = timezone.now()
        threshold_date = now - timedelta(days=60)

        old_archived_templates = ReceiptTemplate.objects.filter(
            is_archived=True,
            updated_at__lt=threshold_date
        )

        count = old_archived_templates.count()
        if count > 0:
            old_archived_templates.delete()
            logger.info(f"Deleted {count} old archived templates")

    @staticmethod
    def resurrect_template_if_needed(template_id: int):
        """
        Check if an archived template should be resurrected due to good performance.

        Args:
            template_id: ID of the template to check
        """
        try:
            template = ReceiptTemplate.objects.get(id=template_id)

            if template.is_archived and template.success_rate > 80:
                template.unarchive()
                logger.info(
                    f"Resurrected template: {template.merchant_name} (ID: {template.pk})")

                # Reset flags that led to archiving
                flag_data = template.calculate_flags()
                good_performance = [
                    f"{flag_name}: {value}"
                    for flag_name, value in flag_data['flags'].items()
                    if not value
                ]
                logger.info(
                    f"Template resurrected due to good metrics: {', '.join(good_performance)}")
        except ReceiptTemplate.DoesNotExist:
            logger.warning(
                f"Cannot resurrect template ID {template_id} - not found")
                
    @staticmethod
    def parse_receipt(ocr_text: str, merchant_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Direct interface for parsing a receipt using the best template.
        This avoids needing to use the view directly.
        
        Args:
            ocr_text: Raw OCR text from receipt
            merchant_name: Optional merchant name hint
            
        Returns:
            Dict with extracted data, confidence, and template info
        """
        # Find best template and extract data
        template, extracted_data = TemplateSuite.find_best_template(ocr_text, merchant_name)
        
        # If no template found or extraction failed, return error
        if not template or not extracted_data:
            return {
                "error": "Failed to parse receipt",
                "extracted_data": {},
                "needs_review": True,
                "confidence": 0,
                "template_id": None
            }
        
        # Map fields to expected response format
        receipt_data = {
            "merchant_name": extracted_data.get('merchant_name', ''),
            "date": extracted_data.get('transaction_time', ''),
            "total_amount": extracted_data.get('total_amount', ''),
            "address": extracted_data.get('merchant_address', ''),
            "reference": extracted_data.get('reference_number', ''),
            "tax": extracted_data.get('tax_amount', ''),
            "subtotal_amount": extracted_data.get('subtotal_amount', ''),
            "cost_list": []
        }
        
        # Add line items if present
        if 'cost_items' in extracted_data:
            for item in extracted_data['cost_items']:
                receipt_data['cost_list'].append({
                    "quantity": item.get('quantity', '1'),
                    "item": item.get('item_name', ''),
                    "total": item.get('total_price', '')
                })
        
        # Calculate confidence based on fields extracted
        expected_fields = len(template.field_extractors) if template.field_extractors else 1
        extracted_fields = sum(1 for k, v in extracted_data.items() if v and k != 'cost_items')
        confidence = (extracted_fields / expected_fields * 100) if expected_fields > 0 else 0
        
        # Determine if user review is needed
        needs_review = confidence < 80 or not receipt_data['merchant_name'] or not receipt_data['total_amount']
        
        return {
            "extracted_data": receipt_data,
            "template_id": template.pk,
            "confidence": confidence,
            "needs_review": needs_review
        }
        
    @staticmethod
    def process_correction(ocr_text: str, template_id: Optional[str], 
                          original_data: Dict[str, Any], 
                          corrected_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Direct interface for processing user corrections to improve templates.
        This avoids needing to use the view directly.
        
        Args:
            ocr_text: Original OCR text
            template_id: ID of template used (optional)
            original_data: Original extracted data (in API format)
            corrected_data: User corrected data (in API format)
            
        Returns:
            Dict with result information
        """
        # Validate input
        if not ocr_text or not corrected_data:
            return {
                "error": "OCR text and corrected data are required",
                "success": False
            }
        
        # Convert corrected data to expected format
        corrected_values = OCRTemplateCorrection(
            merchant_name=corrected_data.get('merchant_name', ''),
            date=corrected_data.get('date', ''),
            total_amount=corrected_data.get('total_amount', ''),
            address=corrected_data.get('address', ''),
            reference=corrected_data.get('reference', ''),
            tax=corrected_data.get('tax', ''),
            subtotal_amount=corrected_data.get('subtotal_amount', ''),
            cost_list=corrected_data.get('cost_list', []),
            description=corrected_data.get('description', ''),
            category=corrected_data.get('category', '')
        )
        
        # If template ID provided, update existing template
        if template_id:
            try:
                template = ReceiptTemplate.objects.get(id=template_id)
                
                # If template is archived, resurrect it
                if template.is_archived:
                    TemplateSuite.resurrect_template_if_needed(int(template_id))
                
                # Update template with corrections
                TemplateSuite.update_template_after_correction(
                    template, ocr_text, original_data, corrected_values
                )
                
                template_action = "updated"
                result_template = template
            except ReceiptTemplate.DoesNotExist:
                # If template not found, create new one
                template = TemplateSuite.create_template_from_correction(ocr_text, corrected_values)
                template_action = "created"
                result_template = template
        else:
            # No template ID provided, create new one
            template = TemplateSuite.create_template_from_correction(ocr_text, corrected_values)
            template_action = "created"
            result_template = template
        
        return {
            "success": True,
            "template_id": result_template.pk,
            "template_action": template_action,
            "message": f"Template successfully {template_action}"
        }
        
    @staticmethod
    def convert_to_internal_format(api_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert from API format to internal data format.
        
        Args:
            api_data: Data in API format
            
        Returns:
            Dict with data in internal format
        """
        # Ensure api_data is a dictionary
        if not isinstance(api_data, dict):
            api_data = {}
            
        internal_data = {
            'merchant_name': api_data.get('merchant_name', ''),
            'transaction_time': api_data.get('date', ''),
            'total_amount': api_data.get('total_amount', ''),
            'merchant_address': api_data.get('address', ''),
            'reference_number': api_data.get('reference', ''),
            'tax_amount': api_data.get('tax', ''),
            'subtotal_amount': api_data.get('subtotal_amount', ''),
            'currency': api_data.get('currency', 'USD'),
        }
        
        # Add line items if present
        if 'cost_list' in api_data and api_data['cost_list']:
            line_items = []
            for item in api_data['cost_list']:
                line_items.append({
                    'item_name': item.get('item', ''),
                    'quantity': item.get('quantity', '1'),
                    'total_price': item.get('total', ''),
                    'unit_price': item.get('unit_price', '')
                })
            internal_data['line_items'] = line_items
            
        return internal_data
        
    @staticmethod
    def convert_to_api_format(internal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert from internal data format to API format.
        
        Args:
            internal_data: Data in internal format (must not be None)
            
        Returns:
            Dict with data in API format
        """
        # Ensure internal_data is a dictionary
        if not isinstance(internal_data, dict):
            internal_data = {}
            
        api_data = {
            'merchant_name': internal_data.get('merchant_name', ''),
            'date': internal_data.get('transaction_time', ''),
            'total_amount': internal_data.get('total_amount', ''),
            'address': internal_data.get('merchant_address', ''),
            'reference': internal_data.get('reference_number', ''),
            'tax': internal_data.get('tax_amount', ''),
            'subtotal_amount': internal_data.get('subtotal_amount', ''),
            'cost_list': []
        }
        
        # Add line items if present
        if 'line_items' in internal_data and internal_data['line_items']:
            for item in internal_data['line_items']:
                api_data['cost_list'].append({
                    'item': item.get('item_name', ''),
                    'quantity': item.get('quantity', '1'),
                    'total': item.get('total_price', '')
                })
                
        return api_data
