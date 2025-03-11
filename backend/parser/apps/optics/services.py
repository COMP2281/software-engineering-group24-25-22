from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import timedelta
from django.utils import timezone
from mongoengine.queryset.visitor import Q
from rapidfuzz import fuzz, process
import json

from .models import ReceiptTemplate
from .lib.templates import OCRTemplate, OCRTemplateCorrection

logger = logging.getLogger(__name__)

"""
MERCHANT FUZZY MATCHING IMPLEMENTATION

This module implements RapidFuzz-based merchant name matching to improve 
template selection reliability. Key improvements:

1. Added find_best_merchant_match() method to compare receipt text with merchant names
   using multiple fuzzy matching strategies (ratio, partial_ratio, token_sort_ratio)

2. Updated find_template_candidates() to use fuzzy matching when receipt text is provided

3. Enhanced parse_receipt() to attempt fuzzy merchant identification before template matching

These improvements help the system better identify merchants regardless of
format variations, spacing differences, or additional text (like "EXPRESS" or "SUPERSTORE").
"""


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
    def preprocess_ocr_text(ocr_text: str) -> str:
        """
        Preprocess OCR text to clean up common artifacts and improve parsing accuracy.
        
        Args:
            ocr_text: Raw OCR text
            
        Returns:
            Cleaned OCR text
        """
        import re
        
        # Fix common OCR misreads
        replacements = [
            # Common digit/letter confusion
            (r'(\d+)m1', r'\1ml'),  # 900m1 -> 900ml
            (r'(\d+)1', r'\1l'),    # 1.51 -> 1.5l (liter)
            (r'(\d+)o', r'\1o'),    # 5o0g -> 500g
            (r'(\d+)O', r'\1O'),    # 5O0g -> 500g
            # Price formatting issues
            (r'(\d)x(\d)', r'\1x\2'),  # Fix spacing in quantities like 2x3
            # General cleanups
            (r'\s{2,}', ' '),       # Multiple spaces to single space
            (r'^\s+', ''),          # Leading spaces on lines 
            (r'\s+$', ''),          # Trailing spaces on lines
        ]
        
        # Process each line to filter out garbage
        cleaned_lines = []
        for line in ocr_text.split('\n'):
            line = line.strip()

            for pattern, replacement in replacements:
                line = re.sub(pattern, replacement, line)
        
            # Skip lines comprised of only adjacent characters spaced by 1
            if re.match(r'^(.)( (.))+$', line):
                continue
            
            # Skip empty lines or very short lines (less than 2 chars)
            if not line or len(line) < 2:
                continue
                
            # Skip lines that are just repeated symbols
            if re.match(r'^([-_.,:;!@#$%^&*()+=~`<>?/\\|])\1{3,}$', line):
                continue
                
            # Skip lines with too many special characters (more aggressive filtering)
            special_chars = re.sub(r'[a-zA-Z0-9\s£$€]', '', line)
            if len(special_chars) > (len(line) * 0.4):  # More than 40% special chars
                continue
                
            # Skip lines with very few alphanumeric characters
            alphanumeric_chars = re.sub(r'[^a-zA-Z0-9]', '', line)
            if len(alphanumeric_chars) < 2 and len(line) > 3:
                continue
                
            # Skip garbage lines that are likely OCR artifacts 
            garbage_patterns = [
                r'^[_\-—–.,:;\'"`*]+$',  # Just punctuation
                r'^[\\\\/|]+$',          # Just slashes or pipes
                r'^[^a-zA-Z0-9£$€]{4,}$',  # 4+ consecutive non-alphanumeric chars
                r'^[a-zA-Z\s]{1,2}$',    # Single letters with spaces
                r'^\s*[_\-—–.]{2,}\s*$',  # Just dashes/underscores
            ]
            
            skip_line = False
            for pattern in garbage_patterns:
                if re.match(pattern, line):
                    skip_line = True
                    break
                    
            if skip_line:
                continue
                
            # Cleanup line - remove garbage at start and end of lines
            line = re.sub(r'^[^a-zA-Z0-9£$€]*([a-zA-Z0-9£$€].*[a-zA-Z0-9£$€])[^a-zA-Z0-9£$€]*$', r'\1', line)

            # Add the cleaned line
            cleaned_lines.append(line)
        
        # Consolidate consecutive empty lines
        text = '\n'.join(cleaned_lines)
        # text = re.sub(r'\n{3,}', '\n\n', text)  # No more than 2 consecutive newlines

        return text
    
    @staticmethod
    def find_best_merchant_match(receipt_text: str, threshold=70):
        """
        Find the best matching merchant from database using fuzzy matching.
        
        Args:
            receipt_text: First 3 lines of receipt text
            merchant_list: Optional list of merchant names (fetched if None)
            threshold: Minimum score (0-100) to consider a match
            
        Returns:
            Tuple of (best_match, score) or (None, 0) if no good match
        """
        # Get merchant list if not provided
        merchant_list = list(ReceiptTemplate.objects.distinct('merchant_name'))
            
        # No merchants to compare with
        if not merchant_list:
            return None, 0

        print("merchant_list", merchant_list)
        print("receipt_text", receipt_text)
            
        # Try each matching strategy
        best_match = None
        best_score = 0
        
        # Try fuzzy matching with different algorithms
        for merchant in merchant_list:
            # Calculate multiple scores to handle different types of variations
            ratio_score = fuzz.ratio(receipt_text, merchant)
            partial_score = fuzz.partial_ratio(receipt_text, merchant)
            token_score = fuzz.token_sort_ratio(receipt_text, merchant)
            
            # Use the highest score from any method
            score = max(ratio_score, partial_score, token_score)
            
            if score > best_score:
                best_score = score
                best_match = merchant
        
        # Return best match if it meets threshold
        if best_score >= threshold:
            return best_match, best_score
        
        return None, 0

    @staticmethod
    def find_template_candidates(merchant_name: str, limit: int = 5, receipt_text: Optional[str] = None) -> List[ReceiptTemplate]:
        """
        Find potential template matches for a given merchant name.
        Uses fuzzy matching to handle variations in merchant names.

        Args:
            merchant_name: The merchant name to match
            limit: Maximum number of templates to return
            receipt_text: Optional full receipt text for better matching

        Returns:
            List of template objects sorted by relevance
        """
        # First, try exact match on active templates
        exact_matches = ReceiptTemplate.objects(
            merchant_name__iexact=merchant_name,
            is_archived=False
        ).order_by('-usage_count')[:limit]

        if exact_matches.count() > 0:
            return list(exact_matches)

        # If receipt text is provided, try fuzzy matching with RapidFuzz
        if receipt_text:
            # Get first 3 lines for merchant matching
            receipt_lines = receipt_text.strip().split('\n')
            first_lines = '\n'.join(receipt_lines[:min(3, len(receipt_lines))])
            
            # Get all active merchant names
            active_merchants = list(ReceiptTemplate.objects(
                is_archived=False
            ).distinct('merchant_name'))
            
            # Find best fuzzy match
            best_match, score = TemplateSuite.find_best_merchant_match(
                first_lines, 
                merchant_list=active_merchants
            )
            
            if best_match:
                logger.info(f"Found fuzzy match for '{merchant_name}': '{best_match}' (score: {score})")
                
                fuzzy_matches = ReceiptTemplate.objects(
                    merchant_name=best_match,
                    is_archived=False
                ).order_by('-usage_count')[:limit]
                
                if fuzzy_matches.count() > 0:
                    return list(fuzzy_matches)
        
        # If no fuzzy match or no receipt text, fall back to basic matching
        # This is a simplified fuzzy match using contains
        basic_fuzzy_matches = ReceiptTemplate.objects(
            merchant_name__icontains=merchant_name.split(
            )[0] if merchant_name.split() else "",
            is_archived=False
        ).order_by('-usage_count')[:limit]

        if basic_fuzzy_matches.count() > 0:
            return list(basic_fuzzy_matches)

        # If still no matches, check archived templates
        archived_matches = ReceiptTemplate.objects(
            Q(merchant_name__iexact=merchant_name) |
            Q(merchant_name__icontains=merchant_name.split()
              [0] if merchant_name.split() else ""),
            is_archived=True
        ).order_by('-usage_count')[:limit]

        if archived_matches.count() > 0:
            return list(archived_matches)

        # If no matches at all, return generic templates
        # Assuming generic templates have merchant_name = 'Generic'
        generic_templates = ReceiptTemplate.objects(
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
            'has_line_items': template.has_line_items,
            'item_patterns': template.item_patterns,
            'line_items_start_line': template.line_items_start_line
        }

        # Extract fields using the template
        extracted_data = ocr_template.extract_fields(template_data)

        # # Update usage statistics periodically
        # if template.usage_count % 10 == 0:  # Every 10 uses
        # Get total uses for this merchant - calculated manually in MongoEngine
        templates = ReceiptTemplate.objects(merchant_name=template.merchant_name)
        total_merchant_uses = sum(t.usage_count for t in templates) or 1

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

        # Find template candidates using both merchant name and receipt text for better matching
        candidates = TemplateSuite.find_template_candidates(merchant_name, receipt_text=ocr_text)

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
            
        # Check if cost items were corrected - this is always considered significant
        cost_items_corrected = False
        corrected_items_count = 0
        extracted_items_count = 0
        
        if 'cost_items' in extracted_data and 'cost_list' in corrected_data:
            extracted_items = extracted_data.get('cost_items', [])
            corrected_items = corrected_data.get('cost_list', [])
            extracted_items_count = len(extracted_items)
            corrected_items_count = len(corrected_items)
            
            # Check if the number of items is different
            if extracted_items_count != corrected_items_count:
                cost_items_corrected = True
                logger.info(f"Cost items corrected: extracted {extracted_items_count} vs corrected {corrected_items_count}")
            else:
                # Even if count is the same, check for content differences
                # This is a simplified check - in reality would need to match items
                for i, (extracted, corrected) in enumerate(zip(extracted_items, corrected_items)):
                    extracted_name = extracted.get('item_name', '')
                    if not extracted_name:
                        extracted_name = extracted.get('item', '')
                    
                    corrected_name = corrected.get('item', '')
                    
                    # Check if names are significantly different
                    if extracted_name != corrected_name and not (extracted_name in corrected_name or corrected_name in extracted_name):
                        cost_items_corrected = True
                        logger.info(f"Cost item content corrected: '{extracted_name}' to '{corrected_name}'")
                        break

        # Always create a new template if cost items were corrected
        # OR if multiple fields were corrected
        if cost_items_corrected or significant_corrections > 0:
            # Create a new template from the correction
            new_template = TemplateSuite.create_template_from_correction(ocr_text, corrected_data)
            
            if cost_items_corrected:
                logger.info(f"Created new template from correction due to cost items needing correction ({extracted_items_count} vs {corrected_items_count})")
            else:
                logger.info(f"Created new template from correction due to {significant_corrections} fields needing correction")
            
            # Return the new template instead of the updated one
            return new_template
        
        # For no corrections (which shouldn't happen often), update the existing template
        # Create a temporary template to extract any updated patterns
        new_ocr_template = OCRTemplate(ocr_text, corrected_data)
        new_data = new_ocr_template.to_model_data()
        
        # Find which field was corrected (if any)
        corrected_field = None
        for field, correct in field_corrections.items():
            if not correct:
                corrected_field = field
                break
        
        # Update the corrected field if one exists
        if corrected_field and corrected_field in new_data['field_extractors']:
            template.field_extractors[corrected_field] = new_data['field_extractors'][corrected_field]
            logger.info(f"Updated pattern for field '{corrected_field}' in template {template.pk}")
        
        # This section is now less likely to be reached, but kept for completeness
        if 'cost_items' in extracted_data and 'cost_list' in corrected_data and new_data['item_patterns']:
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

        old_archived_templates = ReceiptTemplate.objects(
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
            template = ReceiptTemplate.objects(id=template_id).get()

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
        ocr_text = TemplateSuite.preprocess_ocr_text(ocr_text)
        print(ocr_text)
        # Extract merchant name from receipt if not provided
        if not merchant_name:
            receipt_lines = ocr_text.strip().split('\n')
            first_lines = '\n'.join(receipt_lines[:min(4, len(receipt_lines))])

            print(receipt_lines)
            
            # Try fuzzy matching first
            best_match, score = TemplateSuite.find_best_merchant_match(first_lines)
            print("best_match", best_match)
            if best_match and score >= 70:
                merchant_name = best_match
                logger.info(f"Used fuzzy matching to identify merchant: '{merchant_name}' (score: {score})")
            else:
                # Fall back to first line if no good match
                merchant_name = receipt_lines[0].strip() if receipt_lines else "Unknown"

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

        print("--------------------- EXTRACTED DATA -------------------------------")
        print("EXTRACTED_DATA", extracted_data)
        print("--------------------- EXTRACTED DATA END ---------------------------")

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
                    "total": item.get('total_price', ''),
                    "unit_price": item.get("unit_price", "")
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
        
        print("--------------- CONVERT TO INTERNAL FORMAT ----------------------")
        # Add line items if present
        if 'cost_list' in api_data and api_data['cost_list']:
            line_items = []
            for item in api_data['cost_list']:
                print(json.dumps(item))
                line_items.append({
                    'item_name': item.get('item', ''),
                    'quantity': item.get('quantity', '1'),
                    'total_price': item.get('total', ''),
                    'unit_price': item.get('unit_price', '')
                })
            internal_data['line_items'] = line_items
        print("--------------- CONVERT TO INTERNAL FORMAT END ------------------")
            
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
