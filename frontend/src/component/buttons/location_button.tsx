import React from 'react'
import Button from '@mui/material/Button';
import FmdGoodIcon from '@mui/icons-material/FmdGood';

export function LocationButton() {
    return (
        <div> 
            <Button 
                variant="contained" 
            >
                <FmdGoodIcon/>
                Get Location
            </Button>
        </div>
    );
}