export interface Corrections {
	merchant_name?: string;
	transaction_time?: string,
	merchant_address?: string,
	reference_number?: string,
	total_amount?: string,
	tax_amount?: string,
	cost_items?: Array<{ quantity: string, item_name: string, total_price: string, unit_price: string }>,
}

export interface Descriptions {
	description: string,
	category: string
}

