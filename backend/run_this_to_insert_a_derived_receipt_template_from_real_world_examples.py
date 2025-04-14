#!/usr/bin/env python
import os
import json
import sys
import django

# should set this because of the relative path for the mongodb socket in the general settings.py.
os.chdir(os.path.join(os.getcwd(), "general"))


# This is a file to populate your receipt template database, just a simple example
# how the library is written.

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
print(sys.path)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "parser.parser.settings")
django.setup()

from parser.apps.optics.views import TemplateSuite

# Set up Django environment
from parser.apps.optics.lib.templates import OCRTemplate, OCRTemplateCorrection
from parser.apps.optics.models import ReceiptTemplate

# The refined text version
tesco_ocr = """TESCO

A & A & S

Durham Express
Any questions please visit
www.tesco.com/store-1ocator
VAT Number: GB 220 4302 31

1  Tesco 16 Honey Roast Ham 400g P2560
1 Oreo Doughnut 2 Pack 144g £1.50
2 Dairylea Cheese Slices 8 Pack £3.40
8%20.59
£1.70 each
1 Tesco Green Seedless (Grapes £2.30
Pack 500g (c)
Cc £2.00 -£0.30
1 Tesco British Whole Milk £1.45
2.2721, 4 Pints
1 Innocent Tropical Juice 900ml £3.60
Subtotal : £14.90
Savings: -£0.30
Promotions: -£0.30
TOTAL £14.60
Card £14.60
Clubcard points earned: 14
Clubcard points balance: 90
Master Card
AID: A0000000041010
Number KXKXRKKN KK %K% 15RO
Pan sequerce No: 1
Authorisation code: 002064

Merchant: xxxx4805"""

# Cluttered, raw ocr.
tesco_ocr = """Qy

TESCO

ey & & 4

Durham Express
Any questions please Visit
Www . tesco.com/store-1ocator
VAT Number: GB 220 4302 31

1  Tesco 16 Honey Roast Ham 4009 £2.65
1 Oreo Doughnut 2 Pack 1449 £1.90
2 Dairylea Cheese Slices 8 Pack £3.40
8x20.59
£1.70 each
1 Tesco Green Seedless Grapes £2.30
Pack 500g (c)
Cc £2.00 -£0.30
1 Tesco British Whole Milk £1.45
2.2721, 4 Pints
1  Innocent Tropical Juice 900m1 £3.60
Subtotal : £14.90
Savings: -£0.30
Promotions: -£0.30
TOTAL £14.60
Card Il - . £14.60
Clubcard points earned: ‘_—-_“--1;

Clubcard points balance:

- . P = -
e s oo el
,..--‘-‘-—oo - v ma
W S e b e e A
- -

Master Card

ALD: | A000000004101
. B 0
ggmngAuenCQ'n0= Kxxxemxen x589
jsation code: 1
Author e

Merchantzt' | ¢ 4 ks

A L

" 5P9H-1B9U-NO44-7pp

.?---'--
v o e - o
-
‘

————— —
- e e G g W G S
-o——-— L dl
-
_-
-

“—‘-—
-
-
—~—
"""

# Test the OCR preprocessing
def test_preprocessing():
    from parser.apps.optics.lib.templates import OCRTemplate
    
    print("\nTesting OCR preprocessing...")
    print("-" * 50)
    
    # Original OCR text
    print("ORIGINAL OCR TEXT SNIPPET:")
    for i, line in enumerate(tesco_ocr.split('\n')[:20]):
        print(f"{i:2d}: {line}")
    
    # Preprocessed OCR text
    cleaned_text = TemplateSuite.preprocess_ocr_text(tesco_ocr)
    print("\nPREPROCESSED OCR TEXT SNIPPET:")
    for i, line in enumerate(cleaned_text.split('\n')):
        print(f"{i:2d}: {line}")
    
    print("-" * 50)

# User corrected data for this receipt
user_corrections: OCRTemplateCorrection = {
    "merchant_name": "TESCO",
    "transaction_time": "", # No visible date on this receipt
    "merchant_address": "Durham Express",
    "reference_number": "GB 220 4302 31", # Using VAT number as reference
    "total_amount": "14.60",
    "subtotal_amount": "14.90",
    "tax_amount": "", # No visible tax amount
    "category": "groceries",
    "description": "",
    "cost_items": [
        {
            "quantity": "1",
            "item_name": "Tesco 16 Honey Roast Ham 400g",
            "total_price": "2.60" # Assuming P2560 is price £2.60
        },
        {
            "quantity": "1",
            "item_name": "Oreo Doughnut 2 Pack 144g",
            "total_price": "1.50"
        },
        {
            "quantity": "2",
            "item_name": "Dairylea Cheese Slices 8 Pack",
            "total_price": "3.40"
        },
        {
            "quantity": "1",
            "item_name": "Tesco Green Seedless Grapes Pack 500g",
            "total_price": "2.00" # Post-discount price
        },
        {
            "quantity": "1",
            "item_name": "Tesco British Whole Milk 2.272L, 4 Pints",
            "total_price": "1.45"
        },
        {
            "quantity": "1",
            "item_name": "Innocent Tropical Juice 900ml",
            "total_price": "3.60"
        }
    ]
}

def create_template():
    """Create and save a template from the OCR text and user corrections"""
    print("Creating Tesco receipt template...")
    
    # Create the OCRTemplate instance
    # This will run the dedicated routine for preprocessing, cleaning up the artifact 
    # characters/lines
    # And after cleaning up the text, it will be put in, along with user_corrections 
    # to create an ocr template that will be driven from the user creation.
    template = OCRTemplate(TemplateSuite.preprocess_ocr_text(tesco_ocr), user_corrections)
    
    # Convert the internal object version of the template, to its formal model.
    template_data = template.to_model_data()

    print("template_data", json.dumps(template_data, indent=3))
    
    print(f"Creating new template for {template_data['merchant_name']}")
    
    # Create a new ReceiptTemplate
    new_template = ReceiptTemplate(**template_data)
    new_template.save()
    print(f"Created template: {new_template}")
    return new_template

def test_template(template):
    """Test the template by extracting data from the original OCR text"""
    print("\nTesting template with original OCR text...")
    
    # Create a fresh OCRTemplate without corrections
    test_template = OCRTemplate(TemplateSuite.preprocess_ocr_text(tesco_ocr))
    
    # Extract fields using the template model data
    extracted_data = test_template.extract_fields(
        template_model_data={
            'field_extractors': template.field_extractors,
            'has_line_items': template.has_line_items,
            'item_patterns': template.item_patterns,
            'line_items_start_line': template.line_items_start_line
        }
    )
    
    # Display extracted data
    print("\nExtracted data:")
    for field, value in extracted_data.items():
        if field != 'cost_items':
            print(f"{field}: {value}")
    
    # Display extracted line items
    if 'cost_items' in extracted_data:
        print("\nExtracted line items:")
        for i, item in enumerate(extracted_data['cost_items'], 1):
            print(f"Item {i}:")
            for field, value in item.items():
                print(f"  {field}: {value}")
    
    return extracted_data

if __name__ == "__main__":
    # Test the OCR preprocessing
    test_preprocessing()
    
    # Create the template
    template = create_template()
    
    # Test the template
    test_result = test_template(template)
    
    # Print summary
    print("\nTemplate creation complete!")
    print(f"Template ID: {template.pk}")
    print(f"Merchant: {template.merchant_name}")
    print(f"Line item patterns: {len(template.item_patterns)}")
    print(f"Fields configured: {len(template.field_extractors)}")
