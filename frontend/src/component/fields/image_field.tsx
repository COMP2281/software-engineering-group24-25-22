import React from 'react';
import LinearProgress from '@mui/material/LinearProgress';
import ImageIcon from '@mui/icons-material/Image';

import { SubmitButton } from '../buttons/submit_button';
import { OverviewButton } from '../buttons/overview_button';

interface BoxBaseProps {
    image: string;
    progress: number;
}

export function ImageField({ image, progress }: BoxBaseProps) {
    const imagePath = image ? `frontend/dist/assets/items/${image}` : null;

    return (
        <div className="w-full">
            <div className="flex flex-col justify-center items-center ">
                <div className="w-full flex flex-col items-center">
                    {imagePath ? (
                        <img
                            src={imagePath}
                            alt="Item"
                            className="w-[400px] h-[400px] object-contain"
                        />
                    ) : (
                        <ImageIcon style={{ fontSize: '400px' }} />
                    )}
                    <LinearProgress variant="determinate" value={progress} className="w-full mt-2" />
                </div>
                <div className="flex flex-row justify-between p-4 w-full">
                    <OverviewButton />
                    <SubmitButton />
                </div>

                
            </div>
        </div>
    );
}