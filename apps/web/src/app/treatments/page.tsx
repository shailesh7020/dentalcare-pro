"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  AlertCircle,
  ArrowLeft,
  Calendar,
  CheckCircle2,
  Clock,
  ExternalLink,
  FileCheck,
  FileText,
  Filter,
  Plus,
  Search,
  Stethoscope,
  User,
  Users,
} from "lucide-react";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import type { TreatmentDashboardStats, TreatmentRead, TreatmentStatus } from "./types";

export default function TreatmentsDirectoryPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedStatus, setSelectedStatus] = useState<string>("ALL");

  // Fetch Dashboard Metrics
  const statsQuery = useQuery({
    queryKey: ["treatment-dashboard-stats"],
    queryFn: async () => {
      const res = await api.get<TreatmentDashboardStats>("/treatments/dashboard/stats");
      return res.data;
    },
  });

  // Fetch Treatments List
  const treatmentsQuery = useQuery({
    queryKey: ["treatments-list", selectedStatus, searchTerm],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (selectedStatus !== "ALL") {
        params.status = selectedStatus;
      }
      if (searchTerm.trim()) {
        params.search = searchTerm.trim();
      }
      const res = await api.get<TreatmentRead[]>("/treatments", { params });
      return res.data;
    },
  });

  const stats = statsQuery.data;
  const treatments = treatmentsQuery.data || [];

  const getStatusBadge = (status: TreatmentStatus) => {
    switch (status) {
      case "COMPLETED":
        return <Badge variant="success">Completed</Badge>;
      case "IN_PROGRESS":
        return <Badge variant="warning">In Progress</Badge>;
      case "PLANNED":
        return <Badge variant="info">Planned</Badge>;
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
                <h1 className="text-xl font-bold text-slate-900">Clinical Treatments Hub</h1>
                <span className="text-xs bg-teal-50 text-teal-700 border border-teal-200 px-2 py-0.5 rounded-full font-semibold">
                  Phase 4
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Clinical records, procedures performed, SOAP notes, and patient follow-ups
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 w-full sm:w-auto justify-end">
            <Link
              href="/appointments"
              className="inline-flex items-center gap-1.5 px-3 py-2 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 font-semibold text-xs rounded-md shadow-2xs transition-colors"
            >
              <Calendar size={13} /> Appointments Queue
            </Link>
            <Link
              href="/treatments/new"
              className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-teal-700 hover:bg-teal-800 text-white font-semibold text-xs rounded-md shadow-2xs transition-colors"
            >
              <Plus size={14} /> New Treatment
            </Link>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6">
        {/* KPI Dashboard Stats Cards */}
        <section className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3.5 mb-6">
          <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between text-slate-500 text-xs mb-1">
              <span>Total Treatments</span>
              <FileCheck size={16} className="text-teal-600" />
            </div>
            <div className="text-2xl font-bold text-slate-900">
              {statsQuery.isLoading ? <Skeleton className="h-7 w-12" /> : stats?.total_treatments ?? 0}
            </div>
            <p className="text-[11px] text-slate-400 mt-1">All clinical entries</p>
          </div>

          <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between text-slate-500 text-xs mb-1">
              <span>In Progress</span>
              <Activity size={16} className="text-amber-600" />
            </div>
            <div className="text-2xl font-bold text-amber-700">
              {statsQuery.isLoading ? <Skeleton className="h-7 w-12" /> : stats?.in_progress ?? 0}
            </div>
            <p className="text-[11px] text-slate-400 mt-1">Active in chair / open</p>
          </div>

          <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between text-slate-500 text-xs mb-1">
              <span>Planned</span>
              <Clock size={16} className="text-sky-600" />
            </div>
            <div className="text-2xl font-bold text-sky-700">
              {statsQuery.isLoading ? <Skeleton className="h-7 w-12" /> : stats?.planned ?? 0}
            </div>
            <p className="text-[11px] text-slate-400 mt-1">Staged treatment plans</p>
          </div>

          <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-xs">
            <div className="flex items-center justify-between text-slate-500 text-xs mb-1">
              <span>Completed</span>
              <CheckCircle2 size={16} className="text-emerald-600" />
            </div>
            <div className="text-2xl font-bold text-emerald-700">
              {statsQuery.isLoading ? <Skeleton className="h-7 w-12" /> : stats?.completed ?? 0}
            </div>
            <p className="text-[11px] text-slate-400 mt-1">Locked clinical records</p>
          </div>

          <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-xs col-span-2 sm:col-span-1">
            <div className="flex items-center justify-between text-slate-500 text-xs mb-1">
              <span>Follow-ups Due</span>
              <AlertCircle size={16} className="text-rose-600" />
            </div>
            <div className="text-2xl font-bold text-rose-700">
              {statsQuery.isLoading ? <Skeleton className="h-7 w-12" /> : stats?.follow_ups_due ?? 0}
            </div>
            <p className="text-[11px] text-slate-400 mt-1">Next 7 days due</p>
          </div>
        </section>

        {/* Filter and Search Bar */}
        <section className="bg-white p-4 rounded-lg border border-slate-200 shadow-xs mb-6">
          <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3.5">
            {/* Search Input */}
            <div className="relative flex-1">
              <Search
                size={16}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
              />
              <input
                type="text"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Search treatment #, patient name, phone, diagnosis..."
                className="w-full text-xs pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
              />
            </div>

            {/* Status Filter Tabs */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 md:pb-0">
              {[
                { id: "ALL", label: "All Treatments" },
                { id: "IN_PROGRESS", label: "In Progress" },
                { id: "PLANNED", label: "Planned" },
                { id: "COMPLETED", label: "Completed" },
                { id: "CANCELLED", label: "Cancelled" },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setSelectedStatus(tab.id)}
                  className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors whitespace-nowrap ${
                    selectedStatus === tab.id
                      ? "bg-teal-700 text-white shadow-2xs"
                      : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>
        </section>

        {/* Treatments Directory Table */}
        <section className="bg-white rounded-lg border border-slate-200 shadow-xs overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
            <h2 className="text-sm font-bold text-slate-800">
              Treatments Directory ({treatments.length})
            </h2>
            <div className="text-xs text-slate-400">
              Showing {treatments.length} record{treatments.length !== 1 ? "s" : ""}
            </div>
          </div>

          {treatmentsQuery.isLoading ? (
            <div className="p-6 space-y-4">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : treatments.length === 0 ? (
            <div className="py-16 text-center text-slate-500">
              <Stethoscope size={40} className="text-slate-300 mx-auto mb-3" />
              <h3 className="text-sm font-semibold text-slate-800">No treatments found</h3>
              <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
                {searchTerm || selectedStatus !== "ALL"
                  ? "No records match the active search or filter criteria. Try clearing filters."
                  : "No treatment records have been created yet. Start a clinical record from an appointment or directly."}
              </p>
              <div className="mt-4 flex items-center justify-center gap-3">
                {searchTerm || selectedStatus !== "ALL" ? (
                  <button
                    onClick={() => {
                      setSearchTerm("");
                      setSelectedStatus("ALL");
                    }}
                    className="text-xs font-semibold text-teal-700 hover:underline"
                  >
                    Clear all filters
                  </button>
                ) : (
                  <Link
                    href="/treatments/new"
                    className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-teal-700 hover:bg-teal-800 text-white font-semibold text-xs rounded-md shadow-2xs"
                  >
                    <Plus size={13} /> Start First Treatment
                  </Link>
                )}
              </div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider text-[11px]">
                    <th className="py-3 px-4">Treatment #</th>
                    <th className="py-3 px-4">Patient</th>
                    <th className="py-3 px-4">Clinician</th>
                    <th className="py-3 px-4">Clinical Diagnosis</th>
                    <th className="py-3 px-4 text-center">Procedures</th>
                    <th className="py-3 px-4 text-right">Cost (₹)</th>
                    <th className="py-3 px-4 text-center">Status</th>
                    <th className="py-3 px-4">Date</th>
                    <th className="py-3 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {treatments.map((t) => (
                    <tr key={t.id} className="hover:bg-slate-50/80 transition-colors">
                      {/* Treatment # */}
                      <td className="py-3.5 px-4 font-mono font-semibold text-teal-700">
                        <Link href={`/treatments/${t.id}`} className="hover:underline">
                          {t.treatment_number}
                        </Link>
                        {t.is_override && (
                          <span
                            className="ml-1.5 text-[9px] font-bold px-1.5 py-0.2 bg-purple-50 text-purple-700 border border-purple-200 rounded uppercase"
                            title="Administrative Override"
                          >
                            Override
                          </span>
                        )}
                      </td>

                      {/* Patient */}
                      <td className="py-3.5 px-4">
                        <div className="font-semibold text-slate-900 flex items-center gap-1">
                          <Link
                            href={`/patients/${t.patient_id}`}
                            className="hover:text-teal-700 hover:underline"
                          >
                            {t.patient_name || "Unknown Patient"}
                          </Link>
                        </div>
                        <div className="text-[11px] text-slate-400 font-mono">
                          {t.patient_number} · {t.patient_phone}
                        </div>
                      </td>

                      {/* Clinician */}
                      <td className="py-3.5 px-4 text-slate-700 font-medium">
                        Dr. {t.dentist_name || "Unassigned"}
                      </td>

                      {/* Diagnosis */}
                      <td className="py-3.5 px-4 max-w-xs truncate text-slate-800">
                        <span title={t.diagnosis}>{t.diagnosis}</span>
                      </td>

                      {/* Procedures Count */}
                      <td className="py-3.5 px-4 text-center">
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-700">
                          {t.procedures_count} proc{t.procedures_count !== 1 ? "s" : ""}
                        </span>
                      </td>

                      {/* Total Cost */}
                      <td className="py-3.5 px-4 text-right font-mono font-semibold text-slate-900">
                        ₹{t.total_cost.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                      </td>

                      {/* Status */}
                      <td className="py-3.5 px-4 text-center">{getStatusBadge(t.status)}</td>

                      {/* Date */}
                      <td className="py-3.5 px-4 text-slate-500 whitespace-nowrap">
                        {new Date(t.created_at).toLocaleDateString()}
                      </td>

                      {/* Actions */}
                      <td className="py-3.5 px-4 text-right whitespace-nowrap">
                        <div className="inline-flex items-center gap-2">
                          <Link
                            href={`/treatments/${t.id}`}
                            className="px-2.5 py-1 text-xs font-semibold text-teal-700 hover:text-teal-800 bg-teal-50 hover:bg-teal-100 rounded transition-colors"
                          >
                            View
                          </Link>
                          {t.status !== "COMPLETED" && (
                            <Link
                              href={`/treatments/${t.id}/edit`}
                              className="px-2 py-1 text-xs font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded transition-colors"
                            >
                              Edit
                            </Link>
                          )}
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
