import React from 'react';
import IconButton from '@mui/material/IconButton';
import EditIcon from '@mui/icons-material/Edit';

export function BoxBase({ items }: { items: { title: string; description: string }[] }) {
    return (
        <div className="p-4 w-fill h-auto space-y-4">
            {items.map((item, index) => (
                <div
                    key={index}
                    className="text-3xl border-2 bg-gray-200 p-4 rounded"
                >
                    <div className="flex items-center justify-between">
                        <div className="text-black text-xl">{item.title}</div>
                        <IconButton aria-label="edit">
                            <EditIcon />
                        </IconButton>
                    </div>
                    <div className="text-gray-800 text-lg pl-4 mt-2">{item.description}</div>
                </div>
            ))}
        </div>
    );
}
