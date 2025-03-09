import React from 'react'
import { LoginInputFields } from '../component/login_input_fields';
import { LoginButton } from '../component/buttons/login_button';

const fetchWithAuth = async (url: string, options: RequestInit = {}): Promise<Response> => {
    let accessToken = localStorage.getItem('accessToken');

    // Set up headers with authorization
    let headers: HeadersInit = {
        'Content-Type': 'application/json',
        ...options.headers,
        'Authorization': `Bearer ${accessToken}`
    };

    const makeRequest = async (): Promise<Response> => {
        return fetch(url, { ...options, headers });
    };

    try {
        let response = await makeRequest();

        // Handle 401 Unauthorized - token may have expired
        if (response.status === 401) {
            console.warn("Access token expired. Attempting refresh...");

            // Attempt to refresh token
            const newToken = await refreshToken();
            if (newToken) {
                localStorage.setItem('accessToken', newToken);
                headers = {
                    ...headers,
                    'Authorization': `Bearer ${newToken}`
                };

                // Retry request with new token
                response = await makeRequest();
            } else {
                // Redirect to login if refresh failed
                redirectToLogin();
                throw new Error('Authentication failed');
            }
        }

        return response;
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
};

// Mock refreshToken function (should be implemented)
const refreshToken = async (): Promise<string | null> => {
    try {
        const response = await fetch('auth/refresh/', {
            method: 'POST',
            credentials: 'include'
        });

        if (!response.ok) {
            console.error("Failed to refresh token");
            return null;
        }

        const data = await response.json();
        return data.accessToken || null;
    } catch (error) {
        console.error("Error refreshing token:", error);
        return null;
    }
};

const redirectToLogin = () => {
    window.location.hash = 'login'
}

export function Login() {
    return (
        <div className="w-full h-screen flex items-center justify-center bg-gray-100">
            <div className="bg-white p-10 rounded-2xl shadow-lg w-[60rem] flex flex-col items-center">
                <h2 className="text-3xl font-semibold mb-6">Login</h2>
                <div className="w-full">
                    <LoginInputFields />
                </div>
                <div className="w-60 mt-4 flex items-center justify-center">
                    <LoginButton/>
                </div>
                
            </div>
        </div>
    );
}
