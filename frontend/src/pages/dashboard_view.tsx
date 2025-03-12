import React, { useState } from 'react';

import { FieldTable } from '../component/fields/field_table';
import { ImageField } from '../component/fields/image_field';


export function DashBoardView() {
    return (
        <div className="flex flex-col lg:flex-row lg:h-screen  w-full ">
            <div className='lg:w-1/3 w-full p-4 h-full '>
                <ImageField progress={100} edit={false} />
            </div>
            <div className='lg:w-2/3 w-full p-4'>
                <FieldTable edit={false}/>
            </div>
        </div>
    );
}
