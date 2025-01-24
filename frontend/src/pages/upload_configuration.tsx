import React from 'react';

import { PendingUploadBox } from '../component/box/pending_upload_box.tsx';
import { PreviosUploadBox } from '../component/box/previous_upload_box.tsx';

export function UploadConfiguration() {
    return (
        <div className="flex flex-col lg:flex-row lg:h-screen justify-center items-center p-8">
            <div className="lg:w-1/2 w-full  py-4">
                <div className="w-4/5">
                    <PendingUploadBox />
                </div>
            </div>
            <div className="lg:w-1/2 w-full  py-4">
                <div className="w-4/5">
                    <PreviosUploadBox />
                </div>
            </div>
        </div>
    );
}
