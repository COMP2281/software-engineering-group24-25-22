import React, { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { InputTextField } from './text_field';
import { LocationButton } from '../buttons/location_button'
import { SaveButton } from '../buttons/save_button'
import { displayToProperty, propertyToDisplay } from '../../utils/fieldMapping';
import { getReceipt, getParsingStatus } from '../../utils/requests';
import CircularProgress from '@mui/material/CircularProgress';
import Alert from '@mui/material/Alert';
import { JobCache } from '../buttons/upload_button';

export function FieldTable({ edit }: {edit: boolean} ) {
    const { id } = useParams<{ id: string }>();
    const fields = Object.entries(displayToProperty);
    const [isLoading, setIsLoading] = useState(true); // Start with loading state
    const [error, setError] = useState<string | null>(null);
    const [receiptData, setReceiptData] = useState<any>(null);
    const [currentFieldValues, setCurrentFieldValues] = useState<{ [key: string]: string }>({});

    // Fetch data only when component mounts or dependencies change
    useEffect(() => {
        let isMounted = true; // For avoiding state updates after unmount
        
        if (!id) {
            setIsLoading(false);
            setError("No receipt ID provided");
            return;
        }
        
        const loadDataFromProviders = async () => {
            if (edit) {
                // Check if we have cached data for this job
                const cachedData = JobCache.getData(id);
                
                if (cachedData) {
                    // Use cached data - no need for API call
                    if (isMounted) {
                        setReceiptData(cachedData);
                        
                        // Transform the cached data to field values
                        const transformedData: { [key: string]: string } = {
                            ...cachedData,
                            description: cachedData.description || 'Just parsed receipt.',
                            category: cachedData.category || 'Uncategorized',
                        };
                        
                        setCurrentFieldValues(transformedData);
                        setIsLoading(false);
                    }
                    return true; // Data was loaded from cache
				}
            }
			else {
				try {
					// Fetch receipt data from API when in view mode
					const result = await getReceipt(id);

					if (result.success && isMounted) {
						// Transform API data to field values
						const transformedData: { [key: string]: string } = {};
						
						// Process each field from the API response
						for (let index = 0; index < fields.length; index++) {
							const fieldKey = fields[index][1];
							transformedData[fieldKey] = result.data[fieldKey] || '';
						}
						
						setCurrentFieldValues(transformedData);
						setReceiptData(result.data);
						setIsLoading(false);
						return true;
					} else if (!result.success && isMounted) {
						setError(result.error || 'Failed to load receipt data');
						setIsLoading(false);
					}
				} catch (error) {
					if (isMounted) {
						console.error('Error fetching receipt:', error);
						setError('An unexpected error occurred while loading receipt data');
						setIsLoading(false);
					}
				}
			}
            return false; // Data was not loaded from cache
        };
        
        // Load data from cache or API
        loadDataFromProviders();
        
        // Cleanup function runs when component unmounts or dependencies change
        return () => {
            isMounted = false; // Prevent state updates after unmount
        };
    }, [id, edit, fields]);

	if (!id) {
		return (
			<div className="flex justify-center items-center h-64">
				<p>No receipt ID provided</p>
			</div>
		)
	}
    
    // Show loading spinner if data is being fetched
    if (isLoading) {
        return (
            <div className="flex justify-center items-center h-64">
                <CircularProgress />
                <p className="ml-4">Loading receipt data...</p>
            </div>
        );
    }
    
    // Show error if there was an error loading data
    if (error) {
        return (
            <Alert severity="error" className="mb-4">
                {error}
            </Alert>
        );
    }
    
    // For new receipts or after data is loaded
    return (
        <div className="flex flex-col gap-4">
            <div className="grid grid-cols-2 gap-4 w-full p-4 bg-white shadow-lg rounded-lg">
                {fields.map((field) => (
                    <div key={field[1]} className="flex flex-col gap-2">
                        <label className="text-xl font-semibold">{field[0]}</label>
                        <InputTextField 
                            itemID={id}
                            field={field[1]}
                            initialValue={currentFieldValues[field[1]] || ''}
                            setFieldValues={setCurrentFieldValues}
                            edit={edit}
                        />
                        {field[1] === 'merchant_address' && edit === true && <LocationButton />}
                    </div>
                ))}
            </div>
            {
                edit === true && (
                    <div className="flex justify-end mt-4">
                        <SaveButton itemID={id} fieldValues={currentFieldValues} edit={edit} />
                    </div>
                )
            } 
        </div>
    );
}
