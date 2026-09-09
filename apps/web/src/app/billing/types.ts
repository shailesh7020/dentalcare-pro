export type InvoiceStatus =
  | "DRAFT"
  | "UNPAID"
  | "PARTIALLY_PAID"
  | "PAID"
  | "OVERDUE"
  | "CANCELLED";

export type InvoiceItemType =
  | "PROCEDURE"
  | "CONSULTATION"
  | "MEDICATION"
  | "CONSUMABLE"
  | "LABORATORY"
  | "OTHER";

export type PaymentMethod =
  | "CASH"
  | "CARD"
  | "UPI"
  | "BANK_TRANSFER"
  | "CHEQUE"
  | "WALLET"
  | "OTHER";

export type DiscountType = "FIXED" | "PERCENTAGE";

export type PaymentStatus = "COMPLETED" | "REFUNDED" | "FAILED" | "CANCELLED";

export interface InvoiceItemRead {
  id: string;
  invoice_id: string;
  item_type: InvoiceItemType;
  description: string;
  quantity: number;
  unit_price: number;
  discount_amount: number;
  tax_rate: number;
  tax_amount: number;
  total: number;
  procedure_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface InvoiceItemCreate {
  item_type: InvoiceItemType;
  description: string;
  quantity: number;
  unit_price: number;
  discount_amount?: number;
  tax_rate?: number;
  tax_amount?: number;
  procedure_id?: string | null;
}

export interface PaymentRead {
  id: string;
  clinic_id: string;
  invoice_id: string;
  receipt_number: string;
  payment_date?: string | null;
  amount: number;
  method: PaymentMethod;
  transaction_reference?: string | null;
  notes?: string | null;
  received_by: string;
  status: PaymentStatus;
  refund_amount: number;
  refund_reason?: string | null;
  refunded_at?: string | null;
  refunded_by?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PaymentCreate {
  payment_date?: string | null;
  amount: number;
  method: PaymentMethod;
  transaction_reference?: string | null;
  notes?: string | null;
}

export interface PaymentRefund {
  refund_amount: number;
  refund_reason: string;
}

export interface PaymentDetail extends PaymentRead {
  receiver_name?: string | null;
  invoice_number?: string | null;
  patient_name?: string | null;
  patient_number?: string | null;
  clinic_name?: string | null;
  clinic_phone?: string | null;
  clinic_email?: string | null;
  remaining_balance: number;
}

export interface InvoiceDetail {
  id: string;
  clinic_id: string;
  patient_id: string;
  appointment_id?: string | null;
  treatment_id?: string | null;
  dentist_id: string;
  invoice_number: string;
  date?: string | null;
  due_date?: string | null;
  status: InvoiceStatus;
  subtotal: number;
  discount_type: DiscountType;
  discount_value: number;
  discount_amount: number;
  tax_rate: number;
  tax_amount: number;
  grand_total: number;
  amount_paid: number;
  balance_due: number;
  notes?: string | null;
  terms?: string | null;
  cancellation_reason?: string | null;
  version: number;
  created_at: string;
  updated_at: string;
  items: InvoiceItemRead[];
  payments: PaymentRead[];
  patient_name?: string | null;
  patient_number?: string | null;
  patient_phone?: string | null;
  patient_email?: string | null;
  dentist_name?: string | null;
  treatment_number?: string | null;
  appointment_number?: string | null;
  clinic_name?: string | null;
  clinic_phone?: string | null;
  clinic_email?: string | null;
  clinic_address?: string | null;
}

export interface InvoiceCreate {
  patient_id: string;
  appointment_id?: string | null;
  treatment_id?: string | null;
  dentist_id: string;
  date?: string | null;
  due_date?: string | null;
  discount_type: DiscountType;
  discount_value: number;
  tax_rate: number;
  notes?: string | null;
  terms?: string | null;
  items: InvoiceItemCreate[];
}

export interface InvoiceGenerateFromTreatment {
  consultation_fee: number;
  discount_type: DiscountType;
  discount_value: number;
  tax_rate: number;
  notes?: string | null;
  terms?: string | null;
  due_date?: string | null;
}

export interface InvoiceUpdate {
  due_date?: string | null;
  discount_type?: DiscountType;
  discount_value?: number;
  tax_rate?: number;
  notes?: string | null;
  terms?: string | null;
  items?: InvoiceItemCreate[];
}

export interface InvoiceCancel {
  reason: string;
}

export interface BillingDashboardStats {
  total_revenue: number;
  today_revenue: number;
  monthly_revenue: number;
  pending_payments: number;
  outstanding_invoices_count: number;
  paid_invoices_count: number;
  total_invoices_count: number;
  cash_collections: number;
  digital_collections: number;
}

export interface RevenueReportItem {
  period: string;
  total_invoiced: number;
  total_collected: number;
  balance_outstanding: number;
  invoices_count: number;
}

export interface RevenueReport {
  items: RevenueReportItem[];
  total_invoiced: number;
  total_collected: number;
  total_outstanding: number;
  collections_by_method: Record<string, number>;
  dentist_revenue: Record<string, number>;
}

export interface PatientBillingSummary {
  patient_id: string;
  patient_name: string;
  patient_number: string;
  total_invoiced: number;
  total_paid: number;
  balance_due: number;
  invoices_count: number;
  payments_count: number;
  invoices: InvoiceDetail[];
  payments: PaymentDetail[];
}
