import React from 'react';
import Button from '@mui/material/Button';
import { useNavigate } from 'react-router-dom';

export function BackButton() {
    const navigate = useNavigate();

    const handleClick = () => {
        navigate('/upload');
    };

    return (
        <div> 
            <Button 
                variant="contained" 
                sx={{ backgroundColor: 'black', color: 'white', '&:hover': { backgroundColor: '#333' } }}
                onClick={handleClick}
            >
                Back
            </Button>
        </div>
    );
}
