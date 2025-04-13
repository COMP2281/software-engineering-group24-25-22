import React, { useState } from 'react';
import Button from '@mui/material/Button';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import CircularProgress from '@mui/material/CircularProgress';
import { styled } from '@mui/material/styles';
import { parseReceipt } from '../../utils/requests';

// Comprehensive cache for both job data and images
export const JobCache = {
    // Store images by job ID -> image URL
    images: new Map<string, string>(),
    
    // Store extracted data by job ID -> parsed data object
    data: new Map<string, any>(),
    
    // Store image and return an object URL
    storeImage: (jobId: string, file: File): string => {
        const objectUrl = URL.createObjectURL(file);
        JobCache.images.set(jobId, objectUrl);
        return objectUrl;
    },
    
    // Get image URL by job ID
    getImageUrl: (jobId: string): string | undefined => {
        return JobCache.images.get(jobId);
    },
    
    // Store parsed receipt data
    storeData: (jobId: string, extractedData: any): void => {
        JobCache.data.set(jobId, extractedData);
    },
    
    // Get parsed receipt data by job ID
    getData: (jobId: string): any | undefined => {
        return JobCache.data.get(jobId);
    },
    
    // Clean up all job resources when no longer needed
    releaseJob: (jobId: string): void => {
        // Clean up image URL
        const url = JobCache.images.get(jobId);
        if (url) {
            URL.revokeObjectURL(url);
            JobCache.images.delete(jobId);
        }
        
        // Clean up data
        JobCache.data.delete(jobId);
    }
};

const VisuallyHiddenInput = styled('input')({
    clip: 'rect(0 0 0 0)',
    clipPath: 'inset(50%)',
    height: 1,
    overflow: 'hidden',
    position: 'absolute',
    bottom: 0,
    left: 0,
    whiteSpace: 'nowrap',
    width: 1,
});

interface UploadButtonProps {
    onUploadSuccess?: (jobId: string, data: any) => void;
    onUploadError?: (error: string) => void;
}

export function UploadButton({ onUploadSuccess, onUploadError }: UploadButtonProps) {
    const [isUploading, setIsUploading] = useState(false);
    
    const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const files = event.target.files;
        if (!files || files.length === 0) return;
        
        setIsUploading(true);
        
        try {
            // Upload the first file for now (could be enhanced to handle multiple)
            const file = files[0];
            const result = await parseReceipt(file);
            
            if (result.success) {
                // For synchronous API, the data is returned directly, not as a job
                // Use the file name or timestamp as a unique ID if needed
                const uniqueId = result.data.id;
                
                // Store the image file and get its object URL
                const localImageUrl = JobCache.storeImage(uniqueId, file);
                
                // Add the local image URL to the extracted data
                const enhancedData = {
					id: result.data.id,
                    ...result.data.extracted_data,
                    local_image_url: localImageUrl
                };
                
                // Store the extracted data in our cache
                JobCache.storeData(uniqueId, enhancedData);
                
                onUploadSuccess?.(uniqueId, enhancedData);
            } else {
                onUploadError?.(result.error || 'Failed to upload receipt');
            }
        } catch (error) {
            console.error('Error uploading file:', error);
            onUploadError?.('An unexpected error occurred during upload');
        } finally {
            setIsUploading(false);
            // Reset the input so the same file can be uploaded again
            event.target.value = '';
        }
    };
    
    return (
        <Button
            component="label"
            role={undefined}
            variant="contained"
            tabIndex={-1}
            startIcon={!isUploading && <CloudUploadIcon />}
            disabled={isUploading}
            sx={{ 
				backgroundColor: '#3d8c40',
                '&:hover': {
					backgroundColor: '#4CAF50',
                },
            }}
        >
            {isUploading ? (
                <>
                    <CircularProgress size={24} style={{ marginRight: 8 }} /> 
                    Uploading...
                </>
            ) : (
                'Upload Receipt'
            )}
            <VisuallyHiddenInput
                type="file"
                onChange={handleFileChange}
                accept="image/*,.pdf" // Accept images and PDFs
                disabled={isUploading}
            />
        </Button>
    );
}

