import React from 'react'
import Button from '@mui/material/Button';
import { useParams, useNavigate } from 'react-router-dom'
import { displayToProperty } from '../../utils/fieldMapping';

export function SubmitButton() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const fields = Object.values(displayToProperty);
    const numericId = parseInt(id || '0');

    const handleSubmit = () => { 
        const fieldValues: { [key: string]: string } = {};
        
        for (let i = 0; i < fields.length; i++) {
            const fieldId = `text-field-${numericId}-${fields[i]}`;
            const textField = document.getElementById(fieldId) as HTMLInputElement;
            console.log(textField);
            if (textField) {
                fieldValues[fields[i]] = textField.value;
            }
        }
        
        console.log('Field Values:', fieldValues);
        // navigate('/overview');
    };

    return (
        <div> 
            <Button 
                variant="contained" 
                onClick={handleSubmit}
            >
                Submit
            </Button>
        </div>
    );
}
