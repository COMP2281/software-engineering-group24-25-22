import React from 'react'
import Button from '@mui/material/Button';


const handleSubmit = () => { 
    console.log("Submit button clicked");
}
export function SubmitButton() {
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
