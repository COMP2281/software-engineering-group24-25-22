import React, { useState, useEffect } from 'react';
import { BoxBase } from './box_base';
import { UploadEvents } from '../image_upload';
import { PendingItem } from '../../types/receipt';
import CircularProgress from '@mui/material/CircularProgress';
import { JobCache } from '../buttons/upload_button';

export function PendingUploadBox() {
    const [pendingItems, setPendingItems] = useState<PendingItem[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    
    // Only listen for newly parsed receipts since we don't have a jobs list endpoint
    useEffect(() => {
        // No initial loading since we're not fetching
        setIsLoading(false);
        
        // Listen for newly parsed receipts
        UploadEvents.onReceiptParsed = (data: any) => {
            // Convert the parsed data to PendingItem format
            const newReceipt: PendingItem = {
                id: data.id, // Use job_id if available
                title: data.merchant_name || 'Unknown Merchant', // Title is merchant name
                merchant: data.merchant_name || 'Unknown Merchant',
                time: data.date || new Date().toLocaleString(),
                address: data.merchant_address || '',
                ref: data.reference_number || '',
                cost: data.total_amount?.toString() || '0.00',
                description: data.description || 'Just parsed receipt.', // Default description
                tax: data.tax_amount?.toString() || '0.00',
                category: data.category || 'Uncategorized',
                image: data.local_image_url || data.image_url || ''
            };
            
            // Add to the beginning of the list
            setPendingItems(prev => [newReceipt, ...prev]);
        };
        
        // Cleanup
        return () => {
            UploadEvents.onReceiptParsed = null;
        };
    }, []);

    return (
        <div className="bg-gray-300 w-full min-w-[520px] rounded-lg overflow-hidden">
            <div className="font-bold p-4 bg-opacity-30 text-2xl">
                Pending Uploads
            </div>
            <div className="max-h-[50vh] overflow-y-auto rounded">
                {isLoading ? (
                    <div className="flex justify-center items-center p-8">
                        <CircularProgress />
                        <p className="ml-4">Loading pending uploads...</p>
                    </div>
                ) : error ? (
                    <div className="p-8 text-center text-red-500">
                        {error}
                    </div>
                ) : pendingItems.length > 0 ? (
                    <BoxBase items={pendingItems} buttonOption="edit"/>
                ) : (
                    <div className="p-8 text-center text-gray-500">
                        No pending uploads yet. Upload a receipt to get started.
                    </div>
                )}
            </div>
        </div>
    );
}
