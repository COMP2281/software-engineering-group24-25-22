import React, { useState } from 'react'

import TextField from '@mui/material/TextField';

interface fieldBaseProps {
    label: string,
    itemID: number
}

export function Field({label, itemID}: fieldBaseProps) {
    const [value, setValue] = useState('')
    const [error, setError] = useState(false)
    const [rows, setRows] = useState(3)

    const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const inputValue = event.target.value;
        setValue(inputValue)
        setError(inputValue.trim() === '') 

        const lineBreaks = inputValue.split('\n').length
        setRows(Math.max(3, lineBreaks))
    }

    return (
        <div className='h-fill w-fill'> 
            <TextField
                error={error}
                id={`text-field-${itemID}`}
                label={label}
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
