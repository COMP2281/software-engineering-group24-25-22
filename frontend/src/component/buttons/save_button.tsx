import React, { useState } from 'react'
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';
import { useNavigate } from 'react-router-dom';
import { saveReceipt, createReceipt } from '../../utils/requests';
import Alert from '@mui/material/Alert';
import Snackbar from '@mui/material/Snackbar';

interface SaveButtonProps {
    itemID: string;
    edit: boolean;
    fieldValues: { [key: string]: string };
}

export function SaveButton({ edit, itemID, fieldValues }: SaveButtonProps) {
    const navigate = useNavigate();
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [showSuccess, setShowSuccess] = useState(false);

    const handleSubmit = async () => {
        setIsLoading(true);
        setError(null);
        
        try {
            // Use the field values directly - they already have the correct field names
            // from the fieldMapping.ts utility
            const receiptData = {
                merchant_name: fieldValues.merchant_name || '',
                transaction_time: fieldValues.transaction_time || '',
                merchant_address: fieldValues.merchant_address || '',
                reference_number: fieldValues.reference_number || '',
                total_amount: fieldValues.total_amount || '0.00',
                description: fieldValues.description || '',
                tax_amount: fieldValues.tax_amount || '0.00',
                category: fieldValues.category || 'Other',
                cost_items: fieldValues.cost_items || '[]'
            };
            
            // Parse cost items if it's a JSON string
            if (typeof receiptData.cost_items === 'string') {
                try {
                    receiptData.cost_items = JSON.parse(receiptData.cost_items);
                } catch (e) {
                    console.warn('Failed to parse cost_items as JSON, sending as string');
                }
            }
            
            let result;
            if (itemID) {
                // Update existing receipt
                result = await saveReceipt(itemID, receiptData);
            } else {
                // Create new receipt
                result = await createReceipt(receiptData);
            }
            
            if (result.success) {
                setShowSuccess(true);
                // If we're editing, stay on the same page
                // If we're creating a new receipt, go to the upload page
                if (!edit) {
                    setTimeout(() => {
                        navigate('/dashboard');
                    }, 1500);
                }
            } else {
                setError(result.error || 'Failed to save receipt');
            }
        } catch (err) {
            console.error('Error saving receipt:', err);
            setError('An unexpected error occurred. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <>
            <div> 
                <Button 
                    variant="contained" 
                    onClick={handleSubmit} 
                    disabled={isLoading}
                    color="primary"
                >
                    {isLoading ? (
                        <>
                            <CircularProgress size={24} style={{ marginRight: 8 }} /> 
                            Saving...
                        </>
                    ) : 'Save'}
                </Button>
            </div>
            
            <Snackbar 
                open={!!error} 
                autoHideDuration={4000} 
                onClose={() => setError(null)}
                anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
            >
                <Alert severity="error" onClose={() => setError(null)}>
                    {error}
                </Alert>
            </Snackbar>
            
            <Snackbar 
                open={showSuccess} 
                autoHideDuration={3000} 
                onClose={() => setShowSuccess(false)}
                anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
            >
                <Alert severity="success" onClose={() => setShowSuccess(false)}>
                    Receipt saved successfully!
                </Alert>
            </Snackbar>
        </>
    );
}
