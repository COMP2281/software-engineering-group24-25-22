import { Corrections, Descriptions } from "../types/corrections";
import { PendingReceipt, ReceiptFields } from "../types/receipt";

export const displayToProperty: { [key: string]: keyof ReceiptFields } = {
  "Merchant Name": "merchant_name",
  Time: "transaction_time",
  Address: "merchant_address",
  Ref: "reference_number",
  "Cost List": "cost_items",
  "Total Cost": "total_amount",
  "Description (Manual)": "description",
  Tax: "tax_amount",
  "Category (Manual)": "category",
};

// Maps PendingItem property names to display names
export const propertyToDisplay = Object.fromEntries(
  Object.entries(displayToProperty).map(([display, prop]) => [prop, display]),
) as { [K in keyof PendingReceipt]?: string };

export const correctionFields: (keyof Corrections)[] = [
  "merchant_name",
  "transaction_time",
  "merchant_address",
  "reference_number",
  "total_amount",
  "tax_amount",
  "cost_items",
];

export const descriptionFields: (keyof Descriptions)[] = [
	"description",
	"category"
]
