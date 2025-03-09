import React from 'react'

import { InputTextField } from './text_field';
import { LocationButton } from '../buttons/location_button'

interface pendingItem {
    id: string;
    title: string;
    description: string;
}

const pendingItems: pendingItem[] = [
    {
        id: '1',
        title: 'Receipt1',
        description: 'Pending stuff stuff stuff',
    },
    {
        id: '2',
        title: 'Receipt2',
        description: 'More pending stuff new stuff',
    },
    {
        id: '3',
        title: 'Receipt3',
        description: 'More pending stuff new stuff',
    },
    {
        id: '4',
        title: 'Receipt4',
        description: 'More pending stuff new stuff',
    },
    {
        id: '5',
        title: 'Receipt5',
        description: 'More pending stuff new stuff',
    },
];

interface FieldTableProps {
    setFieldValues: React.Dispatch<React.SetStateAction<{ [key: string]: string }>>;
}

export function FieldTable({ setFieldValues }: FieldTableProps) {
    const fields = [
        "Merchant Name",
        "Time",
        "Address",
        "Ref",
        "Total Cost",
        "Description (Manual)",
        "Tax",
        "Category (Manual)"
    ];

    return (
        <div className="grid grid-cols-2 gap-4 w-full p-4 bg-white shadow-lg rounded-lg ">
            {fields.map((field) => (
                <div key={field} className="flex flex-col gap-2">
                    <label className="text-xl font-semibold">{field}</label>
                    <InputTextField itemID={field} setFieldValues={setFieldValues} />
                    {field == 'Address' ? <LocationButton/> : ''}
                </div>
            ))}
        </div>
    );
}