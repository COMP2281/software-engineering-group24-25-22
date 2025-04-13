import { useState } from 'react'
import Button from '@mui/material/Button';
import { useParams, useNavigate } from 'react-router-dom'
import { correctionFields, descriptionFields } from '../../utils/fieldMapping';
import { confirmParsedReceipt } from '../../utils/requests';
import CircularProgress from '@mui/material/CircularProgress';
import Alert from '@mui/material/Alert';
import Snackbar from '@mui/material/Snackbar';
import { Corrections, Descriptions } from '../../types/corrections';
import { JobCache } from '../buttons/upload_button';
import { isEqual } from 'lodash';

export function SubmitButton() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();

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
        const corrections: Corrections = {};
		
        // Get values from form fields. We only send corrections, i.e. modified values.
        for (let i = 0; i < correctionFields.length; i++) {
            const fieldId = `text-field-${id}-${correctionFields[i]}`;
            const textField = document.getElementById(fieldId) as HTMLInputElement;

			if ( correctionFields[i] == "cost_items" ) {
				if (textField && !isEqual(JSON.parse(textField.value), cachedData[correctionFields[i]])) {
					corrections[correctionFields[i]] = JSON.parse(textField.value);
				}
			}
			else{
				if (cachedData[correctionFields[i]] === undefined) {
					cachedData[correctionFields[i]] = ""
				}
				if (textField && textField.value != cachedData[correctionFields[i]]) {
					corrections[correctionFields[i] as Exclude<keyof Corrections, 'cost_items'>] = textField.value;
				}
			}
		}

		const descriptions: Descriptions = {
			description: "", 
			category: "",
		};

		for (let i = 0; i  < descriptionFields.length; i++) {
            const fieldId = `text-field-${id}-${descriptionFields[i]}`;
            const textField = document.getElementById(fieldId) as HTMLInputElement;
			if (textField && textField.value) {
				descriptions[descriptionFields[i]] = textField.value
			}
		}

		setIsLoading(true);
        setError(null);

        try {
            
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
