import React from 'react';
import LinearProgress from '@mui/material/LinearProgress';
import ImageIcon from '@mui/icons-material/Image';

import { SaveButton } from '../buttons/save_button';
import { BackButton } from '../buttons/back_button';

interface BoxBaseProps {
    image: string;
    progress: number;
}

export function ImageField({ image, progress }: BoxBaseProps) {
    const imagePath = image ? `/items/${image}` : null;

    return (                                                                
        <div className="w-full h-full">
            <div className="flex flex-col ">
                <div className="w-full flex flex-col justify-center items-center">
                    {imagePath ? (
                        <img
                        src={imagePath}
                        alt="Item"
                        className="max-h-[700px] max-w-[600px] w-auto h-auto object-contain pb-4"
                        />
                    ) : (
                        <ImageIcon style={{ fontSize: '500px' }} className='pb-4' />
                    )}
                    <LinearProgress variant="determinate" value={progress} className="w-full mt-2" />
                </div>
                <div className="flex flex-row justify-between p-4 w-full">
                    <BackButton />
                </div>

                
            </div>
        </div>
    );
}