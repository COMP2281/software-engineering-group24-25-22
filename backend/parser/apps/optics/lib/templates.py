from typing import TypedDict, List, Dict, Any, Optional, Tuple, Union
import re
from datetime import datetime, timedelta
import logging
import iso4217parse
from collections import Counter
import regex 

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
        'merchant_name': [
            # Common merchant name patterns - typically at the top of receipt
            r"^\s*([A-Z][A-Z\s&.']{2,})\s*$",  # ALL CAPS NAME
            r"^\s*([A-Z][a-zA-Z\s&.']{2,})\s*$",  # Capitalized Name
            r"^\s*(?:Store|Merchant|Shop|Restaurant|Retail|Vendor):\s*([A-Za-z0-9\s&.'-]+)",  # Labeled merchant
            r"^(?:\*{2,}|\s{2,}|\t+)([A-Za-z0-9\s&.'-]+)(?:\*{2,}|\s{2,}|\t+)$",  # Centered/decorated name
        ],
        
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
            # ISO-like formats
            r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})",
            r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}(?::\d{2})?)",
            # More European formats (day first)
            r"(\d{1,2}\.\d{1,2}\.\d{2,4})",
            # Receipt transaction IDs with timestamps
            r"Transaction\s+(?:Date|Time):\s*([A-Za-z0-9\s/:.-]+)",
        ],
        
        'merchant_address': [
            # Address patterns
            r"(?:Address|Location):\s*(.*(?:Street|St|Road|Rd|Avenue|Ave|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Plaza|Plz|Square|Sq|Highway|Hwy|Route|Rt).*)",
            r"(.*(?:Street|St|Road|Rd|Avenue|Ave|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Plaza|Plz|Square|Sq|Highway|Hwy|Route|Rt).*)",
            # Postal/ZIP code patterns
            r"(.*(?:\d{5}|\d{5}-\d{4}|\d{4}\s*[A-Z]{2}).*)",  # US and UK postal codes
            # Multi-line address with city, state, zip
            r"((?:.*,?\s*){1,3}(?:\d{5}|\d{5}-\d{4}|\d{4}\s*[A-Z]{2}))",
            # Store locations that don't have street names
            r"([A-Za-z0-9\s]+(?:Store|Branch|Location|Express|Superstore|Market|Shop))",
            r"([A-Za-z0-9\s]+(?:Mall|Centre|Center|Retail Park))",
            # Generic city/town locations
            r"([A-Za-z\s]+,\s*[A-Za-z\s]+)",  # City, State format
            r"Tel(?:ephone)?:.*?([A-Za-z0-9\s,]+)(?=\n|$)",  # Address near phone number
            # Common store location formats
            r"(?:store|branch)(?:\s*#|\s*no|\s*number)?:?\s*([A-Za-z0-9\s]+)",
            # Branded location formats 
            r"([A-Za-z]+\s+(?:Express|Extra|Metro|Local|Superstore|Supermarket))",
        ],
        
        'reference_number': [
            # Order/receipt number formats
            r"(?:Order|Receipt|Transaction|Ref|Reference|Invoice)(?:\s*#|\s*No|\s*Number)?:\s*([A-Za-z0-9-]+)",
            r"(?:Order|Receipt|Transaction|Ref|Reference|Invoice)(?:\s*#|\s*No|\s*Number)?:\s*([A-Za-z0-9-]+)",
            r"#\s*([A-Za-z0-9-]{5,})",
            # General alphanumeric with separators
            r"([A-Za-z0-9][\w\-]{4,})",
            # VAT/Tax registration numbers
            r"VAT\s*(?:Number|Reg|Registration|No)(?:\s*:|\s+)?\s*([A-Za-z0-9\s-]+)",
            r"Tax\s*(?:ID|Number|Identifier)(?:\s*:|\s+)?\s*([A-Za-z0-9\s-]+)",
            # Receipt-specific identifiers
            r"(?:Check|Bill)\s*(?:#|No|Number)?(?:\s*:|\s+)?\s*([A-Za-z0-9-]+)",
            r"(?:Terminal|Register|Till)(?:\s*:|\s+)?\s*([A-Za-z0-9-]+)",
            # Card transaction references
            r"Auth(?:orization|orisation)?\s*(?:Code|No|#)?(?:\s*:|\s+)?\s*([A-Za-z0-9-]+)",
            r"(?:Payment|Transaction)\s*ID(?:\s*:|\s+)?\s*([A-Za-z0-9-]+)",
        ],
        
        'tax_amount': [
            # Tax amount patterns
            r"(?:Tax|VAT|GST|HST)(?:\s*\(\d+%\))?:\s*(\d+\.\d{2})",
            r"(?:Tax|VAT|GST|HST)(?:\s*\(\d+%\))?(?:\s*:)?\s*(\d+\.\d{2})",
            # Tax amount and percentage
            r"(?:Tax|VAT|GST|HST)\s*\((\d+\.\d{1,2})%\):\s*(\d+\.\d{2})",
            # Additional tax formats
            r"(?:Sales\s+Tax|Tax\s+Total):\s*(\d+\.\d{2})",
            r"(?:Tax|VAT|GST|HST)(?:\s+\d+%)?(?:\s*:)?\s*([£$€]?\d+\.\d{2})",
            # Multiple tax formats (take the last one)
            r"(?:.*Tax.*\n)*.*Tax.*?(\d+\.\d{2})",
            # Tax included format
            r"(?:VAT|Tax)?\s+Included:\s*(\d+\.\d{2})",
        ],
        
        'total_amount': [
            # Total amount patterns
            r"(?:Total|Amount Due|Grand Total|Balance Due|Pay This Amount):\s*(\d+\.\d{2})",
            r"(?:Total|Amount Due|Grand Total|Balance Due|Pay This Amount)(?:\s*:)?\s*(\d+\.\d{2})",
            # Just a number that looks like currency at the end of a receipt
            r"(\d+\.\d{2})\s*$",
            # TOTAL in caps
            r"TOTAL\s*(?::)?\s*[£$€]?(\d+\.\d{2})",
            # Cash/card payment lines
            r"(?:Cash|Card|Credit|Debit)\s+(?:Paid|Payment|Tender|Amount):\s*(\d+\.\d{2})",
            # Labeled total
            r"(?:To Pay|Please Pay|Amount Paid|Paid|Payment)(?:\s*:)?\s*[£$€]?(\d+\.\d{2})",
            # Final amount with currency symbol
            r"(?:Total|Amount Due|Grand Total|Balance Due|Pay This Amount)(?:\s*:)?\s*[£$€](\d+\.\d{2})",
        ],
        
        'subtotal_amount': [
            # Subtotal amount patterns
            r"(?:Subtotal|Sub-total|Net):\s*(\d+\.\d{2})",
            r"(?:Subtotal|Sub-total|Net)(?:\s*:)?\s*(\d+\.\d{2})",
            # Additional formats
            r"(?:Subtotal|Sub-total|Net|Goods)\s+(?:Amount|Value)(?:\s*:)?\s*(\d+\.\d{2})",
            # Before tax subtotal
            r"(?:Amount|Total)\s+(?:Before|Ex)\s+(?:Tax|VAT)(?:\s*:)?\s*(\d+\.\d{2})",
            # Items total
            r"(?:Items|Basket)\s+(?:Total|Amount)(?:\s*:)?\s*(\d+\.\d{2})",
            # With currency symbol
            r"(?:Subtotal|Sub-total|Net)(?:\s*:)?\s*[£$€](\d+\.\d{2})",
        ],
    }

    @staticmethod
    def _preprocess_ocr_text(ocr_text: str) -> str:
        """
        Preprocess OCR text to clean up common artifacts and improve parsing accuracy.
        
        Args:
            ocr_text: Raw OCR text
            
        Returns:
            Cleaned OCR text
        """
        import re
        
        # First, standardize line breaks and strip extra whitespace
        ocr_text = ocr_text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove URL encoding artifacts (common OCR misreads)
        ocr_text = re.sub(r'%20', ' ', ocr_text)
        
        # Fix common OCR misreads
        replacements = [
            # Common digit/letter confusion
            (r'(\d+)m1', r'\1ml'),  # 900m1 -> 900ml
            (r'(\d+)1', r'\1l'),    # 1.51 -> 1.5l (liter)
            (r'(\d+)o', r'\1o'),    # 5o0g -> 500g
            (r'(\d+)O', r'\1O'),    # 5O0g -> 500g
            # Price formatting issues
            (r'([Pp])(\d+)', r'£\2'),  # P250 or p250 -> £250
            (r'(\d)x(\d)', r'\1x\2'),  # Fix spacing in quantities like 2x3
            # Common symbols
            (r'\.com/store-1', r'.com/store-l'),  # Fix common URL misreading
            # General cleanups
            (r'\s{2,}', ' '),       # Multiple spaces to single space
            (r'^\s+', ''),          # Leading spaces on lines 
            (r'\s+$', ''),          # Trailing spaces on lines
        ]
        
        for pattern, replacement in replacements:
            ocr_text = re.sub(pattern, replacement, ocr_text)
        
        # Process each line to filter out garbage
        cleaned_lines = []
        for line in ocr_text.split('\n'):
            line = line.strip()
            
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
        text = re.sub(r'\n{3,}', '\n\n', text)  # No more than 2 consecutive newlines
        
        return text

    def __init__(self, ocr_text: str, corrected_values: Optional[OCRTemplateCorrection] = None):
        """
        Initialize with OCR text and optional corrected values.
        If corrected values are provided, constructs a new template.
        """
        # Preprocess OCR text to clean up artifacts
        cleaned_ocr_text = self._preprocess_ocr_text(ocr_text)

        self.lines = cleaned_ocr_text.strip().split('\n')
        self.corrected_values = corrected_values

        self.merchant_name = self._find_merchant_name()

        print("merchant_name", self.merchant_name)

        # removed detect_currency() call

        if corrected_values:
            # Create a new template from corrections
            self.template_data = self._create_template_from_corrections()

    # currency_code is still unset
    def _detect_currency(self):
        """
        Detect currency symbol and code from OCR text by analyzing each line.
        Uses iso4217parse library to identify currency symbols.
        """

        # Count currency occurrences across all lines
        currency_counts = Counter()

        found_symbols = regex.findall(r'\p{Sc}', "".join(self.lines))

        for symbol in found_symbols:
            currency_counts[symbol] += 1

        # Use the most common currency, fallback to default (GBP)
        if currency_counts:
            self.currency_symbol = currency_counts.most_common(1)[0][0]
            self.currency_code = "unset"

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
        
        # First, find the earliest occurrence of ANY item in the OCR text
        # This ensures we don't miss the start of the items section if the first
        # corrected item isn't actually the first one in the receipt
        earliest_start = None
        earliest_item = None
        
        for item in cost_list:
            item_name = item['item']
            for i, line in enumerate(self.lines):
                if item_name in line:
                    if earliest_start is None or i < earliest_start:
                        earliest_start = i
                        earliest_item = item
                    break
        
        # Use the earliest found item as our starting point
        if earliest_start is not None:
            start_line = earliest_start
            logger.info(f"Found earliest item '{earliest_item['item']}' at line {start_line}")
        else:
            logger.warning("Could not find any corrected items in OCR text")
            return None, None, []

        # Now that we have the correct starting point, find all items
        # This will include items that might appear before others in the user's correction list
        for item in cost_list:
            item_found = False
            # Start searching from the earliest start line we found
            for i in range(start_line, len(self.lines)):
                # Check for exact match or if the item name is contained within the line
                # This helps with multiline items or items with slight OCR differences
                if item['item'] in self.lines[i]:
                    items_found.append({
                        'line': i,
                        'content': self.lines[i],
                        'item': item
                    })
                    if end_line is None or i > end_line:
                        end_line = i
                    item_found = True
                    break
                    
            if not item_found:
                # If we couldn't find an exact match, try a more lenient search
                # This helps with OCR errors or slight formatting differences
                for i in range(start_line, len(self.lines)):
                    # Check if at least 60% of the item name words appear in the line
                    item_words = set(item['item'].lower().split())
                    line_words = set(self.lines[i].lower().split())
                    common_words = item_words.intersection(line_words)
                    
                    if len(common_words) >= max(1, len(item_words) * 0.6):
                        items_found.append({
                            'line': i,
                            'content': self.lines[i],
                            'item': item
                        })
                        if end_line is None or i > end_line:
                            end_line = i
                        break

        # Sort found items by line number to preserve receipt order
        items_found.sort(key=lambda x: x['line'])
        
        if not items_found:
            logger.warning("Could not locate any corrected items in OCR text")
            return None, None, []
            
        logger.info(f"Found {len(items_found)}/{len(cost_list)} corrected items, from line {start_line} to {end_line}")
        print("items_found", items_found)
        return start_line, end_line, items_found

    def _create_line_item_regex(self, item_lines: List[Dict[str, Any]]) -> Optional[LineItemMatcher]:
        """
        Create regex patterns for line items based on the structure observed.
        Uses a library of common patterns and selects the one that matches the most lines.
        """
        if not item_lines:
            return None

        # Library of common line item regex patterns with capture groups
        COMMON_PATTERNS = [
            # Pattern 1: Quantity Item Price
            # Example: "2 MILK 1.80"
            {
                "pattern": r"(\d+(?:\.\d+)?)\s+([A-Za-z0-9\s&'.,\-]+?)\s+(?:[£$€])?(\d+\.\d{2})",
                "groups": {"quantity": 1, "item_name": 2, "total_price": 3}
            },
            
            # Pattern 2: Quantity x Item Price
            # Example: "2 x MILK 1.80" or "2x MILK 1.80"
            {
                "pattern": r"(\d+(?:\.\d+)?)\s*[xX]\s+([A-Za-z0-9\s&'.,\-]+?)\s+(?:[£$€])?(\d+\.\d{2})",
                "groups": {"quantity": 1, "item_name": 2, "total_price": 3}
            },
            
            # Pattern 3: Item Quantity Price
            # Example: "MILK 2 1.80"
            {
                "pattern": r"([A-Za-z0-9\s&'.,\-]+?)\s+(\d+(?:\.\d+)?)\s+(?:[£$€])?(\d+\.\d{2})",
                "groups": {"item_name": 1, "quantity": 2, "total_price": 3}
            },
            
            # Pattern 4: Item Price (quantity implied as 1)
            # Example: "MILK 1.80"
            {
                "pattern": r"([A-Za-z0-9\s&'.,\-]+?)\s+(?:[£$€])?(\d+\.\d{2})",
                "groups": {"item_name": 1, "total_price": 2, "quantity": 1}  # quantity will be set to 1
            },
            
            # Pattern 5: Item Quantity Unit_Price Total_Price
            # Example: "MILK 2 0.90 1.80"
            {
                "pattern": r"([A-Za-z0-9\s&'.,\-]+?)\s+(\d+(?:\.\d+)?)\s+(?:[£$€])?(\d+\.\d{2})\s+(?:[£$€])?(\d+\.\d{2})",
                "groups": {"item_name": 1, "quantity": 2, "unit_price": 3, "total_price": 4}
            },
            
            # Pattern 6: Quantity Item Unit_Price Total_Price
            # Example: "2 MILK 0.90 1.80"
            {
                "pattern": r"(\d+(?:\.\d+)?)\s+([A-Za-z0-9\s&'.,\-]+?)\s+(?:[£$€])?(\d+\.\d{2})\s+(?:[£$€])?(\d+\.\d{2})",
                "groups": {"quantity": 1, "item_name": 2, "unit_price": 3, "total_price": 4}
            },
            
            # Pattern 7: "Pkg" after quantity (common in some stores)
            # Example: "2 Pkg MILK 1.80"
            {
                "pattern": r"(\d+(?:\.\d+)?)\s+(?:Pkg|PKG|pkg)\s+([A-Za-z0-9\s&'.,\-]+?)\s+(?:[£$€])?(\d+\.\d{2})",
                "groups": {"quantity": 1, "item_name": 2, "total_price": 3}
            },
            
            # Pattern 8: Item with weight (kg/lb)
            # Example: "BANANAS 0.5 kg 1.50"
            {
                "pattern": r"([A-Za-z0-9\s&'.,\-]+?)\s+(\d+(?:\.\d+)?)\s*(?:kg|g|lb|oz)\s+(?:[£$€])?(\d+\.\d{2})",
                "groups": {"item_name": 1, "quantity": 2, "total_price": 3}
            }
        ]

        # Test each pattern against all item lines
        pattern_scores = []
        
        for pattern_def in COMMON_PATTERNS:
            pattern = pattern_def["pattern"]
            groups = pattern_def["groups"]
            score = 0
            matches = []
            
            # Test this pattern against each line
            for item in item_lines:
                line = item['content']
                match = re.search(pattern, line)
                
                if match:
                    # Verify the match returns expected values
                    expected_values = {}
                    for field, group_idx in groups.items():
                        if group_idx is not None and group_idx <= len(match.groups()):
                            expected_values[field] = match.group(group_idx)
                        elif field == "quantity":
                            expected_values[field] = "1"  # Default quantity
                    
                    # Check if extracted data matches corrected values
                    correct_match = True
                    if "quantity" in expected_values and "quantity" in item['item']:
                        if expected_values["quantity"] != item['item']["quantity"]:
                            correct_match = False
                    
                    if "item_name" in expected_values:
                        # Use fuzzy matching for item name because exact match might be too strict
                        if item['item']["item"] not in expected_values["item_name"] and expected_values["item_name"] not in item['item']["item"]:
                            correct_match = False
                    
                    if "total_price" in expected_values:
                        if expected_values["total_price"] != item['item']["total"]:
                            correct_match = False
                    
                    if correct_match:
                        score += 1
                        matches.append(line)
            
            # Store score and matches for this pattern
            pattern_scores.append({
                "pattern": pattern,
                "groups": groups,
                "score": score,
                "matches": matches,
                "coverage": score / len(item_lines) if item_lines else 0
            })
        
        # Sort patterns by score (highest first)
        pattern_scores.sort(key=lambda x: x["score"], reverse=True)
        
        # If we have a pattern with good coverage, use it
        if pattern_scores and pattern_scores[0]["coverage"] >= 0.5:  # At least 50% match
            best_pattern = pattern_scores[0]
            logger.info(f"Selected line item pattern with {best_pattern['score']}/{len(item_lines)} matches")
            
            return {
                'start_line': item_lines[0]['line'],
                'regex': best_pattern['pattern'],
                'groups': best_pattern['groups']
            }
        
        # If no pattern matches well, fall back to creating a custom pattern
        # This is a last resort when standard patterns don't work
        logger.warning(f"No common pattern matched well, creating custom pattern")
        
        # Create a pattern that matches the first item as a fallback
        item = item_lines[0]
        line = item['content']
        quantity = item['item'].get('quantity', '1')
        item_name = item['item']['item']
        price = item['item']['total']
        
        # Try to create a more generic pattern based on the structure
        # Look for numbers and text blocks
        numbers = re.findall(r'\d+(?:\.\d+)?', line)
        text_blocks = re.findall(r'[A-Za-z]{2,}(?:\s+[A-Za-z]+)*', line)
        
        if len(numbers) >= 2 and text_blocks:
            # Likely structure: [quantity] [item] [price]
            custom_pattern = r'.*?(\d+(?:\.\d+)?).*?([A-Za-z0-9\s&\'.,\-]+?).*?(\d+\.\d{2}).*'
            custom_groups = {"quantity": 1, "item_name": 2, "total_price": 3}
            
            if quantity == "1" and not re.search(r'\b1\b', line):
                # Quantity might be implicit, structure: [item] [price]
                custom_pattern = r'.*?([A-Za-z0-9\s&\'.,\-]+?).*?(\d+\.\d{2}).*'
                custom_groups = {"item_name": 1, "total_price": 2, "quantity": None}
        else:
            # Fall back to exact matching if structure is unclear
            quantity_escaped = re.escape(quantity)
            item_escaped = re.escape(item_name)
            price_escaped = re.escape(price)
            
            custom_pattern = f".*({quantity_escaped}).*({item_escaped}).*({price_escaped}).*"
            custom_groups = {"quantity": 1, "item_name": 2, "total_price": 3}
        
        return {
            'start_line': item_lines[0]['line'],
            'regex': custom_pattern,
            'groups': custom_groups
        }

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
                    field_extractors['merchant_name'] = {
                        'line': i,
                        'offset_from_last_item': None,
                        'regex': merchant_name,
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

        print("------------------------------------------------------------")
        # Process address (typically at the top) with multi-algorithm fuzzy matching
        if self.corrected_values and self.corrected_values.get('address'):
            from rapidfuzz import fuzz, process
            
            address = self.corrected_values['address']
            best_pattern = None
            best_line = -1
            best_score = 0
            best_method = None
            
            # Try to find the line with the closest match to the address
            for i, line in enumerate(self.lines[:15]):  # Check first 15 lines
                # Calculate similarity using multiple algorithms
                ratio_score = fuzz.ratio(address.lower(), line.lower())
                partial_score = fuzz.partial_ratio(address.lower(), line.lower())
                token_score = fuzz.token_sort_ratio(address.lower(), line.lower())
                token_set_score = fuzz.token_set_ratio(address.lower(), line.lower())
                
                # Use the best score from any method
                score = max(ratio_score, partial_score, token_score, token_set_score)
                method = ["ratio", "partial_ratio", "token_sort_ratio", "token_set_ratio"][
                    [ratio_score, partial_score, token_score, token_set_score].index(score)
                ]
                
                # If this line is a better match than what we've seen, store it
                if score > best_score and score > 70:  # Threshold of 70%
                    best_score = score
                    best_line = i
                    best_method = method
                    
                    # Try to match using our predefined patterns first
                    for pattern in self.FIELD_PATTERNS['merchant_address']:
                        match = re.search(pattern, line)
                        if match and match.group(1):
                            # Verify the extracted address matches our expected address
                            extracted = match.group(1)
                            # Check similarity of extracted text to our address
                            extract_scores = [
                                fuzz.ratio(address.lower(), extracted.lower()),
                                fuzz.partial_ratio(address.lower(), extracted.lower()),
                                fuzz.token_sort_ratio(address.lower(), extracted.lower()),
                                fuzz.token_set_ratio(address.lower(), extracted.lower())
                            ]
                            extract_score = max(extract_scores)
                            if extract_score > 70:
                                best_pattern = pattern
                                logger.info(f"Found address pattern match with {extract_score}% similarity")
                                break
            
            # For address not found with existing patterns but match found with fuzzy matching
            if best_line >= 0 and not best_pattern:
                logger.info(f"Address matched line {best_line} with {best_score}% similarity using {best_method}")
                
                # Create a pattern based on address components for more flexible matching
                address_parts = address.split()
                if len(address_parts) > 2:
                    # For multi-word addresses, create a more flexible pattern
                    # Focus on distinctive parts (longer words, numbers)
                    significant_parts = [
                        part for part in address_parts 
                        if len(part) > 3 or any(c.isdigit() for c in part)
                    ]
                    
                    if significant_parts:
                        # Join significant parts with OR operator
                        parts_pattern = '|'.join(re.escape(part) for part in significant_parts)
                        best_pattern = f".*({parts_pattern}).*"
                    else:
                        # If no significant parts, use the address as is
                        best_pattern = f".*({re.escape(address)}).*"
                else:
                    # For short addresses, use the whole address
                    best_pattern = f".*({re.escape(address)}).*"

            if best_line >= 0:
                field_extractors['merchant_address'] = {
                    'line': best_line,
                    'offset_from_last_item': None,
                    'regex': best_pattern,
                    'expected_present': True
                }
        print("------------------------------------------------------------")

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

        print("template", template)

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

        print("currency code:", self.currency_code)
        print("currency symbol", self.currency_symbol)

        extracted_data = {}
        field_extractors = template_model_data.get('field_extractors', {})
        has_line_items = template_model_data.get('has_line_items', True)

        print("I'm here (extract)")

        # First pass: extract fields with absolutedb.collection_name.deleteMany({}) line positions
        for field, extractor in field_extractors.items():
            if not extractor.get('expected_present', True):
                continue

            # Get line position information
            line = extractor.get('line')

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
                # Keep track of the current item for potential multiline descriptions
                current_item = None
                i = start_line
                
                while i < len(self.lines):
                    matched = False
                    # Try to match this line against our item patterns
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
                                    if group_idx is not None and len(match.groups()) >= group_idx:
                                        item_data[field] = match.group(group_idx)
                                    elif field == "quantity" and group_idx is None:
                                        item_data[field] = "1"  # Default quantity if not in pattern

                                if item_data:
                                    # Found a new regular item
                                    line_items.append(item_data)
                                    current_item = item_data  # Track as current item for potential continuation
                                    end_line = i
                                    matched = True
                                    break
                        if matched:
                            break

                    if not matched:
                        # This line didn't match any item pattern
                        
                        # Check if it might be a continuation of the previous item
                        if current_item and i == end_line + 1:
                            line_text = self.lines[i].strip()
                            
                            # Skip lines that look like they're not part of an item description
                            # These lines indicate either the end of the item or the start of a new item
                            skip_patterns = [
                                r'^\s*\d+\.\d{2}\s*$',                    # Just a price
                                r'^\s*(?:total|subtotal|tax|vat|savings|promotions)[\s:]+', # Common receipt sections
                                r'^\s*$',                                 # Empty line
                                r'^\s*[-=*]+\s*$',                        # Separator line
                                r'^\s*\d+(?:\s*x)?\s*\d+\.\d{2}',         # Quantity and price pattern
                                r'^\s*[£$€]?\d+\.\d{2}\s*(?:-[£$€]?\d+\.\d{2})?$', # Price or discount pattern
                                r'^\s*[£$€]?\d+\.\d{2}\s*each',           # Unit price pattern
                                r'^\s*\d+\s+',                            # Line starting with quantity (new item)
                                r'^[Cc][Cc]',                             # Card or loyalty card references
                            ]
                            
                            is_skip_line = any(re.search(pattern, line_text, re.IGNORECASE) 
                                              for pattern in skip_patterns)
                            
                            # Don't treat very short lines as continuations (likely OCR artifacts)
                            if not is_skip_line and len(line_text) > 2:
                                # Append to the item name field
                                item_name_field = 'item_name' if 'item_name' in current_item else 'item'
                                if item_name_field in current_item:
                                    current_item[item_name_field] += ' ' + line_text
                                    end_line = i  # Update end_line to include this continuation
                                    matched = True
                            
                        if not matched and line_items:
                            # If we didn't find a match for any pattern, check if we already found items
                            # If we've already found items, this could be the end of the items section
                            # Try a few more lines before giving up
                            if i > end_line + 3:
                                break
                    
                    i += 1

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

        print(extracted_data)

        return extracted_data
