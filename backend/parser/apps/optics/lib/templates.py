from typing import TypedDict, List, Dict, Any, Optional, Tuple, Union
import re
import logging
from collections import Counter
import regex 
import json

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
    is_fuzzy_haystack: bool  # Whether this field uses reverse fuzzy matching


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

    def __init__(self, ocr_text: str, corrected_values: Optional[OCRTemplateCorrection] = None):
        """
        Initialize with OCR text and optional corrected values.
        If corrected values are provided, constructs a new template.
        """

        self.lines = ocr_text.strip().split('\n')
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
            self.currency_code = "N/A"

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

    def _find_line_items(self) -> Tuple[int, int, List[Dict[str, Any]]]:
        """
        Locate line items in the receipt and extract their information.
        Returns: (start_line, end_line, extracted_items)
        """
        if not self.corrected_values or 'cost_list' not in self.corrected_values:
            return -1, -1, []

        cost_list = self.corrected_values['cost_list']
        if not cost_list:
            return -1, -1, []

        # Search for line items based on the corrected data
        start_line = -1
        end_line = -1
        items_found = []
        
        # First, find the earliest occurrence of ANY item in the OCR text
        # This ensures we don't miss the start of the items section if the first
        # corrected item isn't actually the first one in the receipt
        earliest_start = None
        earliest_item: OCRTemplateCostList
        
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
            return -1, -1, []

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
            return -1, -1, []
            
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

    def _find_field_positions(self, start_line: int, end_line: int) -> Dict[str, FieldExtractor]:
        """
        Determine positions of fields relative to line items or absolute positions.
        Uses fuzzy matching to find field positions and predefined patterns to create the best extractors.
        """
        from rapidfuzz import fuzz
        
        field_extractors = {}
        field_mapping = {
            'merchant_name': 'merchant_name',
            'date': 'transaction_time',
            'address': 'merchant_address',
            'reference': 'reference_number',
            'total_amount': 'total_amount',
            'tax': 'tax_amount',
            'subtotal_amount': 'subtotal_amount'
        }
        
        # Skip if no corrections provided
        if not self.corrected_values:
            return field_extractors


        before_items = list(range(0, start_line))
        after_items = list(range(end_line + 1, len(self.lines)))
        search_range = before_items + after_items

        # Process each corrected field
        for user_field, system_field in field_mapping.items():
            # Skip if this field wasn't corrected
            if not self.corrected_values.get(user_field):
                continue
                
            corrected_value = self.corrected_values[user_field]
            is_fuzzy_haystack = False
            best_line: int = -1
            best_pattern = None
            best_offset = None
            best_score = 0

            if system_field == 'merchant_name':
                search_range = range(min(end_line, len(self.lines), 3))
            else:
                before_items = list(range(0, start_line))
                after_items = list(range(end_line + 1, len(self.lines)))
                search_range = before_items + after_items

            
            # Find best matching line using fuzzy matching
            for i in search_range:
                line = self.lines[i]
                
                # Calculate similarity score between line and corrected value
                score = fuzz.ratio(corrected_value.lower(), line.lower())
                partial_score = fuzz.partial_ratio(corrected_value.lower(), line.lower())
                token_score = fuzz.token_sort_ratio(corrected_value.lower(), line.lower())
                token_set_score = fuzz.token_set_ratio(corrected_value.lower(), line.lower())
                
                max_score = max(score, partial_score, token_score, token_set_score)
                
                # Check for reversed match (line is part of corrected value)
                # Useful for multi-line fields like address
                reverse_score = fuzz.ratio(line.lower(), corrected_value.lower())

                print(f"{system_field} - line {i} - {corrected_value} >> max: {max_score} and reverse: {reverse_score}")
                print(f"\t{line}")
                
                # If this line matches better than previous ones
                if max_score > best_score and max_score > 70:
                    best_score = max_score
                    print("—————————————————————", best_score)
                    if end_line is not None and i > end_line:
                        best_offset = i - end_line
                        best_line = -1
                    else:
                        best_line = i
                        best_offset = None
                
                # Check for multi-line scenario (especially for addresses)
                if system_field == 'merchant_address' and reverse_score > 80 and reverse_score > best_score:
                    is_fuzzy_haystack = True
                    best_score = reverse_score
                    best_line = i
                    best_offset = None

            print(f"best_line: {best_line}. best_offset: {best_offset}")
            
            # If we found a matching line
            if best_line >= 0 or best_offset is not None:
                # Try each pattern from FIELD_PATTERNS to find best performing one
                patterns = self.FIELD_PATTERNS.get(system_field, [])
                print("patterns", patterns)
                target_line: int = 0
                if best_offset is None:
                    target_line = best_line
                else:
                    target_line = end_line + best_offset

                if 0 <= target_line < len(self.lines):
                    best_pattern_score = 0
                    
                    for pattern in patterns:
                        match = re.search(pattern, self.lines[target_line])
                        if match and match.groups():
                            extracted = match.group(1)
                            
                            # Score this extraction against corrected value
                            pattern_score = fuzz.ratio(corrected_value, extracted)
                            
                            if pattern_score > best_pattern_score:
                                best_pattern_score = pattern_score
                                best_pattern = pattern
                
                # If no pattern matched well, create a custom one
                if not best_pattern:
                    if system_field in ['total_amount', 'tax_amount', 'subtotal_amount'] and self.currency_symbol:
                        best_pattern = f".*(?:{re.escape(self.currency_symbol)})?\\s*({re.escape(corrected_value)}).*"
                    else:
                        best_pattern = f".*({re.escape(corrected_value)}).*"
                
                # Create the field extractor
                field_extractors[system_field] = {
                    'line': best_line,
                    'offset_from_last_item': best_offset,
                    'regex': best_pattern,
                    'expected_present': True,
                    'is_fuzzy_haystack': is_fuzzy_haystack if is_fuzzy_haystack else False
                }
                
                logger.info(f"Found {system_field} at {'line ' + str(best_line) if best_line >= 0 else 'offset ' + str(best_offset)} with score {best_score}")
        
        return field_extractors

    def _create_template_from_corrections(self) -> TemplateData:
        """
        Create a template based on user corrections.
        """
        # Find line items section
        start_line, end_line, items = self._find_line_items()

        # Create template structure
        template: TemplateData = {
            'field_extractors': self._find_field_positions(start_line, end_line),
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

        print("\ntemplate_data =======================================================================")
        print(json.dumps(self.template_data, indent=3))
        print("=====================================================================================\n")

        # Convert our simplified field_extractors to the model format
        for field, extractor in self.template_data['field_extractors'].items():
            print(field)
            print(json.dumps(extractor), "\n")
            field_extractors[field] = {
                'expected_present': extractor.get('expected_present', True),
                'patterns': [extractor['regex']],
                'is_fuzzy_haystack': extractor.get('is_fuzzy_haystack', False)
            }

            if extractor['line'] is not None:
                field_extractors[field]['line'] = extractor['line']
            if 'offset_from_last_item' in extractor:
                if extractor['offset_from_last_item'] is None:
                    extractor['offset_from_last_item'] = 0
                field_extractors[field]['offset_from_last_item'] = int(extractor['offset_from_last_item'])

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
        print("\n=====================================================================================")
        print("\nEXTRACTING")
        print("\n=====================================================================================\n")
        # First detect the currency before extraction
        self._detect_currency()

        print("currency code:", self.currency_code)
        print("currency symbol", self.currency_symbol)

        extracted_data = {}
        field_extractors = template_model_data.get('field_extractors', {})
        has_line_items = template_model_data.get('has_line_items', True)

        print("I'm here (extract)")

        # First pass: extract fields with absolute line positions
        for field, extractor in field_extractors.items():
            if not extractor.get('expected_present', True):
                continue

            # Get line position information
            line = extractor.get('line')
            is_fuzzy_haystack = extractor.get('is_fuzzy_haystack', False)

            # If we have a direct line number, use it
            if line is not None and 0 <= line < len(self.lines):
                patterns = extractor.get('patterns', [])
                if not patterns and 'regex' in extractor:
                    patterns = [extractor['regex']]

                # For monetary fields, create currency-aware variants
                if field in ['total_amount', 'tax_amount', 'subtotal_amount'] and self.currency_symbol:
                    # Create pattern variants with and without currency symbol
                    currency_patterns = []
                    for pattern in patterns:
                        if '\\d+\\.\\d{2}' in pattern:
                            symbol_pattern = pattern.replace('(\\d+\\.\\d{2})',
                                                             f'(?:{re.escape(self.currency_symbol)})?\\s*(\\d+\\.\\d{2})')
                            currency_patterns.append(symbol_pattern)
                    patterns = currency_patterns + patterns

                # Try each pattern
                for pattern in patterns:
                    if not pattern:
                        continue

                    # Handle fuzzy haystack case (multi-line fields)
                    if is_fuzzy_haystack:
                        from rapidfuzz import fuzz
                        
                        # In fuzzy haystack mode, the corrected value is in the regex pattern
                        # and we need to find it in the surrounding lines
                        haystack = re.sub(r'^\.\*\(', '', pattern)
                        haystack = re.sub(r'\)\.\*$', '', haystack)
                        haystack = re.sub(r'\\', '', haystack)  # Remove escaping
                        
                        # Check current line and a few lines below for matches
                        best_match = ""
                        best_score = 0
                        
                        for i in range(line, min(line + 5, len(self.lines))):
                            score = fuzz.partial_ratio(self.lines[i].lower(), haystack.lower())
                            if score > best_score and score > 70:
                                best_score = score
                                if best_match:
                                    best_match += " " + self.lines[i]
                                else:
                                    best_match = self.lines[i]
                        
                        if best_match:
                            extracted_data[field] = best_match
                            break
                    else:
                        # Standard regex matching
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
                
                print("LINE ITEMS")
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
                                print("---------------------- ITEM_DATA --------------------")
                                if set(["total_price", "quantity"]).issubset(pattern_def['groups'].keys()):
                                    item_data['unit_price'] = f"{(float(item_data['total_price']) / float(item_data['quantity'])):.2f}"
                                print(json.dumps(item_data))
                                print("---------------------- ITEM_DATA END --------------------")
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

        print("LAST_ITEM_LINE")
        print(json.dumps(extracted_data[ '_last_item_line' ]))

        # Second pass: extract fields with relative positions from line items
        if '_last_item_line' in extracted_data:
            print("HERE")
            print(json.dumps(field_extractors, indent=3))
            last_item_line = extracted_data['_last_item_line']

            for field, extractor in field_extractors.items():
                if field in extracted_data or not extractor.get('expected_present', True):
                    continue

                offset = extractor.get('offset_from_last_item')
                is_fuzzy_haystack = extractor.get('is_fuzzy_haystack', False)
                
                if offset is not None:
                    target_line = last_item_line + offset
                    if 0 <= target_line < len(self.lines):
                        patterns = extractor.get('patterns', [])
                        if not patterns and 'regex' in extractor:
                            patterns = [extractor['regex']]

                        # For monetary fields, create currency-aware variants
                        if field in ['total_amount', 'tax_amount', 'subtotal_amount'] and self.currency_symbol:
                            currency_patterns = []
                            for pattern in patterns:
                                if '\\d+\\.\\d{2}' in pattern:
                                    symbol_pattern = pattern.replace('(\\d+\\.\\d{2})',
                                                                    f'(?:{re.escape(self.currency_symbol)})?\\s*(\\d+\\.\\d{2})')
                                    currency_patterns.append(symbol_pattern)
                            patterns = currency_patterns + patterns

                        for pattern in patterns:
                            if not pattern:
                                continue
                                
                            # Handle fuzzy haystack case (multi-line fields)
                            if is_fuzzy_haystack:
                                from rapidfuzz import fuzz
                                
                                # In fuzzy haystack mode, the corrected value is in the regex pattern
                                # and we need to find it in the surrounding lines
                                haystack = re.sub(r'^\.\*\(', '', pattern)
                                haystack = re.sub(r'\)\.\*$', '', haystack)
                                haystack = re.sub(r'\\', '', haystack)  # Remove escaping
                                
                                # Check current line and a few lines below for matches
                                best_match = ""
                                best_score = 0
                                
                                for i in range(target_line, min(target_line + 5, len(self.lines))):
                                    score = fuzz.partial_ratio(self.lines[i].lower(), haystack.lower())
                                    if score > best_score and score > 70:
                                        best_score = score
                                        if best_match:
                                            best_match += " " + self.lines[i]
                                        else:
                                            best_match = self.lines[i]
                                
                                if best_match:
                                    extracted_data[field] = best_match
                                    break
                            else:
                                # Standard regex matching
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

        print("extracted_data", extracted_data)

        return extracted_data
