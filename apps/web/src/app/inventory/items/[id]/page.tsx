"use client";

import { use, useState } from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  ArrowLeft,
  Calendar,
  Clock,
  DollarSign,
  History,
  IndianRupee,
  Layers,
  MapPin,
  Package,
  Plus,
  RefreshCw,
  SlidersHorizontal,
  Truck,
  Users,
  X,
} from "lucide-react";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import type {
  InventoryItemDetail,
  StockAdjustmentCreate,
  StockTransactionType,
} from "../../types";

export default function InventoryItemDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const itemId = resolvedParams.id;
  const queryClient = useQueryClient();

  // Stock Adjustment Modal
  const [isAdjustOpen, setIsAdjustOpen] = useState(false);
  const [adjustType, setAdjustType] = useState<StockTransactionType>("ADJUSTMENT");
  const [adjustQty, setAdjustQty] = useState<number>(0);
  const [adjustReason, setAdjustReason] = useState<string>("");
  const [adjustError, setAdjustError] = useState<string | null>(null);

  const itemQuery = useQuery({
    queryKey: ["inventory-item-detail", itemId],
    queryFn: async () => {
      const res = await api.get<InventoryItemDetail>(`/inventory/items/${itemId}`);
      return res.data;
    },
  });

  const adjustMutation = useMutation({
    mutationFn: async (payload: StockAdjustmentCreate) => {
      const res = await api.post(`/inventory/items/${itemId}/adjust`, payload);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inventory-item-detail", itemId] });
      setIsAdjustOpen(false);
      setAdjustQty(0);
      setAdjustReason("");
      setAdjustError(null);
    },
    onError: (err: any) => {
      setAdjustError(err.response?.data?.detail || "Failed to adjust stock.");
    },
  });

  const handleAdjustSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!itemQuery.data) return;
    if (adjustQty === 0) {
      setAdjustError("Quantity delta cannot be 0.");
      return;
    }
    if (adjustQty < 0 && itemQuery.data.current_quantity + adjustQty < 0) {
      setAdjustError(`Cannot reduce below 0. Maximum deduction is ${itemQuery.data.current_quantity}.`);
      return;
    }
    if (!adjustReason.trim()) {
      setAdjustError("Reason is required.");
      return;
    }
    setAdjustError(null);
    adjustMutation.mutate({
      adjustment_type: adjustType,
      quantity: adjustQty,
      reason: adjustReason.trim(),
    });
  };

  const item = itemQuery.data;

  if (itemQuery.isLoading) {
    return (
      <div className="space-y-4 max-w-5xl mx-auto py-8">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!item) {
    return (
      <div className="text-center py-16">
        <Package className="mx-auto h-12 w-12 text-slate-400 mb-3" />
        <h2 className="text-lg font-semibold">Item Not Found</h2>
        <p className="text-sm text-muted-foreground mt-1">This item may have been removed or archived.</p>
        <Link href="/inventory" className="mt-4 inline-block text-sm text-teal-600 font-medium">
          Back to Inventory Directory
        </Link>
      </div>
    );
  }

  const totalValuation = item.current_quantity * item.purchase_price;

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-16">
      {/* Back Link */}
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link href="/inventory" className="hover:text-slate-900 dark:hover:text-slate-100 flex items-center gap-1">
          <ArrowLeft className="h-4 w-4" /> Back to Inventory Hub
        </Link>
      </div>

      {/* Header Banner */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 font-bold">
              {item.sku}
            </span>
            <span className="inline-block rounded bg-teal-50 px-2.5 py-0.5 text-xs font-semibold text-teal-700 dark:bg-teal-950/60 dark:text-teal-400">
              {item.category}
            </span>
            {item.status === "IN_STOCK" && (
              <Badge className="bg-emerald-100 text-emerald-800 hover:bg-emerald-100">In Stock</Badge>
            )}
            {item.status === "LOW_STOCK" && (
              <Badge className="bg-amber-100 text-amber-800 hover:bg-amber-100">Low Stock</Badge>
            )}
            {item.status === "OUT_OF_STOCK" && (
              <Badge className="bg-rose-100 text-rose-800 hover:bg-rose-100">Out of Stock</Badge>
            )}
          </div>
          <h1 className="text-2xl font-bold tracking-tight mt-1">{item.name}</h1>
          {item.generic_name && (
            <p className="text-sm text-muted-foreground">Chemical: {item.generic_name}</p>
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              setIsAdjustOpen(true);
              setAdjustQty(0);
              setAdjustReason("");
              setAdjustError(null);
            }}
            className="inline-flex items-center gap-1.5 rounded-lg bg-teal-600 px-3.5 py-2 text-sm font-medium text-white shadow hover:bg-teal-700 transition"
          >
            <SlidersHorizontal className="h-4 w-4" />
            Adjust Stock
          </button>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <span className="text-xs font-medium text-muted-foreground uppercase">Stock On Hand</span>
          <div className="mt-1 text-2xl font-bold">
            {item.current_quantity} <span className="text-sm font-normal text-muted-foreground">{item.unit}</span>
          </div>
          <p className="text-xs text-muted-foreground mt-1">Min: {item.minimum_stock} · Reorder: {item.reorder_level}</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <span className="text-xs font-medium text-muted-foreground uppercase">Valuation</span>
          <div className="mt-1 text-2xl font-bold text-emerald-700 dark:text-emerald-400">
            ₹{totalValuation.toFixed(2)}
          </div>
          <p className="text-xs text-muted-foreground mt-1">Cost: ₹{item.purchase_price.toFixed(2)} / {item.unit}</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <span className="text-xs font-medium text-muted-foreground uppercase">Primary Supplier</span>
          <div className="mt-1 text-base font-semibold truncate">
            {item.supplier?.name || "None assigned"}
          </div>
          <p className="text-xs text-muted-foreground mt-1">Tax: {item.tax_rate}% GST</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <span className="text-xs font-medium text-muted-foreground uppercase">Storage Location</span>
          <div className="mt-1 text-base font-semibold truncate">
            {item.storage_location || "Not assigned"}
          </div>
          <p className="text-xs text-muted-foreground mt-1">Active Batches: {item.batches?.length || 0}</p>
        </div>
      </div>

      {/* Active Batches Table */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="border-b px-5 py-3 flex items-center justify-between">
          <div>
            <h2 className="font-semibold text-base">Active FIFO Batches</h2>
            <p className="text-xs text-muted-foreground">Track batch expiry dates and multi-batch quantity balances.</p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b bg-slate-50/75 text-xs uppercase font-semibold text-slate-500 dark:bg-slate-800/50">
              <tr>
                <th className="px-4 py-3">Batch / Lot #</th>
                <th className="px-4 py-3">Current Qty</th>
                <th className="px-4 py-3">Initial Qty</th>
                <th className="px-4 py-3">Expiry Date</th>
                <th className="px-4 py-3">Received Date</th>
                <th className="px-4 py-3">Unit Cost</th>
                <th className="px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
              {!item.batches || item.batches.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-muted-foreground text-xs">
                    No active batches recorded for this item.
                  </td>
                </tr>
              ) : (
                item.batches.map((batch) => {
                  const isExpired = batch.expiry_date && new Date(batch.expiry_date) < new Date();
                  return (
                    <tr key={batch.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                      <td className="px-4 py-3 font-mono font-medium">{batch.batch_number}</td>
                      <td className="px-4 py-3 font-bold">
                        {batch.quantity} <span className="text-xs font-normal text-muted-foreground">{item.unit}</span>
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">{batch.initial_quantity}</td>
                      <td className="px-4 py-3">
                        {batch.expiry_date ? (
                          <span className={isExpired ? "text-rose-600 font-semibold" : ""}>
                            {new Date(batch.expiry_date).toLocaleDateString("en-IN")}
                          </span>
                        ) : (
                          "N/A"
                        )}
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">
                        {batch.received_date ? new Date(batch.received_date).toLocaleDateString("en-IN") : "N/A"}
                      </td>
                      <td className="px-4 py-3">₹{batch.purchase_price.toFixed(2)}</td>
                      <td className="px-4 py-3">
                        {isExpired ? (
                          <span className="text-xs px-2 py-0.5 rounded bg-rose-100 text-rose-800 font-medium">Expired</span>
                        ) : (
                          <span className="text-xs px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-medium">Active</span>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recent Stock Movement Ledger */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="border-b px-5 py-3">
          <h2 className="font-semibold text-base">Stock Movement & Consumption Ledger</h2>
          <p className="text-xs text-muted-foreground">Complete immutable audit trail of clinical procedure consumption and stock movements.</p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b bg-slate-50/75 text-xs uppercase font-semibold text-slate-500 dark:bg-slate-800/50">
              <tr>
                <th className="px-4 py-3">Date / Time</th>
                <th className="px-4 py-3">Transaction Type</th>
                <th className="px-4 py-3">Quantity Delta</th>
                <th className="px-4 py-3">Balance</th>
                <th className="px-4 py-3">Reason / Reference</th>
                <th className="px-4 py-3">Recorded By</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
              {!item.recent_transactions || item.recent_transactions.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-muted-foreground text-xs">
                    No transactions recorded yet.
                  </td>
                </tr>
              ) : (
                item.recent_transactions.map((tx) => (
                  <tr key={tx.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                    <td className="px-4 py-3 text-xs text-muted-foreground">
                      {new Date(tx.created_at).toLocaleString("en-IN")}
                    </td>
                    <td className="px-4 py-3">
                      <span className="font-mono text-xs font-semibold">{tx.transaction_type}</span>
                    </td>
                    <td className="px-4 py-3 font-semibold">
                      <span className={tx.quantity > 0 ? "text-emerald-600" : "text-rose-600"}>
                        {tx.quantity > 0 ? `+${tx.quantity}` : tx.quantity}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">
                      {tx.previous_quantity} &rarr; <b>{tx.new_quantity}</b>
                    </td>
                    <td className="px-4 py-3 text-xs">
                      {tx.reason || (tx.related_treatment_id ? `Treatment: ${tx.related_treatment_id.slice(0, 8)}` : "None")}
                    </td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">
                      {tx.actor_name || "System"}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Adjust Modal */}
      {isAdjustOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="font-semibold text-lg">Adjust Stock Quantity</h3>
              <button onClick={() => setIsAdjustOpen(false)}>
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleAdjustSubmit} className="space-y-4 mt-4">
              <div>
                <p className="text-sm font-medium">{item.name}</p>
                <p className="text-xs text-muted-foreground">
                  Current Stock: <b>{item.current_quantity} {item.unit}</b>
                </p>
              </div>

              {adjustError && (
                <div className="rounded-lg bg-rose-50 p-3 text-xs text-rose-700 dark:bg-rose-950/40 dark:text-rose-300">
                  {adjustError}
                </div>
              )}

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Adjustment Type
                </label>
                <select
                  value={adjustType}
                  onChange={(e) => setAdjustType(e.target.value as StockTransactionType)}
                  className="w-full rounded-lg border border-slate-300 bg-white py-2 px-3 text-sm dark:border-slate-700 dark:bg-slate-800"
                >
                  <option value="ADJUSTMENT">Inventory Audit Adjustment</option>
                  <option value="EXPIRY_DISPOSAL">Expired Stock Disposal</option>
                  <option value="RETURN_TO_SUPPLIER">Return to Supplier</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Quantity Delta (Negative for deduction, positive for addition)
                </label>
                <input
                  type="number"
                  value={adjustQty}
                  onChange={(e) => setAdjustQty(parseInt(e.target.value) || 0)}
                  placeholder="e.g. -5 or 10"
                  className="w-full rounded-lg border border-slate-300 bg-white py-2 px-3 text-sm dark:border-slate-700 dark:bg-slate-800"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  New Quantity: <b>{item.current_quantity + adjustQty} {item.unit}</b>
                </p>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Reason <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  value={adjustReason}
                  onChange={(e) => setAdjustReason(e.target.value)}
                  placeholder="e.g. Quarterly audit reconciliation"
                  className="w-full rounded-lg border border-slate-300 bg-white py-2 px-3 text-sm dark:border-slate-700 dark:bg-slate-800"
                  required
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t">
                <button
                  type="button"
                  onClick={() => setIsAdjustOpen(false)}
                  className="rounded-lg border px-4 py-2 text-sm font-medium hover:bg-slate-50 dark:hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={adjustMutation.isPending}
                  className="rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-700 disabled:opacity-50"
                >
                  {adjustMutation.isPending ? "Applying..." : "Confirm Adjustment"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
