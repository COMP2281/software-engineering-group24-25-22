import React, { useState } from 'react'
import { useParams } from 'react-router-dom'
import { pendingItems } from '../../data/receipts';
import { InputTextField } from './text_field';
import { LocationButton } from '../buttons/location_button'
import { SaveButton } from '../buttons/save_button'
import { displayToProperty } from '../../utils/fieldMapping';
import { PendingItem } from '../../types/receipt';

export function FieldTable() {
    const { id } = useParams<{ id: string }>();
    const fields = Object.keys(displayToProperty);
    const numericId = parseInt(id || '0');
    
    const foundItem = pendingItems.find(item => item.id === numericId) as PendingItem | undefined;
    const itemValues: Partial<PendingItem> = foundItem || {};
    
    const [currentFieldValues, setCurrentFieldValues] = useState<{ [key: string]: string }>({});
    
    return (
        <div className="flex flex-col gap-4">
            <div className="grid grid-cols-2 gap-4 w-full p-4 bg-white shadow-lg rounded-lg">
                {fields.map((field) => (
                    <div key={field} className="flex flex-col gap-2">
                        <label className="text-xl font-semibold">{field}</label>
                        <InputTextField 
                            itemID={numericId}
                            field={field}
                            initialValue={String(itemValues[displayToProperty[field]] || '')}
                            setFieldValues={setCurrentFieldValues}
                        />
                        {field === 'Address' && <LocationButton />}
                    </div>
                ))}
            </div>
            <div className="flex justify-end mt-4">
                <SaveButton itemID={numericId} fieldValues={currentFieldValues} />
            </div>
        </div>
    );
}