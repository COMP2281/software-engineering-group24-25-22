import React, { useState, useEffect } from 'react';
import TextField from '@mui/material/TextField';

interface InputTextFieldProps {
    itemID: number;
    field: string;
    initialValue?: string;
    setFieldValues: React.Dispatch<React.SetStateAction<{ [key: string]: string }>>;
    edit: boolean;
}

export function InputTextField({ itemID, field, initialValue = '', setFieldValues, edit }: InputTextFieldProps) {
    const [value, setValue] = useState(initialValue);
    const [error, setError] = useState(false);
    const [rows, setRows] = useState(3);

    useEffect(() => {
        setValue(initialValue);
    }, [initialValue]);

    useEffect(() => {
        setError(value.trim() === '');
        setFieldValues(prevValues => ({
            ...prevValues,
            [field]: value
        }));
    }, [value, field, setFieldValues]);

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
                id={`text-field-${itemID}-${field}`}
                value={value}
                helperText={error ? "Cannot be Empty" : ""}
                onChange={handleChange}
                variant="filled"
                multiline
                rows={rows}
                disabled={!edit}
            />
        </div>
    );
}
