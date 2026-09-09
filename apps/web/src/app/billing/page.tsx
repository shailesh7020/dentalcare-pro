"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import {
  AlertCircle,
  ArrowUpRight,
  CheckCircle2,
  Clock,
  CreditCard,
  DollarSign,
  Download,
  Eye,
  FileSpreadsheet,
  FileText,
  Filter,
  IndianRupee,
  Plus,
  RefreshCw,
  Search,
  User,
  Wallet,
} from "lucide-react";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import type {
  BillingDashboardStats,
  InvoiceDetail,
  InvoiceStatus,
} from "./types";

export default function BillingDirectoryPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedStatus, setSelectedStatus] = useState<string>("ALL");
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  // 1. Fetch Dashboard Stats
  const statsQuery = useQuery({
    queryKey: ["billing-dashboard-stats"],
    queryFn: async () => {
      const res = await api.get<BillingDashboardStats>(
        "/billing/dashboard/stats"
      );
      return res.data;
    },
  });

  // 2. Fetch Invoices List
  const invoicesQuery = useQuery({
    queryKey: ["billing-invoices-list", selectedStatus, searchTerm],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (selectedStatus !== "ALL") {
        params.status = selectedStatus;
      }
      if (searchTerm.trim()) {
        params.search = searchTerm.trim();
      }
      const res = await api.get<InvoiceDetail[]>("/billing/invoices", {
        params,
      });
      return res.data;
    },
  });

  // Download PDF Handler
  const handleDownloadPdf = async (invoiceId: string, invoiceNumber: string) => {
    try {
      setDownloadingId(invoiceId);
      const res = await api.get(`/billing/invoices/${invoiceId}/pdf`, {
        responseType: "blob",
      });
      const blob = new Blob([res.data as BlobPart], { type: "application/pdf" });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `${invoiceNumber}.pdf`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Failed to download invoice PDF", err);
      alert("Failed to download Tax Invoice PDF. Please try again.");
    } finally {
      setDownloadingId(null);
    }
  };

  const stats = statsQuery.data;
  const invoices = invoicesQuery.data || [];

  const getStatusBadge = (status: InvoiceStatus) => {
    switch (status) {
      case "PAID":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
            Paid
          </span>
        );
      case "PARTIALLY_PAID":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
            <Clock className="w-3 h-3 text-amber-600" />
            Partially Paid
          </span>
        );
      case "UNPAID":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
            <AlertCircle className="w-3 h-3 text-rose-600" />
            Unpaid
          </span>
        );
      case "OVERDUE":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-100 text-red-800 border border-red-300">
            <AlertCircle className="w-3 h-3 text-red-600" />
            Overdue
          </span>
        );
      case "CANCELLED":
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200">
            Cancelled
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-700 border border-gray-200">
            Draft
          </span>
        );
    }
  };

  return (
    <div className="min-h-screen bg-slate-50/50 p-6 md:p-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="w-10 h-10 rounded-xl bg-blue-600 text-white flex items-center justify-center shadow-md shadow-blue-500/20">
              <IndianRupee className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-slate-900">
                Billing & Invoicing
              </h1>
              <p className="text-sm text-slate-500">
                Manage patient billing, payments, tax invoices, and clinic revenue
              </p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/billing/reports"
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-slate-700 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors shadow-sm"
          >
            <FileSpreadsheet className="w-4 h-4 text-emerald-600" />
            Revenue Reports
          </Link>
          <Link
            href="/billing/new"
            className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors shadow-sm shadow-blue-500/20"
          >
            <Plus className="w-4 h-4" />
            Create Invoice
          </Link>
        </div>
      </div>

      {/* KPI Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Total Invoiced */}
        <div className="bg-white rounded-xl p-5 border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
            <span>Total Invoiced</span>
            <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
              <FileText className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            {statsQuery.isLoading ? (
              <Skeleton className="h-7 w-28" />
            ) : (
              <span className="text-2xl font-bold text-slate-900">
                ₹{((stats?.total_revenue || 0) + (stats?.pending_payments || 0)).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
              </span>
            )}
            <p className="text-xs text-slate-400 mt-1">
              {stats?.total_invoices_count ?? 0} total invoices
            </p>
          </div>
        </div>

        {/* Collected Revenue */}
        <div className="bg-white rounded-xl p-5 border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
            <span>Collected Revenue</span>
            <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            {statsQuery.isLoading ? (
              <Skeleton className="h-7 w-28" />
            ) : (
              <span className="text-2xl font-bold text-emerald-600">
                ₹{(stats?.total_revenue ?? 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
              </span>
            )}
            <p className="text-xs text-slate-400 mt-1">
              ₹{(stats?.today_revenue ?? 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })} collected today
            </p>
          </div>
        </div>

        {/* Outstanding Balance */}
        <div className="bg-white rounded-xl p-5 border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
            <span>Outstanding Dues</span>
            <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            {statsQuery.isLoading ? (
              <Skeleton className="h-7 w-28" />
            ) : (
              <span className="text-2xl font-bold text-amber-600">
                ₹{(stats?.pending_payments ?? 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
              </span>
            )}
            <p className="text-xs text-slate-400 mt-1">
              {stats?.outstanding_invoices_count ?? 0} invoices pending
            </p>
          </div>
        </div>

        {/* Digital vs Cash Collections */}
        <div className="bg-white rounded-xl p-5 border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
            <span>UPI & Digital</span>
            <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
              <CreditCard className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            {statsQuery.isLoading ? (
              <Skeleton className="h-7 w-28" />
            ) : (
              <span className="text-2xl font-bold text-indigo-600">
                ₹{(stats?.digital_collections ?? 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
              </span>
            )}
            <p className="text-xs text-slate-400 mt-1">
              Cash: ₹{(stats?.cash_collections ?? 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
            </p>
          </div>
        </div>

        {/* Paid Rate */}
        <div className="bg-white rounded-xl p-5 border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between text-slate-500 text-xs font-medium">
            <span>Collection Rate</span>
            <div className="w-8 h-8 rounded-lg bg-teal-50 text-teal-600 flex items-center justify-center">
              <ArrowUpRight className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3">
            {statsQuery.isLoading ? (
              <Skeleton className="h-7 w-28" />
            ) : (
              <span className="text-2xl font-bold text-teal-600">
                {stats?.total_invoices_count
                  ? Math.round((stats.paid_invoices_count / stats.total_invoices_count) * 100)
                  : 0}
                %
              </span>
            )}
            <p className="text-xs text-slate-400 mt-1">
              {stats?.paid_invoices_count ?? 0} settled fully
            </p>
          </div>
        </div>
      </div>

      {/* Filter & Search Bar */}
      <div className="bg-white rounded-xl p-4 border border-slate-200/80 shadow-xs space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          {/* Search */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search invoice #, patient name, patient number..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all text-slate-900"
            />
          </div>

          {/* Status Tabs */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 md:pb-0">
            {[
              { label: "All", value: "ALL" },
              { label: "Unpaid", value: "UNPAID" },
              { label: "Partially Paid", value: "PARTIALLY_PAID" },
              { label: "Paid", value: "PAID" },
              { label: "Cancelled", value: "CANCELLED" },
            ].map((tab) => (
              <button
                key={tab.value}
                onClick={() => setSelectedStatus(tab.value)}
                className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-colors whitespace-nowrap ${
                  selectedStatus === tab.value
                    ? "bg-blue-600 text-white shadow-xs"
                    : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Invoices Table */}
      <div className="bg-white rounded-xl border border-slate-200/80 shadow-xs overflow-hidden">
        {invoicesQuery.isLoading ? (
          <div className="p-8 space-y-4">
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
          </div>
        ) : invoices.length === 0 ? (
          <div className="p-12 text-center space-y-3">
            <div className="w-12 h-12 rounded-full bg-slate-100 text-slate-400 mx-auto flex items-center justify-center">
              <FileText className="w-6 h-6" />
            </div>
            <h3 className="text-base font-semibold text-slate-900">
              No invoices found
            </h3>
            <p className="text-sm text-slate-500 max-w-sm mx-auto">
              {searchTerm || selectedStatus !== "ALL"
                ? "No invoices match your selected filters. Try adjusting your query."
                : "No invoices have been issued yet. Create your first invoice from a treatment or manually."}
            </p>
            <Link
              href="/billing/new"
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors shadow-sm"
            >
              <Plus className="w-4 h-4" />
              Create First Invoice
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="bg-slate-50/75 border-b border-slate-200 text-xs uppercase font-semibold text-slate-500 tracking-wider">
                <tr>
                  <th className="py-3.5 px-4">Invoice #</th>
                  <th className="py-3.5 px-4">Date</th>
                  <th className="py-3.5 px-4">Patient</th>
                  <th className="py-3.5 px-4">Clinician</th>
                  <th className="py-3.5 px-4 text-right">Grand Total</th>
                  <th className="py-3.5 px-4 text-right">Paid</th>
                  <th className="py-3.5 px-4 text-right">Balance Due</th>
                  <th className="py-3.5 px-4 text-center">Status</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {invoices.map((inv) => (
                  <tr
                    key={inv.id}
                    className="hover:bg-slate-50/60 transition-colors"
                  >
                    <td className="py-3.5 px-4 font-semibold text-slate-900">
                      <Link
                        href={`/billing/${inv.id}`}
                        className="text-blue-600 hover:text-blue-800 hover:underline flex items-center gap-1.5"
                      >
                        <FileText className="w-4 h-4 text-slate-400" />
                        {inv.invoice_number}
                      </Link>
                    </td>
                    <td className="py-3.5 px-4 text-slate-600 whitespace-nowrap">
                      {inv.date || inv.created_at.slice(0, 10)}
                    </td>
                    <td className="py-3.5 px-4">
                      <Link
                        href={`/patients/${inv.patient_id}`}
                        className="font-medium text-slate-900 hover:text-blue-600"
                      >
                        {inv.patient_name || "Patient"}
                      </Link>
                      {inv.patient_number && (
                        <div className="text-xs text-slate-400">
                          {inv.patient_number}
                        </div>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-slate-600">
                      {inv.dentist_name || "Doctor"}
                    </td>
                    <td className="py-3.5 px-4 text-right font-semibold text-slate-900 whitespace-nowrap">
                      ₹{inv.grand_total.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-3.5 px-4 text-right font-medium text-emerald-600 whitespace-nowrap">
                      ₹{inv.amount_paid.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-3.5 px-4 text-right font-semibold whitespace-nowrap">
                      {inv.balance_due > 0 ? (
                        <span className="text-rose-600">
                          ₹{inv.balance_due.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                        </span>
                      ) : (
                        <span className="text-slate-400">₹0.00</span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-center whitespace-nowrap">
                      {getStatusBadge(inv.status)}
                    </td>
                    <td className="py-3.5 px-4 text-right whitespace-nowrap">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => handleDownloadPdf(inv.id, inv.invoice_number)}
                          disabled={downloadingId === inv.id}
                          title="Download Tax Invoice PDF"
                          className="p-1.5 text-slate-500 hover:text-blue-600 hover:bg-slate-100 rounded-lg transition-colors disabled:opacity-50"
                        >
                          {downloadingId === inv.id ? (
                            <RefreshCw className="w-4 h-4 animate-spin" />
                          ) : (
                            <Download className="w-4 h-4" />
                          )}
                        </button>
                        <Link
                          href={`/billing/${inv.id}`}
                          title="View Invoice Detail"
                          className="p-1.5 text-slate-500 hover:text-blue-600 hover:bg-slate-100 rounded-lg transition-colors"
                        >
                          <Eye className="w-4 h-4" />
                        </Link>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
