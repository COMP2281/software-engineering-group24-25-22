import React from 'react';
import { Header } from '../header';
import { Outlet } from 'react-router-dom';

export function Layout() {
    return (
        <div className="h-fill flex flex-col">
            <Header />
            <div className="flex-grow">
                <Outlet />
            </div>
        </div>
    );
} 