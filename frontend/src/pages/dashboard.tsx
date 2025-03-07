import React, { useState } from 'react';

import { FieldTable } from '../component/fields/field_table';
import { ImageField } from '../component/fields/image_field';


export function DashBoard() {
    const [fieldValues, setFieldValues] = useState<{ [key: string]: string }>({});

    const totalFields = 8;
    const filledFields = Object.values(fieldValues).filter(value => value.trim() !== "").length;
    const progress = (filledFields / totalFields) * 100;

    return (
        <div className="flex flex-col lg:flex-row lg:h-screen  w-full ">
            <div className='lg:w-1/3 w-full p-4 h-full '>
                <ImageField image={"receipt1.png"} progress={progress} />
            </div>
            <div className='lg:w-2/3 w-full p-4'>
                <FieldTable setFieldValues={setFieldValues} />
            </div>
        </div>
    );
}
