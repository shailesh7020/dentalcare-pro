import { describe, expect, it } from "vitest";
import { z } from "zod";
import type {
  DiscountType,
  InvoiceItemCreate,
  InvoiceStatus,
  PaymentMethod,
  PaymentStatus,
} from "./types";

// ==========================================
// Financial Calculations
// ==========================================
export function calculateLineItemTotal(
  quantity: number,
  unitPrice: number,
  discount: number = 0,
  taxRate: number = 0
): { subtotal: number; taxable: number; taxAmount: number; total: number } {
  const subtotal = Math.max(0, quantity * unitPrice);
  const taxable = Math.max(0, subtotal - discount);
  const taxAmount = (taxable * taxRate) / 100;
  const total = taxable + taxAmount;
  return {
    subtotal: Math.round(subtotal * 100) / 100,
    taxable: Math.round(taxable * 100) / 100,
    taxAmount: Math.round(taxAmount * 100) / 100,
    total: Math.round(total * 100) / 100,
  };
}

export function calculateInvoiceTotals(
  items: Array<{ quantity: number; unit_price: number }>,
  discountType: DiscountType = "FIXED",
  discountValue: number = 0,
  taxRate: number = 0
): {
  subtotal: number;
  discountAmount: number;
  taxableAmount: number;
  taxAmount: number;
  grandTotal: number;
} {
  const subtotal = items.reduce(
    (sum, it) => sum + (Number(it.quantity) || 0) * (Number(it.unit_price) || 0),
    0
  );

  const discountAmount =
    discountType === "PERCENTAGE"
      ? (subtotal * Math.min(100, Math.max(0, discountValue))) / 100
      : Math.min(subtotal, Math.max(0, discountValue));

  const taxableAmount = Math.max(0, subtotal - discountAmount);
  const taxAmount = (taxableAmount * Math.max(0, taxRate)) / 100;
  const grandTotal = taxableAmount + taxAmount;

  return {
    subtotal: Math.round(subtotal * 100) / 100,
    discountAmount: Math.round(discountAmount * 100) / 100,
    taxableAmount: Math.round(taxableAmount * 100) / 100,
    taxAmount: Math.round(taxAmount * 100) / 100,
    grandTotal: Math.round(grandTotal * 100) / 100,
  };
}

export function calculateBalanceDue(
  grandTotal: number,
  amountPaid: number
): number {
  return Math.max(0, Math.round((grandTotal - amountPaid) * 100) / 100);
}

// ==========================================
// Zod Schemas
// ==========================================
export const invoiceItemSchema = z.object({
  item_type: z.enum([
    "PROCEDURE",
    "CONSULTATION",
    "MEDICATION",
    "CONSUMABLE",
    "LABORATORY",
    "OTHER",
  ]),
  description: z.string().min(1, "Description is required").max(255),
  quantity: z.number().int().min(1).max(500),
  unit_price: z.number().min(0, "Unit price cannot be negative"),
  procedure_id: z.string().uuid().optional().nullable(),
});

export const invoiceCreateSchema = z.object({
  patient_id: z.string().uuid("Invalid patient UUID"),
  dentist_id: z.string().uuid("Invalid dentist UUID"),
  treatment_id: z.string().uuid().optional().nullable(),
  appointment_id: z.string().uuid().optional().nullable(),
  discount_type: z.enum(["FIXED", "PERCENTAGE"]).default("FIXED"),
  discount_value: z.number().min(0),
  tax_rate: z.number().min(0).max(100),
  items: z.array(invoiceItemSchema).min(1, "Invoice must contain at least one line item"),
});

export const paymentCreateSchema = z.object({
  amount: z.number().positive("Payment amount must be greater than zero"),
  method: z.enum([
    "CASH",
    "CARD",
    "UPI",
    "BANK_TRANSFER",
    "CHEQUE",
    "WALLET",
    "OTHER",
  ]),
  transaction_reference: z.string().max(100).optional().nullable(),
  notes: z.string().max(1000).optional().nullable(),
});

export const paymentRefundSchema = z.object({
  refund_amount: z.number().positive("Refund amount must be greater than zero"),
  refund_reason: z.string().min(3, "Reason required").max(1000),
});

// ==========================================
// State Machine Transitions
// ==========================================
export const INVOICE_TRANSITIONS: Record<InvoiceStatus, InvoiceStatus[]> = {
  DRAFT: ["UNPAID", "CANCELLED"],
  UNPAID: ["PARTIALLY_PAID", "PAID", "CANCELLED"],
  PARTIALLY_PAID: ["PAID"],
  PAID: [], // Strictly immutable once fully paid
  OVERDUE: ["PARTIALLY_PAID", "PAID", "CANCELLED"],
  CANCELLED: [],
};

export function canTransitionInvoice(
  from: InvoiceStatus,
  to: InvoiceStatus
): boolean {
  return INVOICE_TRANSITIONS[from]?.includes(to) ?? false;
}

// ==========================================
// Tests
// ==========================================
describe("Billing Financial Arithmetic", () => {
  it("calculates single line item total correctly", () => {
    const item = calculateLineItemTotal(2, 1500, 200, 18);
    // subtotal = 3000, discount = 200 -> taxable = 2800, tax 18% = 504 -> total = 3304
    expect(item.subtotal).toBe(3000.0);
    expect(item.taxable).toBe(2800.0);
    expect(item.taxAmount).toBe(504.0);
    expect(item.total).toBe(3304.0);
  });

  it("calculates invoice with fixed discount and GST correctly", () => {
    const items = [
      { quantity: 1, unit_price: 500.0 }, // consultation
      { quantity: 1, unit_price: 3500.0 }, // root canal
    ];
    // subtotal = 4000, fixed discount = 500 -> taxable = 3500, 18% tax = 630 -> grand total = 4130
    const res = calculateInvoiceTotals(items, "FIXED", 500.0, 18.0);
    expect(res.subtotal).toBe(4000.0);
    expect(res.discountAmount).toBe(500.0);
    expect(res.taxableAmount).toBe(3500.0);
    expect(res.taxAmount).toBe(630.0);
    expect(res.grandTotal).toBe(4130.0);
  });

  it("calculates invoice with percentage discount correctly", () => {
    const items = [{ quantity: 2, unit_price: 2500.0 }];
    // subtotal = 5000, 10% discount = 500 -> taxable = 4500, 12% tax = 540 -> grand total = 5040
    const res = calculateInvoiceTotals(items, "PERCENTAGE", 10.0, 12.0);
    expect(res.subtotal).toBe(5000.0);
    expect(res.discountAmount).toBe(500.0);
    expect(res.taxableAmount).toBe(4500.0);
    expect(res.taxAmount).toBe(540.0);
    expect(res.grandTotal).toBe(5040.0);
  });

  it("computes remaining balance due correctly and clamps to zero", () => {
    expect(calculateBalanceDue(5000, 2000)).toBe(3000.0);
    expect(calculateBalanceDue(5000, 5000)).toBe(0.0);
    expect(calculateBalanceDue(5000, 6000)).toBe(0.0); // No negative balances
  });
});

describe("Invoice & Payment Validation Schemas", () => {
  it("validates a complete and valid invoice payload", () => {
    const valid = {
      patient_id: "11111111-1111-4111-8111-111111111111",
      dentist_id: "22222222-2222-4222-8222-222222222222",
      discount_type: "FIXED",
      discount_value: 100,
      tax_rate: 18,
      items: [
        {
          item_type: "PROCEDURE",
          description: "Composite Restoration",
          quantity: 1,
          unit_price: 1500,
        },
      ],
    };
    const result = invoiceCreateSchema.safeParse(valid);
    expect(result.success).toBe(true);
  });

  it("rejects an invoice with no line items", () => {
    const invalid = {
      patient_id: "11111111-1111-4111-8111-111111111111",
      dentist_id: "22222222-2222-4222-8222-222222222222",
      items: [],
    };
    const result = invoiceCreateSchema.safeParse(invalid);
    expect(result.success).toBe(false);
  });

  it("rejects an item with negative unit price", () => {
    const item = {
      item_type: "PROCEDURE",
      description: "Invalid Item",
      quantity: 1,
      unit_price: -50,
    };
    const result = invoiceItemSchema.safeParse(item);
    expect(result.success).toBe(false);
  });

  it("validates valid payment creation", () => {
    const payment = {
      amount: 1500,
      method: "UPI",
      transaction_reference: "UPI/123456789",
      notes: "Google Pay payment",
    };
    const result = paymentCreateSchema.safeParse(payment);
    expect(result.success).toBe(true);
  });

  it("rejects zero or negative payment amount", () => {
    const zeroPay = { amount: 0, method: "CASH" };
    expect(paymentCreateSchema.safeParse(zeroPay).success).toBe(false);

    const negPay = { amount: -500, method: "CASH" };
    expect(paymentCreateSchema.safeParse(negPay).success).toBe(false);
  });

  it("validates payment refund payload", () => {
    const refund = {
      refund_amount: 500,
      refund_reason: "Treatment rescheduled by patient",
    };
    expect(paymentRefundSchema.safeParse(refund).success).toBe(true);
  });
});

describe("Invoice State Transitions", () => {
  it("allows transition from UNPAID to PARTIALLY_PAID and PAID", () => {
    expect(canTransitionInvoice("UNPAID", "PARTIALLY_PAID")).toBe(true);
    expect(canTransitionInvoice("UNPAID", "PAID")).toBe(true);
    expect(canTransitionInvoice("UNPAID", "CANCELLED")).toBe(true);
  });

  it("allows transition from PARTIALLY_PAID to PAID", () => {
    expect(canTransitionInvoice("PARTIALLY_PAID", "PAID")).toBe(true);
  });

  it("enforces immutability of PAID invoices", () => {
    expect(canTransitionInvoice("PAID", "UNPAID")).toBe(false);
    expect(canTransitionInvoice("PAID", "CANCELLED")).toBe(false);
    expect(canTransitionInvoice("PAID", "DRAFT")).toBe(false);
  });

  it("prevents transition out of CANCELLED status", () => {
    expect(canTransitionInvoice("CANCELLED", "UNPAID")).toBe(false);
    expect(canTransitionInvoice("CANCELLED", "PAID")).toBe(false);
  });
});
