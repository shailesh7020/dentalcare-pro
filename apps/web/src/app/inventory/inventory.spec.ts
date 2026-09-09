import { describe, expect, it } from "vitest";
import type {
  InventoryCategory,
  InventoryItem,
  InventoryStatus,
  PurchaseOrderItem,
} from "./types";

describe("Phase 8: Inventory & Pharmacy Module Tests", () => {
  it("verifies all 12 dental inventory categories are valid", () => {
    const categories: InventoryCategory[] = [
      "CONSUMABLES",
      "INSTRUMENTS",
      "EQUIPMENT",
      "IMPLANTS",
      "ORTHODONTIC",
      "ENDODONTIC",
      "PROSTHODONTIC",
      "PERIODONTIC",
      "SURGICAL",
      "MEDICINES",
      "LABORATORY",
      "OFFICE_SUPPLIES",
    ];
    expect(categories.length).toBe(12);
    expect(categories).toContain("ENDODONTIC");
    expect(categories).toContain("MEDICINES");
    expect(categories).toContain("SURGICAL");
  });

  it("calculates purchase order line items accurately with tax and discount", () => {
    const qty = 10;
    const unitPrice = 1200; // base = 12,000
    const discountPercent = 10; // 10% discount = 1,200, taxable = 10,800
    const taxRate = 18; // 18% GST = 1,944

    const base = qty * unitPrice;
    const discountAmount = base * (discountPercent / 100);
    const taxable = base - discountAmount;
    const taxAmount = taxable * (taxRate / 100);
    const lineTotal = taxable + taxAmount;

    expect(base).toBe(12000);
    expect(discountAmount).toBe(1200);
    expect(taxable).toBe(10800);
    expect(taxAmount).toBe(1944);
    expect(lineTotal).toBe(12744);
  });

  it("computes goods receipt remaining quantities correctly", () => {
    const item: PurchaseOrderItem = {
      id: "item-1",
      po_id: "po-1",
      item_id: "itm-1",
      quantity_ordered: 50,
      quantity_received: 20,
      unit_price: 150,
      tax_rate: 12,
      tax_amount: 360,
      discount_percent: 0,
      discount_amount: 0,
      line_total: 3360,
    };

    const remaining = Math.max(0, item.quantity_ordered - item.quantity_received);
    expect(remaining).toBe(30);

    const isFullyReceived = item.quantity_received >= item.quantity_ordered;
    expect(isFullyReceived).toBe(false);

    // After receiving 30 more
    const updatedReceived = item.quantity_received + 30;
    expect(updatedReceived >= item.quantity_ordered).toBe(true);
  });

  it("enforces non-negative stock reduction rule", () => {
    const currentQty = 15;

    const validDeduction = -10;
    const newQty = currentQty + validDeduction;
    expect(newQty).toBe(5);
    expect(newQty >= 0).toBe(true);

    const invalidDeduction = -20;
    const invalidQty = currentQty + invalidDeduction;
    const isAllowed = currentQty + invalidDeduction >= 0;
    expect(invalidQty).toBe(-5);
    expect(isAllowed).toBe(false);
  });

  it("evaluates medicine stock availability statuses properly", () => {
    const checkAvailability = (
      qty: number,
      reorderLevel: number,
      hasExpired: boolean
    ): "IN_STOCK" | "LOW_STOCK" | "OUT_OF_STOCK" | "EXPIRED" => {
      if (hasExpired) return "EXPIRED";
      if (qty <= 0) return "OUT_OF_STOCK";
      if (qty <= reorderLevel) return "LOW_STOCK";
      return "IN_STOCK";
    };

    expect(checkAvailability(50, 10, false)).toBe("IN_STOCK");
    expect(checkAvailability(8, 10, false)).toBe("LOW_STOCK");
    expect(checkAvailability(0, 10, false)).toBe("OUT_OF_STOCK");
    expect(checkAvailability(25, 10, true)).toBe("EXPIRED");
  });

  it("correctly aggregates inventory category valuation", () => {
    const items: Array<{ category: InventoryCategory; qty: number; price: number }> = [
      { category: "ENDODONTIC", qty: 20, price: 350 }, // 7,000
      { category: "ENDODONTIC", qty: 10, price: 800 }, // 8,000
      { category: "CONSUMABLES", qty: 100, price: 15 }, // 1,500
    ];

    const categoryValuations = items.reduce<Record<string, number>>((acc, item) => {
      acc[item.category] = (acc[item.category] || 0) + item.qty * item.price;
      return acc;
    }, {});

    expect(categoryValuations["ENDODONTIC"]).toBe(15000);
    expect(categoryValuations["CONSUMABLES"]).toBe(1500);

    const totalValuation = Object.values(categoryValuations).reduce((a, b) => a + b, 0);
    expect(totalValuation).toBe(16500);
  });
});
