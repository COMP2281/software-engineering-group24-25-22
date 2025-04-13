export interface PendingReceipt {
    id: number;
    title: string;
    merchant: string;
    time: string;
    address: string;
    ref: string;
    cost: string;
    description: string;
    tax: string;
    category: string;
    image: string;
} 

export interface ReceiptFields {
	merchant_name: string;
	transaction_time: string;
	merchant_address: string;
	reference_number: string;
	cost_items: { [key:string]: string | number };
	total_amount: string;
	description: string;
	tax_amount: string;
	category: string;
}
