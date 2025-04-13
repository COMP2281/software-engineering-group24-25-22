import React, { useState } from 'react'
import Button from '@mui/material/Button';
import { useParams, useNavigate } from 'react-router-dom'
import { displayToProperty } from '../../utils/fieldMapping';
import { confirmParsedReceipt } from '../../utils/requests';
import CircularProgress from '@mui/material/CircularProgress';
import Alert from '@mui/material/Alert';
import Snackbar from '@mui/material/Snackbar';
import { JobCache } from '../buttons/upload_button';

export function SubmitButton() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const fields = Object.values(displayToProperty);
    
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);

	if (!id) {
		return (
			<div>
				<Button variant="contained" disabled>
					Confirm Receipt
				</Button>
			</div>
		)
	}

	const cachedData = JobCache.getData(id);

    const handleSubmit = async () => {
        const corrections: { [key: string]: string } = {};
		const fieldValues: { [key: string]: string } = {};
        
        // Get values from form fields. We only send corrections, i.e. modified values.
        for (let i = 0; i < fields.length; i++) {
            const fieldId = `text-field-${id}-${fields[i]}`;
            const textField = document.getElementById(fieldId) as HTMLInputElement;
            if (textField && textField != cachedData[fields[i]]) {
                fieldValues[fields[i]] = textField.value;
            }
        }
        
        setIsLoading(true);
        setError(null);

        try {
            // Convert field values to the format expected by the API
			const descriptions = {
				description: fieldValues['description'],
				category: fieldValues['category']
			}
            
            // Call API to confirm the parsing job
            const result = await confirmParsedReceipt(id, corrections, descriptions);
            
            if (result.success) {
                setSuccess(true);
                
                // Release all cached data since we've confirmed the receipt
                // The server now has a permanent copy
                JobCache.releaseJob(id);
                
                // Wait a bit before navigating away
                setTimeout(() => {
                    navigate('/dashboard');
                }, 1500);
            } else {
                setError(result.error || 'Failed to confirm receipt');
            }
        } catch (err) {
            console.error('Error confirming receipt:', err);
            setError('An unexpected error occurred');
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
                >
                    {isLoading ? (
                        <>
                            <CircularProgress size={24} style={{ marginRight: 8 }} />
                            Confirming...
                        </>
                    ) : 'Confirm Receipt'}
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
                open={success}
                autoHideDuration={3000}
                onClose={() => setSuccess(false)}
                anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
            >
                <Alert severity="success" onClose={() => setSuccess(false)}>
                    Receipt confirmed successfully!
                </Alert>
            </Snackbar>
        </>
    );
}
