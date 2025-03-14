import React from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '@mui/material/Button';
import LogoutIcon from '@mui/icons-material/Logout';
import { logout } from '../utils/requests';

export function Header() {
    const navigate = useNavigate();
    
    const handleLogout = async () => {
        try {
            await logout();
            navigate('/login');
        } catch (error) {
            console.error('Logout error:', error);
            // Even if API logout fails, clear tokens
            localStorage.removeItem('accessToken');
            localStorage.removeItem('refreshToken');
            localStorage.removeItem('user');
            navigate('/login');
        }
    };
    
    return (
        <div className="w-full bg-cyan-900 flex items-center justify-between px-4">
            <h1 className="font-semibold text-[min(8vh,8vw)] leading-none text-green-200">
                Waterstons
            </h1>
            
            <Button 
                variant="contained" 
                color="error" 
                onClick={handleLogout}
                startIcon={<LogoutIcon />}
                className="ml-auto"
            >
                Logout
            </Button>
        </div>
    );
}
