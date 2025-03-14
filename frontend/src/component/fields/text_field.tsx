import React, { useState, useEffect } from 'react';
import TextField from '@mui/material/TextField';

interface InputTextFieldProps {
    itemID: string;
    field: string;
    initialValue?: string;
    setFieldValues: React.Dispatch<React.SetStateAction<{ [key: string]: string }>>;
    edit: boolean;
}

export function InputTextField({ itemID, field, initialValue = '', setFieldValues, edit }: InputTextFieldProps) {
	let formattedInitialValue = initialValue;
	if (field === 'cost_items') {
		formattedInitialValue = JSON.stringify(initialValue, null, 2);
	}

    const [value, setValue] = useState(formattedInitialValue);
    const [error, setError] = useState(false);
    const [rows, setRows] = useState(3);

    // Update value when initialValue changes (important for API loaded data)
    useEffect(() => {
        let newValue = initialValue;
        if (field === 'cost_items') {
            newValue = JSON.stringify(initialValue, null, 2);
        }
        setValue(newValue);
    }, [initialValue, field]);

    const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const inputValue = event.target.value;
        setValue(inputValue);
        setError(inputValue.trim() === '');

        // Update the parent component's state with the new value
        setFieldValues(prev => ({
            ...prev,
            [field]: inputValue
        }));

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
                InputProps={{
                    readOnly: !edit
                }}
            />
        </div>
    );
}
