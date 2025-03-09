import React from 'react';
import { BoxBase } from './box_base';
import { Description } from '@mui/icons-material';

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
        title: 'Receipt2',
        description: 'More pending stuff new stuff',
    },
    {
        id: '4',
        title: 'Receipt2',
        description: 'More pending stuff new stuff',
    },
    {
        id: '5',
        title: 'Receipt2',
        description: 'More pending stuff new stuff',
    },
];

export function PendingUploadBox() {
    return (
        <div className="bg-gray-300 w-fill">
            <div className="font-bold p-4 bg-opacity-30 text-2xl">
                Pending Uploads
            </div>
            <div className=" max-h-[50vh] overflow-y-auto rounded">
                <BoxBase items={pendingItems} buttonOption="edit"/>
            </div>
        </div>
    );
}
