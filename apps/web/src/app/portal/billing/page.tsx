"use client";

import React, { useState } from "react";
import {
  CreditCard,
  FileText,
  CheckCircle2,
  AlertCircle,
  Download,
  ShieldCheck,
  Building,
} from "lucide-react";
import { PortalShell } from "../portal-shell";
import type { PortalInvoiceRead } from "../types";

const mockInvoices: PortalInvoiceRead[] = [
  {
    id: "inv-1",
    invoice_number: "INV-2026-01",
    date: "2026-09-01",
    total_amount: 500.0,
    discount_amount: 50.0,
    tax_amount: 22.5,
    final_amount: 472.5,
    paid_amount: 200.0,
    balance_due: 272.5,
    status: "PARTIALLY_PAID",
  },
  {
    id: "inv-2",
    invoice_number: "INV-2026-0038",
    date: "2026-08-10",
    total_amount: 350.0,
    discount_amount: 0.0,
    tax_amount: 17.5,
    final_amount: 367.5,
    paid_amount: 367.5,
    balance_due: 0.0,
    status: "PAID",
  },
];

export default function PortalBillingPage() {
  const [invoices] = useState(mockInvoices);
  const [payTarget, setPayTarget] = useState<PortalInvoiceRead | null>(null);
  const [paySuccess, setPaySuccess] = useState(false);

  const totalOutstanding = invoices.reduce((acc, inv) => acc + inv.balance_due, 0);

  const handleSimulatePayment = () => {
    setPaySuccess(true);
    setTimeout(() => {
      setPaySuccess(false);
      setPayTarget(null);
    }, 2000);
  };

  return (
    <PortalShell>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Invoices & Financial Summary</h1>
          <p className="text-xs text-slate-500">Transparent dental treatment bills and online payment settlement</p>
        </div>
      </div>

      {/* Summary Card */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs mb-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Outstanding Balance</span>
          <div className="text-3xl font-black text-slate-900 mt-1">₹{totalOutstanding.toFixed(2)}</div>
          <p className="text-xs text-slate-500 mt-1">Settled invoices are available for tax / insurance reimbursement</p>
        </div>

        {totalOutstanding > 0 && (
          <button
            onClick={() => setPayTarget(invoices[0])}
            className="px-5 py-2.5 bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs rounded-xl shadow-xs transition flex items-center gap-2"
          >
            <CreditCard className="w-4 h-4" /> Pay Outstanding Balance
          </button>
        )}
      </div>

      {/* Invoices List */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden divide-y divide-slate-100">
        <div className="p-4 bg-slate-50 flex items-center justify-between text-xs font-semibold text-slate-500 uppercase tracking-wider">
          <span>Invoice & Date</span>
          <span>Grand Total</span>
          <span>Paid</span>
          <span>Balance Due</span>
          <span>Status</span>
          <span className="text-right">Action</span>
        </div>

        {invoices.map((inv) => (
          <div key={inv.id} className="p-4 flex items-center justify-between hover:bg-slate-50 transition text-xs">
            <div>
              <span className="font-bold text-slate-900">{inv.invoice_number}</span>
              <p className="text-slate-400 text-[11px] mt-0.5">{inv.date}</p>
            </div>

            <div className="font-semibold text-slate-700">
              ₹{inv.final_amount.toFixed(2)}
            </div>

            <div className="text-slate-600">
              ₹{inv.paid_amount.toFixed(2)}
            </div>

            <div className={`font-bold ${inv.balance_due > 0 ? "text-amber-600" : "text-emerald-600"}`}>
              ₹{inv.balance_due.toFixed(2)}
            </div>

            <div>
              <span
                className={`px-2.5 py-1 rounded-full font-bold text-[10px] ${
                  inv.status === "PAID"
                    ? "bg-emerald-100 text-emerald-800"
                    : "bg-amber-100 text-amber-800"
                }`}
              >
                {inv.status}
              </span>
            </div>

            <div className="flex items-center gap-2">
              {inv.balance_due > 0 && (
                <button
                  onClick={() => setPayTarget(inv)}
                  className="px-3 py-1 bg-teal-600 hover:bg-teal-700 text-white font-bold rounded-lg transition"
                >
                  Pay Now
                </button>
              )}
              <button
                className="text-slate-400 hover:text-slate-700 p-1"
                title="Download Invoice PDF"
              >
                <Download className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Payment Modal */}
      {payTarget && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200 animate-scale-up">
            <h3 className="text-base font-bold text-slate-900 mb-1">Pay Invoice: {payTarget.invoice_number}</h3>
            <p className="text-xs text-slate-500 mb-4">Secure digital payment gateway</p>

            {paySuccess ? (
              <div className="p-6 text-center space-y-2">
                <CheckCircle2 className="w-10 h-10 text-emerald-600 mx-auto" />
                <h4 className="text-sm font-bold text-slate-900">Payment Processed Successfully!</h4>
                <p className="text-xs text-slate-500">Your clinic receipt has been generated.</p>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 text-xs space-y-2">
                  <div className="flex justify-between">
                    <span className="text-slate-500">Amount Due:</span>
                    <strong className="text-slate-900 text-sm">₹{payTarget.balance_due.toFixed(2)}</strong>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Beneficiary:</span>
                    <span className="text-slate-800">City Dental Care Pro</span>
                  </div>
                </div>

                <div className="space-y-2 text-xs">
                  <span className="font-semibold text-slate-700 block">Select Payment Method:</span>
                  <div className="grid grid-cols-2 gap-2">
                    <button className="p-3 border-2 border-teal-600 bg-teal-50/50 rounded-xl text-center font-bold text-teal-800">
                      UPI / QR Code
                    </button>
                    <button className="p-3 border border-slate-200 rounded-xl text-center font-medium text-slate-700 hover:bg-slate-50">
                      Debit / Credit Card
                    </button>
                  </div>
                </div>

                <div className="flex justify-end gap-2 pt-2">
                  <button
                    onClick={() => setPayTarget(null)}
                    className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl transition"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSimulatePayment}
                    className="px-5 py-2 text-xs font-bold text-white bg-teal-600 hover:bg-teal-700 rounded-xl shadow-sm transition"
                  >
                    Authorize Payment of ₹{payTarget.balance_due.toFixed(2)}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </PortalShell>
  );
}
