"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  AlertCircle,
  ArrowLeft,
  Calendar,
  CheckCircle2,
  Clock,
  FileCheck,
  FileText,
  IndianRupee,
  Layers,
  Percent,
  Plus,
  Receipt,
  Search,
  Stethoscope,
  Trash2,
  User,
  Zap,
} from "lucide-react";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import type {
  DiscountType,
  InvoiceCreate,
  InvoiceDetail,
  InvoiceItemCreate,
  InvoiceItemType,
} from "../types";

interface PatientOption {
  id: string;
  first_name: string;
  last_name: string;
  patient_number: string;
  mobile_number?: string;
  email?: string;
}

interface UserOption {
  id: string;
  first_name: string;
  last_name: string;
  role: string;
}

interface TreatmentProcedureOption {
  id: string;
  procedure_name: string;
  tooth_number?: string;
  cost: number;
}

interface TreatmentOption {
  id: string;
  treatment_number: string;
  diagnosis: string;
  procedures: TreatmentProcedureOption[];
}

function InvoiceComposerContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const queryPatientId = searchParams.get("patient_id") || "";
  const queryTreatmentId = searchParams.get("treatment_id") || "";
  const queryAppointmentId = searchParams.get("appointment_id") || "";

  const [patientId, setPatientId] = useState<string>(queryPatientId);
  const [patientSearch, setPatientSearch] = useState<string>("");
  const [dentistId, setDentistId] = useState<string>("");
  const [treatmentId, setTreatmentId] = useState<string>(queryTreatmentId);
  const [appointmentId, setAppointmentId] = useState<string>(queryAppointmentId);
  const [invoiceDate, setInvoiceDate] = useState<string>(
    new Date().toISOString().slice(0, 10)
  );
  const [dueDate, setDueDate] = useState<string>(
    new Date(Date.now() + 7 * 86400000).toISOString().slice(0, 10)
  );

  const [discountType, setDiscountType] = useState<DiscountType>("FIXED");
  const [discountValue, setDiscountValue] = useState<number>(0);
  const [taxRate, setTaxRate] = useState<number>(18.0);
  const [notes, setNotes] = useState<string>("Thank you for choosing DentalCare Pro.");
  const [terms, setTerms] = useState<string>(
    "1. Payment is due within 7 days of invoice issuance.\n2. In case of queries regarding treatments billed, please contact reception."
  );

  const [items, setItems] = useState<InvoiceItemCreate[]>([
    {
      item_type: "CONSULTATION",
      description: "Comprehensive Dental Examination",
      quantity: 1,
      unit_price: 500,
      discount_amount: 0,
      tax_rate: 0,
      tax_amount: 0,
    },
  ]);

  // 1. Fetch Patients
  const patientsQuery = useQuery({
    queryKey: ["billing-patients-search", patientSearch, patientId],
    queryFn: async () => {
      const res = await api.get<{ items: PatientOption[] } | PatientOption[]>("/patients", {
        params: { search: patientSearch.trim() || undefined, limit: 50 },
      });
      const data = res.data;
      const list: PatientOption[] = Array.isArray(data)
        ? data
        : Array.isArray(data?.items)
        ? data.items
        : [];

      if (patientId && !list.some((p) => p.id === patientId)) {
        try {
          const singleRes = await api.get<PatientOption>(`/patients/${patientId}`);
          if (singleRes.data?.id) {
            return [singleRes.data, ...list];
          }
        } catch {
          // Ignore if patient lookup fails
        }
      }
      return list;
    },
  });

  // 2. Fetch Clinicians
  const usersQuery = useQuery({
    queryKey: ["billing-dentists-list"],
    queryFn: async () => {
      try {
        const res = await api.get<{ items: UserOption[] } | UserOption[]>("/users", {
          params: { limit: 50 },
        });
        const data = res.data;
        const list: UserOption[] = Array.isArray(data)
          ? data
          : Array.isArray(data?.items)
          ? data.items
          : [];
        return list.filter((u) =>
          ["DENTIST", "CLINIC_ADMIN", "SUPER_ADMIN"].includes(u.role)
        );
      } catch {
        const fallback = await api.get<{ items: UserOption[] } | UserOption[]>("/dentists");
        const data = fallback.data;
        return Array.isArray(data)
          ? data
          : Array.isArray(data?.items)
          ? data.items
          : [];
      }
    },
  });

  // Set default dentist if available
  const cliniciansList: UserOption[] = Array.isArray(usersQuery.data) ? usersQuery.data : [];
  useEffect(() => {
    if (!dentistId && cliniciansList.length > 0) {
      setDentistId(cliniciansList[0].id);
    }
  }, [cliniciansList, dentistId]);

  // 3. Fetch Treatment Details if treatment_id is set
  const treatmentQuery = useQuery({
    queryKey: ["billing-treatment-detail", treatmentId],
    queryFn: async () => {
      if (!treatmentId) return null;
      const res = await api.get<TreatmentOption>(`/treatments/${treatmentId}`);
      return res.data;
    },
    enabled: !!treatmentId,
  });

  // If treatment query resolves, auto-populate line items if only default consultation is present
  const handleLoadTreatmentProcedures = (trt: TreatmentOption) => {
    const newItems: InvoiceItemCreate[] = [
      {
        item_type: "CONSULTATION",
        description: `Consultation - Treatment #${trt.treatment_number}`,
        quantity: 1,
        unit_price: 300,
        discount_amount: 0,
        tax_rate: 0,
        tax_amount: 0,
      },
    ];

    if (trt.procedures && trt.procedures.length > 0) {
      for (const p of trt.procedures) {
        newItems.push({
          item_type: "PROCEDURE",
          description: p.tooth_number
            ? `${p.procedure_name} (Tooth #${p.tooth_number})`
            : p.procedure_name,
          quantity: 1,
          unit_price: p.cost,
          discount_amount: 0,
          tax_rate: 0,
          tax_amount: 0,
          procedure_id: p.id,
        });
      }
    }

    setItems(newItems);
  };

  // Add line item
  const handleAddItem = () => {
    setItems([
      ...items,
      {
        item_type: "PROCEDURE",
        description: "",
        quantity: 1,
        unit_price: 0,
        discount_amount: 0,
        tax_rate: 0,
        tax_amount: 0,
      },
    ]);
  };

  // Remove line item
  const handleRemoveItem = (index: number) => {
    if (items.length <= 1) {
      alert("An invoice must contain at least one line item.");
      return;
    }
    setItems(items.filter((_, i) => i !== index));
  };

  // Update line item
  const handleUpdateItem = (
    index: number,
    field: keyof InvoiceItemCreate,
    value: string | number
  ) => {
    const next = [...items];
    next[index] = { ...next[index], [field]: value };
    setItems(next);
  };

  // Real-time calculations
  const subtotal = items.reduce(
    (sum, it) => sum + (Number(it.quantity) || 0) * (Number(it.unit_price) || 0),
    0
  );

  const discountAmount =
    discountType === "PERCENTAGE"
      ? (subtotal * (Number(discountValue) || 0)) / 100
      : Math.min(subtotal, Number(discountValue) || 0);

  const taxableAmount = Math.max(0, subtotal - discountAmount);
  const taxAmount = (taxableAmount * (Number(taxRate) || 0)) / 100;
  const grandTotal = taxableAmount + taxAmount;

  // Invoice Mutation
  const createInvoiceMutation = useMutation({
    mutationFn: async (payload: InvoiceCreate) => {
      const res = await api.post<InvoiceDetail>("/billing/invoices", payload);
      return res.data;
    },
    onSuccess: (created) => {
      router.push(`/billing/${created.id}`);
    },
    onError: (err: any) => {
      const msg = err.response?.data?.detail || "Failed to create invoice";
      alert(msg);
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!patientId) {
      alert("Please select a patient.");
      return;
    }
    if (!dentistId) {
      alert("Please select a clinician.");
      return;
    }
    for (let i = 0; i < items.length; i++) {
      if (!items[i].description.trim()) {
        alert(`Please specify a description for line item #${i + 1}.`);
        return;
      }
      if (items[i].unit_price < 0) {
        alert(`Unit price cannot be negative for line item #${i + 1}.`);
        return;
      }
    }

    const payload: InvoiceCreate = {
      patient_id: patientId,
      dentist_id: dentistId,
      treatment_id: treatmentId || null,
      appointment_id: appointmentId || null,
      date: invoiceDate,
      due_date: dueDate,
      discount_type: discountType,
      discount_value: Number(discountValue) || 0,
      tax_rate: Number(taxRate) || 0,
      notes: notes.trim() || null,
      terms: terms.trim() || null,
      items: items.map((it) => ({
        ...it,
        quantity: Number(it.quantity) || 1,
        unit_price: Number(it.unit_price) || 0,
      })),
    };

    createInvoiceMutation.mutate(payload);
  };

  const patientsList: PatientOption[] = Array.isArray(patientsQuery.data)
    ? patientsQuery.data
    : Array.isArray((patientsQuery.data as any)?.items)
    ? (patientsQuery.data as any).items
    : [];
  const selectedPatient = patientsList.find((p) => p.id === patientId);

  return (
    <div className="min-h-screen bg-slate-50/50 p-6 md:p-8">
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Top bar */}
        <div className="flex items-center justify-between">
          <Link
            href="/billing"
            className="inline-flex items-center gap-2 text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Invoices
          </Link>
          <div className="text-xs text-slate-400">
            Phase 7: Financial Management
          </div>
        </div>

        {/* Title */}
        <div className="bg-white rounded-xl p-6 border border-slate-200/80 shadow-xs flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-blue-600 text-sm font-semibold uppercase tracking-wider">
              <Receipt className="w-4 h-4" />
              Invoice Composer
            </div>
            <h1 className="text-2xl font-bold text-slate-900 mt-1">
              Create Patient Invoice
            </h1>
            <p className="text-sm text-slate-500 mt-0.5">
              Generate itemized tax invoices with automated procedure conversion, GST calculation, and printable format
            </p>
          </div>

          {treatmentQuery.data && (
            <button
              type="button"
              onClick={() => handleLoadTreatmentProcedures(treatmentQuery.data!)}
              className="inline-flex items-center gap-2 px-3.5 py-2 text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-lg hover:bg-emerald-100 transition-colors"
            >
              <Zap className="w-4 h-4 text-emerald-600" />
              Load {treatmentQuery.data.procedures?.length || 0} Procedures from Treatment #{treatmentQuery.data.treatment_number}
            </button>
          )}
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Metadata Section */}
          <div className="bg-white rounded-xl p-6 border border-slate-200/80 shadow-xs grid grid-cols-1 md:grid-cols-3 gap-5">
            {/* Patient Picker */}
            <div className="space-y-2 md:col-span-1">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-600 flex items-center gap-1.5">
                <User className="w-3.5 h-3.5 text-blue-600" />
                Select Patient *
              </label>
              <select
                value={patientId}
                onChange={(e) => setPatientId(e.target.value)}
                className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium text-slate-900"
                required
              >
                <option value="">-- Choose Patient --</option>
                {patientsList.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.first_name} {p.last_name} ({p.patient_number})
                  </option>
                ))}
              </select>
              {selectedPatient && (
                <div className="text-xs text-slate-500">
                  {selectedPatient.mobile_number && `📞 ${selectedPatient.mobile_number}`}
                  {selectedPatient.email && ` | ✉️ ${selectedPatient.email}`}
                </div>
              )}
            </div>

            {/* Clinician Picker */}
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-600 flex items-center gap-1.5">
                <Stethoscope className="w-3.5 h-3.5 text-blue-600" />
                Treating Clinician *
              </label>
              <select
                value={dentistId}
                onChange={(e) => setDentistId(e.target.value)}
                className="w-full px-3 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium text-slate-900"
                required
              >
                <option value="">-- Choose Clinician --</option>
                {cliniciansList.map((u) => (
                  <option key={u.id} value={u.id}>
                    Dr. {u.first_name} {u.last_name} ({u.role || "DENTIST"})
                  </option>
                ))}
              </select>
            </div>

            {/* Dates */}
            <div className="space-y-2 grid grid-cols-2 gap-2">
              <div>
                <label className="text-xs font-semibold uppercase tracking-wider text-slate-600 flex items-center gap-1">
                  <Calendar className="w-3.5 h-3.5 text-blue-600" />
                  Date
                </label>
                <input
                  type="date"
                  value={invoiceDate}
                  onChange={(e) => setInvoiceDate(e.target.value)}
                  className="w-full px-2.5 py-1.5 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-900"
                  required
                />
              </div>
              <div>
                <label className="text-xs font-semibold uppercase tracking-wider text-slate-600 flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5 text-amber-600" />
                  Due Date
                </label>
                <input
                  type="date"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  className="w-full px-2.5 py-1.5 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-900"
                  required
                />
              </div>
            </div>
          </div>

          {/* Line Items Section */}
          <div className="bg-white rounded-xl p-6 border border-slate-200/80 shadow-xs space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-base font-semibold text-slate-900 flex items-center gap-2">
                  <Layers className="w-4 h-4 text-blue-600" />
                  Billable Items & Services
                </h3>
                <p className="text-xs text-slate-500">
                  Procedures, consultations, diagnostic scans, and clinical materials
                </p>
              </div>
              <button
                type="button"
                onClick={handleAddItem}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors"
              >
                <Plus className="w-3.5 h-3.5" />
                Add Item
              </button>
            </div>

            <div className="space-y-3">
              {items.map((item, idx) => {
                const rowTotal = (Number(item.quantity) || 0) * (Number(item.unit_price) || 0);
                return (
                  <div
                    key={idx}
                    className="p-3.5 rounded-xl bg-slate-50/70 border border-slate-200/80 grid grid-cols-1 md:grid-cols-12 gap-3 items-center"
                  >
                    {/* Item Type */}
                    <div className="md:col-span-3">
                      <label className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-1">
                        Type
                      </label>
                      <select
                        value={item.item_type}
                        onChange={(e) =>
                          handleUpdateItem(idx, "item_type", e.target.value as InvoiceItemType)
                        }
                        className="w-full px-2.5 py-1.5 text-xs bg-white border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium text-slate-800"
                      >
                        <option value="PROCEDURE">Procedure</option>
                        <option value="CONSULTATION">Consultation</option>
                        <option value="MEDICATION">Medication</option>
                        <option value="CONSUMABLE">Consumable</option>
                        <option value="LABORATORY">Laboratory</option>
                        <option value="OTHER">Other</option>
                      </select>
                    </div>

                    {/* Description */}
                    <div className="md:col-span-4">
                      <label className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-1">
                        Description *
                      </label>
                      <input
                        type="text"
                        placeholder="e.g. Scaling, Root Canal, Ceramic Crown"
                        value={item.description}
                        onChange={(e) => handleUpdateItem(idx, "description", e.target.value)}
                        className="w-full px-2.5 py-1.5 text-xs bg-white border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium text-slate-900"
                        required
                      />
                    </div>

                    {/* Quantity */}
                    <div className="md:col-span-1">
                      <label className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-1">
                        Qty
                      </label>
                      <input
                        type="number"
                        min="1"
                        max="500"
                        value={item.quantity}
                        onChange={(e) =>
                          handleUpdateItem(idx, "quantity", parseInt(e.target.value) || 1)
                        }
                        className="w-full px-2 py-1.5 text-xs bg-white border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium text-slate-900 text-center"
                        required
                      />
                    </div>

                    {/* Unit Price (₹) */}
                    <div className="md:col-span-2">
                      <label className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-1">
                        Unit Price (₹)
                      </label>
                      <input
                        type="number"
                        min="0"
                        step="0.01"
                        value={item.unit_price}
                        onChange={(e) =>
                          handleUpdateItem(idx, "unit_price", parseFloat(e.target.value) || 0)
                        }
                        className="w-full px-2 py-1.5 text-xs bg-white border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-medium text-slate-900 text-right"
                        required
                      />
                    </div>

                    {/* Total & Delete */}
                    <div className="md:col-span-2 flex items-center justify-between md:justify-end gap-3 pt-4 md:pt-0">
                      <div className="text-right">
                        <span className="text-[11px] text-slate-400 block">Total</span>
                        <span className="text-xs font-bold text-slate-900">
                          ₹{rowTotal.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleRemoveItem(idx)}
                        className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                        title="Delete Item"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Pricing, Discount, Tax & Financial Breakdown */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Notes & Terms */}
            <div className="bg-white rounded-xl p-6 border border-slate-200/80 shadow-xs space-y-4">
              <h3 className="text-sm font-semibold text-slate-900">
                Notes & Terms of Service
              </h3>
              <div className="space-y-3">
                <div>
                  <label className="text-xs font-medium text-slate-600 block mb-1">
                    Invoice Notes (Printed on PDF)
                  </label>
                  <textarea
                    rows={2}
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    className="w-full p-2.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-900"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-600 block mb-1">
                    Payment Terms & Clinical Policy
                  </label>
                  <textarea
                    rows={3}
                    value={terms}
                    onChange={(e) => setTerms(e.target.value)}
                    className="w-full p-2.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-slate-900"
                  />
                </div>
              </div>
            </div>

            {/* Financial Summary Calculation Card */}
            <div className="bg-white rounded-xl p-6 border border-slate-200/80 shadow-xs space-y-4">
              <h3 className="text-sm font-semibold text-slate-900 flex items-center justify-between">
                <span>Summary Breakdown</span>
                <span className="text-xs font-medium text-slate-400">INR (₹)</span>
              </h3>

              <div className="space-y-3 text-sm">
                {/* Subtotal */}
                <div className="flex items-center justify-between text-slate-600">
                  <span>Subtotal</span>
                  <span className="font-semibold text-slate-900">
                    ₹{subtotal.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                  </span>
                </div>

                {/* Discount settings */}
                <div className="flex items-center justify-between gap-3 pt-2 border-t border-slate-100">
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs font-medium text-slate-600">Discount:</span>
                    <select
                      value={discountType}
                      onChange={(e) => setDiscountType(e.target.value as DiscountType)}
                      className="px-2 py-0.5 text-xs bg-slate-100 border border-slate-200 rounded text-slate-800"
                    >
                      <option value="FIXED">Fixed (₹)</option>
                      <option value="PERCENTAGE">Percent (%)</option>
                    </select>
                  </div>
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      min="0"
                      step="0.1"
                      value={discountValue}
                      onChange={(e) => setDiscountValue(parseFloat(e.target.value) || 0)}
                      className="w-20 px-2 py-0.5 text-xs bg-slate-50 border border-slate-200 rounded text-right font-medium"
                    />
                    <span className="text-rose-600 font-medium">
                      -₹{discountAmount.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                </div>

                {/* Tax settings */}
                <div className="flex items-center justify-between gap-3 pt-2 border-t border-slate-100">
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs font-medium text-slate-600">GST / Tax Rate:</span>
                    <select
                      value={taxRate}
                      onChange={(e) => setTaxRate(parseFloat(e.target.value) || 0)}
                      className="px-2 py-0.5 text-xs bg-slate-100 border border-slate-200 rounded text-slate-800 font-medium"
                    >
                      <option value="0">0% (Exempt)</option>
                      <option value="5">5% GST</option>
                      <option value="12">12% GST</option>
                      <option value="18">18% GST (Standard)</option>
                    </select>
                  </div>
                  <span className="text-slate-900 font-medium">
                    +₹{taxAmount.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                  </span>
                </div>

                {/* Grand Total */}
                <div className="flex items-center justify-between pt-3 border-t-2 border-slate-900 text-base">
                  <span className="font-bold text-slate-900">Grand Total</span>
                  <span className="font-extrabold text-blue-600 text-xl">
                    ₹{grandTotal.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                  </span>
                </div>
              </div>

              {/* Submit Button */}
              <div className="pt-2">
                <button
                  type="submit"
                  disabled={createInvoiceMutation.isPending}
                  className="w-full py-3 px-4 text-sm font-bold text-white bg-blue-600 rounded-xl hover:bg-blue-700 transition-colors shadow-md shadow-blue-500/20 disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  <CheckCircle2 className="w-5 h-5" />
                  {createInvoiceMutation.isPending ? "Generating Invoice..." : "Create & Issue Invoice"}
                </button>
              </div>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function InvoiceComposerPage() {
  return (
    <Suspense
      fallback={
        <div className="p-8 max-w-5xl mx-auto space-y-4">
          <Skeleton className="h-10 w-48" />
          <Skeleton className="h-40 w-full" />
          <Skeleton className="h-60 w-full" />
        </div>
      }
    >
      <InvoiceComposerContent />
    </Suspense>
  );
}
