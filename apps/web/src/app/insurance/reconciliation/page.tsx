"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Receipt,
  Plus,
  Search,
  CheckCircle2,
  Clock,
  AlertTriangle,
  X,
  FileSpreadsheet,
} from "lucide-react";
import { api } from "@/lib/api";
import { InsuranceNav } from "../nav";
import type { InsurancePaymentReconciliation, SettlementType } from "../types";

export default function PaymentReconciliationPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isModalOpen) {
        setIsModalOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isModalOpen]);

  // Form State
  const [claimId, setClaimId] = useState("");
  const [invoiceId, setInvoiceId] = useState("");
  const [reference, setReference] = useState("");
  const [paymentDate, setPaymentDate] = useState("2026-09-08");
  const [settledAmount, setSettledAmount] = useState(8000);
  const [patientCopayDue, setPatientCopayDue] = useState(2000);
  const [adjustmentAmount, setAdjustmentAmount] = useState(0);
  const [settlementType, setSettlementType] = useState<SettlementType>("FULL");

  const { data: reconciliations = [], isLoading } = useQuery<InsurancePaymentReconciliation[]>({
    queryKey: ["insurance-reconciliations"],
    queryFn: async () => {
      const res = await api.get<InsurancePaymentReconciliation[]>("/insurance/reconciliations");
      return res.data;
    },
  });

  const createMutation = useMutation({
    mutationFn: async () => {
      await api.post("/insurance/reconciliations", {
        claim_id: claimId,
        invoice_id: invoiceId || null,
        reconciliation_reference: reference,
        payment_date: paymentDate,
        insurance_settled_amount: Number(settledAmount),
        patient_copay_due: Number(patientCopayDue),
        adjustment_amount: Number(adjustmentAmount),
        settlement_type: settlementType,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["insurance-reconciliations"] });
      setIsModalOpen(false);
      resetForm();
    },
  });

  const resetForm = () => {
    setClaimId("");
    setInvoiceId("");
    setReference("");
    setSettledAmount(8000);
    setPatientCopayDue(2000);
    setAdjustmentAmount(0);
    setSettlementType("FULL");
  };

  const filteredReconciliations = reconciliations.filter((r) => {
    if (!search.trim()) return true;
    return r.reconciliation_reference.toLowerCase().includes(search.toLowerCase());
  });

  return (
    <div className="min-h-screen bg-slate-50/50">
      <InsuranceNav />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Payment Reconciliation (ERA)</h1>
            <p className="text-sm text-slate-600 mt-1">
              Electronic Remittance Advice posting, copay adjustments, write-offs, and automated billing ledger sync.
            </p>
          </div>
          <button
            onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-teal-600 text-white rounded-lg text-sm font-semibold hover:bg-teal-700 shadow-sm transition-colors cursor-pointer"
          >
            <Plus className="w-4 h-4" /> Post Remittance Advice
          </button>
        </div>

        {/* Search */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex items-center gap-3">
          <div className="relative w-full sm:w-80">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search by Remittance / EFT Reference..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
            />
          </div>
        </div>

        {/* Reconciliations Table */}
        {isLoading ? (
          <div className="text-center py-12 text-slate-500 text-sm">Loading reconciliations...</div>
        ) : filteredReconciliations.length === 0 ? (
          <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
            <Receipt className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <h3 className="text-base font-semibold text-slate-800">No payment reconciliations recorded</h3>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              Post an Electronic Remittance Advice (ERA) or cheque payment to balance insurance AR and update patient copay dues.
            </p>
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200">
                  <tr>
                    <th className="py-3 px-4">Reference #</th>
                    <th className="py-3 px-4">Payment Date</th>
                    <th className="py-3 px-4">Payer Settled</th>
                    <th className="py-3 px-4">Patient Co-pay Due</th>
                    <th className="py-3 px-4">Adjustment / Write-off</th>
                    <th className="py-3 px-4">Settlement Type</th>
                    <th className="py-3 px-4">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredReconciliations.map((rec) => (
                    <tr key={rec.id} className="hover:bg-slate-50/50 transition-colors">
                      <td className="py-3 px-4 font-mono font-bold text-slate-900">
                        {rec.reconciliation_reference}
                      </td>
                      <td className="py-3 px-4 text-slate-600">{rec.payment_date}</td>
                      <td className="py-3 px-4 font-bold text-emerald-700">
                        ₹{rec.insurance_settled_amount.toLocaleString()}
                      </td>
                      <td className="py-3 px-4 font-semibold text-amber-700">
                        ₹{rec.patient_copay_due.toLocaleString()}
                      </td>
                      <td className="py-3 px-4 text-slate-600">
                        {rec.adjustment_amount ? `₹${rec.adjustment_amount.toLocaleString()}` : "₹0"}
                      </td>
                      <td className="py-3 px-4">
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-700">
                          {rec.settlement_type}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                          <CheckCircle2 className="w-3 h-3" /> {rec.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Modal: Post Remittance */}
        {isModalOpen && (
          <div 
            className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/75 p-4 overflow-y-auto"
            onClick={(e) => {
              if (e.target === e.currentTarget) setIsModalOpen(false);
            }}
          >
            <div className="bg-white dark:bg-slate-900 rounded-xl shadow-2xl border border-slate-200 dark:border-slate-800 w-full max-w-lg max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-800">
                <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">Post Remittance Advice (ERA)</h3>
                <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300">
                  <X className="w-5 h-5" />
                </button>
              </div>
              <div className="p-6 space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="col-span-2">
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Claim UUID *</label>
                    <input
                      type="text"
                      placeholder="Paste Claim ID"
                      value={claimId}
                      onChange={(e) => setClaimId(e.target.value)}
                      className="w-full text-xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-md p-2"
                    />
                  </div>
                  <div className="col-span-2">
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                      Billing Invoice UUID (Optional - Auto Updates Balance)
                    </label>
                    <input
                      type="text"
                      placeholder="Paste Invoice ID"
                      value={invoiceId}
                      onChange={(e) => setInvoiceId(e.target.value)}
                      className="w-full text-xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-md p-2"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">EFT / Cheque Ref *</label>
                    <input
                      type="text"
                      placeholder="e.g. EFT-2026-9921"
                      value={reference}
                      onChange={(e) => setReference(e.target.value)}
                      className="w-full text-xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-md p-2 uppercase"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Payment Date</label>
                    <input
                      type="date"
                      value={paymentDate}
                      onChange={(e) => setPaymentDate(e.target.value)}
                      className="w-full text-xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-md p-2"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Payer Settled Amount (₹) *</label>
                    <input
                      type="number"
                      value={settledAmount}
                      onChange={(e) => setSettledAmount(Number(e.target.value))}
                      className="w-full text-xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-md p-2"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Patient Copay Due (₹)</label>
                    <input
                      type="number"
                      value={patientCopayDue}
                      onChange={(e) => setPatientCopayDue(Number(e.target.value))}
                      className="w-full text-xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-md p-2"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Contractual Write-Off (₹)</label>
                    <input
                      type="number"
                      value={adjustmentAmount}
                      onChange={(e) => setAdjustmentAmount(Number(e.target.value))}
                      className="w-full text-xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-md p-2"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Settlement Type</label>
                    <select
                      value={settlementType}
                      onChange={(e) => setSettlementType(e.target.value as SettlementType)}
                      className="w-full text-xs border border-slate-300 dark:border-slate-700 rounded-md p-2 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100"
                    >
                      <option value="FULL">Full Settlement</option>
                      <option value="PARTIAL">Partial Settlement</option>
                      <option value="REJECTED_ZERO">Zero Settlement / Denied</option>
                      <option value="OVERPAYMENT">Overpayment</option>
                    </select>
                  </div>
                </div>
              </div>
              <div className="px-6 py-3 bg-slate-50 dark:bg-slate-800/60 border-t border-slate-200 dark:border-slate-800 flex justify-end gap-2">
                <button
                  onClick={() => setIsModalOpen(false)}
                  className="px-3 py-1.5 text-xs font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-800 rounded-md transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={() => createMutation.mutate()}
                  disabled={!claimId || !reference || !settledAmount || createMutation.isPending}
                  className="px-4 py-1.5 text-xs font-semibold text-white bg-teal-600 hover:bg-teal-700 rounded-md shadow-sm cursor-pointer disabled:opacity-50 transition-colors"
                >
                  {createMutation.isPending ? "Posting..." : "Post & Sync Ledger"}
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
