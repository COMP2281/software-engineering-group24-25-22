import React from 'react'
import Button from '@mui/material/Button';
import PublishIcon from '@mui/icons-material/Publish';

export function ConvertToCSV() {
    return (
        <div> 
            <Button 
                variant="contained" 
            >
                <PublishIcon/>
                Convert to CSV
            </Button>
        </div>
    );
}