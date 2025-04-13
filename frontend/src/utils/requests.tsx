import { Corrections, Descriptions } from "../types/corrections";
// Base URL for API requests
// Using import.meta.env for Vite instead of process.env
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Authentication functions
// Function to get CSRF token if needed
const getCSRFToken = (): string | null => {
    // Try to get the CSRF token from the meta tag
    const tokenElement = document.querySelector('meta[name="csrf-token"]');
    if (tokenElement && tokenElement.getAttribute('content')) {
        return tokenElement.getAttribute('content');
    }
    
    // Try to get it from cookies
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        cookie = cookie.trim();
        if (cookie.startsWith('csrftoken=')) {
            return cookie.substring('csrftoken='.length);
        }
    }
    
    return null;
};

export const login = async (email: string, password: string): Promise<{ success: boolean; data?: any; error?: string }> => {
    try {
        // Build headers
        const headers: HeadersInit = {
            'Content-Type': 'application/json',
        };
        
        // Add CSRF token if available
        const csrfToken = getCSRFToken();
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
        }
        
        const response = await fetch(`${API_BASE_URL}/api/auth/login/`, {
            method: 'POST',
            headers,
            credentials: 'include', // Include cookies
            body: JSON.stringify({ email, password }),
        });

        const data = await response.json();

        if (!response.ok) {
            // Handle different error formats from the backend
            let errorMessage = 'Login failed';
            
            if (data.non_field_errors && data.non_field_errors.length > 0) {
                // Handle Django Rest Framework's non_field_errors
                errorMessage = data.non_field_errors.join(",");
            } else if (data.detail) {
                errorMessage = data.detail;
            } else if (data.error) {
                errorMessage = data.error;
            } else if (typeof data === 'string') {
                errorMessage = data;
            }
            
            return { 
                success: false, 
                error: errorMessage
            };
        }

        // Store tokens in localStorage
        localStorage.setItem('accessToken', data.access);
        localStorage.setItem('refreshToken', data.refresh);
        localStorage.setItem('user', JSON.stringify(data.user));

        return { success: true, data };
    } catch (error) {
        console.error('Login error:', error);
        return { 
            success: false, 
            error: 'Network error occurred' 
        };
    }
};

export const logout = async (): Promise<boolean> => {
    try {
		const accessToken = localStorage.getItem('accessToken');
        const refreshToken = localStorage.getItem('refreshToken');
        if (!refreshToken) return true;

        const response = await fetch(`${API_BASE_URL}/api/auth/logout/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
				'Authorization': `Bearer ${accessToken}`
            },
            body: JSON.stringify({ refresh: refreshToken }),
        });

        // Clear localStorage regardless of response
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('user');

        return response.ok;
    } catch (error) {
        console.error('Logout error:', error);
        
        // Clear localStorage on error too
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('user');
        
        return false;
    }
};

// Function to redirect to login page
export const redirectToLogin = () => {
    window.location.href = '/login';
};

// Token refresh functionality
const refreshToken = async (): Promise<string | null> => {
    try {
        const refreshToken = localStorage.getItem('refreshToken');
        if (!refreshToken) return null;

        // Build headers
        const headers: HeadersInit = {
            'Content-Type': 'application/json',
        };
        
        // Add CSRF token if available
        const csrfToken = getCSRFToken();
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
        }

        const response = await fetch(`${API_BASE_URL}/api/auth/refresh/`, {
            method: 'POST',
            headers,
            credentials: 'include', // Include cookies
            body: JSON.stringify({ refresh: refreshToken }),
        });

        if (!response.ok) {
            console.error("Failed to refresh token");
            return null;
        }

        const data = await response.json();
        return data.access || null;
    } catch (error) {
        console.error("Error refreshing token:", error);
        return null;
    }
};

// Main fetch utility for authenticated requests
export const fetchWithAuth = async (url: string, options: RequestInit = {}): Promise<Response> => {
    let accessToken = localStorage.getItem('accessToken');

    let headers: Record<string, string> = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`
    };
    
    // Merge any existing headers from options
    if (options.headers) {
        const optionHeaders = options.headers as Record<string, string>;
        Object.keys(optionHeaders).forEach(key => {
            headers[key] = optionHeaders[key];
        });
    }
    
    // Add CSRF token if available and not already present
    if (!headers['X-CSRFToken']) {
        const csrfToken = getCSRFToken();
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
        }
    }

    const makeRequest = async (): Promise<Response> => {
        return fetch(`${API_BASE_URL}${url}`, { 
            ...options, 
            headers,
            credentials: 'include', // Include cookies
        });
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

// Receipt API functions
export const getReceipts = async (): Promise<{ success: boolean; data?: any; error?: string }> => {
    try {
        const response = await fetchWithAuth('/api/receipts/');
        
        if (!response.ok) {
            return {
                success: false,
                error: 'Failed to fetch receipts'
            };
        }
        
        const data = await response.json();
        return { success: true, data };
    } catch (error) {
        console.error('Error fetching receipts:', error);
        return {
            success: false,
            error: 'Network error occurred'
        };
    }
};

export const getReceipt = async (id: string): Promise<{ success: boolean; data?: any; error?: string }> => {
    try {
        const response = await fetchWithAuth(`/api/receipts/${id}/`);
        
        if (!response.ok) {
            return {
                success: false,
                error: 'Failed to fetch receipt'
            };
        }
        
        const data = await response.json();
        return { success: true, data };
    } catch (error) {
        console.error(`Error fetching receipt ${id}:`, error);
        return {
            success: false,
            error: 'Network error occurred'
        };
    }
};

export const saveReceipt = async (id: string, receiptData: any): Promise<{ success: boolean; data?: any; error?: string }> => {
    try {
        const response = await fetchWithAuth(`/api/receipts/${id}/`, {
            method: 'PUT',
            body: JSON.stringify(receiptData)
        });
        
        if (!response.ok) {
            return {
                success: false,
                error: 'Failed to update receipt'
            };
        }
        
        const data = await response.json();
        return { success: true, data };
    } catch (error) {
        console.error(`Error updating receipt ${id}:`, error);
        return {
            success: false,
            error: 'Network error occurred'
        };
    }
};

export const createReceipt = async (receiptData: any): Promise<{ success: boolean; data?: any; error?: string }> => {
    try {
        const response = await fetchWithAuth('/api/receipts/', {
            method: 'POST',
            body: JSON.stringify(receiptData)
        });
        
        if (!response.ok) {
            return {
                success: false,
                error: 'Failed to create receipt'
            };
        }
        
        const data = await response.json();
        return { success: true, data };
    } catch (error) {
        console.error('Error creating receipt:', error);
        return {
            success: false,
            error: 'Network error occurred'
        };
    }
};

export const deleteReceipt = async (id: string): Promise<{ success: boolean; error?: string }> => {
    try {
        const response = await fetchWithAuth(`/api/receipts/${id}/`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            return {
                success: false,
                error: 'Failed to delete receipt'
            };
        }
        
        return { success: true };
    } catch (error) {
        console.error(`Error deleting receipt ${id}:`, error);
        return {
            success: false,
            error: 'Network error occurred'
        };
    }
};

// Receipt Parser API functions
export const parseReceipt = async (file: File): Promise<{ success: boolean; data?: any; error?: string }> => {
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        // For FormData, we need to remove the Content-Type header so the browser can set it with the boundary
        const headers: HeadersInit = {
            'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
            // Remove Content-Type so browser sets it with boundary
        };
        
        // Add CSRF token if available
        const csrfToken = getCSRFToken();
        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;
        }
        
        const response = await fetch(`${API_BASE_URL}/api/parser/parse/`, {
            method: 'POST',
            headers,
            credentials: 'include', // Include cookies
            body: formData
        });
        
        if (!response.ok) {
            return {
                success: false,
                error: 'Failed to parse receipt'
            };
        }
        
        const data = await response.json();
        return { success: true, data };
    } catch (error) {
        console.error('Error parsing receipt:', error);
        return {
            success: false,
            error: 'Network error occurred'
        };
    }
};

export const getAllJobs = async (): Promise<{ success: boolean; data?: any; error?: string }> => {
    try {
        const response = await fetchWithAuth(`/api/parser/all`, {
			method: 'GET'
		});
        
        if (!response.ok) {
            return {
                success: false,
                error: 'Failed to get parsing status'
            };
        }
        
        const data = await response.json();
        return { success: true, data, };
    } catch (error) {
        console.error(`Error getting user's job list:`, error);
        return {
            success: false,
            error: 'Network error occurred'
        };
    }
}

export const getParsingStatus = async (jobId: string): Promise<{ success: boolean; data?: any; error?: string }> => {
    try {
        const response = await fetchWithAuth(`/api/parser/status/${jobId}/`);
        
        if (!response.ok) {
            return {
                success: false,
                error: 'Failed to get parsing status'
            };
        }
        
        const data = await response.json();
        return { success: true, data };
    } catch (error) {
        console.error(`Error getting parsing status for job ${jobId}:`, error);
        return {
            success: false,
            error: 'Network error occurred'
        };
    }
};

export const confirmParsedReceipt = async (jobId: string, corrections: Corrections, descriptions: Descriptions): Promise<{ success: boolean; data?: any; error?: string }> => {
    try {
        const response = await fetchWithAuth(`/api/parser/confirm/${jobId}/`, {
            method: 'POST',
            body: JSON.stringify({ corrections: corrections, descriptions: descriptions })
        });
        
        if (!response.ok) {
            return {
                success: false,
                error: 'Failed to confirm receipt'
            };
        }
        
        const data = await response.json();
        return { success: true, data };
    } catch (error) {
        console.error(`Error confirming parsed receipt for job ${jobId}:`, error);
        return {
            success: false,
            error: 'Network error occurred'
        };
    }
};

export const discardParsedReceipt = async (jobId: string): Promise<{ success: boolean; error?: string }> => {
    try {
        const response = await fetchWithAuth(`/api/parser/discard/${jobId}/`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            return {
                success: false,
                error: 'Failed to discard receipt'
            };
        }
        
        return { success: true };
    } catch (error) {
        console.error(`Error discarding parsed receipt for job ${jobId}:`, error);
        return {
            success: false,
            error: 'Network error occurred'
        };
    }
};
