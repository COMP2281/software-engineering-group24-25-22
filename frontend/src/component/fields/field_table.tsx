import React from 'react'
import { useParams } from 'react-router-dom'

import { InputTextField } from './text_field';
import { LocationButton } from '../buttons/location_button'
import { displayToProperty } from '../../utils/fieldMapping';

interface FieldTableProps {
    setFieldValues: React.Dispatch<React.SetStateAction<{ [key: string]: string }>>;
    initialValues?: { [key: string]: string };
}

export function FieldTable({setFieldValues, initialValues = {} }: FieldTableProps) {
    const { id } = useParams<{ id: string }>();
    const fields = Object.keys(displayToProperty);

    return (
        <div className="grid grid-cols-2 gap-4 w-full p-4 bg-white shadow-lg rounded-lg">
            {fields.map((field) => (
                <div key={field} className="flex flex-col gap-2">
                    <label className="text-xl font-semibold">{field}</label>
                    <InputTextField 
                        itemID={parseInt(id || '0')}
                        field={field}
                        initialValue={initialValues[field] || ''}
                        setFieldValues={setFieldValues}
                    />
                    {field === 'Address' && <LocationButton />}
                </div>
            ))}
        </div>
    );
}