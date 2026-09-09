"use client";

import { use, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertCircle,
  AlertTriangle,
  ArrowLeft,
  Banknote,
  Building2,
  Calendar,
  CheckCircle2,
  Clock,
  CreditCard,
  Download,
  FileCheck,
  FileText,
  IndianRupee,
  Layers,
  Phone,
  Plus,
  Printer,
  Receipt,
  RotateCcw,
  Stethoscope,
  Trash2,
  Undo2,
  User,
  Wallet,
  XCircle,
} from "lucide-react";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import type {
  InvoiceCancel,
  InvoiceDetail,
  InvoiceStatus,
  PaymentCreate,
  PaymentMethod,
  PaymentRead,
  PaymentRefund,
} from "../types";

export default function InvoiceDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const queryClient = useQueryClient();

  // Modals state
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [selectedPaymentForRefund, setSelectedPaymentForRefund] =
    useState<PaymentRead | null>(null);

  // Payment form state
  const [paymentAmount, setPaymentAmount] = useState<number>(0);
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>("UPI");
  const [paymentDate, setPaymentDate] = useState<string>(
    new Date().toISOString().slice(0, 10)
  );
  const [transactionRef, setTransactionRef] = useState<string>("");
  const [paymentNotes, setPaymentNotes] = useState<string>("");

  // Refund form state
  const [refundAmount, setRefundAmount] = useState<number>(0);
  const [refundReason, setRefundReason] = useState<string>("");

  // Cancel form state
  const [cancelReason, setCancelReason] = useState<string>("");

  const [downloadingPdf, setDownloadingPdf] = useState(false);
  const [downloadingReceiptId, setDownloadingReceiptId] = useState<string | null>(
    null
  );

  // Fetch Invoice Details
  const invoiceQuery = useQuery({
    queryKey: ["billing-invoice-detail", id],
    queryFn: async () => {
      const res = await api.get<InvoiceDetail>(`/billing/invoices/${id}`);
      return res.data;
    },
  });

  const invoice = invoiceQuery.data;

  // Record Payment Mutation
  const recordPaymentMutation = useMutation({
    mutationFn: async (payload: PaymentCreate) => {
      const res = await api.post(`/billing/invoices/${id}/payments`, payload);
      return res.data;
    },
    onSuccess: () => {
      setShowPaymentModal(false);
      void queryClient.invalidateQueries({
        queryKey: ["billing-invoice-detail", id],
      });
      void queryClient.invalidateQueries({
        queryKey: ["billing-dashboard-stats"],
      });
    },
    onError: (err: any) => {
      alert(err.response?.data?.detail || "Failed to record payment.");
    },
  });

  // Refund Payment Mutation
  const refundMutation = useMutation({
    mutationFn: async ({
      paymentId,
      payload,
    }: {
      paymentId: string;
      payload: PaymentRefund;
    }) => {
      const res = await api.post(
        `/billing/payments/${paymentId}/refund`,
        payload
      );
      return res.data;
    },
    onSuccess: () => {
      setSelectedPaymentForRefund(null);
      void queryClient.invalidateQueries({
        queryKey: ["billing-invoice-detail", id],
      });
      void queryClient.invalidateQueries({
        queryKey: ["billing-dashboard-stats"],
      });
    },
    onError: (err: any) => {
      alert(err.response?.data?.detail || "Failed to process refund.");
    },
  });

  // Cancel Invoice Mutation
  const cancelInvoiceMutation = useMutation({
    mutationFn: async (payload: InvoiceCancel) => {
      const res = await api.post(`/billing/invoices/${id}/cancel`, payload);
      return res.data;
    },
    onSuccess: () => {
      setShowCancelModal(false);
      void queryClient.invalidateQueries({
        queryKey: ["billing-invoice-detail", id],
      });
    },
    onError: (err: any) => {
      alert(err.response?.data?.detail || "Failed to cancel invoice.");
    },
  });

  // Download Invoice PDF
  const handleDownloadInvoicePdf = async () => {
    if (!invoice) return;
    try {
      setDownloadingPdf(true);
      const res = await api.get(`/billing/invoices/${id}/pdf`, {
        responseType: "blob",
      });
      const blob = new Blob([res.data as BlobPart], { type: "application/pdf" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.setAttribute("download", `${invoice.invoice_number}.pdf`);
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Failed to download PDF", err);
      alert("Failed to download PDF invoice. Please try again.");
    } finally {
      setDownloadingPdf(false);
    }
  };

  // Download Receipt PDF
  const handleDownloadReceiptPdf = async (
    paymentId: string,
    receiptNo: string
  ) => {
    try {
      setDownloadingReceiptId(paymentId);
      const res = await api.get(`/billing/payments/${paymentId}/receipt/pdf`, {
        responseType: "blob",
      });
      const blob = new Blob([res.data as BlobPart], { type: "application/pdf" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.setAttribute("download", `${receiptNo}.pdf`);
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Failed to download receipt PDF", err);
      alert("Failed to download Payment Receipt PDF.");
    } finally {
      setDownloadingReceiptId(null);
    }
  };

  if (invoiceQuery.isLoading) {
    return (
      <div className="p-8 max-w-5xl mx-auto space-y-6">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-64 w-full rounded-2xl" />
        <Skeleton className="h-96 w-full rounded-2xl" />
      </div>
    );
  }

  if (invoiceQuery.isError || !invoice) {
    return (
      <div className="p-12 max-w-md mx-auto text-center space-y-4">
        <AlertCircle className="w-12 h-12 text-rose-500 mx-auto" />
        <h2 className="text-xl font-bold text-slate-900">Invoice Not Found</h2>
        <p className="text-sm text-slate-500">
          The requested invoice record could not be found in this clinic.
        </p>
        <Link
          href="/billing"
          className="inline-flex items-center gap-2 px-4 py-2 text-sm font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Billing
        </Link>
      </div>
    );
  }

  const getStatusBadge = (status: InvoiceStatus) => {
    switch (status) {
      case "PAID":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            PAID IN FULL
          </span>
        );
      case "PARTIALLY_PAID":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-300">
            <Clock className="w-3.5 h-3.5 text-amber-600" />
            PARTIALLY PAID
          </span>
        );
      case "UNPAID":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-100 text-rose-800 border border-rose-300">
            <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
            UNPAID
          </span>
        );
      case "CANCELLED":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-slate-200 text-slate-700 border border-slate-300">
            <XCircle className="w-3.5 h-3.5 text-slate-600" />
            CANCELLED
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-gray-100 text-gray-700">
            DRAFT
          </span>
        );
    }
  };

  return (
    <div className="min-h-screen bg-slate-50/50 p-6 md:p-8 space-y-6">
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Navigation & Actions Top Bar */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <Link
            href="/billing"
            className="inline-flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Invoices
          </Link>

          <div className="flex flex-wrap items-center gap-2.5">
            {/* Download Official Tax Invoice PDF */}
            <button
              onClick={handleDownloadInvoicePdf}
              disabled={downloadingPdf}
              className="inline-flex items-center gap-2 px-3.5 py-2 text-xs font-semibold text-slate-700 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors shadow-xs"
            >
              <Download className="w-3.5 h-3.5 text-blue-600" />
              {downloadingPdf ? "Generating PDF..." : "Download Tax Invoice PDF"}
            </button>

            {/* Print Button */}
            <button
              onClick={() => window.print()}
              className="inline-flex items-center gap-2 px-3.5 py-2 text-xs font-semibold text-slate-700 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors shadow-xs"
            >
              <Printer className="w-3.5 h-3.5 text-slate-600" />
              Print
            </button>

            {/* Record Payment Button */}
            {invoice.status !== "PAID" &&
              invoice.status !== "CANCELLED" &&
              invoice.balance_due > 0 && (
                <button
                  onClick={() => {
                    setPaymentAmount(invoice.balance_due);
                    setShowPaymentModal(true);
                  }}
                  className="inline-flex items-center gap-2 px-4 py-2 text-xs font-bold text-white bg-emerald-600 rounded-lg hover:bg-emerald-700 transition-colors shadow-sm shadow-emerald-500/20"
                >
                  <IndianRupee className="w-3.5 h-3.5" />
                  Record Payment
                </button>
              )}

            {/* Cancel Invoice Button */}
            {invoice.status !== "CANCELLED" && invoice.amount_paid === 0 && (
              <button
                onClick={() => setShowCancelModal(true)}
                className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-rose-600 bg-rose-50 hover:bg-rose-100 rounded-lg transition-colors border border-rose-200"
              >
                <XCircle className="w-3.5 h-3.5" />
                Cancel Invoice
              </button>
            )}
          </div>
        </div>

        {/* Invoice Card / Printable View Container */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden p-6 md:p-10 space-y-8">
          {/* Header */}
          <div className="flex flex-col md:flex-row md:items-start justify-between gap-6 border-b border-slate-100 pb-8">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <div className="w-9 h-9 rounded-xl bg-blue-600 text-white flex items-center justify-center font-black text-sm">
                  D+
                </div>
                <div>
                  <h2 className="text-xl font-extrabold text-slate-900 tracking-tight">
                    {invoice.clinic_name || "DentalCare Pro Center"}
                  </h2>
                  <p className="text-xs text-slate-500">
                    {invoice.clinic_address || "Advanced Multispeciality Dental Operatory"}
                  </p>
                </div>
              </div>
              <div className="text-xs text-slate-500 pt-1 space-y-0.5">
                {invoice.clinic_phone && <div>📞 {invoice.clinic_phone}</div>}
                {invoice.clinic_email && <div>✉️ {invoice.clinic_email}</div>}
              </div>
            </div>

            <div className="text-left md:text-right space-y-2">
              <div className="flex items-center md:justify-end gap-2">
                <span className="text-xs font-semibold uppercase tracking-widest text-slate-400">
                  TAX INVOICE
                </span>
                {getStatusBadge(invoice.status)}
              </div>
              <h3 className="text-2xl font-black text-blue-600 tracking-tight">
                {invoice.invoice_number}
              </h3>
              <div className="text-xs text-slate-500 space-y-0.5">
                <div>
                  Date:{" "}
                  <span className="font-semibold text-slate-800">
                    {invoice.date || invoice.created_at.slice(0, 10)}
                  </span>
                </div>
                {invoice.due_date && (
                  <div>
                    Due Date:{" "}
                    <span className="font-semibold text-slate-800">
                      {invoice.due_date}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Billed To & Clinician Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 bg-slate-50/70 p-5 rounded-xl border border-slate-100">
            <div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                Billed To (Patient)
              </span>
              <h4 className="text-base font-bold text-slate-900">
                <Link
                  href={`/patients/${invoice.patient_id}`}
                  className="hover:text-blue-600 transition-colors"
                >
                  {invoice.patient_name || "Patient Record"}
                </Link>
              </h4>
              <div className="text-xs text-slate-600 mt-1 space-y-0.5">
                {invoice.patient_number && (
                  <div>Patient ID: <span className="font-medium">{invoice.patient_number}</span></div>
                )}
                {invoice.patient_phone && <div>Phone: {invoice.patient_phone}</div>}
                {invoice.patient_email && <div>Email: {invoice.patient_email}</div>}
              </div>
            </div>

            <div className="md:text-right">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-1">
                Treating Doctor & Context
              </span>
              <h4 className="text-base font-bold text-slate-900">
                {invoice.dentist_name || "Clinician"}
              </h4>
              <div className="text-xs text-slate-600 mt-1 space-y-0.5">
                {invoice.treatment_number && (
                  <div>
                    Treatment:{" "}
                    <Link
                      href={`/treatments/${invoice.treatment_id}`}
                      className="font-medium text-blue-600 hover:underline"
                    >
                      {invoice.treatment_number}
                    </Link>
                  </div>
                )}
                {invoice.appointment_number && (
                  <div>Appointment: #{invoice.appointment_number}</div>
                )}
              </div>
            </div>
          </div>

          {/* Line Items Table */}
          <div className="space-y-2">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
              Services & Procedures Itemization
            </h4>
            <div className="border border-slate-200 rounded-xl overflow-hidden">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase">
                  <tr>
                    <th className="py-3 px-4">#</th>
                    <th className="py-3 px-4">Type</th>
                    <th className="py-3 px-4">Description</th>
                    <th className="py-3 px-4 text-center">Qty</th>
                    <th className="py-3 px-4 text-right">Unit Price</th>
                    <th className="py-3 px-4 text-right">Amount</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {invoice.items.map((item, idx) => (
                    <tr key={item.id} className="hover:bg-slate-50/40">
                      <td className="py-3 px-4 text-xs text-slate-400 font-medium">
                        {idx + 1}
                      </td>
                      <td className="py-3 px-4 text-xs font-medium text-slate-600">
                        <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                          {item.item_type}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-semibold text-slate-900">
                        {item.description}
                      </td>
                      <td className="py-3 px-4 text-center text-slate-700 font-medium">
                        {item.quantity}
                      </td>
                      <td className="py-3 px-4 text-right text-slate-700 font-medium">
                        ₹{item.unit_price.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                      </td>
                      <td className="py-3 px-4 text-right font-bold text-slate-900">
                        ₹{item.total.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Totals & Financial Balance */}
          <div className="flex flex-col md:flex-row justify-between gap-8 pt-4">
            {/* Notes & Terms */}
            <div className="flex-1 space-y-3 text-xs text-slate-500">
              {invoice.notes && (
                <div>
                  <span className="font-bold text-slate-700 block mb-0.5">Notes:</span>
                  <p className="whitespace-pre-line">{invoice.notes}</p>
                </div>
              )}
              {invoice.terms && (
                <div>
                  <span className="font-bold text-slate-700 block mb-0.5">Payment Terms:</span>
                  <p className="whitespace-pre-line">{invoice.terms}</p>
                </div>
              )}
              {invoice.cancellation_reason && (
                <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-rose-700">
                  <span className="font-bold block">Cancellation Reason:</span>
                  <p>{invoice.cancellation_reason}</p>
                </div>
              )}
            </div>

            {/* Calculations Box */}
            <div className="w-full md:w-80 space-y-2.5 text-sm">
              <div className="flex justify-between text-slate-600">
                <span>Subtotal</span>
                <span className="font-semibold text-slate-900">
                  ₹{invoice.subtotal.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                </span>
              </div>

              {invoice.discount_amount > 0 && (
                <div className="flex justify-between text-rose-600">
                  <span>
                    Discount {invoice.discount_type === "PERCENTAGE" ? `(${invoice.discount_value}%)` : ""}
                  </span>
                  <span className="font-semibold">
                    -₹{invoice.discount_amount.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                  </span>
                </div>
              )}

              {invoice.tax_amount > 0 && (
                <div className="flex justify-between text-slate-600">
                  <span>Tax ({invoice.tax_rate}% GST)</span>
                  <span className="font-semibold text-slate-900">
                    +₹{invoice.tax_amount.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                  </span>
                </div>
              )}

              <div className="flex justify-between pt-2 border-t border-slate-200 text-base font-bold text-slate-900">
                <span>Grand Total</span>
                <span className="text-blue-600 font-extrabold text-lg">
                  ₹{invoice.grand_total.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                </span>
              </div>

              <div className="flex justify-between text-emerald-700 font-medium">
                <span>Amount Paid</span>
                <span>
                  ₹{invoice.amount_paid.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                </span>
              </div>

              <div className="flex justify-between pt-2 border-t-2 border-slate-900 text-base font-black">
                <span>Balance Due</span>
                <span className={invoice.balance_due > 0 ? "text-rose-600" : "text-emerald-600"}>
                  ₹{invoice.balance_due.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                </span>
              </div>
            </div>
          </div>

          {/* Payment History & Receipts Section */}
          <div className="border-t border-slate-200 pt-8 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <Receipt className="w-4 h-4 text-emerald-600" />
                  Payment Records & Receipts
                </h4>
                <p className="text-xs text-slate-500">
                  Immutable audit trail of all transactions, receipts, and approved refunds
                </p>
              </div>

              {invoice.status !== "PAID" &&
                invoice.status !== "CANCELLED" &&
                invoice.balance_due > 0 && (
                  <button
                    onClick={() => {
                      setPaymentAmount(invoice.balance_due);
                      setShowPaymentModal(true);
                    }}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 rounded-lg transition-colors border border-emerald-200"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    Add Payment
                  </button>
                )}
            </div>

            {invoice.payments.length === 0 ? (
              <div className="p-6 bg-slate-50/70 rounded-xl text-center text-xs text-slate-400">
                No payment transactions recorded for this invoice yet.
              </div>
            ) : (
              <div className="border border-slate-200 rounded-xl overflow-hidden">
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-50 text-xs uppercase font-semibold text-slate-500 border-b border-slate-200">
                    <tr>
                      <th className="py-2.5 px-4">Receipt #</th>
                      <th className="py-2.5 px-4">Date</th>
                      <th className="py-2.5 px-4">Method</th>
                      <th className="py-2.5 px-4">Reference</th>
                      <th className="py-2.5 px-4 text-right">Amount</th>
                      <th className="py-2.5 px-4 text-center">Status</th>
                      <th className="py-2.5 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {invoice.payments.map((p) => (
                      <tr key={p.id} className="hover:bg-slate-50/40">
                        <td className="py-3 px-4 font-bold text-slate-900 text-xs">
                          {p.receipt_number}
                        </td>
                        <td className="py-3 px-4 text-xs text-slate-600">
                          {p.payment_date || p.created_at.slice(0, 10)}
                        </td>
                        <td className="py-3 px-4 text-xs font-semibold text-slate-700">
                          <span className="px-2 py-0.5 rounded bg-slate-100">
                            {p.method}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-xs text-slate-500">
                          {p.transaction_reference || "—"}
                        </td>
                        <td className="py-3 px-4 text-right font-bold text-slate-900">
                          ₹{p.amount.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                        </td>
                        <td className="py-3 px-4 text-center">
                          {p.status === "COMPLETED" ? (
                            <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                              <CheckCircle2 className="w-3 h-3" />
                              Success
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-[11px] font-bold text-rose-700 bg-rose-50 px-2 py-0.5 rounded-full border border-rose-200">
                              <RotateCcw className="w-3 h-3" />
                              Refunded (₹{p.refund_amount})
                            </span>
                          )}
                        </td>
                        <td className="py-3 px-4 text-right">
                          <div className="flex items-center justify-end gap-2">
                            {/* Receipt PDF */}
                            <button
                              onClick={() => handleDownloadReceiptPdf(p.id, p.receipt_number)}
                              disabled={downloadingReceiptId === p.id}
                              title="Download Receipt PDF"
                              className="p-1 text-slate-500 hover:text-blue-600 rounded transition-colors"
                            >
                              <Download className="w-4 h-4" />
                            </button>

                            {/* Refund Button */}
                            {p.status === "COMPLETED" && (
                              <button
                                onClick={() => {
                                  setSelectedPaymentForRefund(p);
                                  setRefundAmount(p.amount);
                                }}
                                title="Issue Refund"
                                className="p-1 text-slate-400 hover:text-rose-600 rounded transition-colors"
                              >
                                <Undo2 className="w-4 h-4" />
                              </button>
                            )}
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
      </div>

      {/* RECORD PAYMENT MODAL */}
      {showPaymentModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-in fade-in duration-150">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-5">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-lg font-bold text-slate-900">
                  Record Payment
                </h3>
                <p className="text-xs text-slate-500">
                  Invoice #{invoice.invoice_number} • Remaining Due: ₹{invoice.balance_due.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                </p>
              </div>
              <button
                onClick={() => setShowPaymentModal(false)}
                className="text-slate-400 hover:text-slate-600 text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4 text-sm">
              <div>
                <label className="text-xs font-semibold uppercase tracking-wider text-slate-600 block mb-1">
                  Payment Amount (₹) *
                </label>
                <input
                  type="number"
                  min="0.01"
                  max={invoice.balance_due}
                  step="0.01"
                  value={paymentAmount}
                  onChange={(e) => setPaymentAmount(parseFloat(e.target.value) || 0)}
                  className="w-full px-3 py-2 text-base font-bold bg-slate-50 border border-slate-200 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              <div>
                <label className="text-xs font-semibold uppercase tracking-wider text-slate-600 block mb-1">
                  Payment Method *
                </label>
                <select
                  value={paymentMethod}
                  onChange={(e) => setPaymentMethod(e.target.value as PaymentMethod)}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg font-medium text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="UPI">UPI (Google Pay, PhonePe, Paytm)</option>
                  <option value="CASH">Cash</option>
                  <option value="CARD">Credit / Debit Card</option>
                  <option value="BANK_TRANSFER">Bank Transfer (NEFT/IMPS)</option>
                  <option value="CHEQUE">Cheque</option>
                  <option value="WALLET">Wallet</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold uppercase tracking-wider text-slate-600 block mb-1">
                    Date
                  </label>
                  <input
                    type="date"
                    value={paymentDate}
                    onChange={(e) => setPaymentDate(e.target.value)}
                    className="w-full px-2.5 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg"
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold uppercase tracking-wider text-slate-600 block mb-1">
                    Txn / UTR Ref
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. UPI-123456"
                    value={transactionRef}
                    onChange={(e) => setTransactionRef(e.target.value)}
                    className="w-full px-2.5 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold uppercase tracking-wider text-slate-600 block mb-1">
                  Notes
                </label>
                <input
                  type="text"
                  placeholder="Optional payment notes"
                  value={paymentNotes}
                  onChange={(e) => setPaymentNotes(e.target.value)}
                  className="w-full px-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowPaymentModal(false)}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => {
                  if (paymentAmount <= 0) {
                    alert("Amount must be greater than 0");
                    return;
                  }
                  if (paymentAmount > invoice.balance_due) {
                    alert("Amount cannot exceed outstanding balance");
                    return;
                  }
                  recordPaymentMutation.mutate({
                    amount: paymentAmount,
                    method: paymentMethod,
                    payment_date: paymentDate,
                    transaction_reference: transactionRef.trim() || null,
                    notes: paymentNotes.trim() || null,
                  });
                }}
                disabled={recordPaymentMutation.isPending}
                className="px-4 py-2 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg transition-colors shadow-sm disabled:opacity-50 flex items-center gap-1.5"
              >
                <CheckCircle2 className="w-4 h-4" />
                {recordPaymentMutation.isPending ? "Recording..." : "Confirm Payment"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* REFUND MODAL */}
      {selectedPaymentForRefund && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-5">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-lg font-bold text-slate-900">
                  Process Payment Refund
                </h3>
                <p className="text-xs text-slate-500">
                  Receipt #{selectedPaymentForRefund.receipt_number} • Max Refund: ₹{selectedPaymentForRefund.amount.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                </p>
              </div>
              <button
                onClick={() => setSelectedPaymentForRefund(null)}
                className="text-slate-400 hover:text-slate-600 text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4 text-sm">
              <div>
                <label className="text-xs font-semibold uppercase tracking-wider text-slate-600 block mb-1">
                  Refund Amount (₹) *
                </label>
                <input
                  type="number"
                  min="0.01"
                  max={selectedPaymentForRefund.amount}
                  step="0.01"
                  value={refundAmount}
                  onChange={(e) => setRefundAmount(parseFloat(e.target.value) || 0)}
                  className="w-full px-3 py-2 text-base font-bold bg-slate-50 border border-slate-200 rounded-lg text-slate-900"
                  required
                />
              </div>

              <div>
                <label className="text-xs font-semibold uppercase tracking-wider text-slate-600 block mb-1">
                  Clinical / Audited Reason for Refund *
                </label>
                <textarea
                  rows={3}
                  placeholder="Provide clinical or billing rationale for refund"
                  value={refundReason}
                  onChange={(e) => setRefundReason(e.target.value)}
                  className="w-full p-2.5 text-xs bg-slate-50 border border-slate-200 rounded-lg"
                  required
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setSelectedPaymentForRefund(null)}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => {
                  if (refundAmount <= 0) {
                    alert("Refund amount must be greater than 0");
                    return;
                  }
                  if (!refundReason.trim()) {
                    alert("Please provide a reason for the refund");
                    return;
                  }
                  refundMutation.mutate({
                    paymentId: selectedPaymentForRefund.id,
                    payload: {
                      refund_amount: refundAmount,
                      refund_reason: refundReason.trim(),
                    },
                  });
                }}
                disabled={refundMutation.isPending}
                className="px-4 py-2 text-xs font-bold text-white bg-rose-600 hover:bg-rose-700 rounded-lg transition-colors shadow-sm disabled:opacity-50"
              >
                {refundMutation.isPending ? "Refunding..." : "Approve & Process Refund"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CANCEL INVOICE MODAL */}
      {showCancelModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-5">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-lg font-bold text-slate-900">
                  Cancel Invoice
                </h3>
                <p className="text-xs text-slate-500">
                  Invoice #{invoice.invoice_number}
                </p>
              </div>
              <button
                onClick={() => setShowCancelModal(false)}
                className="text-slate-400 hover:text-slate-600 text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4 text-sm">
              <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-700 space-y-1">
                <span className="font-bold flex items-center gap-1">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  Irreversible Action
                </span>
                <p>
                  Cancelling an invoice permanently voids the document. An audit event and patient timeline entry will be created.
                </p>
              </div>

              <div>
                <label className="text-xs font-semibold uppercase tracking-wider text-slate-600 block mb-1">
                  Cancellation Reason *
                </label>
                <textarea
                  rows={3}
                  placeholder="Specify why this invoice is being cancelled..."
                  value={cancelReason}
                  onChange={(e) => setCancelReason(e.target.value)}
                  className="w-full p-2.5 text-xs bg-slate-50 border border-slate-200 rounded-lg"
                  required
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowCancelModal(false)}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg"
              >
                Dismiss
              </button>
              <button
                type="button"
                onClick={() => {
                  if (!cancelReason.trim()) {
                    alert("Please provide a reason for cancellation");
                    return;
                  }
                  cancelInvoiceMutation.mutate({
                    reason: cancelReason.trim(),
                  });
                }}
                disabled={cancelInvoiceMutation.isPending}
                className="px-4 py-2 text-xs font-bold text-white bg-rose-600 hover:bg-rose-700 rounded-lg transition-colors shadow-sm disabled:opacity-50"
              >
                {cancelInvoiceMutation.isPending ? "Cancelling..." : "Confirm Cancellation"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
