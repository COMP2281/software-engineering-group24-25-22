from mongoengine import Document, StringField, DateTimeField, IntField
from mongoengine import FloatField, BooleanField, ListField, DictField
from django.utils import timezone
from django.core.exceptions import ValidationError
from typing import Optional
import re


def validate_currency_info(value):
    """
    Validates the currency_info JSON structure.

    Required fields:
    - iso_code: 3-letter currency code (ISO 4217)
    - symbol: Currency symbol
    """
    required_fields = ["iso_code", "symbol"]

    if not isinstance(value, dict):
        raise ValidationError("Currency info must be a dictionary")

    # Check required fields
    for field in required_fields:
        if field not in value:
            raise ValidationError(f"Missing required field '{field}' in currency_info")

    # Validate ISO code format (3 uppercase letters)
    if not re.match(r"^[A-Z]{3}$", value.get("iso_code", "")):
        raise ValidationError(
            "Currency iso_code must be 3 uppercase letters (ISO 4217 format)"
        )

    # Symbol can be empty, but if provided, should be a reasonable length
    symbol = value.get("symbol", "")
    if symbol and len(symbol) > 3:  # Most currency symbols are 1-3 characters
        raise ValidationError("Currency symbol is unusually long")


def validate_field_extractors(value):
    """
    Validates the field_extractors JSON structure.

    Each field extractor should have:
    - expected_present: Boolean indicating if field is expected
    - regex: Single regex pattern for extraction
    - One of:
      - line: Absolute line number for fields before line items
      - offset_from_last_item: Relative position from last line item
    - Optional:
      - is_fuzzy_haystack: Boolean indicating if this field uses reverse fuzzy matching
    """
    if not isinstance(value, dict):
        raise ValidationError("field_extractors must be a dictionary")

    for field_name, extractor in value.items():
        # Check basic structure
        if not isinstance(extractor, dict):
            raise ValidationError(f"Extractor for '{field_name}' must be a dictionary")

        # Check required fields
        if "expected_present" not in extractor:
            raise ValidationError(
                f"Missing 'expected_present' in extractor for '{field_name}'"
            )

        if not isinstance(extractor.get("expected_present"), bool):
            raise ValidationError(
                f"'expected_present' for '{field_name}' must be a boolean"
            )

        # Check for regex pattern (can be in 'regex' or 'patterns' for backward compatibility)
        has_regex = "regex" in extractor
        has_patterns = "patterns" in extractor

        if not (has_regex or has_patterns):
            raise ValidationError(f"Missing regex pattern for '{field_name}'")

        # Validate single regex
        if has_regex:
            regex = extractor.get("regex")
            if not isinstance(regex, str):
                raise ValidationError(f"'regex' for '{field_name}' must be a string")
            try:
                re.compile(regex)
            except re.error:
                raise ValidationError(
                    f"Invalid regex pattern in '{field_name}': {regex}"
                )

        # Validate patterns list (legacy format)
        if has_patterns:
            patterns = extractor.get("patterns", [])
            if not isinstance(patterns, list):
                raise ValidationError(f"'patterns' for '{field_name}' must be a list")

            # Validate each pattern is a valid regex
            for pattern in patterns:
                if not isinstance(pattern, str):
                    raise ValidationError(f"Pattern in '{field_name}' must be a string")
                try:
                    re.compile(pattern)
                except re.error:
                    raise ValidationError(
                        f"Invalid regex pattern in '{field_name}': {pattern}"
                    )

        # Validate position information - either line or offset_from_last_item must be present
        has_line = "line" in extractor
        has_offset = "offset_from_last_item" in extractor

        if not (has_line or has_offset):
            raise ValidationError(
                f"Field `{field_name}` must have position information (line or offset_from_last_item)"
            )

        if has_line and not isinstance(extractor["line"], int):
            raise ValidationError(f"'line' for '{field_name}' must be an integer")

        if has_offset and not isinstance(extractor["offset_from_last_item"], int):
            raise ValidationError(
                f"'offset_from_last_item' for '{field_name}' must be an integer"
            )

        # Validate is_fuzzy_haystack if present
        if "is_fuzzy_haystack" in extractor and not isinstance(
            extractor["is_fuzzy_haystack"], bool
        ):
            raise ValidationError(
                f"'is_fuzzy_haystack' for '{field_name}' must be a boolean"
            )

        # Validate context_words if present
        context_words = extractor.get("context_words", [])
        if context_words and not isinstance(context_words, list):
            raise ValidationError(
                f"'context_words' for '{field_name}' must be a list of strings"
            )


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
        if "pattern" not in pattern_def:
            raise ValidationError(f"Missing 'pattern' in item pattern at index {i}")

        if "groups" not in pattern_def:
            raise ValidationError(f"Missing 'groups' in item pattern at index {i}")

        # Validate pattern is a valid regex
        try:
            re.compile(pattern_def["pattern"])
        except re.error:
            raise ValidationError(f"Invalid regex in item pattern at index {i}")

        # Validate groups are a dictionary mapping names to indices
        groups = pattern_def.get("groups", {})
        if not isinstance(groups, dict):
            raise ValidationError(
                f"'groups' in item pattern at index {i} must be a dictionary"
            )

        for field, group_idx in groups.items():
            if not isinstance(field, str):
                raise ValidationError(
                    f"Group field name must be a string in item pattern at index {i}"
                )

            if not isinstance(group_idx, int) or group_idx < 1:
                raise ValidationError(
                    f"Group index for '{field}' must be a positive integer in item pattern at index {i}"
                )


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


def validate_field_edit_distances(value):
    """
    Validates the field_edit_distances JSON structure.

    Each field should map to a non-negative float value
    """
    if not isinstance(value, dict):
        raise ValidationError("field_edit_distances must be a dictionary")

    for field, distance in value.items():
        if not isinstance(distance, (int, float)):
            raise ValidationError(f"Edit distance for '{field}' must be a number")

        if distance < 0:
            raise ValidationError(f"Edit distance for '{field}' must be non-negative")


def validate_recent_usage(value):
    """
    Validates the recent_usage JSON structure.

    Should contain usage statistics for archiving decisions
    """
    if not isinstance(value, dict):
        raise ValidationError("recent_usage must be a dictionary")

    expected_fields = ["last_30_days", "total_merchant_uses", "usage_percentage"]

    # Not all fields may be required, but if present, they should be valid
    for field in expected_fields:
        if field in value:
            if not isinstance(value[field], (int, float)):
                raise ValidationError(f"'{field}' in recent_usage must be a number")

            if field == "usage_percentage" and (value[field] < 0 or value[field] > 100):
                raise ValidationError(f"usage_percentage must be between 0 and 100")
            elif field in ["last_30_days", "total_merchant_uses"] and value[field] < 0:
                raise ValidationError(f"'{field}' must be non-negative")


class ReceiptTemplate(Document):
    """
    MongoDB-backed template model for pattern-based receipt parsing.
    Templates evolve through continuous refinement from user corrections.
    """

    # Tracking metadata
    created_at = DateTimeField(default=timezone.now)
    updated_at = DateTimeField()
    last_used_at = DateTimeField(default=timezone.now)
    usage_count = IntField(default=0)
    success_rate = FloatField(default=0.0)  # 0-100 percentage
    override_rate = FloatField(default=0.0)  # 0-100 percentage
    avg_edit_distance = FloatField(default=0.0)  # Average character-level differences
    is_archived = BooleanField(default=False)
    archived_at = DateTimeField()

    # Additional metadata including source template info
    metadata = DictField(default=dict)

    # Merchant identifiers
    merchant_name = StringField(max_length=255, required=True)

    # Currency information - stored as a nested document
    currency_info = DictField(default=dict, validation=validate_currency_info)
    # Example structure:
    # {
    #    "iso_code": "GBP",
    #    "symbol": "£",
    #    "decimal_separator": ".",
    #    "thousands_separator": ",",
    #    "typical_format": "£X,XXX.XX"
    # }

    # Field extractors - complex patterns for finding specific data points
    field_extractors = DictField(default=dict, validation=validate_field_extractors)
    # Example structure:
    # {
    #    "merchant_name": {
    #        "expected_present": true,
    #        "patterns": ["^([A-Z][A-Z\\s&.']+)$"],
    #        "line": 0
    #    },
    #    "transaction_time": {
    #        "expected_present": true,
    #        "patterns": ["Date:\\s*(\\d{1,2}/\\d{1,2}/\\d{4})"],
    #        "line": 2
    #    },
    #    "total_amount": {
    #        "expected_present": true,
    #        "patterns": ["Total:\\s*£?(\\d+\\.\\d{2})"],
    #        "offset_from_last_item": 3
    #    }
    # }

    # Line items configuration
    has_line_items = BooleanField(default=True)
    line_items_start_line = IntField(default=5)

    # Item patterns - for extracting line items from receipts
    item_patterns = ListField(
        field=DictField(), default=list, validation=validate_item_patterns
    )
    # Example structure:
    # [
    #    {
    #        "pattern": "^(.+?)\\s+£(\\d+\\.\\d{2})$",
    #        "groups": {"name": 1, "price": 2}
    #    }
    # ]

    # Field-specific accuracy tracking
    field_accuracy = DictField(default=dict, validation=validate_field_accuracy)
    # Example structure:
    # {
    #    "merchant_name": 97.5,
    #    "transaction_time": 92.3,
    #    "total_amount": 95.1
    # }

    # Field-specific edit distances
    field_edit_distances = DictField(
        default=dict, validation=validate_field_edit_distances
    )
    # Example structure:
    # {
    #    "merchant_name": 0.5,  # Average edit distance for this field
    #    "transaction_time": 2.3,
    #    "total_amount": 0.1
    # }

    # Usage statistics for template archiving decisions
    recent_usage = DictField(default=dict, validation=validate_recent_usage)
    # Example structure:
    # {
    #    "last_30_days": 5,         # Number of uses in last 30 days
    #    "total_merchant_uses": 12, # Total uses across all templates for this merchant
    #    "usage_percentage": 41.6   # Percentage of merchant's templates uses (5/12 * 100)
    # }

    meta = {
        "collection": "receipt_templates",
        "indexes": ["merchant_name", "is_archived", "last_used_at"],
    }

    def __str__(self):
        status = "Archived" if self.is_archived else "Active"
        return f"Template: {self.merchant_name} ({status}, Usage: {self.usage_count}, Success: {self.success_rate:.1f}%)"

    def record_usage(self):
        """
        Update usage statistics when template is used
        """
        now = timezone.now()
        # With mongoengine directly, we modify attributes and save
        self.last_used_at = now
        self.usage_count += 1
        self.save()

    def calculate_updated_accuracy(self, field_name, current_result):
        """
        Updates accuracy metrics with weighted average approach:
        70% historical accuracy + 30% new result

        Args:
            field_name: The field being evaluated
            current_result: Boolean indicating if extraction was correct
        """
        current_accuracy = self.field_accuracy.get(
            field_name, 50.0
        )  # Default 50% if no data
        new_accuracy = 100.0 if current_result else 0.0

        # Calculate weighted average (70% historical, 30% new)
        updated_accuracy = (current_accuracy * 0.7) + (new_accuracy * 0.3)

        # Update the field_accuracy dictionary
        self.field_accuracy[field_name] = updated_accuracy
        return updated_accuracy

    def update_recent_usage_stats(self, total_merchant_uses):
        """
        Update the recent usage statistics for this template

        Args:
            total_merchant_uses: Total number of uses across all templates for this merchant
        """
        # Count uses in last 30 days (simplified - would use proper date query in production)
        last_30_days_uses = (
            self.usage_count
        )  # Simplified; real impl would filter by date

        # Calculate percentage of merchant's template uses
        usage_percentage = (
            (last_30_days_uses / total_merchant_uses * 100)
            if total_merchant_uses > 0
            else 0
        )

        # Update the field and save
        self.recent_usage = {
            "last_30_days": last_30_days_uses,
            "total_merchant_uses": total_merchant_uses,
            "usage_percentage": usage_percentage,
        }

        self.save()

    def archive(self):
        """Archive this template"""
        if not self.is_archived:
            now = timezone.now()
            self.is_archived = True
            self.archived_at = now
            self.save()

    def unarchive(self):
        """Unarchive this template"""
        if self.is_archived:
            self.is_archived = False
            self.archived_at = None
            self.save()

    def calculate_edit_distance(self, str1: Optional[str], str2: Optional[str]) -> int:
        """
        Calculate Levenshtein edit distance between two strings

        Args:
            str1: First string
            str2: Second string

        Returns:
            Edit distance (number of character-level edits required)
        """
        if str1 is None:
            str1 = ""
        if str2 is None:
            str2 = ""

        # Convert to string if not already
        str1 = str(str1)
        str2 = str(str2)

        # Simple case handling
        if str1 == str2:
            return 0
        if len(str1) == 0:
            return len(str2)
        if len(str2) == 0:
            return len(str1)

        # Initialize matrix
        matrix = [[0 for _ in range(len(str2) + 1)] for _ in range(len(str1) + 1)]

        # Fill first row and column
        for i in range(len(str1) + 1):
            matrix[i][0] = i
        for j in range(len(str2) + 1):
            matrix[0][j] = j

        # Fill the matrix
        for i in range(1, len(str1) + 1):
            for j in range(1, len(str2) + 1):
                if str1[i - 1] == str2[j - 1]:
                    matrix[i][j] = matrix[i - 1][j - 1]
                else:
                    # Min cost of delete, insert, or substitute
                    matrix[i][j] = min(
                        matrix[i - 1][j] + 1,  # Delete
                        matrix[i][j - 1] + 1,  # Insert
                        matrix[i - 1][j - 1] + 1,  # Substitute
                    )

        return matrix[len(str1)][len(str2)]

    def update_edit_distance(
        self, field_name: str, extracted_value: str, corrected_value: str
    ):
        """
        Update the edit distance metrics for a field

        Args:
            field_name: The field being compared
            extracted_value: Value extracted by the template
            corrected_value: Value corrected by the user
        """
        # Calculate edit distance
        distance = self.calculate_edit_distance(extracted_value, corrected_value)

        # Get current average (default to 0 if no data)
        current_avg = self.field_edit_distances.get(field_name, 0)

        # Get count of previous calculations for this field
        count = self.usage_count

        # Calculate new running average
        if count <= 1:
            new_avg = distance
        else:
            # Formula: new_avg = old_avg * (n-1)/n + new_value/n
            new_avg = current_avg * ((count - 1) / count) + (distance / count)

        # Update the field_edit_distances dictionary
        self.field_edit_distances[field_name] = new_avg

        # Update the overall average edit distance
        if self.field_edit_distances:
            self.avg_edit_distance = sum(self.field_edit_distances.values()) / len(
                self.field_edit_distances
            )
        else:
            self.avg_edit_distance = 0

        return new_avg

    def calculate_flags(self):
        """
        Calculate flags for archiving decisions based on our metrics

        Returns:
            Dictionary of flags and their values, plus flag count
        """
        now = timezone.now()

        # Age flag: Unused for > 30 days
        age_flag = (now - self.last_used_at).days > 30

        # Usage flag: Used < 3 times in last 60 days or < 10% of merchant's template uses
        usage_count_flag = self.recent_usage.get("last_30_days", 0) < 3
        usage_percent_flag = self.recent_usage.get("usage_percentage", 0) < 10
        usage_flag = usage_count_flag or usage_percent_flag

        # Override flag: User override rate > 40%
        override_flag = self.override_rate > 40

        # Extraction flag: Field extraction success < 70%
        avg_accuracy = (
            sum(self.field_accuracy.values()) / len(self.field_accuracy)
            if self.field_accuracy
            else 0
        )
        extraction_flag = avg_accuracy < 70

        # Accuracy flag: Based on edit distance - threshold depends on average field length
        # Using 5.0 as a somewhat arbitrary threshold - could be tuned based on data
        accuracy_flag = self.avg_edit_distance > 5.0

        flags = {
            "age_flag": age_flag,
            "usage_flag": usage_flag,
            "override_flag": override_flag,
            "extraction_flag": extraction_flag,
            "accuracy_flag": accuracy_flag,
        }

        flag_count = sum(1 for flag in flags.values() if flag)

        return {"flags": flags, "flag_count": flag_count}
