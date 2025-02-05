import React from 'react'

import { FieldTable } from '../component/fields/field_table'

export function DashBoard() {
    return (
        <div className="flex flex-col lg:flex-row lg:h-screen justify-center items-center p-8 w-full">
            <div className='lg:w-1/3'>
                Test
            </div>
            <div className='lg:w-2/3'>
                <FieldTable/>
            </div>
            
            
            
            
        </div>
    );
}
