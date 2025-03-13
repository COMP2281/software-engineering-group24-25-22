import React from 'react';
import { BoxBase } from './box_base';
import { pendingItems } from '../../data/receipts';

export function PendingUploadBox() {
    return (
        <div className="bg-gray-300 w-fill">
            <div className="font-bold p-4 bg-opacity-30 text-2xl">
                Pending Uploads
            </div>
            <div className="max-h-[50vh] overflow-y-auto rounded">
                <BoxBase items={pendingItems} buttonOption="edit"/>
            </div>
        </div>
    );
}
