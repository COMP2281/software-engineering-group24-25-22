import React from 'react'

import { UploadButton } from '../component/buttons/upload_button.tsx'
import ImageIcon from '@mui/icons-material/Image';

export function ImageUpload() {
    return (
        <div className='bg-gray-300 w-fill'> 
            <div className='flex flex-col justify-center items-center p-3'>
                <div className='justify-center items-center text-2xl font-bold'>
                    Upload
                </div>
                <div className='h-[80%] w-fill'>
                    <ImageIcon style={{ fontSize: '200px' }} />
                </div>
                <div className="w-fill">
                    <UploadButton/>
                </div>
            </div>
        </div>
    );
}
