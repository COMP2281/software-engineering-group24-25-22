import React from 'react';
import { FiEdit } from 'react-icons/fi'; // Replace EditIcon with a Tailwind-compatible icon

export function BoxBase() {
    const itemName = ['receipt1', 'receipt2'];

    return (
        <div className="bg-gray-400 p-4 w-1/2 h-auto">
            {itemName.map((value, index) => (
                <div
                    key={index}
                    className="flex items-center justify-between p-4 py-8 bg-gray-600 bg-opacity-30 text-3xl border-4 mb-4 last:mb-0"
                >
                    <div className="text-black text-xl">
                        {value}
                    </div>
                    <button
                        aria-label="edit"
                        className="p-2 bg-transparent hover:bg-gray-700 rounded-full"
                    >
                        <FiEdit className="text-black text-xl" />
                    </button>
                </div>
            ))}
        </div>
    );
}