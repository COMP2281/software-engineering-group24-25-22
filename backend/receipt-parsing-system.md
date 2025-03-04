# Receipt Parser Template System

## Core Concept
A self-improving receipt parsing system driven by user corrections rather than AI, using regex-based templates organized by merchant name.

## Template Structure

Each template contains:

```json
{
  "merchant_name": "Tesco",
  "field_extractors": {
    "merchant_name": {
      "line": 0,
      "regex": "^(.+)$"
    },
    "transaction_time": {
      "line": 2,
      "regex": "Date:\\s*(\\d{2}/\\d{2}/\\d{4})"
    },
    "merchant_address": {
      "line": 1,
      "regex": "(.+)"
    },
    "total_amount": {
      "offset_from_last_item": 3,
      "regex": "Total:\\s*£?(\\d+\\.\\d{2})"
    }
    // Only include fields this merchant uses
  },
  "line_items": {
    "start_line": 5,
    "regex": "^\\s*(\\d+)\\s+(.+)\\s+(£?\\d+\\.\\d{2})\\s*$",
    "groups": {
      "quantity": 1,
      "item_name": 2, 
      "total_price": 3
    }
  },
  "has_line_items": true,
  
  // Template performance metrics
  "last_used": "2025-03-04T15:30:22Z",
  "use_count": 42,
  "override_count": 5,
  "extraction_success_rate": 0.95,
  "avg_edit_distance": 1.2,
  "is_archived": false
}
```

## Field Positioning Strategies

### Fixed Position Fields (Top of Receipt)
- Use absolute line numbers: `"line": 0`
- Typically include: merchant_name, merchant_address, transaction_time, reference_number
- Always look in exact line specified

### Dynamic Position Fields (After Line Items)
- Use relative offsets: `"offset_from_last_item": 3`
- Typically include: subtotal_amount, tax_amount, total_amount
- Position calculated at runtime based on where line items end

### Special Case: Receipts Without Line Items
- All fields use absolute line numbers
- `"has_line_items": false` flag indicates no line items section
- No relative positioning needed

## Line Items Extraction
1. Start at line specified in `line_items.start_line`
2. Apply regex pattern to each subsequent line
3. Continue until pattern fails to match
4. Mark last successful match as `last_item_line`
5. Use as anchor point for fields with relative positioning

## Field Extraction Process
1. Identify merchant using fuzzy matching + spell checking on first few lines
2. Select best template based on merchant name
3. Extract fixed position fields using absolute line numbers
4. Identify line items section and extract items
5. Extract dynamic position fields using offsets from last item line
6. Return extracted data for user verification

## Template Lifecycle Management

### Creation
- Templates only created from user corrections
- Each template tied to specific merchant name
- Multiple templates per merchant allowed (different formats)

### Evaluation Metrics
1. **Age**: Time since last successful use
   ```
   days_since_use = current_date - last_used_date
   age_flag = days_since_use > 30
   ```

2. **Usage Frequency**: Percentage use among merchant's templates
   ```
   template_uses_last_30_days / total_merchant_template_uses_last_30_days
   usage_flag = percentage < threshold
   ```

3. **Override Rate**: Percentage of times users correct output
   ```
   override_rate = override_count / use_count
   override_flag = override_rate > 0.4  # 40%
   ```

4. **Extraction Success Rate**: Percentage of fields successfully extracted
   ```
   extraction_rate = extracted_fields / expected_fields
   extraction_flag = extraction_rate < 0.7  # 70%
   ```

5. **Edit Distance**: Character-level accuracy of extracted values
   ```
   avg_edit_distance = sum_edit_distances / num_corrected_fields
   accuracy_flag = avg_edit_distance > threshold
   ```

### Archiving Decision System
Templates are archived when:
- 3+ flags are triggered, OR
- Age flag + any other flag, OR
- Override flag + Extraction flag

### Template Pools
1. **Active Pool**: Regular templates in current use
2. **Archive Pool**: Underperforming templates (kept for 2 months)
3. **Generic Pool**: Fallback templates for unknown merchants

### Archive Recovery
- Archived templates checked when active templates perform poorly
- If archived template performs well, it's restored to active status

## Template Selection Process
1. Identify merchant name from receipt
2. Look for active templates matching merchant name
3. If none found or all perform poorly, check archived templates
4. If still no match, fall back to generic template
5. Track template performance with each use

## Missing Fields Handling
- Fields not used by a merchant are simply omitted from template
- No need for explicit "field not present" flags
- User corrections teach system which fields to expect

## System Evolution
- Templates evolve solely through user corrections
- No AI or derived templates
- Poor performing templates naturally cycle out
- System self-improves with usage
- Exceptions handled by human intervention

## Manual Curation
- Only generic templates are manually curated
- Merchant-specific templates evolve organically
- Edge cases handled by users directly

## Fields Extracted
- merchant_name
- transaction_time
- merchant_address
- reference_number
- tax_amount
- total_amount
- subtotal_amount
- currency
- line items (quantity, item_name, unit_price, total_price)

*Note: category and description are entered manually by users, not extracted*