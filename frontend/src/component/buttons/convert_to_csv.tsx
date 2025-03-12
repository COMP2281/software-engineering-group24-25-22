import React from 'react'
import Button from '@mui/material/Button';
import PublishIcon from '@mui/icons-material/Publish';
import { finished_receipts } from '../../data/receipts';

export function ConvertToCSV() {
    const handleConvertToCSV = () => {
        const headers = ['Title', 'Merchant', 'Time', 'Address', 'Reference', 'Cost', 'Description', 'Tax', 'Category'];
        const csvRows = [headers];

        finished_receipts.forEach(receipt => {
            const row = [
                receipt.title,
                receipt.merchant,
                receipt.time,
                receipt.address,
                receipt.ref,
                receipt.cost,
                receipt.description,
                receipt.tax,
                receipt.category
            ];
            csvRows.push(row);
        });

        const csvContent = csvRows.map(row => row.map(cell => 
            `"${cell?.replace(/"/g, '""')}"`).join(',')
        ).join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', 'receipts.csv');
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
    return (
        <div> 
            <Button 
                variant="contained"
                onClick={handleConvertToCSV}
            >
                <PublishIcon/>
                Convert to CSV
            </Button>
        </div>
    );
}