import React from 'react'
import TextField from '@mui/material/TextField';

export function LoginInputFields() {
    return (
        <div className='flex flex-col items-center'> 
            <img
                        src={'items/waterstons.png'}
                        alt="Waterstons Icon"
                        className="max-h-[700px] max-w-[600px] w-auto h-auto object-contain pb-4"
                        />
            <TextField
                required
                id="outlined-required"
                label="Username"
                variant="filled"
            />
            <TextField
                id="outlined-password-input"
                label="Password"
                type="password"
                autoComplete="current-password"
                variant="filled"
            />
            
        </div>
    );
}
