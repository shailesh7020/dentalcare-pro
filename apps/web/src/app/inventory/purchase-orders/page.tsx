"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import {
  AlertCircle,
  ArrowLeft,
  Calendar,
  CheckCircle2,
  Clock,
  Download,
  Eye,
  FileText,
  Filter,
  IndianRupee,
  Package,
  Plus,
  RefreshCw,
  Search,
  ShoppingCart,
  Truck,
  XCircle,
} from "lucide-react";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import type { PurchaseOrder, PurchaseOrderStatus } from "../types";

export default function PurchaseOrdersDirectoryPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedStatus, setSelectedStatus] = useState<string>("ALL");
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const poQuery = useQuery({
    queryKey: ["inventory-purchase-orders-list", selectedStatus, searchTerm],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (selectedStatus !== "ALL") params.status = selectedStatus;
      const res = await api.get<PurchaseOrder[]>("/inventory/purchase-orders", { params });
      return res.data;
    },
  });

  const handleDownloadPdf = async (po: PurchaseOrder) => {
    try {
      setDownloadingId(po.id);
      const res = await api.get(`/inventory/purchase-orders/${po.id}/pdf`, {
        responseType: "blob",
      });
      const blob = new Blob([res.data], { type: "application/pdf" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${po.po_number}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert("Failed to download Purchase Order PDF.");
    } finally {
      setDownloadingId(null);
    }
  };

  const allPOs = poQuery.data || [];
  const filtered = allPOs.filter((po) => {
    if (!searchTerm.trim()) return true;
    const term = searchTerm.toLowerCase();
    return (
      po.po_number.toLowerCase().includes(term) ||
      (po.supplier?.name || "").toLowerCase().includes(term)
    );
  });

  const draftCount = allPOs.filter((p) => p.status === "DRAFT").length;
  const sentCount = allPOs.filter((p) => p.status === "SENT" || p.status === "PARTIALLY_RECEIVED").length;
  const receivedCount = allPOs.filter((p) => p.status === "RECEIVED").length;

  return (
    <div className="space-y-6 pb-16">
      {/* Back & Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link href="/inventory" className="hover:text-slate-900 dark:hover:text-slate-100 flex items-center gap-1">
          <ArrowLeft className="h-4 w-4" /> Back to Inventory Hub
        </Link>
      </div>

      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-lg bg-teal-50 text-teal-700 dark:bg-teal-950/50 dark:text-teal-400">
              <Truck className="h-6 w-6" />
            </span>
            <div>
              <h1 className="text-2xl font-bold tracking-tight">Purchase Orders & Procurement</h1>
              <p className="text-sm text-muted-foreground">
                Track clinical vendor orders, goods receipt, delivery timelines, and PDF orders.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Link
            href="/inventory/purchase-orders/new"
            className="inline-flex items-center gap-1.5 rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-teal-700 transition"
          >
            <Plus className="h-4 w-4" />
            Create Purchase Order
          </Link>
        </div>
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <span className="text-xs font-medium text-muted-foreground uppercase">Total Orders</span>
          <div className="mt-1 text-2xl font-bold">{allPOs.length}</div>
          <p className="text-xs text-muted-foreground mt-1">All clinical procurement</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <span className="text-xs font-medium text-muted-foreground uppercase">Drafts</span>
          <div className="mt-1 text-2xl font-bold text-slate-700 dark:text-slate-300">{draftCount}</div>
          <p className="text-xs text-muted-foreground mt-1">Pending approval or sending</p>
        </div>

        <div className="rounded-xl border border-blue-200 bg-blue-50/40 p-4 shadow-sm dark:border-blue-900/40 dark:bg-blue-950/20">
          <span className="text-xs font-medium text-blue-800 dark:text-blue-400 uppercase">In Transit / Sent</span>
          <div className="mt-1 text-2xl font-bold text-blue-700 dark:text-blue-400">{sentCount}</div>
          <p className="text-xs text-blue-700/80 dark:text-blue-400/80 mt-1">Awaiting goods receipt</p>
        </div>

        <div className="rounded-xl border border-emerald-200 bg-emerald-50/40 p-4 shadow-sm dark:border-emerald-900/40 dark:bg-emerald-950/20">
          <span className="text-xs font-medium text-emerald-800 dark:text-emerald-400 uppercase">Fulfilled / Received</span>
          <div className="mt-1 text-2xl font-bold text-emerald-700 dark:text-emerald-400">{receivedCount}</div>
          <p className="text-xs text-emerald-700/80 dark:text-emerald-400/80 mt-1">Stock credited to warehouse</p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search by PO number or supplier name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full rounded-lg border border-slate-300 bg-white py-2 pl-9 pr-3 text-sm focus:border-teal-500 focus:outline-none dark:border-slate-700 dark:bg-slate-900"
          />
        </div>

        <div className="flex items-center gap-2">
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="rounded-lg border border-slate-300 bg-white py-2 px-3 text-sm focus:border-teal-500 focus:outline-none dark:border-slate-700 dark:bg-slate-900"
          >
            <option value="ALL">All Statuses</option>
            <option value="DRAFT">Draft</option>
            <option value="SENT">Sent</option>
            <option value="PARTIALLY_RECEIVED">Partially Received</option>
            <option value="RECEIVED">Received</option>
            <option value="CANCELLED">Cancelled</option>
          </select>

          <button
            onClick={() => poQuery.refetch()}
            className="p-2 rounded-lg border border-slate-300 bg-white text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
            title="Refresh"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Orders Table */}
      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b bg-slate-50/75 text-xs uppercase font-semibold text-slate-500 dark:bg-slate-800/50">
              <tr>
                <th className="px-4 py-3">PO Number</th>
                <th className="px-4 py-3">Supplier</th>
                <th className="px-4 py-3">Order Date</th>
                <th className="px-4 py-3">Expected Delivery</th>
                <th className="px-4 py-3">Line Items</th>
                <th className="px-4 py-3">Grand Total</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
              {poQuery.isLoading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i}>
                    <td colSpan={8} className="px-4 py-3">
                      <Skeleton className="h-6 w-full" />
                    </td>
                  </tr>
                ))
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-4 py-12 text-center text-muted-foreground">
                    <Truck className="mx-auto h-8 w-8 text-slate-400 mb-2" />
                    <p className="text-base font-medium">No purchase orders found</p>
                    <p className="text-xs mt-1">Create a purchase order to order materials from your suppliers.</p>
                  </td>
                </tr>
              ) : (
                filtered.map((po) => (
                  <tr key={po.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition-colors">
                    <td className="px-4 py-3 font-mono font-semibold">
                      <Link
                        href={`/inventory/purchase-orders/${po.id}`}
                        className="text-teal-600 hover:text-teal-700 dark:text-teal-400"
                      >
                        {po.po_number}
                      </Link>
                    </td>
                    <td className="px-4 py-3 font-medium">
                      {po.supplier?.name || "Unknown Supplier"}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {new Date(po.order_date).toLocaleDateString("en-IN")}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {po.expected_delivery_date
                        ? new Date(po.expected_delivery_date).toLocaleDateString("en-IN")
                        : "Not specified"}
                    </td>
                    <td className="px-4 py-3">
                      {po.items?.length || 0} item(s)
                    </td>
                    <td className="px-4 py-3 font-bold text-slate-900 dark:text-slate-100">
                      ₹{po.grand_total.toFixed(2)}
                    </td>
                    <td className="px-4 py-3">
                      {po.status === "DRAFT" && (
                        <Badge className="bg-slate-100 text-slate-800 hover:bg-slate-100">Draft</Badge>
                      )}
                      {po.status === "SENT" && (
                        <Badge className="bg-blue-100 text-blue-800 hover:bg-blue-100">Sent</Badge>
                      )}
                      {po.status === "PARTIALLY_RECEIVED" && (
                        <Badge className="bg-amber-100 text-amber-800 hover:bg-amber-100">Partial</Badge>
                      )}
                      {po.status === "RECEIVED" && (
                        <Badge className="bg-emerald-100 text-emerald-800 hover:bg-emerald-100">Received</Badge>
                      )}
                      {po.status === "CANCELLED" && (
                        <Badge className="bg-rose-100 text-rose-800 hover:bg-rose-100">Cancelled</Badge>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => handleDownloadPdf(po)}
                          disabled={downloadingId === po.id}
                          className="rounded p-1.5 text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                          title="Download PDF"
                        >
                          <Download className="h-4 w-4" />
                        </button>
                        <Link
                          href={`/inventory/purchase-orders/${po.id}`}
                          className="rounded p-1.5 text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                          title="View Details"
                        >
                          <Eye className="h-4 w-4" />
                        </Link>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
