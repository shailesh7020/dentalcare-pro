"use client";

import { use, useState } from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  AlertCircle,
  ArrowLeft,
  Calendar,
  CheckCircle2,
  Clock,
  Download,
  FileCheck,
  FileText,
  IndianRupee,
  Package,
  PackageCheck,
  Send,
  Truck,
  X,
  XCircle,
} from "lucide-react";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import type {
  PurchaseOrder,
  PurchaseOrderReceive,
  PurchaseOrderReceiveItem,
} from "../../types";

export default function PurchaseOrderDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const resolvedParams = use(params);
  const poId = resolvedParams.id;
  const queryClient = useQueryClient();

  // Goods Receipt Modal
  const [isReceiveModalOpen, setIsReceiveModalOpen] = useState(false);
  const [receiveRows, setReceiveRows] = useState<{
    po_item_id: string;
    item_name: string;
    ordered: number;
    received_so_far: number;
    qty_now: number;
    batch_number: string;
    expiry_date: string;
  }[]>([]);
  const [receiveError, setReceiveError] = useState<string | null>(null);
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);

  const poQuery = useQuery({
    queryKey: ["inventory-purchase-order-detail", poId],
    queryFn: async () => {
      const res = await api.get<PurchaseOrder>(`/inventory/purchase-orders/${poId}`);
      return res.data;
    },
  });

  const sendMutation = useMutation({
    mutationFn: async () => {
      const res = await api.patch(`/inventory/purchase-orders/${poId}`, { status: "SENT" });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inventory-purchase-order-detail", poId] });
    },
  });

  const cancelMutation = useMutation({
    mutationFn: async () => {
      const res = await api.post(`/inventory/purchase-orders/${poId}/cancel`);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inventory-purchase-order-detail", poId] });
    },
  });

  const receiveMutation = useMutation({
    mutationFn: async (payload: PurchaseOrderReceive) => {
      const res = await api.post(`/inventory/purchase-orders/${poId}/receive`, payload);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inventory-purchase-order-detail", poId] });
      setIsReceiveModalOpen(false);
      setReceiveError(null);
    },
    onError: (err: any) => {
      setReceiveError(err.response?.data?.detail || "Failed to receive goods.");
    },
  });

  const handleDownloadPdf = async () => {
    if (!poQuery.data) return;
    try {
      setIsDownloadingPdf(true);
      const res = await api.get(`/inventory/purchase-orders/${poId}/pdf`, {
        responseType: "blob",
      });
      const blob = new Blob([res.data], { type: "application/pdf" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${poQuery.data.po_number}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      alert("Failed to download PDF.");
    } finally {
      setIsDownloadingPdf(false);
    }
  };

  const openReceiveModal = () => {
    if (!poQuery.data) return;
    const defaultBatch = `B-${new Date().getFullYear()}-${Math.floor(100 + Math.random() * 900)}`;
    const rows = poQuery.data.items.map((item) => {
      const remaining = Math.max(0, item.quantity_ordered - item.quantity_received);
      return {
        po_item_id: item.id,
        item_name: item.item_name || "Item",
        ordered: item.quantity_ordered,
        received_so_far: item.quantity_received,
        qty_now: remaining,
        batch_number: defaultBatch,
        expiry_date: "",
      };
    });
    setReceiveRows(rows);
    setReceiveError(null);
    setIsReceiveModalOpen(true);
  };

  const handleReceiveSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const activeToReceive = receiveRows.filter((r) => r.qty_now > 0);
    if (activeToReceive.length === 0) {
      setReceiveError("Please specify at least 1 item with quantity to receive.");
      return;
    }
    for (const r of activeToReceive) {
      if (!r.batch_number.trim()) {
        setReceiveError(`Batch number is required for ${r.item_name}.`);
        return;
      }
    }

    const payload: PurchaseOrderReceive = {
      items: activeToReceive.map((r) => ({
        po_item_id: r.po_item_id,
        quantity_to_receive: r.qty_now,
        batch_number: r.batch_number.trim(),
        expiry_date: r.expiry_date || undefined,
      })),
    };
    receiveMutation.mutate(payload);
  };

  const po = poQuery.data;

  if (poQuery.isLoading) {
    return (
      <div className="space-y-4 max-w-5xl mx-auto py-8">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (!po) {
    return (
      <div className="text-center py-16">
        <Truck className="mx-auto h-12 w-12 text-slate-400 mb-3" />
        <h2 className="text-lg font-semibold">Purchase Order Not Found</h2>
        <Link href="/inventory/purchase-orders" className="mt-4 inline-block text-sm text-teal-600 font-medium">
          Back to Orders
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-16">
      {/* Back Link */}
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link href="/inventory/purchase-orders" className="hover:text-slate-900 dark:hover:text-slate-100 flex items-center gap-1">
          <ArrowLeft className="h-4 w-4" /> Back to Purchase Orders
        </Link>
      </div>

      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight">{po.po_number}</h1>
            {po.status === "DRAFT" && <Badge className="bg-slate-100 text-slate-800">Draft</Badge>}
            {po.status === "SENT" && <Badge className="bg-blue-100 text-blue-800">Sent to Vendor</Badge>}
            {po.status === "PARTIALLY_RECEIVED" && <Badge className="bg-amber-100 text-amber-800">Partially Received</Badge>}
            {po.status === "RECEIVED" && <Badge className="bg-emerald-100 text-emerald-800">Received & Stocked</Badge>}
            {po.status === "CANCELLED" && <Badge className="bg-rose-100 text-rose-800">Cancelled</Badge>}
          </div>
          <p className="text-sm text-muted-foreground mt-0.5">
            Vendor: <b>{po.supplier?.name}</b> · Created by {po.creator_name || "Admin"} on {new Date(po.order_date).toLocaleDateString("en-IN")}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={handleDownloadPdf}
            disabled={isDownloadingPdf}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200 transition"
          >
            <Download className="h-4 w-4" />
            {isDownloadingPdf ? "Downloading..." : "Download PDF"}
          </button>

          {po.status === "DRAFT" && (
            <>
              <button
                onClick={() => sendMutation.mutate()}
                disabled={sendMutation.isPending}
                className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-3.5 py-2 text-sm font-medium text-white shadow hover:bg-blue-700 transition"
              >
                <Send className="h-4 w-4" />
                {sendMutation.isPending ? "Sending..." : "Mark as Sent"}
              </button>
              <button
                onClick={() => cancelMutation.mutate()}
                disabled={cancelMutation.isPending}
                className="rounded-lg border border-rose-300 px-3.5 py-2 text-sm font-medium text-rose-600 hover:bg-rose-50"
              >
                Cancel PO
              </button>
            </>
          )}

          {(po.status === "SENT" || po.status === "PARTIALLY_RECEIVED") && (
            <button
              onClick={openReceiveModal}
              className="inline-flex items-center gap-1.5 rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white shadow hover:bg-teal-700 transition"
            >
              <PackageCheck className="h-4 w-4" />
              Receive Physical Goods
            </button>
          )}
        </div>
      </div>

      {/* Meta Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <span className="text-xs font-medium text-muted-foreground uppercase">Grand Total</span>
          <div className="mt-1 text-2xl font-bold text-teal-600 dark:text-teal-400">
            ₹{po.grand_total.toFixed(2)}
          </div>
          <p className="text-xs text-muted-foreground mt-1">Subtotal: ₹{po.subtotal.toFixed(2)}</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <span className="text-xs font-medium text-muted-foreground uppercase">Vendor Contact</span>
          <div className="mt-1 text-base font-semibold truncate">
            {po.supplier?.contact_person || "Vendor Support"}
          </div>
          <p className="text-xs text-muted-foreground mt-1">{po.supplier?.phone || po.supplier?.email || "No direct phone"}</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <span className="text-xs font-medium text-muted-foreground uppercase">Expected Delivery</span>
          <div className="mt-1 text-base font-semibold">
            {po.expected_delivery_date
              ? new Date(po.expected_delivery_date).toLocaleDateString("en-IN")
              : "Standard Dispatch"}
          </div>
          <p className="text-xs text-muted-foreground mt-1">Ordered: {new Date(po.order_date).toLocaleDateString("en-IN")}</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <span className="text-xs font-medium text-muted-foreground uppercase">Taxes & Discounts</span>
          <div className="mt-1 text-base font-semibold">
            GST: ₹{po.tax_amount.toFixed(2)}
          </div>
          <p className="text-xs text-muted-foreground mt-1">Discount: ₹{po.discount_amount.toFixed(2)}</p>
        </div>
      </div>

      {/* Ordered Items Table */}
      <div className="rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="border-b px-5 py-3">
          <h2 className="font-semibold text-base">Procurement Items & Receipt Progress</h2>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b bg-slate-50/75 text-xs uppercase font-semibold text-slate-500 dark:bg-slate-800/50">
              <tr>
                <th className="px-4 py-3">Item Description</th>
                <th className="px-4 py-3">Ordered Qty</th>
                <th className="px-4 py-3">Received Qty</th>
                <th className="px-4 py-3">Unit Price (₹)</th>
                <th className="px-4 py-3">GST %</th>
                <th className="px-4 py-3">Disc %</th>
                <th className="px-4 py-3 text-right">Line Total (₹)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
              {po.items.map((item) => {
                const isFullyReceived = item.quantity_received >= item.quantity_ordered;
                return (
                  <tr key={item.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                    <td className="px-4 py-3">
                      <p className="font-medium">{item.item_name || "Catalog Material"}</p>
                      <span className="font-mono text-xs text-muted-foreground">{item.item_sku}</span>
                    </td>
                    <td className="px-4 py-3 font-semibold">{item.quantity_ordered} {item.item_unit || ""}</td>
                    <td className="px-4 py-3">
                      <span className={isFullyReceived ? "font-bold text-emerald-600" : "font-medium text-amber-600"}>
                        {item.quantity_received} / {item.quantity_ordered}
                      </span>
                    </td>
                    <td className="px-4 py-3">₹{item.unit_price.toFixed(2)}</td>
                    <td className="px-4 py-3">{item.tax_rate}%</td>
                    <td className="px-4 py-3">{item.discount_percent}%</td>
                    <td className="px-4 py-3 text-right font-semibold">₹{item.line_total.toFixed(2)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Goods Receipt Modal */}
      {isReceiveModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-2xl rounded-xl bg-white p-6 shadow-xl dark:bg-slate-900 border border-slate-200 dark:border-slate-800 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b pb-3">
              <div className="flex items-center gap-2">
                <PackageCheck className="h-5 w-5 text-teal-600" />
                <h3 className="font-semibold text-lg">Receive Goods & Create Stock Batches</h3>
              </div>
              <button onClick={() => setIsReceiveModalOpen(false)}>
                <X className="h-5 w-5" />
              </button>
            </div>

            <p className="text-xs text-muted-foreground mt-2 mb-4">
              Enter received quantities, batch numbers, and expiry dates to immediately credit physical inventory.
            </p>

            {receiveError && (
              <div className="mb-4 rounded-lg bg-rose-50 p-3 text-xs text-rose-700 dark:bg-rose-950/40 dark:text-rose-300">
                {receiveError}
              </div>
            )}

            <form onSubmit={handleReceiveSubmit} className="space-y-4">
              <div className="space-y-3">
                {receiveRows.map((row, idx) => (
                  <div key={row.po_item_id} className="rounded-lg border p-3 bg-slate-50/50 dark:bg-slate-800/40 space-y-2">
                    <div className="flex justify-between items-center text-sm font-medium">
                      <span>{row.item_name}</span>
                      <span className="text-xs text-muted-foreground">
                        Ordered: {row.ordered} · Already Received: {row.received_so_far}
                      </span>
                    </div>

                    <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
                      <div>
                        <label className="block text-xs text-muted-foreground mb-0.5">Receiving Qty</label>
                        <input
                          type="number"
                          min="0"
                          max={row.ordered - row.received_so_far}
                          value={row.qty_now}
                          onChange={(e) => {
                            const updated = [...receiveRows];
                            updated[idx].qty_now = parseInt(e.target.value) || 0;
                            setReceiveRows(updated);
                          }}
                          className="w-full rounded border bg-white py-1 px-2 text-sm dark:bg-slate-800"
                        />
                      </div>

                      <div>
                        <label className="block text-xs text-muted-foreground mb-0.5">Batch / Lot # *</label>
                        <input
                          type="text"
                          value={row.batch_number}
                          onChange={(e) => {
                            const updated = [...receiveRows];
                            updated[idx].batch_number = e.target.value;
                            setReceiveRows(updated);
                          }}
                          placeholder="e.g. LOT-2026-01"
                          className="w-full rounded border bg-white py-1 px-2 text-sm dark:bg-slate-800"
                          required={row.qty_now > 0}
                        />
                      </div>

                      <div>
                        <label className="block text-xs text-muted-foreground mb-0.5">Expiry Date</label>
                        <input
                          type="date"
                          value={row.expiry_date}
                          onChange={(e) => {
                            const updated = [...receiveRows];
                            updated[idx].expiry_date = e.target.value;
                            setReceiveRows(updated);
                          }}
                          className="w-full rounded border bg-white py-1 px-2 text-sm dark:bg-slate-800"
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t">
                <button
                  type="button"
                  onClick={() => setIsReceiveModalOpen(false)}
                  className="rounded-lg border px-4 py-2 text-sm font-medium hover:bg-slate-50 dark:hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={receiveMutation.isPending}
                  className="rounded-lg bg-teal-600 px-5 py-2 text-sm font-medium text-white hover:bg-teal-700 disabled:opacity-50"
                >
                  {receiveMutation.isPending ? "Crediting Stock..." : "Confirm Goods Receipt"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
