import React from 'react';
import IconButton from '@mui/material/IconButton';
import EditIcon from '@mui/icons-material/Edit';

export function BoxBase() {
    const itemName = [
        {
            title: 'Receipt1',
            content: 'stuff stuff stuff stuff stuff stuff stuff',
        },
        {
            title: 'Receipt2',
            content: 'new stuff new stuff new stuff stuff',
        },
    ];

    return (
        <div className="bg-gray-400 p-4 w-1/2 h-auto">
            {itemName.map((item, index) => (
                <div
                    key={index}
                    className="p-4 py-8 bg-gray-600 bg-opacity-30 text-3xl border-2 mb-4 last:mb-0"
                >
                    <div className="flex items-center justify-between">
                        <div className="text-black text-xl font-bold">{item.title}</div>
                        <IconButton aria-label="edit">
                            <EditIcon />
                        </IconButton>
                    </div>
                    <div className="text-black text-lg pl-4">
                        {item.content}
                    </div>
                </div>
            ))}
        </div>
    );
}