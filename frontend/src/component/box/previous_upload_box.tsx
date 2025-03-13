import React from 'react'
import { BoxBase } from './box_base';
import { finished_receipts } from '../../data/receipts';

export function PreviosUploadBox() {
    return (
            <div className="bg-gray-300 w-fill">
                <div className="font-bold p-4 bg-opacity-30 text-2xl">
                    Previous Upload
                </div>
                <div className=" lg:max-h-[80vh] max-h-[50vh] overflow-y-auto rounded">
                    <BoxBase items={finished_receipts} buttonOption={"view"} />
                </div>
            </div>
        );
}
