# Self-Improving Receipt Template System

## Introduction

The self-improving receipt template system provides an automated, adaptive approach to extracting structured data from receipts. Unlike conventional OCR solutions that rely on either fixed templates or AI-driven approaches, this system implements a human-in-the-loop feedback mechanism that progressively refines extraction templates based on user corrections. This document explains the technical architecture, data structures, algorithms, and lifecycle management that enable continuous improvement without relying on machine learning.

## System Architecture

The template system consists of several key components:

### Template Model

At the core of the system is the `ReceiptTemplate` model, a MongoDB-backed document model that stores extraction patterns and performance metrics. Each template corresponds to a specific merchant and contains:

- Field extractors: Regex patterns for extracting fields like totals, dates, and tax amounts
- Line item extractors: Patterns for identifying and extracting repeating line items
- Performance metrics: Usage statistics, success rate, edit distances, and more
- Lifecycle attributes: Creation date, last used date, archival status

The template model serves as both a repository of extraction knowledge and a metric-tracking mechanism for the template's performance over time.

### Template Service

The `TemplateService` acts as the orchestration layer, providing methods for:

- Finding the best template for a given receipt
- Creating new templates from user corrections
- Updating existing templates with new patterns
- Managing template lifecycle (archiving, resurrection)
- Evaluating template performance

This service implements the decision logic for when to create new templates versus updating existing ones, based on the number of fields requiring correction.

### OCR Template Parser

The `OCRTemplate` class handles the actual parsing of OCR text using templates. It provides functionality for:

- Extracting fields using regex patterns
- Detecting receipt structure including line items
- Determining field positions (absolute or relative to line items)
- Currency detection through symbol identification

This component bridges the gap between raw OCR text and structured data by applying the patterns stored in templates.

## Template Creation and Evolution

### Creation Triggers

New templates are created under specific conditions:

1. When a merchant is encountered for the first time
2. When a user corrects multiple fields (2+) in an existing template's output
3. When an admin explicitly creates a template

The threshold of "2+ fields needing correction" represents a balance between creating too many similar templates and not capturing meaningful variations in receipt formats.

### Template Structure

Templates store extraction patterns in a structured JSON format:

```json
{
  "field_extractors": {
    "merchant_name": {
      "expected_present": true,
      "patterns": ["^(.+)$"],
      "line": 0
    },
    "transaction_time": {
      "expected_present": true,
      "patterns": ["Date:\\s*(\\d{1,2}/\\d{1,2}/\\d{4})"],
      "line": 2
    },
    "total_amount": {
      "expected_present": true,
      "patterns": ["Total:\\s*£?(\\d+\\.\\d{2})"],
      "offset_from_last_item": 3
    }
  },
  "has_line_items": true,
  "line_items_start_line": 5,
  "item_patterns": [
    {
      "pattern": "^\\s*(\\d+)\\s+(.+)\\s+(£?\\d+\\.\\d{2})\\s*$",
      "groups": {
        "quantity": 1,
        "item_name": 2,
        "total_price": 3
      }
    }
  ]
}
```

This structure allows for both absolute positioning (using `line` for fields at the top) and relative positioning (using `offset_from_last_item` for fields below the line items section).

### Pattern Generation

When a user corrects extracted data, the system:

1. Identifies which fields were corrected
2. Generates optimal regex patterns for those fields
3. Determines appropriate line positions or offsets
4. For monetary fields, creates currency-aware patterns

For pattern generation, the system tries multiple predefined regex candidates for each field type and selects the one that matches the corrected value. If no predefined pattern works, it falls back to creating a custom pattern from the exact corrected text.

### Currency Detection

The template system automatically detects currency using the iso4217parse library:

1. Scans the OCR text for currency symbols
2. Maps symbols to currency codes
3. Uses the detected currency to enhance extraction patterns
4. Dynamically generates variants of monetary field patterns with and without currency symbols

This approach allows the same template to handle small formatting differences like "$10.99" versus "10.99".

## Adaptive Positioning

A key innovation in the template system is its adaptive positioning mechanism, which addresses the variable length of receipts.

### Field Classification

Fields are classified into two categories:
1. **Fixed-position fields**: Located at the top of the receipt (merchant name, date)
2. **Relative-position fields**: Located after the line items section (subtotal, tax, total)

### Line Items as Anchor Points

Line items serve as the "anchor point" that divides the receipt. For fixed-position fields, absolute line numbers are stored. For relative-position fields, offsets from the last line item are stored.

When parsing a new receipt:
1. Fixed fields are extracted using absolute line positions
2. Line items are located and extracted
3. The last line item position becomes the reference point
4. Relative fields are extracted by applying their stored offsets from this point

This approach allows the template to adapt to receipts of varying lengths while maintaining positional awareness.

## Performance Metrics and Lifecycle Management

The template system implements sophisticated lifecycle management to ensure templates remain relevant and accurate over time.

### Performance Metrics

Each template tracks multiple performance metrics:

- **Usage count**: How many times the template has been used
- **Success rate**: Percentage of fields correctly extracted
- **Override rate**: Percentage of fields corrected by users
- **Edit distances**: Character-level differences between extracted and corrected values
- **Recent usage**: Usage patterns over the last 30 days
- **Field-specific accuracy**: Accuracy rates for individual fields

These metrics provide a multi-dimensional view of template performance beyond simple success/failure rates.

### Flag-Based Archiving

Templates are evaluated for archiving using a flag-based system:

1. **Age flag**: Triggered when a template hasn't been used for >30 days
2. **Usage flag**: Triggered when usage is <3 times in the last 60 days or <10% of the merchant's template uses
3. **Override flag**: Triggered when override rate exceeds 40%
4. **Extraction flag**: Triggered when field extraction success falls below 70%
5. **Accuracy flag**: Triggered when average edit distance exceeds 5.0

A template is archived if:
- 3+ flags are triggered
- The age flag plus any other flag are triggered
- Both the override and extraction flags are triggered

This multi-criteria approach prevents premature archiving while ensuring poorly performing templates don't remain active.

### Template Resurrection

Archived templates aren't immediately deleted but enter a "dormant" state where:

1. They aren't used in primary template matching
2. They're checked only when active templates perform poorly
3. If an archived template suddenly performs well, it's "resurrected"
4. After 60 days in the archived state, templates are permanently deleted

This resurrection mechanism provides a safety net for seasonal templates (like holiday receipts) that might be used infrequently but still have value.

## Field Extraction Process

The field extraction process combines regex pattern matching with positional awareness:

1. **Currency Detection**: Scan for currency symbols to enhance monetary field extraction
2. **First Pass - Fixed Fields**: Extract fields with absolute line positions
3. **Line Item Extraction**: Locate and extract line items using patterns
4. **Second Pass - Relative Fields**: Extract fields with relative offsets from the last line item
5. **Validation**: Apply basic validation to ensure extracted data is plausible

For monetary fields, the system tries both currency-aware and plain patterns, prioritizing the currency-aware match when available.

### Error Handling

The extraction process includes robust error handling:

- Missing fields are gracefully handled based on `expected_present` flags
- Type conversion errors are caught and logged
- Extraction failures for individual fields don't halt the entire process
- Field confidence is tracked to indicate potential issues

## User Correction Workflow

The user correction workflow completes the feedback loop:

1. User uploads a receipt for processing
2. System selects the best template and extracts fields
3. If confidence is low or key fields are missing, user review is requested
4. User corrects any inaccurate fields
5. Corrected data is submitted back to the system
6. System compares original extraction with corrected values
7. Based on the number of corrections:
   - If 2+ fields required correction, a new template is created
   - If 1 field required correction, the existing template is updated
8. Template performance metrics are updated

This workflow ensures the system continuously learns from user interactions without requiring explicit training.

## Edge Cases and Limitations

### Handling Missing Fields

Not all receipts contain all possible fields. The template system addresses this through:

- Field-specific `expected_present` flags
- Omitting non-existent fields from templates
- Confidence scoring that accounts for intentionally missing fields

### Receipt Format Changes

When merchants change their receipt format significantly:

1. The existing template will perform poorly
2. User corrections will trigger creation of a new template
3. The old template will gradually be used less frequently
4. Eventually, the old template will be archived through the flag system

### OCR Quality Issues

The template system distinguishes between template problems and OCR quality issues:

- Edit distance tracking helps identify OCR errors versus template errors
- Consistent failure patterns across multiple templates suggest OCR issues
- Field-specific accuracy metrics highlight problematic fields

## Future Enhancements

The current template system could be enhanced in several ways:

1. **Field Grouping**: Identifying related fields that tend to change together
2. **Spatial Awareness**: Incorporating visual layout information beyond line numbers
3. **Pattern Generalization**: Automatically generalizing patterns across similar merchants
4. **Smart Template Suggestions**: Suggesting the most relevant template patterns during user correction
5. **Automated Pattern Testing**: Validating new patterns against historical data

## Conclusion

The self-improving receipt template system represents a pragmatic approach to the receipt parsing problem. By combining rule-based extraction with user-driven feedback, it achieves continuous improvement without complex machine learning pipelines. The system's strengths lie in its adaptability to new formats, its robust performance metrics, and its intelligent lifecycle management.

The flag-based archiving system, relative positioning mechanism, and currency-aware pattern generation address common challenges in receipt parsing, creating a solution that balances automation with human oversight. As the system processes more receipts and incorporates more user corrections, its template library naturally evolves to handle an increasingly diverse range of receipt formats.