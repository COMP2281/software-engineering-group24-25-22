from typing import TypedDict, List, Dict, Any, Optional, Tuple, Union
import re
from datetime import datetime, timedelta
import logging
import iso4217parse
from collections import Counter

logger = logging.getLogger(__name__)


class OCRTemplateCostList(TypedDict):
    quantity: str
    item: str
    total: str


class OCRTemplateCorrection(TypedDict):
    merchant_name: str
    date: str
    total_amount: str
    address: str
    reference: str
    cost_list: List[OCRTemplateCostList]
    description: str
    tax: str
    category: str
    subtotal_amount: str


class FieldExtractor(TypedDict):
    line: Optional[int]  # Absolute line number (for fields before cost items)
    # Relative position (for fields after cost items)
    offset_from_last_item: Optional[int]
    regex: str  # Regex pattern for extraction
    expected_present: bool  # Whether this field is expected in this template


class LineItemMatcher(TypedDict):
    start_line: int  # Where to start looking for line items
    regex: str  # Pattern to match each line item
    groups: Dict[str, int]  # Mapping of field names to capture groups


class TemplateData(TypedDict):
    field_extractors: Dict[str, FieldExtractor]
    line_items: Optional[LineItemMatcher]
    has_line_items: bool


class OCRTemplate:
    """
    Provides tools for creating and updating OCR templates based on user corrections.
    Handles both creation of new templates and extraction using existing templates.
    """

    lines: List[str]
    corrected_values: Optional[OCRTemplateCorrection]
    template_data: TemplateData
    merchant_name: str
    currency_symbol: str = ''
    currency_code: str = 'GBP'  # Default to British Pounds

    # Pre-defined regex patterns for different field types
    FIELD_PATTERNS = {
        'transaction_time': [
            # Common date formats
            r"Date:\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"Date:\s*(\d{1,2}\s+[A-Za-z]{3,}\s+\d{2,4})",  # 12 Jan 2023
            r"(\d{1,2}\s+[A-Za-z]{3,}\s+\d{2,4})",
            # Time formats
            r"Time:\s*(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?)",
            r"(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?)",
            # Combined date and time
            r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\s+\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?)",
        ],
        'merchant_address': [
            # Address patterns
            r"(?:Address|Location):\s*(.*(?:Street|St|Road|Rd|Avenue|Ave|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Plaza|Plz|Square|Sq|Highway|Hwy|Route|Rt).*)",
            r"(.*(?:Street|St|Road|Rd|Avenue|Ave|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Plaza|Plz|Square|Sq|Highway|Hwy|Route|Rt).*)",
            # Postal/ZIP code patterns
            # US and UK formats
            r"(.*(?:\d{5}|\d{5}-\d{4}|\d{4}\s*[A-Z]{2}).*)",
            # Multi-line address with city, state, zip
            r"((?:.*,?\s*){1,3}(?:\d{5}|\d{5}-\d{4}|\d{4}\s*[A-Z]{2}))",
        ],
        'reference_number': [
            # Order/receipt number formats
            r"(?:Order|Receipt|Transaction|Ref|Reference|Invoice)(?:\s*#|\s*No|\s*Number)?:\s*([A-Za-z0-9-]+)",
            r"(?:Order|Receipt|Transaction|Ref|Reference|Invoice)(?:\s*#|\s*No|\s*Number)?:\s*([A-Za-z0-9-]+)",
            r"#\s*([A-Za-z0-9-]{5,})",
            # General alphanumeric with separators
            r"([A-Za-z0-9][\w\-]{4,})",
        ],
        'tax_amount': [
            # Tax amount patterns
            r"(?:Tax|VAT|GST|HST)(?:\s*\(\d+%\))?:\s*(\d+\.\d{2})",
            r"(?:Tax|VAT|GST|HST)(?:\s*\(\d+%\))?(?:\s*:)?\s*(\d+\.\d{2})",
            # Tax amount and percentage
            r"(?:Tax|VAT|GST|HST)\s*\((\d+\.\d{1,2})%\):\s*(\d+\.\d{2})",
        ],
        'total_amount': [
            # Total amount patterns
            r"(?:Total|Amount Due|Grand Total|Balance Due|Pay This Amount):\s*(\d+\.\d{2})",
            r"(?:Total|Amount Due|Grand Total|Balance Due|Pay This Amount)(?:\s*:)?\s*(\d+\.\d{2})",
            # Just a number that looks like currency at the end of a receipt
            r"(\d+\.\d{2})\s*$",
        ],
        'subtotal_amount': [
            # Subtotal amount patterns
            r"(?:Subtotal|Sub-total|Net):\s*(\d+\.\d{2})",
            r"(?:Subtotal|Sub-total|Net)(?:\s*:)?\s*(\d+\.\d{2})",
        ],
    }

    def __init__(self, ocr_text: str, corrected_values: Optional[OCRTemplateCorrection] = None):
        """
        Initialize with OCR text and optional corrected values.
        If corrected values are provided, constructs a new template.
        """
        self.lines = ocr_text.strip().split('\n')
        self.corrected_values = corrected_values

        # Detect currency from OCR text
        self._detect_currency()

        self.merchant_name = self._find_merchant_name()

        if corrected_values:
            # Create a new template from corrections
            self.template_data = self._create_template_from_corrections()

    def _detect_currency(self):
        """
        Detect currency symbol and code from OCR text by analyzing each line.
        Uses iso4217parse library to identify currency symbols.
        """

        # Count currency occurrences across all lines
        currency_counts = Counter()

        # Use iso4217parse library for currency detection
        for line in self.lines:
            try:
                currencies = iso4217parse.by_symbol_match(line)
                if currencies:
                    for currency in currencies:
                        currency_counts[currency.alpha3] += 1
                        # Store the first symbol for this currency
                        if not self.currency_symbol and currency.symbols:
                            self.currency_symbol = currency.symbols[0]
            except Exception as e:
                logger.warning(f"Error detecting currency: {e}")

        # Use the most common currency, fallback to default (GBP)
        if currency_counts:
            self.currency_code = currency_counts.most_common(1)[0][0]

            # Find the corresponding symbol if not set
            if not self.currency_symbol:
                for line in self.lines:
                    try:
                        currencies = iso4217parse.by_symbol_match(line)
                        if currencies:
                            for currency in currencies:
                                if currency.alpha3 == self.currency_code and currency.symbols:
                                    self.currency_symbol = currency.symbols[0]
                                    break
                            if self.currency_symbol:
                                break
                    except Exception:
                        pass

        # If still no symbol found, use common mappings
        if not self.currency_symbol and self.currency_code:
            self.currency_symbol = {'GBP': '£', 'USD': '$', 'EUR': '€', 'JPY': '¥'}.get(
                self.currency_code, '')

        logger.info(
            f"Detected currency: {self.currency_code} (symbol: {self.currency_symbol})")

    def _find_merchant_name(self) -> str:
        """
        Find merchant name in the OCR text, either from corrected values
        or by looking at the first few lines of the receipt.
        """
        if self.corrected_values and self.corrected_values.get('merchant_name'):
            return self.corrected_values['merchant_name']

        # If no correction provided, try to extract from first 3 lines
        potential_names = []
        for i in range(min(3, len(self.lines))):
            line = self.lines[i].strip()
            if line and len(line) < 50:  # Avoid very long lines
                potential_names.append(line)

        if potential_names:
            return potential_names[0]  # Return the first potential name
        return "Unknown Merchant"

    def _find_line_items(self) -> Tuple[Optional[int], Optional[int], List[Dict[str, Any]]]:
        """
        Locate line items in the receipt and extract their information.
        Returns: (start_line, end_line, extracted_items)
        """
        if not self.corrected_values or 'cost_list' not in self.corrected_values:
            return None, None, []

        cost_list = self.corrected_values['cost_list']
        if not cost_list:
            return None, None, []

        # Search for line items based on the corrected data
        start_line = None
        end_line = None
        items_found = []

        # Look for the first item in the OCR text
        first_item = cost_list[0]['item']
        for i, line in enumerate(self.lines):
            if first_item in line:
                start_line = i
                break

        # If found start line, extract all items and find end line
        if start_line is not None:
            for item in cost_list:
                for i in range(start_line, len(self.lines)):
                    if item['item'] in self.lines[i]:
                        items_found.append({
                            'line': i,
                            'content': self.lines[i],
                            'item': item
                        })
                        end_line = i
                        break

        return start_line, end_line, items_found

    def _create_line_item_regex(self, item_lines: List[Dict[str, Any]]) -> Optional[LineItemMatcher]:
        """
        Create regex patterns for line items based on the structure observed.
        """
        if not item_lines:
            return None

        # Find common patterns in line items
        patterns = []
        for item in item_lines:
            line = item['content']
            # Try to identify quantity, item name, and price
            # This is a simplified approach - real implementation would be more robust
            quantity = item['item'].get('quantity', '1')
            item_name = item['item']['item']
            price = item['item']['total']

            # Escape regex special characters
            quantity_escaped = re.escape(quantity)
            item_escaped = re.escape(item_name)
            price_escaped = re.escape(price)

            # Create a pattern that matches this line
            pattern = f".*({quantity_escaped}).*({item_escaped}).*({price_escaped}).*"
            patterns.append({
                'line': line,
                'pattern': pattern,
                'groups': {
                    'quantity': 1,
                    'item_name': 2,
                    'total_price': 3
                }
            })

        # For now, use the first pattern as our matcher
        # A more sophisticated approach would find the most common pattern
        if patterns:
            return {
                'start_line': item_lines[0]['line'],
                'regex': patterns[0]['pattern'],
                'groups': patterns[0]['groups']
            }

        return None

    def _find_field_positions(self, end_line: Optional[int]) -> Dict[str, FieldExtractor]:
        """
        Determine positions of fields relative to line items or absolute positions.
        Uses both user corrections and predefined patterns to create the best possible extractor.
        """
        field_extractors = {}

        # Process merchant name (typically at the top)
        if self.corrected_values and self.corrected_values.get('merchant_name'):
            merchant_name = self.corrected_values['merchant_name']
            for i, line in enumerate(self.lines[:5]):  # Check first 5 lines
                if merchant_name in line:
                    pattern = f".*({re.escape(merchant_name)}).*"
                    field_extractors['merchant_name'] = {
                        'line': i,
                        'offset_from_last_item': None,
                        'regex': pattern,
                        'expected_present': True
                    }
                    break

        # Process date/transaction time (typically at the top)
        if self.corrected_values and self.corrected_values.get('date'):
            date_value = self.corrected_values['date']
            best_pattern = None
            best_line = -1

            # Try to find the line where the date appears
            for i, line in enumerate(self.lines[:10]):  # Check first 10 lines
                if date_value in line:
                    best_line = i

                    # Try to match using our predefined patterns first
                    for pattern in self.FIELD_PATTERNS['transaction_time']:
                        match = re.search(pattern, line)
                        if match and match.group(1) == date_value:
                            best_pattern = pattern
                            break

                    # If no predefined pattern matched, create a custom one
                    if not best_pattern:
                        best_pattern = f".*({re.escape(date_value)}).*"

                    break

            if best_line >= 0:
                field_extractors['transaction_time'] = {
                    'line': best_line,
                    'offset_from_last_item': None,
                    'regex': best_pattern,
                    'expected_present': True
                }

        # Process address (typically at the top)
        if self.corrected_values and self.corrected_values.get('address'):
            address = self.corrected_values['address']
            best_pattern = None
            best_line = -1

            # Try to find the line where the address appears
            for i, line in enumerate(self.lines[:10]):  # Check first 10 lines
                if address in line:
                    best_line = i

                    # Try to match using our predefined patterns first
                    for pattern in self.FIELD_PATTERNS['merchant_address']:
                        match = re.search(pattern, line)
                        if match and match.group(1) == address:
                            best_pattern = pattern
                            break

                    # If no predefined pattern matched, create a custom one
                    if not best_pattern:
                        best_pattern = f".*({re.escape(address)}).*"

                    break

            if best_line >= 0:
                field_extractors['merchant_address'] = {
                    'line': best_line,
                    'offset_from_last_item': None,
                    'regex': best_pattern,
                    'expected_present': True
                }

        # For fields that appear after line items, use relative offsets
        if end_line is not None:
            # Process total amount (typically after line items)
            if self.corrected_values and self.corrected_values.get('total_amount'):
                total = self.corrected_values['total_amount']
                best_pattern = None
                best_offset = -1

                # Try to find where the total appears
                for i in range(end_line + 1, min(end_line + 10, len(self.lines))):
                    if total in self.lines[i]:
                        best_offset = i - end_line

                        # Try our predefined patterns first
                        for pattern in self.FIELD_PATTERNS['total_amount']:
                            # Create version with currency symbol if available
                            if self.currency_symbol and '\\d+\\.\\d{2}' in pattern:
                                # Insert optional currency symbol before the amount
                                symbol_pattern = pattern.replace('(\\d+\\.\\d{2})',
                                                                 f'(?:{re.escape(self.currency_symbol)})?\\s*(\\d+\\.\\d{2})')
                                match = re.search(
                                    symbol_pattern, self.lines[i])
                                if match and match.group(1) == total:
                                    best_pattern = symbol_pattern
                                    break

                            # Try original pattern too
                            match = re.search(pattern, self.lines[i])
                            if match and match.group(1) == total:
                                best_pattern = pattern
                                break

                        # If no pattern matched, create a custom one
                        if not best_pattern:
                            if self.currency_symbol:
                                best_pattern = f".*(?:{re.escape(self.currency_symbol)})?\\s*({re.escape(total)}).*"
                            else:
                                best_pattern = f".*({re.escape(total)}).*"

                        break

                if best_offset >= 0:
                    field_extractors['total_amount'] = {
                        'line': None,
                        'offset_from_last_item': best_offset,
                        'regex': best_pattern,
                        'expected_present': True
                    }

            # Process tax (typically after line items, before total)
            if self.corrected_values and self.corrected_values.get('tax'):
                tax = self.corrected_values['tax']
                best_pattern = None
                best_offset = -1

                # Try to find where the tax appears
                for i in range(end_line + 1, min(end_line + 10, len(self.lines))):
                    if tax in self.lines[i]:
                        best_offset = i - end_line

                        # Try our predefined patterns first
                        for pattern in self.FIELD_PATTERNS['tax_amount']:
                            # Create version with currency symbol if available
                            if self.currency_symbol and '\\d+\\.\\d{2}' in pattern:
                                # Insert optional currency symbol before the amount
                                symbol_pattern = pattern.replace('(\\d+\\.\\d{2})',
                                                                 f'(?:{re.escape(self.currency_symbol)})?\\s*(\\d+\\.\\d{2})')
                                match = re.search(
                                    symbol_pattern, self.lines[i])
                                if match and match.group(1) == tax:
                                    best_pattern = symbol_pattern
                                    break

                            # Try original pattern too
                            match = re.search(pattern, self.lines[i])
                            if match and match.group(1) == tax:
                                best_pattern = pattern
                                break

                        # If no pattern matched, create a custom one
                        if not best_pattern:
                            if self.currency_symbol:
                                best_pattern = f".*(?:{re.escape(self.currency_symbol)})?\\s*({re.escape(tax)}).*"
                            else:
                                best_pattern = f".*({re.escape(tax)}).*"

                        break

                if best_offset >= 0:
                    field_extractors['tax_amount'] = {
                        'line': None,
                        'offset_from_last_item': best_offset,
                        'regex': best_pattern,
                        'expected_present': True
                    }

            # Process reference number (can be anywhere, check after line items first)
            if self.corrected_values and self.corrected_values.get('reference'):
                ref = self.corrected_values['reference']
                best_pattern = None
                best_offset = -1

                # Try after line items
                for i in range(end_line + 1, min(end_line + 10, len(self.lines))):
                    if ref in self.lines[i]:
                        best_offset = i - end_line

                        # Try to match using our predefined patterns first
                        for pattern in self.FIELD_PATTERNS['reference_number']:
                            match = re.search(pattern, self.lines[i])
                            if match and match.group(1) == ref:
                                best_pattern = pattern
                                break

                        # If no predefined pattern matched, create a custom one
                        if not best_pattern:
                            best_pattern = f".*({re.escape(ref)}).*"

                        break

                if best_offset >= 0:
                    field_extractors['reference_number'] = {
                        'line': None,
                        'offset_from_last_item': best_offset,
                        'regex': best_pattern,
                        'expected_present': True
                    }
                else:
                    # If not found after line items, check before line items
                    best_line = -1
                    for i in range(min(15, len(self.lines))):
                        if ref in self.lines[i]:
                            best_line = i

                            # Try to match using our predefined patterns first
                            for pattern in self.FIELD_PATTERNS['reference_number']:
                                match = re.search(pattern, self.lines[i])
                                if match and match.group(1) == ref:
                                    best_pattern = pattern
                                    break

                            # If no predefined pattern matched, create a custom one
                            if not best_pattern:
                                best_pattern = f".*({re.escape(ref)}).*"

                            break

                    if best_line >= 0:
                        field_extractors['reference_number'] = {
                            'line': best_line,
                            'offset_from_last_item': None,
                            'regex': best_pattern,
                            'expected_present': True
                        }

        # Process subtotal_amount if provided
        if self.corrected_values and self.corrected_values.get('subtotal_amount'):
            subtotal = self.corrected_values['subtotal_amount']
            best_pattern = None
            best_offset = -1
            best_line = -1

            # Try after line items if we have line items
            if end_line is not None:
                for i in range(end_line + 1, min(end_line + 10, len(self.lines))):
                    if subtotal in self.lines[i]:
                        best_offset = i - end_line

                        # Try predefined patterns with currency symbol
                        for pattern in self.FIELD_PATTERNS['subtotal_amount']:
                            if self.currency_symbol and '\\d+\\.\\d{2}' in pattern:
                                symbol_pattern = pattern.replace('(\\d+\\.\\d{2})',
                                                                 f'(?:{re.escape(self.currency_symbol)})?\\s*(\\d+\\.\\d{2})')
                                match = re.search(
                                    symbol_pattern, self.lines[i])
                                if match and match.group(1) == subtotal:
                                    best_pattern = symbol_pattern
                                    break

                            # Try original pattern too
                            match = re.search(pattern, self.lines[i])
                            if match and match.group(1) == subtotal:
                                best_pattern = pattern
                                break

                        if not best_pattern:
                            if self.currency_symbol:
                                best_pattern = f".*(?:{re.escape(self.currency_symbol)})?\\s*({re.escape(subtotal)}).*"
                            else:
                                best_pattern = f".*({re.escape(subtotal)}).*"

                        break

                if best_offset >= 0:
                    field_extractors['subtotal_amount'] = {
                        'line': None,
                        'offset_from_last_item': best_offset,
                        'regex': best_pattern,
                        'expected_present': True
                    }
            else:
                # If no line items, search through the entire receipt
                for i, line in enumerate(self.lines):
                    if subtotal in line:
                        best_line = i

                        # Try predefined patterns
                        for pattern in self.FIELD_PATTERNS['subtotal_amount']:
                            match = re.search(pattern, line)
                            if match and match.group(1) == subtotal:
                                best_pattern = pattern
                                break

                        if not best_pattern:
                            best_pattern = f".*({re.escape(subtotal)}).*"

                        break

                if best_line >= 0:
                    field_extractors['subtotal_amount'] = {
                        'line': best_line,
                        'offset_from_last_item': None,
                        'regex': best_pattern,
                        'expected_present': True
                    }

        return field_extractors

    def _create_template_from_corrections(self) -> TemplateData:
        """
        Create a template based on user corrections.
        """
        # Find line items section
        start_line, end_line, items = self._find_line_items()

        # Create template structure
        template: TemplateData = {
            'field_extractors': self._find_field_positions(end_line),
            'has_line_items': bool(items),
            'line_items': None
        }

        # Add line items matcher if we found items
        if items:
            template['line_items'] = self._create_line_item_regex(items)
        else:
            template['line_items'] = None

        return template

    def to_model_data(self) -> Dict[str, Any]:
        """
        Convert template to a format that can be stored in the database model.
        """
        field_extractors = {}

        if self.template_data is None:
            return {"error": "Template data not available"}

        # Convert our simplified field_extractors to the model format
        for field, extractor in self.template_data['field_extractors'].items():
            field_extractors[field] = {
                'expected_present': extractor.get('expected_present', True),
                'patterns': [extractor['regex']],
            }

            if extractor['line'] is not None:
                field_extractors[field]['line'] = extractor['line']
            elif extractor['offset_from_last_item'] is not None:
                field_extractors[field]['offset_from_last_item'] = extractor['offset_from_last_item']

        # Convert line items to the model format
        item_patterns = []
        has_line_items = self.template_data['has_line_items']
        line_items_start_line = None

        if has_line_items and self.template_data['line_items']:
            item_patterns.append({
                'pattern': self.template_data['line_items']['regex'],
                'groups': self.template_data['line_items']['groups']
            })
            line_items_start_line = self.template_data['line_items'].get(
                'start_line', 5)

        return {
            'merchant_name': self.merchant_name,
            'field_extractors': field_extractors,
            'item_patterns': item_patterns,
            'has_line_items': has_line_items,
            'line_items_start_line': line_items_start_line,
            'currency_info': {
                'iso_code': self.currency_code,
                'symbol': self.currency_symbol
            },
            'field_accuracy': {
                field: 80.0 for field in self.template_data['field_extractors'].keys()
            },
            'field_edit_distances': {
                field: 0.0 for field in self.template_data['field_extractors'].keys()
            }
        }

    def extract_fields(self, template_model_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract fields from OCR text using a template.

        Args:
            template_model_data: Template data from the database model

        Returns:
            Dictionary of extracted fields
        """
        # First detect the currency before extraction
        self._detect_currency()

        extracted_data = {}
        field_extractors = template_model_data.get('field_extractors', {})
        has_line_items = template_model_data.get('has_line_items', True)

        # First pass: extract fields with absolute line positions
        for field, extractor in field_extractors.items():
            if not extractor.get('expected_present', True):
                continue

            # Get line position information
            line = extractor.get('line')
            line_hints = extractor.get('line_hints', [])

            # If we have a direct line number, use it
            if line is not None and 0 <= line < len(self.lines):
                patterns = [extractor.get('regex')]

                # For monetary fields, create currency-aware variants
                if field in ['total_amount', 'tax_amount', 'subtotal_amount'] and self.currency_symbol:
                    # Create two pattern variants - with and without currency symbol
                    if '\\d+\\.\\d{2}' in patterns[0]:
                        symbol_pattern = patterns[0].replace('(\\d+\\.\\d{2})',
                                                             f'(?:{re.escape(self.currency_symbol)})?\\s*(\\d+\\.\\d{2})')
                        patterns = [symbol_pattern, patterns[0]]

                # Try each pattern
                for pattern in patterns:
                    if not pattern:
                        continue

                    match = re.search(pattern, self.lines[line])
                    if match and match.groups():
                        extracted_data[field] = match.group(1)
                        break

            # If we have line hints, try those too
            elif line_hints:
                patterns = [extractor.get('regex')]

                # For monetary fields, create currency-aware variants
                if field in ['total_amount', 'tax_amount', 'subtotal_amount'] and self.currency_symbol:
                    if '\\d+\\.\\d{2}' in patterns[0]:
                        symbol_pattern = patterns[0].replace('(\\d+\\.\\d{2})',
                                                             f'(?:{re.escape(self.currency_symbol)})?\\s*(\\d+\\.\\d{2})')
                        patterns = [symbol_pattern, patterns[0]]

                # Try each line hint with each pattern
                for line_hint in line_hints:
                    if 0 <= line_hint < len(self.lines):
                        for pattern in patterns:
                            if not pattern:
                                continue

                            match = re.search(pattern, self.lines[line_hint])
                            if match and match.groups():
                                extracted_data[field] = match.group(1)
                                break

                        # If we found a match, move to the next field
                        if field in extracted_data:
                            break

        # Extract line items if present and enabled
        line_items = []
        item_patterns = template_model_data.get('item_patterns', [])

        if has_line_items and item_patterns:
            # Determine where line items start
            start_line = None

            # Check if we have a specific line_items_start_line
            if 'line_items_start_line' in template_model_data:
                start_line = template_model_data['line_items_start_line']

            # If not, look for field extractors that might indicate the start
            if start_line is None:
                for field, extractor in field_extractors.items():
                    if field == 'line_items_start' and extractor.get('line') is not None:
                        start_line = extractor['line']
                        break

            # If still no start line, try to find it using the first pattern
            if start_line is None and item_patterns:
                first_pattern = item_patterns[0]

                # Create versions with and without currency symbol
                patterns = [first_pattern['pattern']]
                if self.currency_symbol and '\\d+\\.\\d{2}' in patterns[0]:
                    symbol_pattern = patterns[0].replace('(\\d+\\.\\d{2})',
                                                         f'(?:{re.escape(self.currency_symbol)})?\\s*(\\d+\\.\\d{2})')
                    patterns = [symbol_pattern, patterns[0]]

                # Try to find the first line that matches our item pattern
                for i, line in enumerate(self.lines):
                    for pattern in patterns:
                        match = re.search(pattern, line)
                        if match:
                            start_line = i
                            break
                    if start_line is not None:
                        break

            # Extract items
            if start_line is not None:
                end_line = start_line
                for i in range(start_line, len(self.lines)):
                    matched = False
                    for pattern_def in item_patterns:
                        # Create both regular and currency-symbol versions
                        patterns = [pattern_def['pattern']]
                        if self.currency_symbol and '\\d+\\.\\d{2}' in patterns[0]:
                            symbol_pattern = patterns[0].replace('(\\d+\\.\\d{2})',
                                                                 f'(?:{re.escape(self.currency_symbol)})?\\s*(\\d+\\.\\d{2})')
                            patterns = [symbol_pattern, patterns[0]]

                        for pattern in patterns:
                            match = re.search(pattern, self.lines[i])
                            if match:
                                item_data = {}
                                for field, group_idx in pattern_def['groups'].items():
                                    if len(match.groups()) >= group_idx:
                                        item_data[field] = match.group(
                                            group_idx)

                                if item_data:
                                    line_items.append(item_data)
                                    end_line = i
                                    matched = True
                                    break
                        if matched:
                            break

                    if not matched and line_items:
                        # If we didn't find a match for any pattern, check if we already found items
                        # If we've already found items, this could be the end of the items section
                        # Try a few more lines before giving up
                        if i > end_line + 3:
                            break

                # Store the last line of items for second pass
                if line_items:
                    extracted_data['_last_item_line'] = end_line

        # Second pass: extract fields with relative positions from line items
        if '_last_item_line' in extracted_data:
            last_item_line = extracted_data['_last_item_line']

            for field, extractor in field_extractors.items():
                if field in extracted_data or not extractor.get('expected_present', True):
                    continue

                offset = extractor.get('offset_from_last_item')
                if offset is not None:
                    target_line = last_item_line + offset
                    if 0 <= target_line < len(self.lines):
                        patterns = [extractor.get('regex')]

                        # For monetary fields, create currency-aware variants
                        if field in ['total_amount', 'tax_amount', 'subtotal_amount'] and self.currency_symbol:
                            if patterns[0] and '\\d+\\.\\d{2}' in patterns[0]:
                                symbol_pattern = patterns[0].replace('(\\d+\\.\\d{2})',
                                                                     f'(?:{re.escape(self.currency_symbol)})?\\s*(\\d+\\.\\d{2})')
                                patterns = [symbol_pattern, patterns[0]]

                        for pattern in patterns:
                            if not pattern:
                                continue

                            match = re.search(pattern, self.lines[target_line])
                            if match and match.groups():
                                extracted_data[field] = match.group(1)
                                break

        # Add line items to the output
        if line_items:
            extracted_data['cost_items'] = line_items

        # Add currency info to output
        if self.currency_symbol or self.currency_code:
            extracted_data['currency'] = self.currency_code
            extracted_data['currency_symbol'] = self.currency_symbol

        # Clean up internal fields
        if '_last_item_line' in extracted_data:
            del extracted_data['_last_item_line']

        return extracted_data
