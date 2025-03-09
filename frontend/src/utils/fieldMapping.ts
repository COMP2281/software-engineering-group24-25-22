import { PendingItem } from '../types/receipt';

// Maps display names to PendingItem property names
export const displayToProperty: { [key: string]: keyof PendingItem } = {
    'Merchant Name': 'merchant',
    'Time': 'time',
    'Address': 'address',
    'Ref': 'ref',
    'Total Cost': 'cost',
    'Description (Manual)': 'description',
    'Tax': 'tax',
    'Category (Manual)': 'category'
};

// Maps PendingItem property names to display names
export const propertyToDisplay = Object.fromEntries(
    Object.entries(displayToProperty).map(([display, prop]) => [prop, display])
) as { [K in keyof PendingItem]?: string }; 