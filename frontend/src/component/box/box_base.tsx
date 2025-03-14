import React from 'react';
import { useNavigate } from 'react-router-dom';
import IconButton from '@mui/material/IconButton';
import EditIcon from '@mui/icons-material/Edit';
import VisibilityIcon from '@mui/icons-material/Visibility';

interface BoxBaseProps {
    items: { id: number; title: string; description: string }[];
    buttonOption: "edit" | "view";
}

export function BoxBase({ items, buttonOption }: BoxBaseProps) {    
    const navigate = useNavigate();

    const handleEdit = (id: number) => {
		console.log(id)
        navigate(`/upload/${id}`);
    };

    const handleView = (id: number) => {
        navigate(`/dashboard/${id}`);
    };

    return (
        <div className="p-4 w-full h-auto space-y-4">
            {items.map((item) => (
                <div
                    key={item.id}
                    className="text-3xl border-2 bg-gray-200 p-4 rounded"
                >
                    <div className="flex items-center justify-between">
                        <div className="text-black text-xl">{item.title}</div>
                        {buttonOption === "edit" ? (
                            <IconButton 
                                aria-label="edit"
                                onClick={() => handleEdit(item.id)}
                            >
                                <EditIcon />
                            </IconButton>
                        ) : (
                            <IconButton 
                                aria-label="view"
                                onClick={() => handleView(item.id)}
                            >
                                <VisibilityIcon />
                            </IconButton>
                        )}
                    </div>
                    <div className="text-gray-800 text-lg pl-4 mt-2">{item.description}</div>
                </div>
            ))}
        </div>
    );
}
