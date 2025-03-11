import React from 'react'
import Button from '@mui/material/Button';
import { useNavigate } from 'react-router-dom';
import { pendingItems } from '../../data/receipts';
import { PendingItem } from '../../types/receipt';

interface SaveButtonProps {
    itemID: number;
    fieldValues: { [key: string]: string };
}

export function SaveButton({ itemID, fieldValues }: SaveButtonProps) {
    const navigate = useNavigate();

    const handleSubmit = () => {
        
        const itemIndex = pendingItems.findIndex(item => item.id === itemID)
        if (itemIndex !== -1) {
            const updatedItem = { ...pendingItems[itemIndex] } as PendingItem;
            Object.entries(fieldValues).forEach(([itemName, value]) => {
                if (itemName in updatedItem) {
                    (updatedItem as unknown as { [key: string]: string })[itemName] = value;
                }
            });
            pendingItems[itemIndex] = updatedItem;
            
            
            navigate('/upload');
        }
    };

    return (
        <div> 
            <Button variant="contained" onClick={handleSubmit}>Save</Button>
        </div>
    );
}
