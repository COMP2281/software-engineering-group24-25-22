import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { BackButton } from '../buttons/back_button';
import { SubmitButton } from '../buttons/submit_button';
import ImageIcon from '@mui/icons-material/Image';
import LinearProgress from '@mui/material/LinearProgress';
import CircularProgress from '@mui/material/CircularProgress';
import { getParsingStatus, API_BASE_URL, getReceipt } from '../../utils/requests';
import { JobCache } from '../buttons/upload_button';

interface BoxBaseProps {
    progress: number;
    edit: boolean;
}

export function ImageField({ progress, edit }: BoxBaseProps) {
    const { id } = useParams<{ id: string }>();
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [imageUrl, setImageUrl] = useState<string | null>(null);

    useEffect(() => {
        if (id) {
            // First check if we have the image cached locally
            const cachedImageUrl = JobCache.getImageUrl(id);
            
            if (cachedImageUrl) {
                setImageUrl(cachedImageUrl);
                setIsLoading(false);
            } else {
				if (edit === true) {
					// If not in cache, fetch from server
					fetchJobDetails();
				} else {
					fetchReceiptDetails();
				}
                setIsLoading(false);
            }
        } else {
            setIsLoading(false);
        }
        
        // Clean up on unmount
        return () => {
            // Note: We don't release the URL here as we might need it again
            // The cache can be managed separately with a cleanup strategy
        };
    }, [id]);

	if (!id) {
		return (
			<div className="flex justify-center items-center h-96">
				<p>No receipt ID provided</p>
			</div>
		)
	}

	const fetchReceiptDetails = async() => {
		try {
			const result = await getReceipt(id);

			if (result.success) {
				
				if (result.data.local_image_url) {
					setImageUrl(result.data.local_image_url);
				} 
				else if (result.data.file) {
					const dataUrl = `data:image/jpeg;base64,${result.data.file}`;
					setImageUrl(dataUrl);
					
					// Optionally cache this for future use
					if (id) {
						// Convert base64 to blob for efficient storage
						const byteCharacters = atob(result.data.file);
						const byteArrays = [];
						for (let i = 0; i < byteCharacters.length; i += 1024) {
							const slice = byteCharacters.slice(i, i + 1024);
							const byteNumbers = new Array(slice.length);
							for (let j = 0; j < slice.length; j++) {
								byteNumbers[j] = slice.charCodeAt(j);
							}
							const byteArray = new Uint8Array(byteNumbers);
							byteArrays.push(byteArray);
						}
						const blob = new Blob(byteArrays, { type: 'image/jpeg' });
						
						// Store in cache
						const objectUrl = URL.createObjectURL(blob);
						JobCache.images.set(id, objectUrl);
					}
				}
				else if (result.data.image_url) {
					setImageUrl(result.data.image_url);
				} 
				else if (result.data.file_id) {
					setImageUrl(`${API_BASE_URL}/api/parser/image/${result.data.file_id}/`);
				} 
				else {
					setImageUrl(null);
				}
			} else {
				setError('Failed to load receipt image');
			}
		} catch (error) {
			console.error('Error fetching receipt details:', error);
			setError('An error occurred while loading the receipt image');
		} finally {
			setIsLoading(false);
		}
	}
    
    const fetchJobDetails = async () => {
        try {
            const result = await getParsingStatus(id);
            
            if (result.success) {
                // Check multiple possible image sources in order of preference
                
                // 1. First check if the response has a local_image_url
                if (result.data.local_image_url) {
                    setImageUrl(result.data.local_image_url);
                } 
                // 2. Then check if the response has an image_url
                else if (result.data.image_url) {
                    setImageUrl(result.data.image_url);
                } 
                // 3. Then check if the response has a file_id to construct URL
                else if (result.data.file_id) {
                    setImageUrl(`${API_BASE_URL}/api/parser/image/${result.data.file_id}/`);
                } 
                // 4. Default - no image available
                else {
                    setImageUrl(null);
                }
            } else {
                setError('Failed to load receipt image');
            }
        } catch (error) {
            console.error('Error fetching job details:', error);
            setError('An error occurred while loading the receipt image');
        } finally {
            setIsLoading(false);
        }
    };
    return (                                                                
        <div className="w-full h-full">
            <div className="flex flex-col">
                <div className="w-full flex flex-col justify-center items-center">
                    {isLoading ? (
                        <div className="flex justify-center items-center h-96">
                            <CircularProgress />
                            <p className="ml-4">Loading receipt image...</p>
                        </div>
                    ) : imageUrl ? (
                        <img
                            src={imageUrl}
                            alt="Receipt"
                            className="max-h-[700px] max-w-[600px] w-auto h-auto object-contain pb-4"
                        />
                    ) : (
                        <div className="flex flex-col items-center">
                            <ImageIcon style={{ fontSize: '500px' }} className='pb-4' />
                            {error && <p className="text-red-500 mb-4">{error}</p>}
                        </div>
                    )}
                    <LinearProgress variant="determinate" value={progress} className="w-full mt-2" />
                </div>
                <div className="flex flex-row justify-between p-4 w-full">
                    <BackButton />
                    {edit === true && <SubmitButton />}
                </div>
            </div>
        </div>
    );
}
