import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { LoginInputFields } from '../component/fields/login_input_fields';
import { LoginButton } from '../component/buttons/login_button';
import { login } from '../utils/requests';
import Snackbar from '@mui/material/Snackbar';
import Alert from '@mui/material/Alert';

export function Login() {
    const navigate = useNavigate();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | undefined>();
    const [showSuccess, setShowSuccess] = useState(false);
    
    const handleInputChange = (field: string, value: string) => {
        if (field === 'email') {
            setEmail(value);
        } else if (field === 'password') {
            setPassword(value);
        }
        
        // Clear error when user types
        if (error) setError(undefined);
    };
    
    const handleLogin = async () => {
        if (!email || !password) {
            setError('Email and password are required');
            return;
        }
        
        setIsLoading(true);
        setError(undefined);
        
        try {
            const result = await login(email, password);
            
            if (result.success) {
                setShowSuccess(true);
                setTimeout(() => {
                    navigate('/dashboard');
                }, 1000);
            } else {
                // Parse error messages if they're in a specific format
                let errorMsg = result.error;
                if (typeof errorMsg === 'string') {
                    // Extract the actual error message if it's wrapped
                    const match = errorMsg.match(/ErrorDetail\(string='([^']+)'/);
                    if (match && match[1]) {
                        errorMsg = match[1];
                    }
                }
                setError(errorMsg);
            }
        } catch (err) {
            setError('An unexpected error occurred. Please try again.');
            console.error('Login error:', err);
        } finally {
            setIsLoading(false);
        }
    };
    
    return (
        <div className="w-full h-screen flex items-center justify-center bg-gray-100">
            <div className="bg-white p-10 rounded-2xl shadow-lg w-[60rem] flex flex-col items-center">
                <h2 className="text-3xl font-semibold mb-6">Login</h2>
                <div className="w-full">
                    <LoginInputFields 
                        onInputChange={handleInputChange}
                        email={email}
                        password={password}
                        error={error}
                    />
                </div>
                <div className="w-60 mt-4 flex items-center justify-center">
                    <LoginButton 
                        onLogin={handleLogin}
                        isLoading={isLoading}
                        disabled={!email || !password}
                    />
                </div>
            </div>
            
            <Snackbar 
                open={showSuccess} 
                autoHideDuration={3000} 
                onClose={() => setShowSuccess(false)}
                anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
            >
                <Alert severity="success">Login successful! Redirecting...</Alert>
            </Snackbar>
        </div>
    );
}
