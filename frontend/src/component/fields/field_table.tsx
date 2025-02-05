import React from 'react'

import { InputTextField } from './text_field';


const oneItem = {title: 'Receipt1', description: 'Pending stuff stuff stuff'}
const pendingItems = [
    {
        title: 'Receipt1',
        description: 'Pending stuff stuff stuff',
    },
    {
        title: 'Receipt2',
        description: 'More pending stuff new stuff',
    },
    {
        title: 'Receipt3',
        description: 'More pending stuff new stuff',
    },
    {
        title: 'Receipt4',
        description: 'More pending stuff new stuff',
    },
    {
        title: 'Receipt5',
        description: 'More pending stuff new stuff',
    },
];

export function FieldTable() {
    return (
        <div className="grid grid-cols-2 gap-4 w-full p-4">
            <div className='w-full p-4 text-2xl '>
                Merchant Name
                <InputTextField itemID={oneItem.title} />
            </div>
            <div className='w-full p-4 text-2xl '>
                Time
                <InputTextField itemID={oneItem.title} />
            </div>
            <div className='w-full p-4 text-2xl '>
                Address
                <InputTextField itemID={oneItem.title} />
            </div>
            <div className='w-full p-4 text-2xl '>
                Ref
                <InputTextField itemID={oneItem.title} />
            </div>
            <div className='w-full p-4 text-2xl '>
                Cost List
                <InputTextField itemID={oneItem.title} />
            </div>
            <div className='w-full p-4 text-2xl '>
                Description (Manual)
                <InputTextField itemID={oneItem.title} />
            </div>
            <div className='w-full p-4 text-2xl '>
                Tax
                <InputTextField itemID={oneItem.title} />
            </div>
            <div className='w-full p-4 text-2xl '>
                Category (Manual)
                <InputTextField itemID={oneItem.title} />
            </div>
            
        </div>
    );
}
