import React from 'react'
import Button from '@mui/material/Button';
import FmdGoodIcon from '@mui/icons-material/FmdGood';

export function LocationButton() {
    return (
        <div> 
            <Button 
                variant="contained" 
                sx={{ backgroundColor: 'black', color: 'white', '&:hover': { backgroundColor: '#333' } }}
            >
                <FmdGoodIcon/>
                Get Location
            </Button>
        </div>
    );
}