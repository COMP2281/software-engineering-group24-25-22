import { PendingReceipt } from '../types/receipt';

export const displayToProperty: { [key: string]: keyof PendingReceipt } = {
    'Merchant Name': 'merchant_name',
    'Time': 'transaction_time',
    'Address': 'merchant_address',
    'Ref': 'reference_number',
	'Cost List': 'cost_items',
    'Total Cost': 'total_amount',
    'Description (Manual)': 'description',
    'Tax': 'tax_amount',
    'Category (Manual)': 'category'
};

// Maps PendingItem property names to display names
export const propertyToDisplay = Object.fromEntries(
    Object.entries(displayToProperty).map(([display, prop]) => [prop, display])
) as { [K in keyof PendingReceipt]?: string }; 
