import React from 'react'
import Button from '@mui/material/Button';
import { useParams, useNavigate } from 'react-router-dom'
import { displayToProperty } from '../../utils/fieldMapping';
import { pendingItems } from '../../data/receipts';
import { PendingItem } from '../../types/receipt';

export function SubmitButton() {
    const { id } = useParams<{ id: string }>();
    const numericId = parseInt(id || '0');
    const navigate = useNavigate();
    const fields = Object.values(displayToProperty);

    const handleSubmit = () => { 
        const fieldValues: { [key: string]: string } = {};
        
        // Get the existing item to preserve the image
        const existingItem = pendingItems.find(item => item.id === numericId);
        if (!existingItem) {
            console.error('Item not found');
            return;
        }
        
        // Get values from text fields
        for (let i = 0; i < fields.length; i++) {
            const fieldId = `text-field-${numericId}-${fields[i]}`;
            const textField = document.getElementById(fieldId) as HTMLInputElement;
            if (textField) {
                fieldValues[fields[i]] = textField.value;
            }
        }

        // Update the item in pendingItems
        const itemIndex = pendingItems.findIndex(item => item.id === numericId);
        if (itemIndex !== -1) {
            const updatedItem: PendingItem = {
                ...existingItem,
                ...fieldValues,
                id: numericId,
                image: existingItem.image // Preserve the image
            };
            pendingItems[itemIndex] = updatedItem;
            console.log('Updated item:', updatedItem);
        }
        
        navigate('/upload');
    };

    return (
        <div> 
            <Button 
                variant="contained" 
                onClick={handleSubmit}
            >
                Submit
            </Button>
        </div>
    );
}
