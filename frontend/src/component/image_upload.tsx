import React from 'react'
import { UploadButton } from '../component/buttons/upload_button.tsx'

import ImageIcon from '@mui/icons-material/Image';

export function ImageUpload() {
    return (
        <div className='bg-gray-300 w-fill'> 
            <div className='flex flex-col'>
                <div className='h-[80%] w-fill flex justify-center items-center'>
                    <ImageIcon style={{ fontSize: '200px' }} /> {/* Custom size */}
                </div>
            
                <UploadButton/>
            </div>
        </div>
    );
}
