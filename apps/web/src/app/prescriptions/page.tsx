"use client";

import { useState } from "react";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertCircle,
  AlertTriangle,
  ArrowLeft,
  Calendar,
  CheckCircle2,
  Clock,
  Copy,
  Download,
  Eye,
  FileCheck,
  FileText,
  Filter,
  Pill,
  Plus,
  Printer,
  Search,
  Stethoscope,
  User,
} from "lucide-react";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import type {
  PrescriptionDashboardStats,
  PrescriptionDetail,
  PrescriptionStatus,
} from "./types";

export default function PrescriptionsDirectoryPage() {
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedStatus, setSelectedStatus] = useState<string>("ALL");
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  // Fetch Metrics
  const statsQuery = useQuery({
    queryKey: ["prescription-dashboard-stats"],
    queryFn: async () => {
      const res = await api.get<PrescriptionDashboardStats>(
        "/prescriptions/dashboard/stats"
      );
      return res.data;
    },
  });

  // Fetch Prescriptions List
  const prescriptionsQuery = useQuery({
    queryKey: ["prescriptions-list", selectedStatus, searchTerm],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (selectedStatus !== "ALL") {
        params.status = selectedStatus;
      }
      if (searchTerm.trim()) {
        params.search = searchTerm.trim();
      }
      const res = await api.get<PrescriptionDetail[]>("/prescriptions", {
        params,
      });
      return res.data;
    },
  });

  // Duplicate Prescription Mutation
  const duplicateMutation = useMutation({
    mutationFn: async (id: string) => {
      const res = await api.post<PrescriptionDetail>(
        `/prescriptions/${id}/duplicate`
      );
      return res.data;
    },
    onSuccess: (newRx) => {
      void queryClient.invalidateQueries({
        queryKey: ["prescriptions-list"],
      });
      void queryClient.invalidateQueries({
        queryKey: ["prescription-dashboard-stats"],
      });
      window.location.href = `/prescriptions/${newRx.id}`;
    },
  });

  const handleDownloadPdf = async (rx: PrescriptionDetail) => {
    try {
      setDownloadingId(rx.id);
      const res = await api.get(`/prescriptions/${rx.id}/pdf`, {
        responseType: "blob",
      });
      const blob = new Blob([res.data], { type: "application/pdf" });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", `Prescription-${rx.prescription_number}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Failed to download PDF", err);
      alert("Could not generate prescription PDF. Please try again.");
    } finally {
      setDownloadingId(null);
    }
  };

  const stats = statsQuery.data;
  const prescriptions = prescriptionsQuery.data || [];

  const getStatusBadge = (status: PrescriptionStatus) => {
    switch (status) {
      case "ISSUED":
        return <Badge variant="success">Issued & Signed</Badge>;
      case "DRAFT":
        return <Badge variant="warning">Draft</Badge>;
      case "CANCELLED":
        return <Badge variant="destructive">Cancelled</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  return (
    <main className="min-h-screen bg-slate-50/60 pb-20">
      {/* Top Header */}
      <div className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-2xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-md transition-colors"
              title="Back to Dashboard"
            >
              <ArrowLeft size={18} />
            </Link>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold text-slate-900">
                  Prescriptions & Medication Hub
                </h1>
                <span className="text-xs bg-teal-50 text-teal-700 border border-teal-200 px-2 py-0.5 rounded-full font-semibold">
                  Phase 6
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Clinical dental pharmacotherapy, A4 official prescriptions, templates, and immutable records
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2.5 w-full sm:w-auto justify-end">
            <Link
              href="/prescriptions/new"
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-teal-700 hover:bg-teal-800 text-white text-xs font-semibold rounded-md shadow-2xs transition-colors"
            >
              <Plus size={15} /> Write Prescription
            </Link>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6 space-y-6">
        {/* KPI Metrics */}
        <section className="grid grid-cols-2 md:grid-cols-5 gap-3.5">
          <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-2xs">
            <div className="flex items-center justify-between text-slate-500 mb-1.5">
              <span className="text-xs font-medium">Total Prescriptions</span>
              <Pill size={15} className="text-teal-600" />
            </div>
            {statsQuery.isLoading ? (
              <Skeleton className="h-7 w-16" />
            ) : (
              <p className="text-2xl font-bold text-slate-900">
                {stats?.total_prescriptions ?? 0}
              </p>
            )}
            <p className="text-[11px] text-slate-500 mt-1">All-time clinic records</p>
          </div>

          <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-2xs">
            <div className="flex items-center justify-between text-slate-500 mb-1.5">
              <span className="text-xs font-medium">Issued Today</span>
              <Clock size={15} className="text-emerald-600" />
            </div>
            {statsQuery.isLoading ? (
              <Skeleton className="h-7 w-16" />
            ) : (
              <p className="text-2xl font-bold text-emerald-700">
                {stats?.today_prescriptions ?? 0}
              </p>
            )}
            <p className="text-[11px] text-emerald-600 font-medium mt-1">
              Active dispensing
            </p>
          </div>

          <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-2xs">
            <div className="flex items-center justify-between text-slate-500 mb-1.5">
              <span className="text-xs font-medium">Active Drafts</span>
              <FileText size={15} className="text-amber-500" />
            </div>
            {statsQuery.isLoading ? (
              <Skeleton className="h-7 w-16" />
            ) : (
              <p className="text-2xl font-bold text-amber-600">
                {stats?.draft_prescriptions ?? 0}
              </p>
            )}
            <p className="text-[11px] text-slate-500 mt-1">Awaiting clinician sign-off</p>
          </div>

          <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-2xs">
            <div className="flex items-center justify-between text-slate-500 mb-1.5">
              <span className="text-xs font-medium">Follow-ups Due</span>
              <Calendar size={15} className="text-blue-600" />
            </div>
            {statsQuery.isLoading ? (
              <Skeleton className="h-7 w-16" />
            ) : (
              <p className="text-2xl font-bold text-blue-700">
                {stats?.follow_ups_due ?? 0}
              </p>
            )}
            <p className="text-[11px] text-blue-600 font-medium mt-1">
              Next 7 days review
            </p>
          </div>

          <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-2xs col-span-2 md:col-span-1">
            <div className="flex items-center justify-between text-slate-500 mb-1.5">
              <span className="text-xs font-medium">Cancelled</span>
              <AlertCircle size={15} className="text-rose-500" />
            </div>
            {statsQuery.isLoading ? (
              <Skeleton className="h-7 w-16" />
            ) : (
              <p className="text-2xl font-bold text-rose-600">
                {stats?.cancelled_prescriptions ?? 0}
              </p>
            )}
            <p className="text-[11px] text-slate-500 mt-1">Audited changes</p>
          </div>
        </section>

        {/* Filter and Search Bar */}
        <section className="bg-white rounded-lg border border-slate-200 shadow-2xs p-3.5 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
          <div className="relative flex-1">
            <Search
              size={15}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
            />
            <input
              type="text"
              placeholder="Search by Rx number, patient name, patient ID, or diagnosis..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-3.5 py-1.5 text-xs bg-slate-50/70 border border-slate-200 rounded-md focus:outline-hidden focus:ring-1 focus:ring-teal-600 focus:bg-white"
            />
          </div>

          {/* Status Filter Tabs */}
          <div className="flex items-center gap-1 bg-slate-100/80 p-1 rounded-md">
            {["ALL", "ISSUED", "DRAFT", "CANCELLED"].map((statusKey) => (
              <button
                key={statusKey}
                onClick={() => setSelectedStatus(statusKey)}
                className={`px-3 py-1 text-xs font-semibold rounded-sm transition-all ${
                  selectedStatus === statusKey
                    ? "bg-white text-teal-800 shadow-2xs"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                {statusKey === "ALL" ? "All Prescriptions" : statusKey}
              </button>
            ))}
          </div>
        </section>

        {/* Prescriptions Data Table */}
        <section className="bg-white rounded-lg border border-slate-200 shadow-2xs overflow-hidden">
          {prescriptionsQuery.isLoading ? (
            <div className="p-6 space-y-4">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-14 w-full" />
              <Skeleton className="h-14 w-full" />
              <Skeleton className="h-14 w-full" />
            </div>
          ) : prescriptions.length === 0 ? (
            <div className="p-12 text-center">
              <Pill size={40} className="text-slate-300 mx-auto mb-3" />
              <h3 className="text-sm font-bold text-slate-800">
                No Prescriptions Found
              </h3>
              <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                {searchTerm || selectedStatus !== "ALL"
                  ? "Try refining your search keywords or switching filters."
                  : "Start by issuing a new dental prescription or applying a procedure template."}
              </p>
              <div className="mt-4">
                <Link
                  href="/prescriptions/new"
                  className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-teal-700 hover:bg-teal-800 text-white text-xs font-semibold rounded-md shadow-2xs transition-colors"
                >
                  <Plus size={14} /> Write Prescription
                </Link>
              </div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50/80 border-b border-slate-200 text-[11px] font-bold text-slate-600 uppercase tracking-wider">
                    <th className="py-3 px-4">Rx Number</th>
                    <th className="py-3 px-4">Date</th>
                    <th className="py-3 px-4">Patient</th>
                    <th className="py-3 px-4">Diagnosis & Meds</th>
                    <th className="py-3 px-4">Prescribing Doctor</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-xs text-slate-700">
                  {prescriptions.map((rx) => (
                    <tr
                      key={rx.id}
                      className="hover:bg-slate-50/60 transition-colors"
                    >
                      {/* Rx Number */}
                      <td className="py-3 px-4 font-mono font-bold text-teal-800">
                        <Link
                          href={`/prescriptions/${rx.id}`}
                          className="hover:underline flex items-center gap-1"
                        >
                          <Pill size={13} className="text-teal-600" />
                          {rx.prescription_number}
                        </Link>
                      </td>

                      {/* Date */}
                      <td className="py-3 px-4 text-slate-600 whitespace-nowrap">
                        {new Date(rx.date).toLocaleDateString("en-IN", {
                          day: "numeric",
                          month: "short",
                          year: "numeric",
                        })}
                      </td>

                      {/* Patient */}
                      <td className="py-3 px-4">
                        <Link
                          href={`/patients/${rx.patient_id}`}
                          className="font-bold text-slate-900 hover:text-teal-700 transition-colors block"
                        >
                          {rx.patient_name || "Unknown Patient"}
                        </Link>
                        <div className="flex items-center gap-1.5 mt-0.5">
                          <span className="text-[11px] text-slate-500 font-mono">
                            {rx.patient_number}
                          </span>
                          {rx.patient_alerts && rx.patient_alerts.length > 0 && (
                            <span
                              className="inline-flex items-center gap-0.5 text-[10px] font-bold px-1.5 py-0.2 bg-rose-50 text-rose-700 border border-rose-200 rounded"
                              title={rx.patient_alerts.join(", ")}
                            >
                              <AlertTriangle size={10} /> Alert
                            </span>
                          )}
                        </div>
                      </td>

                      {/* Diagnosis & Meds count */}
                      <td className="py-3 px-4 max-w-xs">
                        <p className="font-semibold text-slate-900 truncate">
                          {rx.diagnosis}
                        </p>
                        <p className="text-[11px] text-slate-500 truncate mt-0.5">
                          {rx.items_count} medication(s):{" "}
                          {rx.items
                            ?.map((i) => i.medicine_name)
                            .slice(0, 2)
                            .join(", ")}
                          {rx.items && rx.items.length > 2 ? "..." : ""}
                        </p>
                      </td>

                      {/* Clinician */}
                      <td className="py-3 px-4">
                        <p className="font-medium text-slate-800">
                          {rx.dentist_name || "Clinician"}
                        </p>
                        {rx.dentist_registration && (
                          <p className="text-[10px] text-slate-400 font-mono">
                            {rx.dentist_registration}
                          </p>
                        )}
                      </td>

                      {/* Status */}
                      <td className="py-3 px-4 whitespace-nowrap">
                        {getStatusBadge(rx.status)}
                      </td>

                      {/* Actions */}
                      <td className="py-3 px-4 text-right whitespace-nowrap">
                        <div className="flex items-center justify-end gap-1.5">
                          <Link
                            href={`/prescriptions/${rx.id}`}
                            className="p-1.5 text-slate-500 hover:text-teal-700 hover:bg-slate-100 rounded transition-colors"
                            title="View Prescription"
                          >
                            <Eye size={15} />
                          </Link>

                          <button
                            onClick={() => handleDownloadPdf(rx)}
                            disabled={downloadingId === rx.id}
                            className="p-1.5 text-slate-500 hover:text-emerald-700 hover:bg-slate-100 rounded transition-colors disabled:opacity-50"
                            title="Download PDF"
                          >
                            <Download size={15} />
                          </button>

                          <button
                            onClick={() => duplicateMutation.mutate(rx.id)}
                            disabled={duplicateMutation.isPending}
                            className="p-1.5 text-slate-500 hover:text-blue-700 hover:bg-slate-100 rounded transition-colors disabled:opacity-50"
                            title="Duplicate as New Draft"
                          >
                            <Copy size={15} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
