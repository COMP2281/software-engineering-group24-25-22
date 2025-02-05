import React from 'react';
import Button from '@mui/material/Button';

export function OverviewButton() {
    const handleClick = () => {
        window.location.hash = 'overview';
    };

    return (
        <div> 
            <Button 
                variant="contained" 
                sx={{ backgroundColor: 'black', color: 'white', '&:hover': { backgroundColor: '#333' } }}
                onClick={handleClick}
            >
                Overview
            </Button>
        </div>
    );
}
