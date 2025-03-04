from djongo import models
from django.utils import timezone
from django.core.exceptions import ValidationError
import re

def validate_currency_info(value):
    """
    Validates the currency_info JSON structure.
    
    Required fields:
    - iso_code: 3-letter currency code (ISO 4217)
    - symbol: Currency symbol
    - decimal_separator: Character used to separate decimals
    - thousands_separator: Character used to separate thousands
    - typical_format: Example of formatted currency
    """
    required_fields = ['iso_code', 'symbol', 'decimal_separator', 'thousands_separator']
    
    if not isinstance(value, dict):
        raise ValidationError("Currency info must be a dictionary")
    
    # Check required fields
    for field in required_fields:
        if field not in value:
            raise ValidationError(f"Missing required field '{field}' in currency_info")
    
    # Validate ISO code format (3 uppercase letters)
    if not re.match(r'^[A-Z]{3}$', value.get('iso_code', '')):
        raise ValidationError("Currency iso_code must be 3 uppercase letters (ISO 4217 format)")
    
    # Validate separators (must be single characters)
    if len(value.get('decimal_separator', '')) != 1:
        raise ValidationError("decimal_separator must be a single character")
    
    if len(value.get('thousands_separator', '')) != 1:
        raise ValidationError("thousands_separator must be a single character")


def validate_field_extractors(value):
    """
    Validates the field_extractors JSON structure.
    
    Each field extractor should have:
    - expected_present: Boolean indicating if field is expected
    - patterns: List of regex patterns for extraction
    - Optional: line_hints or context_words for locating field
    """
    if not isinstance(value, dict):
        raise ValidationError("field_extractors must be a dictionary")
    
    for field_name, extractor in value.items():
        # Check basic structure
        if not isinstance(extractor, dict):
            raise ValidationError(f"Extractor for '{field_name}' must be a dictionary")
        
        # Check required fields
        if 'expected_present' not in extractor:
            raise ValidationError(f"Missing 'expected_present' in extractor for '{field_name}'")
        
        if 'patterns' not in extractor:
            raise ValidationError(f"Missing 'patterns' in extractor for '{field_name}'")
        
        # Validate patterns are list of strings
        patterns = extractor.get('patterns', [])
        if not isinstance(patterns, list):
            raise ValidationError(f"'patterns' for '{field_name}' must be a list")
        
        # Validate each pattern is a valid regex
        for pattern in patterns:
            if not isinstance(pattern, str):
                raise ValidationError(f"Pattern in '{field_name}' must be a string")
            try:
                re.compile(pattern)
            except re.error:
                raise ValidationError(f"Invalid regex pattern in '{field_name}': {pattern}")
        
        # Validate line_hints if present
        line_hints = extractor.get('line_hints', [])
        if line_hints and not isinstance(line_hints, list):
            raise ValidationError(f"'line_hints' for '{field_name}' must be a list of integers")
        
        # Validate context_words if present
        context_words = extractor.get('context_words', [])
        if context_words and not isinstance(context_words, list):
            raise ValidationError(f"'context_words' for '{field_name}' must be a list of strings")


def validate_item_patterns(value):
    """
    Validates the item_patterns JSON structure.
    
    Each item pattern should have:
    - pattern: Regex pattern for matching line items
    - groups: Dictionary mapping field names to capture group indices
    """
    if not isinstance(value, list):
        raise ValidationError("item_patterns must be a list")
    
    for i, pattern_def in enumerate(value):
        if not isinstance(pattern_def, dict):
            raise ValidationError(f"Item pattern at index {i} must be a dictionary")
        
        # Check required fields
        if 'pattern' not in pattern_def:
            raise ValidationError(f"Missing 'pattern' in item pattern at index {i}")
        
        if 'groups' not in pattern_def:
            raise ValidationError(f"Missing 'groups' in item pattern at index {i}")
        
        # Validate pattern is a valid regex
        try:
            re.compile(pattern_def['pattern'])
        except re.error:
            raise ValidationError(f"Invalid regex in item pattern at index {i}")
        
        # Validate groups are a dictionary mapping names to indices
        groups = pattern_def.get('groups', {})
        if not isinstance(groups, dict):
            raise ValidationError(f"'groups' in item pattern at index {i} must be a dictionary")
        
        for field, group_idx in groups.items():
            if not isinstance(field, str):
                raise ValidationError(f"Group field name must be a string in item pattern at index {i}")
            
            if not isinstance(group_idx, int) or group_idx < 1:
                raise ValidationError(f"Group index for '{field}' must be a positive integer in item pattern at index {i}")


def validate_field_accuracy(value):
    """
    Validates the field_accuracy JSON structure.
    
    Each field should map to a percentage value (0-100)
    """
    if not isinstance(value, dict):
        raise ValidationError("field_accuracy must be a dictionary")
    
    for field, accuracy in value.items():
        if not isinstance(accuracy, (int, float)):
            raise ValidationError(f"Accuracy for '{field}' must be a number")
        
        if accuracy < 0 or accuracy > 100:
            raise ValidationError(f"Accuracy for '{field}' must be between 0 and 100")


class ReceiptTemplate(models.Model):
    """
    MongoDB-backed template model for pattern-based receipt parsing.
    Templates evolve through continuous refinement from user corrections.
    """
    # Tracking metadata
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    usage_count = models.IntegerField(default=0)
    success_rate = models.FloatField(default=0.0)  # 0-100 percentage
    is_archived = models.BooleanField(default=False)
    
    # Merchant identifiers
    merchant_name = models.CharField(max_length=255)
    
    # Currency information - stored as a nested document
    currency_info = models.JSONField(
        default=dict,
        validators=[validate_currency_info]
    )
    # Example structure:
    # {
    #    "iso_code": "GBP",
    #    "symbol": "£",
    #    "decimal_separator": ".",
    #    "thousands_separator": ",",
    #    "typical_format": "£X,XXX.XX"
    # }
    
    # Field extractors - complex patterns for finding specific data points
    field_extractors = models.JSONField(
        default=dict,
        validators=[validate_field_extractors]
    )
    # Example structure:
    # {
    #    "merchant_name": {
    #        "expected_present": true,
    #        "patterns": ["^([A-Z][A-Z\\s&.']+)$"],
    #        "line_hints": [0, 1]
    #    },
    #    "date": {
    #        "expected_present": true,
    #        "patterns": ["Date:\\s*(\\d{1,2}/\\d{1,2}/\\d{4})"],
    #        "context_words": ["date", "time"]
    #    }
    # }
    
    # Item patterns - for extracting line items from receipts
    item_patterns = models.JSONField(
        default=list,
        validators=[validate_item_patterns]
    )
    # Example structure:
    # [
    #    {
    #        "pattern": "^(.+?)\\s+£(\\d+\\.\\d{2})$",
    #        "groups": {"name": 1, "price": 2}
    #    }
    # ]
    
    # Field-specific accuracy tracking
    field_accuracy = models.JSONField(
        default=dict,
        validators=[validate_field_accuracy]
    )
    # Example structure:
    # {
    #    "merchant_name": 97.5,
    #    "date": 92.3,
    #    "total_amount": 95.1
    # }
    
    class Meta:
        db_table = 'receipt_templates'
        indexes = [
            models.Index(fields=['merchant_name']),
            models.Index(fields=['is_archived']),
        ]
    
    def __str__(self):
        return f"Template: {self.merchant_name} (Usage: {self.usage_count}, Success: {self.success_rate:.1f}%)"
    
    def calculate_updated_accuracy(self, field_name, current_result):
        """
        Updates accuracy metrics with weighted average approach:
        70% historical accuracy + 30% new result
        
        Args:
            field_name: The field being evaluated
            current_result: Boolean indicating if extraction was correct
        """
        current_accuracy = self.field_accuracy.get(field_name, 50.0)  # Default 50% if no data
        new_accuracy = 100.0 if current_result else 0.0
        
        # Calculate weighted average (70% historical, 30% new)
        updated_accuracy = (current_accuracy * 0.7) + (new_accuracy * 0.3)
        
        # Update the field_accuracy dictionary
        self.field_accuracy[field_name] = updated_accuracy
        return updated_accuracy
