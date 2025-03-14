import React from 'react'
import Button from '@mui/material/Button';
import CircularProgress from '@mui/material/CircularProgress';

interface LoginButtonProps {
    onLogin: () => void;
    isLoading: boolean;
    disabled: boolean;
}

export function LoginButton({ onLogin, isLoading, disabled }: LoginButtonProps) {
    return (
        <div> 
            <Button 
                variant="contained" 
                onClick={onLogin}
                disabled={isLoading || disabled}
                style={{ position: 'relative' }}
            >
                {isLoading ? (
                    <CircularProgress 
                        size={24} 
                        style={{ 
                            position: 'absolute',
                            top: '50%',
                            left: '50%',
                            marginTop: '-12px',
                            marginLeft: '-12px'
                        }} 
                    />
                ) : 'Login'}
            </Button>
        </div>
    );
}