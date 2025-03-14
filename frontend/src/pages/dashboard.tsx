import React from 'react';

import { PendingUploadBox } from '../component/box/pending_upload_box.tsx';
import { PreviosUploadBox } from '../component/box/previous_upload_box.tsx';
import { ImageUpload } from '../component/image_upload.tsx'
import { ConvertToCSV } from '../component/buttons/convert_to_csv.tsx';

export function Dashboard() {
    return (
        <div className="flex flex-col lg:flex-row lg:h-screen justify-center items-center p-8">
            <div className="lg:w-1/2 flex justify-center items-center h-full">
                    
                <div className="w-fill flex flex-col gap-y-4">
                    <ImageUpload />
                    <PendingUploadBox />
                    
                </div>
            </div>

            <div className="lg:h-full lg:w-1 bg-gray-700 w-full h-1 my-4 lg:my-0 lg:mx-4"></div>

            <div className="lg:w-1/2 w-full flex justify-center items-center py-4 h-full">
                <div className="flex flex-col gap-y-4 items-center">
                    <ConvertToCSV />
                    <PreviosUploadBox />
                </div>
            </div>
        </div>
    );
}

