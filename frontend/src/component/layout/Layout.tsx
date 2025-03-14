import React, { useEffect, useState } from 'react';
import { Header } from '../header';
import { Outlet, Navigate } from 'react-router-dom';
import CircularProgress from '@mui/material/CircularProgress';

export function Layout() {
    const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
    const [isChecking, setIsChecking] = useState<boolean>(true);

    // Check if the user is authenticated
    useEffect(() => {
        const checkAuth = () => {
            const token = localStorage.getItem('accessToken');
            
            // If no token exists, user is not authenticated
            if (!token) {
                setIsAuthenticated(false);
                setIsChecking(false);
                return;
            }
            
            // Token exists, check if it's valid (not expired)
            // For simplicity, we're just checking if token exists
            setIsAuthenticated(true);
            setIsChecking(false);
        };
        
        checkAuth();
    }, []);

    // While checking authentication status, show loading indicator
    if (isChecking) {
        return (
            <div className="flex items-center justify-center h-screen">
                <CircularProgress />
                <p className="ml-4">Loading...</p>
            </div>
        );
    }

    // If not authenticated, redirect to login
    if (!isAuthenticated) {
        return <Navigate to="/login" replace />;
    }

    // If authenticated, show the layout with header and outlet for child routes
    return (
        <div className="h-fill flex flex-col">
            <Header />
            <div className="flex-grow">
                <Outlet />
            </div>
        </div>
    );
} 