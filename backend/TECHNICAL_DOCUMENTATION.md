# Receipt Parser Job System Technical Documentation

## Overview

This document describes the implementation of an asynchronous job processing system for the Receipt Parser application. The system handles receipt upload, OCR processing, template-based data extraction, user corrections, and persistent storage.

## Architecture

The system consists of two main components:

1. **Job Management System** - Handles job lifecycle, file storage, and API endpoints
2. **Template Processing System** - Handles OCR, data extraction, and template learning

### Key Components

- **ProcessingJob Model**: Core data structure for tracking job state
- **TemplateSuite**: Comprehensive toolkit for template management
- **Celery Tasks**: Functions for asynchronous processing
- **REST API Endpoints**: Interface for client applications

## Job Lifecycle

```
┌────────────┐     ┌────────────┐     ┌────────────┐
│   Pending  │────▶│   Queued   │────▶│ Processing │
└────────────┘     └────────────┘     └────────────┘
                                            │
       ┌───────────────────────────────────┐│┌───────────────┐
       │                                   ││               ▼
       ▼                                   ▼│    ┌────────────┐
┌────────────┐                   ┌────────────┐  │  Discarded │
│  Confirmed │◀──────────────────│  Completed │  └────────────┘
└────────────┘                   └────────────┘
```

1. **Pending**: Initial state when job is created
2. **Queued**: Job submitted for processing
3. **Processing**: Active OCR and data extraction
4. **Completed**: Processing finished, ready for user review
5. **Confirmed**: User accepted the extracted data, data moved to permanent storage
6. **Discarded**: User rejected the job, temporary files cleaned up

## API Endpoints

The system exposes these primary endpoints:

- **POST /api/parser/upload/** - Upload a file for processing
- **GET /api/parser/status/{job_id}/** - Check processing status
- **POST /api/parser/confirm/{job_id}/** - Confirm extracted data
- **DELETE /api/parser/discard/{job_id}/** - Discard the job
- **POST /api/parser/edit/{job_id}/** - Submit corrected data

## Data Flow

```
┌───────────┐     ┌────────────┐     ┌─────────────┐
│  Upload   │────▶│ Processing │────▶│  Completed  │
└───────────┘     └────────────┘     └─────────────┘
                                            │
                                            ▼
                                    ┌───────────────┐
┌──────────────┐                    │  User Review  │
│ Template     │◀───────────────────┤  & Correction │
│ Improvement  │                    └───────────────┘
└──────────────┘                           │
                                           ▼
┌──────────────┐                   ┌──────────────┐
│ GridFS       │◀──────────────────│ Confirmation │
│ Permanent    │                   └──────────────┘
│ Storage      │
└──────────────┘
```

## Key Models

### ProcessingJob

```python
class ProcessingJob(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('queued', 'Queued'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('confirmed', 'Confirmed'),
        ('failed', 'Failed'),
        ('discarded', 'Discarded'),
    )
    
    job_id = models.UUIDField(primary_key=True)
    user_id = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    
    # File details
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50)
    uploaded_file = models.FileField()
    
    # Processing details
    processed_data = models.JSONField(null=True, blank=True)
    template_used = models.CharField(max_length=50, null=True)
    
    # Metadata and tracking
    metadata = models.JSONField(default=dict)
    task_id = models.CharField(max_length=50, blank=True, null=True)
    
    # Methods for status management
    def update_status(self, new_status, error_message=None):
        # Updates status and related timestamps
```

## TemplateSuite

Core services for template management:

```python
class TemplateSuite:
    # Template finding and matching
    @staticmethod
    def find_template_candidates(merchant_name: str, limit: int = 5) -> List[ReceiptTemplate]
    
    @staticmethod
    def find_best_template(ocr_text: str, merchant_name: Optional[str] = None)
    
    # Template creation and evolution
    @staticmethod
    def create_template_from_correction(ocr_text: str, corrected_values)
    
    @staticmethod
    def update_template_after_correction(template, ocr_text, extracted_data, corrected_values)
    
    # Direct interfaces for processing
    @staticmethod
    def parse_receipt(ocr_text: str, merchant_name: Optional[str] = None) -> Dict[str, Any]
    
    @staticmethod
    def process_correction(ocr_text: str, template_id: Optional[str], 
                           original_data: Dict[str, Any], 
                           corrected_data: Dict[str, Any]) -> Dict[str, Any]
    
    # Format conversion utilities
    @staticmethod
    def convert_to_internal_format(api_data: Dict[str, Any]) -> Dict[str, Any]
    
    @staticmethod
    def convert_to_api_format(internal_data: Dict[str, Any]) -> Dict[str, Any]
```

## Scheduled Tasks

The following tasks run on a schedule to maintain system health:

1. **Template Maintenance** - Runs daily at 3:00 AM to archive underperforming templates
2. **Temporary File Cleanup** - Runs daily at 2:00 AM to remove files older than 7 days
3. **Old Job Cleanup** - Runs weekly on Mondays at 1:00 AM to remove jobs older than 90 days

## Error Handling and Type Safety

The implementation includes robust error handling and type safety mechanisms:

1. **Defensive Programming**:
   - All dictionary access uses `.get()` with defaults
   - Null checks before accessing attributes
   - Type validation before operations
   
2. **JSON Handling**:
   - JSON serialization and deserialization for model fields
   - Type conversions with `dict()` for mutable copies
   - Empty dictionary fallbacks for null values

3. **File Operations**:
   - Path existence checks before file operations
   - Try/except blocks around file operations
   - Proper cleanup in error cases

## Template Learning Mechanism

The system implements a feedback loop to improve templates based on user corrections:

1. Job is processed using the best matching template
2. User reviews and corrects extracted data if needed
3. System analyzes which fields were corrected
4. Corrections are submitted to TemplateSuite
5. Template is updated or a new template is created
6. Future jobs benefit from improved templates

This feedback loop allows the system to continuously improve without direct AI intervention, learning specifically from user corrections.

## Technical Considerations

### Concurrency

- Limited to 3 concurrent workers with `CELERY_WORKER_CONCURRENCY = 3`
- Jobs are processed in FIFO order
- Each job is independent with its own temporary storage

### Security

- API key authentication for parser endpoints
- File typing and validation
- Temporary storage isolation by job ID
- Proper error handling to prevent data leakage

### Data Retention

- Temporary files removed after 7 days
- Completed jobs removed after 90 days
- Archived templates removed after 60 days

## Future Enhancements

1. **Integration with Django Admin** - For template management and job monitoring
2. **User Notification System** - To alert users when jobs complete
3. **Statistical Dashboard** - To track system performance and template accuracy
4. **Batch Processing** - To handle multiple files in a single job

## Implementation Notes

This system was designed with a clear separation of concerns:
- Jobs app manages job lifecycle and storage
- Optics app manages templates and parsing
- Clear interfaces between components
- Direct service methods rather than view dependencies

The implementation follows Django's app-based architecture, allowing components to be reused in other contexts if needed.



# Receipt Parser Template System - Technical Documentation

## 1. System Overview

The Receipt Parser Template System is a self-improving, template-based approach to extract structured data from receipt images without relying on AI. The system uses regex-based templates organized by merchant name to extract information accurately and improve over time through user corrections.

```
+-------------------+      +-------------------+      +-----------------+
|                   |      |                   |      |                 |
|  Receipt Upload   | ---> |  Template-based   | ---> | User Correction |
|                   |      |  Data Extraction  |      | & Verification  |
|                   |      |                   |      |                 |
+-------------------+      +-------------------+      +-----------------+
                                                             |
                                                             |
                                                             v
+-------------------+      +-------------------+      +-----------------+
|                   |      |                   |      |                 |
|  Export Data      | <--- |  Data Storage     | <--- | Template        |
|  to CSV/JSON      |      |  in Database      |      | Improvement     |
|                   |      |                   |      |                 |
+-------------------+      +-------------------+      +-----------------+
```

## 2. Core Components

### 2.1 Template Structure

Each template in the system is represented by the `ReceiptTemplate` model and contains:

- **Merchant Identification**: The merchant's name used for template selection
- **Field Extractors**: Regex patterns for extracting specific data points with position information
- **Line Items Configuration**: Patterns for identifying and extracting repeated line items
- **Performance Metrics**: Usage and accuracy statistics for template evolution

```
+----- Template Structure ---------+
|                                  |
| merchant_name: "Tesco"           |
|                                  |
| field_extractors: {              |
|   merchant_name: {               |
|     line: 0,                     |
|     regex: "^(.+)$"              |
|   },                             |
|   transaction_time: {            |
|     line: 2,                     |
|     regex: "Date: (.+)"          |
|   },                             |
|   total_amount: {                |
|     offset_from_last_item: 3     |
|     regex: "Total: (.+)"         |
|   }                              |
| }                                |
|                                  |
| line_items: {                    |
|   start_line: 5,                 |
|   regex: "^(.*)(\\d+\\.\\d{2})$" |
| }                                |
|                                  |
| performance_metrics: {           |
|   usage_count: 42,               |
|   success_rate: 95.2,            |
|   override_rate: 11.9            |
| }                                |
+----------------------------------+
```

### 2.2 Field Positioning Strategies

The system supports two primary approaches for locating data on receipts:

#### 2.2.1 Fixed Position Fields
- Used for data typically appearing at the top of receipts (merchant name, address, date)
- Specified with absolute line numbers: `"line": 0`
- Always searches at the exact line specified

#### 2.2.2 Dynamic Position Fields
- Used for data appearing after line items (subtotal, tax, total amount)
- Specified with relative offsets: `"offset_from_last_item": 3`
- Position calculated at runtime based on where line items end

```
+------ Sample Receipt -------+    +------ Field Mapping -------+
| TESCO STORE                 | -> | merchant_name (line: 0)    |
| 123 Main Street             | -> | merchant_address (line: 1) |
| Date: 01/03/2025            | -> | transaction_time (line: 2) |
| Ref: 12345-ABC              | -> | reference_number (line: 3) |
|                             |    |                            |
| Items:                      |    | (line_items_start_line: 5) |
| Milk         2   £2.50      | -> | Line Item #1               |
| Bread        1   £1.20      | -> | Line Item #2               |
| Eggs         6   £1.80      | -> | Line Item #3               |
|                             |    | (last_item_line: 8)        |
| Subtotal:        £5.50      | -> | subtotal (offset: 1)       |
| Tax:              £0.50     | -> | tax_amount (offset: 2)     |
| TOTAL:            £6.00     | -> | total_amount (offset: 3)   |
+-----------------------------+    +----------------------------+
```

### 2.3 Template Selection Process

1. The system identifies the merchant name from receipt's first few lines using fuzzy matching
2. Active templates matching the merchant name are considered first
3. If no active templates are found or they perform poorly, archived templates are checked
4. If still no match, a generic template is used as fallback
5. Template performance is tracked with each use

```
+-------------+     +----------------+     +------------------+
| Receipt     |     | Merchant       |     | Search Active    |
| Uploaded    |---->| Identification |---->| Template Pool    |
+-------------+     +----------------+     +------------------+
                                                   |
                                                   | If no match
                                                   v
                    +----------------+     +------------------+
                    | Use Generic    |<----| Search Archive   |
                    | Template       |     | Template Pool    |
                    +----------------+     +------------------+
                            |
                            v
                    +----------------+
                    | Extract Data   |
                    | Using Template |
                    +----------------+
                            |
                            v
                    +----------------+
                    | Track Template |
                    | Performance    |
                    +----------------+
```

## 3. Template Lifecycle Management

### 3.1 Creation
- Templates are only created from user corrections
- Each template is tied to a specific merchant name
- Multiple templates per merchant are allowed for different formats

### 3.2 Performance Evaluation

Templates are evaluated using five key metrics:

1. **Age**: Time since last successful use
   ```python
   days_since_use = current_date - last_used_date
   age_flag = days_since_use > 30
   ```

2. **Usage Frequency**: Percentage use among merchant's templates
   ```python
   usage_percentage = template_uses / total_merchant_template_uses * 100
   usage_flag = usage_percentage < 10
   ```

3. **Override Rate**: Percentage of times users correct output
   ```python
   override_rate = override_count / use_count
   override_flag = override_rate > 40  # 40%
   ```

4. **Extraction Success Rate**: Percentage of fields successfully extracted
   ```python
   extraction_rate = avg_field_accuracy
   extraction_flag = extraction_rate < 70  # 70%
   ```

5. **Edit Distance**: Character-level accuracy of extracted values
   ```python
   accuracy_flag = avg_edit_distance > 5.0
   ```

```
+---------- Template Performance Metrics ----------+
|                                                  |
|  +------------+  +------------+  +------------+  |
|  | Age        |  | Usage      |  | Override   |  |
|  | Metric     |  | Frequency  |  | Rate       |  |
|  |            |  |            |  |            |  |
|  | days > 30  |  | usage <10% |  | rate >40%  |  |
|  +------------+  +------------+  +------------+  |
|                                                  |
|  +------------+  +------------+                  |
|  | Extraction |  | Edit       |                  |
|  | Success    |  | Distance   |                  |
|  |            |  |            |                  |
|  | rate <70%  |  | avg >5.0   |                  |
|  +------------+  +------------+                  |
|                                                  |
+--------------------------------------------------+
```

### 3.3 Template Pools

The system maintains three distinct pools of templates:

1. **Active Pool**: Regular templates in current use
2. **Archive Pool**: Underperforming templates (kept for 2 months)
3. **Generic Pool**: Fallback templates for unknown merchants

```
+----------------+      +----------------+      +----------------+
|                |      |                |      |                |
| Active Pool    |----->| Archive Pool   |----->| Delete After   |
| Current Use    |      | Underperforming|      | 2 Months       |
|                |      |                |      |                |
+----------------+      +----------------+      +----------------+
        ^                      |
        |                      |
        +----------------------+
         Performance improves
```

### 3.4 Archiving Decision System

Templates are archived when:
- 3+ flags are triggered, OR
- Age flag + any other flag, OR
- Override flag + Extraction flag

```
+------- Archiving Decision Tree -------+
|                                       |
|               START                   |
|                 |                     |
|                 v                     |
|        Count Triggered Flags          |
|                 |                     |
|                 v                     |
|          /------+------\              |
|         /                \            |
|        /                  \           |
|       /                    \          |
|  3+ Flags?             < 3 Flags?     |
|     |                       |         |
|     | YES                   | NO      |
|     v                       v         |
|  ARCHIVE             Age Flag True?   |
|                           /  \        |
|                      YES /    \ NO    |
|                         /      \      |
|                        v        v     |
|             Any Other Flag?    Keep   |
|                   / \                 |
|              YES /   \ NO             |
|                 /     \               |
|                v       v              |
|            ARCHIVE    Keep            |
|                                       |
+---------------------------------------+
```

## 4. Extraction Process

### 4.1 Line Items Extraction
1. Start at line specified in `line_items_start_line`
2. Apply regex pattern to each subsequent line
3. Continue until pattern fails to match
4. Mark last successful match as `last_item_line`
5. Use as anchor point for fields with relative positioning

### 4.2 Field Extraction
1. Extract fixed position fields using absolute line numbers
2. Identify line items section and extract items
3. Extract dynamic position fields using offsets from last item line
4. Return extracted data for user verification

```
+---------- Extraction Process -------------+
|                                           |
| +-----------+  +----------+  +---------+  |
| | Extract   |  | Extract  |  | Extract |  |
| | Fixed Pos |->| Line     |->| Dynamic |  |
| | Fields    |  | Items    |  | Fields  |  |
| +-----------+  +----------+  +---------+  |
|       ^            |             ^        |
|       |            v             |        |
|  +----------+  +----------+  +----------+ |
|  | Absolute |  | Find     |  | Relative | |
|  | Line     |  | Last     |  | to Last  | |
|  | Numbers  |  | Item Line|  | Item Line| |
|  +----------+  +----------+  +----------+ |
|                                           |
+-------------------------------------------+
```

### 4.3 Missing Fields Handling
- Fields not used by a merchant are simply omitted from template
- No explicit "field not present" flags needed
- User corrections teach system which fields to expect from each merchant

## 5. System Evolution

### 5.1 Self-Improvement Mechanism
- Templates evolve solely through user corrections
- No AI or derived templates
- Poor performing templates naturally cycle out
- System self-improves with usage
- Exceptions handled by human intervention

```
+----------+     +------------+     +----------------+     +-----------------+
| Initial  |     | Template   |     | User           |     | Updated         |
| Template |---->| Data       |---->| Correction     |---->| Template        |
|          |     | Extraction |     | & Verification |     | (Self-Improving)|
+----------+     +------------+     +----------------+     +-----------------+
                       |                    ^                       |
                       |                    |                       |
                       +--------------------+-----------------------+
                           Continuous Feedback Loop
```

### 5.2 Edit Distance Calculation
The system uses Levenshtein distance to measure the character-level differences between extracted and corrected values:
```python
def calculate_edit_distance(str1, str2):
    # Implementation of Levenshtein distance algorithm
    # Returns number of character-level edits required
```

### 5.3 Accuracy Calculation
Field accuracy is updated using a weighted average approach:
```python
updated_accuracy = (current_accuracy * 0.7) + (new_accuracy * 0.3)
```

## 6. Data Model

### 6.1 ReceiptTemplate Model

The `ReceiptTemplate` model stores all template information in MongoDB:

```python
class ReceiptTemplate(models.Model):
    # Tracking metadata
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    last_used_at = models.DateTimeField()
    usage_count = models.IntegerField()
    success_rate = models.FloatField()
    override_rate = models.FloatField()
    avg_edit_distance = models.FloatField()
    is_archived = models.BooleanField()
    
    # Merchant identifiers
    merchant_name = models.CharField()
    
    # Template configuration
    currency_info = models.JSONField()
    field_extractors = models.JSONField()
    has_line_items = models.BooleanField()
    line_items_start_line = models.IntegerField()
    item_patterns = models.JSONField()
    
    # Performance metrics
    field_accuracy = models.JSONField()
    field_edit_distances = models.JSONField()
    recent_usage = models.JSONField()
```

```
+------------ Data Model Relationships -------------+
|                                                   |
|   +---------------+       +-------------------+   |
|   | ReceiptTemplate|      | Extracted Receipt |   |
|   |---------------|       |-------------------|   |
|   | merchant_name |<------| using_template_id |   |
|   | field_patterns|       | merchant_name     |   |
|   | performance   |       | extracted_fields  |   |
|   +---------------+       | user_corrections  |   |
|          ^                +-------------------+   |
|          |                         |              |
|          |                         v              |
|   +---------------+       +-------------------+   |
|   | MerchantInfo  |       | User Submission   |   |
|   |---------------|       |-------------------|   |
|   | name          |       | user_id           |   |
|   | aliases       |       | receipt_id        |   |
|   | template_count|       | original_file     |   |
|   +---------------+       +-------------------+   |
|                                                   |
+---------------------------------------------------+
```

### 6.2 Field Validators

The system includes validators for each JSON field to ensure data integrity:

- `validate_currency_info`: Ensures currency information follows ISO 4217 standard
- `validate_field_extractors`: Validates extraction patterns and positioning information
- `validate_item_patterns`: Ensures line item patterns have valid regex and group mappings
- `validate_field_accuracy`: Ensures accuracy percentages are between 0-100
- `validate_field_edit_distances`: Ensures edit distances are non-negative values
- `validate_recent_usage`: Validates usage statistics for archiving decisions

## 7. Integration Points

### 7.1 Parser Service Integration
The template system is integrated with the receipt parsing service via:
- Template selection based on merchant identification
- Extraction process that applies template patterns
- Feedback loop for user corrections

```
+----------------+     +----------------+     +----------------+
|                |     |                |     |                |
| OCR Service    |---->| Template       |---->| Extraction     |
| Image to Text  |     | Selection      |     | Service        |
|                |     |                |     |                |
+----------------+     +----------------+     +----------------+
                                                      |
                                                      v
+----------------+     +----------------+     +-----------------+
|                |     |                |     |                 |
| Template       |<----| User           |<----| Frontend        |
| Update Service |     | Correction API |     | Verification UI |
|                |     |                |     |                 |
+----------------+     +----------------+     +-----------------+
```

### 7.2 User Interface Integration
The system connects to the frontend through:
- Displaying extracted data for user verification
- Collecting user corrections to improve templates
- Providing confidence scores for extracted fields

## 9. Fields Extracted

The system is designed to extract the following fields from receipts:
- merchant_name
- transaction_time
- merchant_address
- reference_number
- tax_amount
- total_amount
- subtotal_amount
- currency
- line items (quantity, item_name, unit_price, total_price)

*Note: Category and description are entered manually by users, not extracted*
