import React from 'react'
import { BoxBase } from './box_base';

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
        title: 'Receipt2',
        description: 'More pending stuff new stuff',
    },
    {
        title: 'Receipt2',
        description: 'More pending stuff new stuff',
    },
    {
        title: 'Receipt2',
        description: 'More pending stuff new stuff',
    },
];

export function PreviosUploadBox() {
    return (
            <div className="bg-gray-300 w-fill">
                <div className="font-bold p-4 bg-opacity-30 text-2xl">
                    Pending Uploads
                </div>
                <div className=" max-h-[50vh] overflow-y-auto rounded">
                    <BoxBase items={pendingItems} showEditButton={false} />
                </div>
            </div>
        );
}
