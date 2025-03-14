import React, { useState } from 'react';
import TextField from '@mui/material/TextField';
import waterstonLogo from '../../items/waterstons.png';

interface LoginInputProps {
    onInputChange: (field: string, value: string) => void;
    email: string;
    password: string;
    error?: string;
}

export function LoginInputFields({ onInputChange, email, password, error }: LoginInputProps) {
    return (
        <div className='flex flex-col h-fill w-fill items-center'> 
            <img
                src={waterstonLogo}
                alt="Waterstons Icon"
                className="max-h-[700px] max-w-[600px] w-auto h-auto object-contain py-4"
            />
            <TextField
                required
                id="email-input"
                label="Email"
                variant="filled"
                className='lg:w-1/3 w-4/5 mb-4'
                value={email}
                onChange={(e) => onInputChange('email', e.target.value)}
                error={!!error}
                helperText={error}
            />
            <TextField
                id="password-input"
                label="Password"
                type="password"
                autoComplete="current-password"
                variant="filled"
                className='lg:w-1/3 w-4/5'
                value={password}
                onChange={(e) => onInputChange('password', e.target.value)}
            />
        </div>
    );
}
