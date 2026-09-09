"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useQuery, useMutation } from "@tanstack/react-query";
import { ArrowLeft, Plus, Save, Trash2 } from "lucide-react";
import { api } from "@/lib/api";
import type {
  InventoryItem,
  PurchaseOrderCreate,
  PurchaseOrderItemCreate,
  Supplier,
} from "../../types";

interface LineItemDraft extends PurchaseOrderItemCreate {
  selectedItem?: InventoryItem | null;
  line_total: number;
}

export default function NewPurchaseOrderPage() {
  const router = useRouter();
  const [supplierId, setSupplierId] = useState("");
  const [orderDate, setOrderDate] = useState(new Date().toISOString().split("T")[0]);
  const [expectedDelivery, setExpectedDelivery] = useState("");
  const [terms, setTerms] = useState("Payment net 30 days upon physical goods receipt and inspection.");
  const [notes, setNotes] = useState("");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Line items
  const [lineItems, setLineItems] = useState<LineItemDraft[]>([
    { item_id: "", quantity_ordered: 1, unit_price: 0, tax_rate: 18, discount_percent: 0, line_total: 0 },
  ]);

  // Fetch Suppliers
  const suppliersQuery = useQuery({
    queryKey: ["inventory-suppliers-list"],
    queryFn: async () => {
      const res = await api.get<Supplier[]>("/inventory/suppliers");
      return res.data;
    },
  });

  // Fetch Items
  const itemsQuery = useQuery({
    queryKey: ["inventory-items-dropdown"],
    queryFn: async () => {
      const res = await api.get<{ items: InventoryItem[] }>("/inventory/items?limit=200");
      return res.data.items;
    },
  });

  const availableItems = itemsQuery.data || [];

  const handleItemChange = (index: number, itemId: string) => {
    const item = availableItems.find((i) => i.id === itemId);
    const updated = [...lineItems];
    updated[index].item_id = itemId;
    updated[index].selectedItem = item;
    if (item) {
      updated[index].unit_price = item.purchase_price;
      updated[index].tax_rate = item.tax_rate;
    }
    recalculateLine(updated, index);
    setLineItems(updated);
  };

  const handleFieldChange = (index: number, field: keyof LineItemDraft, val: number) => {
    const updated = [...lineItems];
    (updated[index] as any)[field] = val;
    recalculateLine(updated, index);
    setLineItems(updated);
  };

  const recalculateLine = (items: LineItemDraft[], index: number) => {
    const line = items[index];
    const qty = line.quantity_ordered || 0;
    const price = line.unit_price || 0;
    const base = qty * price;
    const discount = base * ((line.discount_percent || 0) / 100);
    const taxable = base - discount;
    const tax = taxable * ((line.tax_rate || 0) / 100);
    line.line_total = taxable + tax;
  };

  const addLine = () => {
    setLineItems([
      ...lineItems,
      { item_id: "", quantity_ordered: 1, unit_price: 0, tax_rate: 18, discount_percent: 0, line_total: 0 },
    ]);
  };

  const removeLine = (index: number) => {
    if (lineItems.length === 1) return;
    setLineItems(lineItems.filter((_, i) => i !== index));
  };

  // Calculations
  const subtotal = lineItems.reduce((acc, l) => acc + (l.quantity_ordered || 0) * (l.unit_price || 0), 0);
  const totalDiscount = lineItems.reduce((acc, l) => {
    const base = (l.quantity_ordered || 0) * (l.unit_price || 0);
    return acc + base * ((l.discount_percent || 0) / 100);
  }, 0);
  const totalTax = lineItems.reduce((acc, l) => {
    const base = (l.quantity_ordered || 0) * (l.unit_price || 0);
    const taxable = base - base * ((l.discount_percent || 0) / 100);
    return acc + taxable * ((l.tax_rate || 0) / 100);
  }, 0);
  const grandTotal = subtotal - totalDiscount + totalTax;

  const createMutation = useMutation({
    mutationFn: async (payload: PurchaseOrderCreate) => {
      const res = await api.post("/inventory/purchase-orders", payload);
      return res.data;
    },
    onSuccess: (data) => {
      router.push(`/inventory/purchase-orders/${data.id}`);
    },
    onError: (err: any) => {
      setErrorMsg(err.response?.data?.detail || "Failed to create purchase order.");
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!supplierId) {
      setErrorMsg("Please select a supplier.");
      return;
    }
    const validItems = lineItems.filter((l) => l.item_id && l.quantity_ordered > 0);
    if (validItems.length === 0) {
      setErrorMsg("Please add at least one valid item to the purchase order.");
      return;
    }

    setErrorMsg(null);
    const payload: PurchaseOrderCreate = {
      supplier_id: supplierId,
      order_date: orderDate,
      expected_delivery_date: expectedDelivery || undefined,
      terms: terms.trim() || undefined,
      notes: notes.trim() || undefined,
      items: validItems.map((l) => ({
        item_id: l.item_id,
        quantity_ordered: Number(l.quantity_ordered),
        unit_price: Number(l.unit_price),
        tax_rate: Number(l.tax_rate),
        discount_percent: Number(l.discount_percent),
      })),
    };

    createMutation.mutate(payload);
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-16">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link href="/inventory/purchase-orders" className="hover:text-slate-900 dark:hover:text-slate-100 flex items-center gap-1">
          <ArrowLeft className="h-4 w-4" /> Back to Purchase Orders
        </Link>
      </div>

      <div className="border-b pb-4">
        <h1 className="text-2xl font-bold tracking-tight">Create Purchase Order</h1>
        <p className="text-sm text-muted-foreground">
          Procure clinical consumables, medicines, or equipment with line item tax and discount calculations.
        </p>
      </div>

      {errorMsg && (
        <div className="rounded-lg bg-rose-50 p-4 text-sm text-rose-700 dark:bg-rose-950/50 dark:text-rose-300">
          {errorMsg}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Supplier & Order Meta */}
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900 space-y-4">
          <h2 className="text-base font-semibold border-b pb-2">Order Information</h2>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Supplier / Vendor <span className="text-rose-500">*</span>
              </label>
              <select
                value={supplierId}
                onChange={(e) => setSupplierId(e.target.value)}
                className="w-full rounded-lg border border-slate-300 bg-white py-2 px-3 text-sm focus:border-teal-500 focus:outline-none dark:border-slate-700 dark:bg-slate-800"
                required
              >
                <option value="">-- Choose Vendor --</option>
                {(suppliersQuery.data || []).map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name} {s.contact_person ? `(${s.contact_person})` : ""}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Order Date <span className="text-rose-500">*</span>
              </label>
              <input
                type="date"
                value={orderDate}
                onChange={(e) => setOrderDate(e.target.value)}
                className="w-full rounded-lg border border-slate-300 bg-white py-2 px-3 text-sm focus:border-teal-500 focus:outline-none dark:border-slate-700 dark:bg-slate-800"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Expected Delivery Date
              </label>
              <input
                type="date"
                value={expectedDelivery}
                onChange={(e) => setExpectedDelivery(e.target.value)}
                className="w-full rounded-lg border border-slate-300 bg-white py-2 px-3 text-sm focus:border-teal-500 focus:outline-none dark:border-slate-700 dark:bg-slate-800"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Payment & Commercial Terms
              </label>
              <input
                type="text"
                value={terms}
                onChange={(e) => setTerms(e.target.value)}
                className="w-full rounded-lg border border-slate-300 bg-white py-2 px-3 text-sm dark:border-slate-700 dark:bg-slate-800"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Delivery Notes / Special Instructions
              </label>
              <input
                type="text"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="e.g. Please deliver between 10am - 1pm"
                className="w-full rounded-lg border border-slate-300 bg-white py-2 px-3 text-sm dark:border-slate-700 dark:bg-slate-800"
              />
            </div>
          </div>
        </div>

        {/* Dynamic Line Items Editor */}
        <div className="rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900 p-6 space-y-4">
          <div className="flex items-center justify-between border-b pb-2">
            <h2 className="text-base font-semibold">Ordered Line Items</h2>
            <button
              type="button"
              onClick={addLine}
              className="inline-flex items-center gap-1 text-xs font-medium text-teal-600 hover:text-teal-700 dark:text-teal-400"
            >
              <Plus className="h-4 w-4" /> Add Item Line
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b bg-slate-50/75 text-xs uppercase font-semibold text-slate-500 dark:bg-slate-800/50">
                <tr>
                  <th className="px-3 py-2 w-2/5">Inventory Item</th>
                  <th className="px-3 py-2 w-24">Quantity</th>
                  <th className="px-3 py-2 w-28">Unit Price (₹)</th>
                  <th className="px-3 py-2 w-20">GST %</th>
                  <th className="px-3 py-2 w-20">Disc %</th>
                  <th className="px-3 py-2 w-28">Line Total (₹)</th>
                  <th className="px-3 py-2 text-right w-10"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                {lineItems.map((line, idx) => (
                  <tr key={idx}>
                    <td className="px-3 py-2">
                      <select
                        value={line.item_id}
                        onChange={(e) => handleItemChange(idx, e.target.value)}
                        className="w-full rounded-lg border border-slate-300 bg-white py-1.5 px-2 text-sm dark:border-slate-700 dark:bg-slate-800"
                        required
                      >
                        <option value="">-- Choose Stock Item --</option>
                        {availableItems.map((item) => (
                          <option key={item.id} value={item.id}>
                            [{item.sku}] {item.name} ({item.unit})
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="px-3 py-2">
                      <input
                        type="number"
                        min="1"
                        value={line.quantity_ordered}
                        onChange={(e) => handleFieldChange(idx, "quantity_ordered", parseInt(e.target.value) || 1)}
                        className="w-full rounded-lg border border-slate-300 bg-white py-1.5 px-2 text-sm dark:border-slate-700 dark:bg-slate-800"
                      />
                    </td>
                    <td className="px-3 py-2">
                      <input
                        type="number"
                        step="0.01"
                        min="0"
                        value={line.unit_price}
                        onChange={(e) => handleFieldChange(idx, "unit_price", parseFloat(e.target.value) || 0)}
                        className="w-full rounded-lg border border-slate-300 bg-white py-1.5 px-2 text-sm dark:border-slate-700 dark:bg-slate-800"
                      />
                    </td>
                    <td className="px-3 py-2">
                      <input
                        type="number"
                        min="0"
                        value={line.tax_rate}
                        onChange={(e) => handleFieldChange(idx, "tax_rate", parseFloat(e.target.value) || 0)}
                        className="w-full rounded-lg border border-slate-300 bg-white py-1.5 px-2 text-sm dark:border-slate-700 dark:bg-slate-800"
                      />
                    </td>
                    <td className="px-3 py-2">
                      <input
                        type="number"
                        min="0"
                        max="100"
                        value={line.discount_percent}
                        onChange={(e) => handleFieldChange(idx, "discount_percent", parseFloat(e.target.value) || 0)}
                        className="w-full rounded-lg border border-slate-300 bg-white py-1.5 px-2 text-sm dark:border-slate-700 dark:bg-slate-800"
                      />
                    </td>
                    <td className="px-3 py-2 font-semibold">
                      ₹{line.line_total.toFixed(2)}
                    </td>
                    <td className="px-3 py-2 text-right">
                      <button
                        type="button"
                        onClick={() => removeLine(idx)}
                        disabled={lineItems.length === 1}
                        className="text-slate-400 hover:text-rose-600 disabled:opacity-30"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Financial Calculation Breakdown */}
          <div className="flex justify-end pt-4 border-t">
            <div className="w-72 space-y-1.5 text-sm">
              <div className="flex justify-between text-muted-foreground">
                <span>Subtotal:</span>
                <span>₹{subtotal.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-muted-foreground">
                <span>Total Discount:</span>
                <span>- ₹{totalDiscount.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-muted-foreground">
                <span>GST Tax:</span>
                <span>+ ₹{totalTax.toFixed(2)}</span>
              </div>
              <div className="flex justify-between font-bold text-base border-t pt-1 text-slate-900 dark:text-slate-100">
                <span>Grand Total:</span>
                <span className="text-teal-600 dark:text-teal-400">₹{grandTotal.toFixed(2)}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Form Actions */}
        <div className="flex items-center justify-end gap-3">
          <Link
            href="/inventory/purchase-orders"
            className="rounded-lg border px-4 py-2 text-sm font-medium hover:bg-slate-50 dark:hover:bg-slate-800"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={createMutation.isPending}
            className="inline-flex items-center gap-1.5 rounded-lg bg-teal-600 px-5 py-2 text-sm font-medium text-white shadow hover:bg-teal-700 disabled:opacity-50 transition"
          >
            <Save className="h-4 w-4" />
            {createMutation.isPending ? "Generating PO..." : "Issue Purchase Order"}
          </button>
        </div>
      </form>
    </div>
  );
}
