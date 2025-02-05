import React, { useState, useEffect } from 'react';
import TextField from '@mui/material/TextField';

interface InputTextFieldProps {
    itemID: string;
    setFieldValues: React.Dispatch<React.SetStateAction<{ [key: string]: string }>>;
}

export function InputTextField({ itemID, setFieldValues }: InputTextFieldProps) {
    const [value, setValue] = useState('');
    const [error, setError] = useState(false);
    const [rows, setRows] = useState(3);

    useEffect(() => {
        setError(value.trim() === '');
        setFieldValues(prevValues => ({
            ...prevValues,
            [itemID]: value
        }));
    }, [value, itemID, setFieldValues]);

    const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const inputValue = event.target.value;
        setValue(inputValue);
        setError(inputValue.trim() === '');

        const lineBreaks = inputValue.split('\n').length;
        setRows(Math.max(3, lineBreaks));
    };

    return (
        <div className='h-fill'>
            <TextField
                className='w-full'
                error={error}
                id={`text-field-${itemID}`}
                value={value}
                helperText={error ? "Cannot be Empty" : ""}
                onChange={handleChange}
                variant="filled"
                multiline
                rows={rows}
            />
        </div>
    );
}
