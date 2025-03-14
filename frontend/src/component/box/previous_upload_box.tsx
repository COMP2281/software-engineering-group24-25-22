import React, { useState, useEffect } from 'react'
import { BoxBase } from './box_base';
import { PendingItem } from '../../types/receipt';
import { getReceipts } from '../../utils/requests';
import CircularProgress from '@mui/material/CircularProgress';

export function PreviosUploadBox() {
    const [receipts, setReceipts] = useState<PendingItem[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    
    // Fetch receipts when component mounts
    useEffect(() => {
        fetchReceipts();
    }, []);
    
    const fetchReceipts = async () => {
        setIsLoading(true);
        setError(null);
        
        try {
            const result = await getReceipts();
            
            if (result.success && result.data) {
                // Convert backend Receipt format to PendingItem format for display
                const formattedReceipts: PendingItem[] = result.data.map((receipt: any) => ({
                    id: receipt.id,
                    title: receipt.merchant_name || 'Unknown Merchant',
                    merchant: receipt.merchant_name || 'Unknown Merchant',
                    time: receipt.transaction_time || '',
                    address: receipt.merchant_address || '',
                    ref: receipt.reference_number || '',
                    cost: receipt.total_amount?.toString() || '0.00',
                    description: receipt.description || 'No description available',
                    tax: receipt.tax_amount?.toString() || '0.00',
                    category: receipt.category || 'Uncategorized',
                    image: receipt.image_url || ''
                }));
                
                setReceipts(formattedReceipts);
            } else {
                setError('Failed to load receipts');
            }
        } catch (err) {
            console.error('Error fetching receipts:', err);
            setError('An error occurred while loading receipts');
        } finally {
            setIsLoading(false);
        }
    };
    
    return (
        <div className="bg-gray-300 w-full min-w-[520px] rounded-lg overflow-hidden">
            <div className="font-bold p-4 bg-opacity-30 text-2xl">
                Previous Uploads
            </div>
            <div className="lg:max-h-[80vh] max-h-[50vh] overflow-y-auto rounded">
                {isLoading ? (
                    <div className="flex justify-center items-center p-8">
                        <CircularProgress />
                        <p className="ml-4">Loading receipts...</p>
                    </div>
                ) : error ? (
                    <div className="p-8 text-center text-red-500">
                        {error}
                    </div>
                ) : receipts.length > 0 ? (
                    <BoxBase items={receipts} buttonOption="view" />
                ) : (
                    <div className="p-8 text-center text-gray-500">
                        No receipts found. Confirmed receipts will appear here.
                    </div>
                )}
            </div>
        </div>
    );
}
