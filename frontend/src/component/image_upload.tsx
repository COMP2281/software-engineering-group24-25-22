import React, { useState } from 'react';
import { UploadButton } from './buttons/upload_button';
import ImageIcon from '@mui/icons-material/Image';
import Alert from '@mui/material/Alert';
import Snackbar from '@mui/material/Snackbar';
import { getParsingStatus } from '../utils/requests';

interface UploadedJob {
    jobId: string;
    status: 'pending' | 'processing' | 'completed' | 'failed';
    data?: any;
}

// Create a simple event system to notify other components
export const UploadEvents = {
    onReceiptParsed: null as ((data: any) => void) | null
};

export function ImageUpload() {
    const [uploadedJobs, setUploadedJobs] = useState<UploadedJob[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [showSuccess, setShowSuccess] = useState(false);
    
    const handleUploadSuccess = (jobId: string, data: any) => {
        // Create a new job with completed status since parsing is done
        const newJob = { 
            jobId, 
            status: 'completed' as const, // Mark as completed immediately
            data
        };
        
        setUploadedJobs(prev => [newJob, ...prev]);
        setShowSuccess(true);
        
        // Notify other components about the new receipt
        if (UploadEvents.onReceiptParsed) {
            UploadEvents.onReceiptParsed(data);
        }
    };
    
    const handleUploadError = (errorMessage: string) => {
        setError(errorMessage);
    };
    
    const checkJobStatus = async (jobId: string) => {
        try {
            const result = await getParsingStatus(jobId);
            
            if (result.success) {
                const status = result.data.status;
                
                // Update job status
                setUploadedJobs(prev => prev.map(job => 
                    job.jobId === jobId ? { ...job, status, data: result.data } : job
                ));
                
                // Continue polling if not complete
                if (status === 'pending' || status === 'processing') {
                    setTimeout(() => checkJobStatus(jobId), 2000);
                }
            } else {
                // Mark as failed if there's an error
                setUploadedJobs(prev => prev.map(job => 
                    job.jobId === jobId ? { ...job, status: 'failed' } : job
                ));
            }
        } catch (error) {
            console.error(`Error checking job status for ${jobId}:`, error);
        }
    };
    
    return (
        <div className='bg-gray-300 w-full min-w-[520px] rounded-lg overflow-hidden'> 
            <div className='flex flex-col justify-center items-center p-3'>
                <div className='justify-center items-center text-2xl font-bold'>
                    Upload
                </div>
                <div className='h-[80%] w-fill'>
                    <ImageIcon style={{ fontSize: '200px' }} />
                </div>
                <div className="w-fill">
                    <UploadButton
                        onUploadSuccess={handleUploadSuccess}
                        onUploadError={handleUploadError}
                    />
                </div>
            </div>
            
            <Snackbar 
                open={!!error} 
                autoHideDuration={4000} 
                onClose={() => setError(null)}
                anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
            >
                <Alert severity="error" onClose={() => setError(null)}>
                    {error}
                </Alert>
            </Snackbar>
            
            <Snackbar 
                open={showSuccess} 
                autoHideDuration={3000} 
                onClose={() => setShowSuccess(false)}
                anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
            >
                <Alert severity="success" onClose={() => setShowSuccess(false)}>
                    Receipt uploaded and parsed successfully!
                </Alert>
            </Snackbar>
        </div>
    );
}
