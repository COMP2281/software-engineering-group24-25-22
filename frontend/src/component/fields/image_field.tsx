import React from 'react';
import { useParams } from 'react-router-dom';
import { pendingItems } from '../../data/receipts';
import { BackButton } from '../buttons/back_button';
import { SubmitButton } from '../buttons/submit_button';
import ImageIcon from '@mui/icons-material/Image';
import LinearProgress from '@mui/material/LinearProgress';

interface BoxBaseProps {
    progress: number;
}

export function ImageField({ progress, edit }: BoxBaseProps) {
    const { id } = useParams<{ id: string }>();
    const numericId = parseInt(id || '0');
    const foundItem = pendingItems.find(item => item.id === numericId);
    const image = foundItem?.image || "None";

    return (                                                                
        <div className="w-full h-full">
            <div className="flex flex-col">
                <div className="w-full flex flex-col justify-center items-center">
                    {image !== "None" ? (
                        <img
                            src={image}
                            alt="Receipt"
                            className="max-h-[700px] max-w-[600px] w-auto h-auto object-contain pb-4"
                        />
                    ) : (
                        <ImageIcon style={{ fontSize: '500px' }} className='pb-4' />
                    )}
                    <LinearProgress variant="determinate" value={progress} className="w-full mt-2" />
                </div>
                <div className="flex flex-row justify-between p-4 w-full ">
                    <BackButton />
                    {edit === true && <SubmitButton />}
                </div>
            </div>
        </div>
    );
}