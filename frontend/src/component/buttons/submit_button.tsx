import React from 'react'
import Button from '@mui/material/Button';
import { useParams, useNavigate } from 'react-router-dom'
import { displayToProperty } from '../../utils/fieldMapping';
import { pendingItems, finished_receipts } from '../../data/receipts';
import { PendingItem } from '../../types/receipt';

export function SubmitButton() {
    const { id } = useParams<{ id: string }>();
    const numericId = parseInt(id || '0');
    const navigate = useNavigate();
    const fields = Object.values(displayToProperty);

    const handleSubmit = () => { 
        const fieldValues: { [key: string]: string } = {};
        
        const existingItem = pendingItems.find(item => item.id === numericId);
        if (!existingItem) {
            console.error('Item not found');
            return;
        }
        
        for (let i = 0; i < fields.length; i++) {
            const fieldId = `text-field-${numericId}-${fields[i]}`;
            const textField = document.getElementById(fieldId) as HTMLInputElement;
            if (textField) {
                fieldValues[fields[i]] = textField.value;
            }
        }

        const updatedItem: PendingItem = {
            ...existingItem,
            ...fieldValues,
            id: numericId,
            image: existingItem.image,
        };

        const itemIndex = pendingItems.findIndex(item => item.id === numericId);
        if (itemIndex !== -1) {
            pendingItems.splice(itemIndex, 1);
        }

        finished_receipts.push(updatedItem);
        
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
