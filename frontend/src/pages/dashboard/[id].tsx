import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FieldTable } from '../../component/fields/field_table';
import { pendingItems } from '../../data/receipts';
import { PendingItem } from '../../types/receipt';
import { displayToProperty } from '../../utils/fieldMapping';

export default function ReceiptDashboard() {
    const { id } = useParams<{ id: string }>();
    const numericId = id ? parseInt(id, 10) : null;
    const navigate = useNavigate();
    const [receipt, setReceipt] = useState<PendingItem | null>(null);
    const [fieldValues, setFieldValues] = useState<{ [key: string]: string }>({});

    useEffect(() => {
        if (!numericId) return;
        
        const foundReceipt = pendingItems.find(item => item.id === numericId);
        
        if (!foundReceipt) {
            console.error(`Receipt with ID ${numericId} not found`);
            navigate('/upload');
            return;
        }

        setReceipt(foundReceipt);

        // Convert numeric values to strings for the form
        const initialValues = Object.entries(displayToProperty).reduce((acc, [display, prop]) => {
            acc[display] = String(foundReceipt[prop]);
            return acc;
        }, {} as { [key: string]: string });

        setFieldValues(initialValues);
    }, [numericId, navigate]);

    if (!receipt || !numericId) {
        return (
            <div className="p-8">
                <h1 className="text-2xl font-bold mb-4">Loading receipt data...</h1>
            </div>
        );
    }

    return (
        <div className="p-8">
            <h1 className="text-2xl font-bold mb-4">Receipt Details - {receipt.title}</h1>
            <div className="mb-8">
                <FieldTable 
                    itemID={numericId}
                    setFieldValues={setFieldValues} 
                    initialValues={fieldValues}
                />
            </div>
            <div className="flex justify-end space-x-4">
                <button
                    onClick={() => navigate('/upload')}
                    className="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300"
                >
                    Back
                </button>
                <button
                    onClick={() => {
                        const updatedReceipt = { ...receipt };
                        Object.entries(fieldValues).forEach(([display, value]) => {
                            const prop = displayToProperty[display];
                            if (prop) {
                                updatedReceipt[prop] = value;
                            }
                        });
                        console.log('Saving updated receipt:', updatedReceipt);
                        navigate('/upload');
                    }}
                    className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                >
                    Save Changes
                </button>
            </div>
        </div>
    );
} 