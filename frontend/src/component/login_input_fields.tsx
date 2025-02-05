import React from 'react'
import TextField from '@mui/material/TextField';

export function LoginInputFields() {
    return (
        <div className='flex flex-col h-fill w-fill items-center'> 
            <img
                        src={'items/waterstons.png'}
                        alt="Waterstons Icon"
                        className="max-h-[700px] max-w-[600px] w-auto h-auto object-contain py-4"
                        />
            <TextField
                required
                id="outlined-required"
                label="Username"
                variant="filled"
                className='lg:w-1/3 w-4/5'
            />
            <TextField
                id="outlined-password-input"
                label="Password"
                type="password"
                autoComplete="current-password"
                variant="filled"
                className='lg:w-1/3 w-4/5'
            />
            
        </div>
    );
}
