"use client";

import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Archive,
  ArrowUpDown,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Edit2,
  Eye,
  RotateCcw,
  Search,
  UserPlus,
  Users,
  X,
} from "lucide-react";
import { useState } from "react";

import { api } from "@/lib/api";
import { useAuthSession } from "../auth-session";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Dialog } from "@/components/ui/dialog";

type Patient = {
  id: string;
  clinic_id: string;
  patient_number: string;
  first_name: string;
  middle_name: string | null;
  last_name: string;
  gender: string;
  date_of_birth: string;
  age: number;
  mobile_number: string;
  email: string | null;
  city: string | null;
  blood_group: string | null;
  photo_url: string | null;
  status: "ACTIVE" | "ARCHIVED";
  created_at: string;
  deleted_at: string | null;
};

type PatientList = {
  items: Patient[];
  total: number;
  skip: number;
  limit: number;
};

export default function PatientsPage() {
  const { state } = useAuthSession();
  const queryClient = useQueryClient();

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<"active" | "archived" | "all">("active");
  const [genderFilter, setGenderFilter] = useState<string>("");
  const [bloodGroupFilter, setBloodGroupFilter] = useState<string>("");
  const [sortField, setSortField] = useState<string>("created_at");
  const [descending, setDescending] = useState<boolean>(true);
  const [page, setPage] = useState<number>(0);
  const pageSize = 20;

  const [selectedPatientForArchive, setSelectedPatientForArchive] = useState<Patient | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: [
      "patients",
      search,
      statusFilter,
      genderFilter,
      bloodGroupFilter,
      sortField,
      descending,
      page,
    ],
    enabled: state === "authenticated",
    queryFn: async () => {
      const params: Record<string, unknown> = {
        search: search.trim() || undefined,
        status: statusFilter,
        gender: genderFilter || undefined,
        blood_group: bloodGroupFilter || undefined,
        sort: sortField,
        descending,
        skip: page * pageSize,
        limit: pageSize,
      };
      const res = await api.get<PatientList>("/patients", { params });
      return res.data;
    },
  });

  const archiveMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/patients/${id}`);
    },
    onSuccess: () => {
      setSelectedPatientForArchive(null);
      showToast("Patient record successfully archived.");
      void queryClient.invalidateQueries({ queryKey: ["patients"] });
    },
  });

  const restoreMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.post(`/patients/${id}/restore`);
    },
    onSuccess: () => {
      showToast("Patient record successfully restored.");
      void queryClient.invalidateQueries({ queryKey: ["patients"] });
    },
  });

  function showToast(msg: string) {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 4000);
  }

  function handleSort(field: string) {
    if (sortField === field) {
      setDescending((prev) => !prev);
    } else {
      setSortField(field);
      setDescending(true);
    }
    setPage(0);
  }

  function clearFilters() {
    setSearch("");
    setStatusFilter("active");
    setGenderFilter("");
    setBloodGroupFilter("");
    setPage(0);
  }

  if (state === "loading") {
    return (
      <main className="session-loading">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-3 border-teal-600 border-t-transparent rounded-full animate-spin" />
          <p className="text-slate-600 text-sm font-medium">Verifying clinic session...</p>
        </div>
      </main>
    );
  }

  const total = data?.total ?? 0;
  const startIdx = page * pageSize + 1;
  const endIdx = Math.min((page + 1) * pageSize, total);

  return (
    <main className="min-h-screen bg-slate-50/60 pb-16">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed top-6 right-6 z-50 flex items-center gap-2.5 px-4 py-3 bg-emerald-900 text-emerald-50 rounded-lg shadow-lg border border-emerald-700 animate-in slide-in-from-top duration-300">
          <CheckCircle2 size={18} className="text-emerald-400" />
          <span className="text-sm font-medium">{toastMessage}</span>
        </div>
      )}

      {/* Main Container */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8">
        {/* Breadcrumb & Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-slate-200">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-teal-700 bg-teal-50 px-2 py-0.5 rounded">
              Patient Management Module
            </span>
            <h1 className="text-2xl font-bold text-slate-900 mt-1.5 flex items-center gap-2">
              <Users size={24} className="text-teal-700" /> Clinic Patients
            </h1>
            <p className="text-sm text-slate-500 mt-0.5">
              Comprehensive electronic health records, clinical histories, and patient directory.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/patients/new"
              className="inline-flex items-center gap-2 bg-teal-700 hover:bg-teal-800 text-white font-semibold text-xs px-4 py-2.5 rounded-md shadow-sm transition-colors"
            >
              <UserPlus size={16} /> Register Patient
            </Link>
          </div>
        </div>

        {/* Search and Filters Bar */}
        <section className="bg-white p-4 rounded-lg border border-slate-200 shadow-xs mt-6 mb-4">
          <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-3">
            {/* Search Input */}
            <div className="relative flex-1 max-w-md">
              <Search
                size={16}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
              />
              <input
                type="text"
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(0);
                }}
                placeholder="Search patient name, number, mobile, email..."
                className="w-full pl-9 pr-8 py-2 text-xs bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600 focus:border-teal-600 text-slate-900"
              />
              {search && (
                <button
                  onClick={() => {
                    setSearch("");
                    setPage(0);
                  }}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  <X size={14} />
                </button>
              )}
            </div>

            {/* Filter Selects */}
            <div className="flex flex-wrap items-center gap-2">
              <select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value as "active" | "archived" | "all");
                  setPage(0);
                }}
                className="text-xs bg-slate-50 border border-slate-200 rounded-md px-2.5 py-2 text-slate-700 focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
              >
                <option value="active">Active Only</option>
                <option value="archived">Archived Records</option>
                <option value="all">All Statuses</option>
              </select>

              <select
                value={genderFilter}
                onChange={(e) => {
                  setGenderFilter(e.target.value);
                  setPage(0);
                }}
                className="text-xs bg-slate-50 border border-slate-200 rounded-md px-2.5 py-2 text-slate-700 focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
              >
                <option value="">All Genders</option>
                <option value="FEMALE">Female</option>
                <option value="MALE">Male</option>
                <option value="NON_BINARY">Non-Binary</option>
                <option value="PREFER_NOT_TO_SAY">Prefer not to say</option>
              </select>

              <select
                value={bloodGroupFilter}
                onChange={(e) => {
                  setBloodGroupFilter(e.target.value);
                  setPage(0);
                }}
                className="text-xs bg-slate-50 border border-slate-200 rounded-md px-2.5 py-2 text-slate-700 focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
              >
                <option value="">All Blood Groups</option>
                <option value="A+">A+</option>
                <option value="A-">A-</option>
                <option value="B+">B+</option>
                <option value="B-">B-</option>
                <option value="AB+">AB+</option>
                <option value="AB-">AB-</option>
                <option value="O+">O+</option>
                <option value="O-">O-</option>
              </select>

              {(search || statusFilter !== "active" || genderFilter || bloodGroupFilter) && (
                <button
                  onClick={clearFilters}
                  className="text-xs text-slate-500 hover:text-slate-800 underline px-2 py-1"
                >
                  Clear filters
                </button>
              )}
            </div>
          </div>
        </section>

        {/* Patient Table */}
        <div className="bg-white rounded-lg border border-slate-200 shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50/80 border-b border-slate-200 text-xs font-semibold text-slate-600">
                  <th className="py-3 px-4">
                    <button
                      onClick={() => handleSort("patient_number")}
                      className="flex items-center gap-1.5 hover:text-teal-700"
                    >
                      Patient Number <ArrowUpDown size={12} />
                    </button>
                  </th>
                  <th className="py-3 px-4">
                    <button
                      onClick={() => handleSort("name")}
                      className="flex items-center gap-1.5 hover:text-teal-700"
                    >
                      Patient Name <ArrowUpDown size={12} />
                    </button>
                  </th>
                  <th className="py-3 px-4">
                    <button
                      onClick={() => handleSort("mobile_number")}
                      className="flex items-center gap-1.5 hover:text-teal-700"
                    >
                      Mobile <ArrowUpDown size={12} />
                    </button>
                  </th>
                  <th className="py-3 px-4">
                    <button
                      onClick={() => handleSort("date_of_birth")}
                      className="flex items-center gap-1.5 hover:text-teal-700"
                    >
                      Age / Gender <ArrowUpDown size={12} />
                    </button>
                  </th>
                  <th className="py-3 px-4">Blood Group</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs text-slate-700">
                {isLoading ? (
                  Array.from({ length: 6 }).map((_, i) => (
                    <tr key={i}>
                      <td className="py-3.5 px-4"><Skeleton className="h-4 w-28" /></td>
                      <td className="py-3.5 px-4"><Skeleton className="h-4 w-36" /></td>
                      <td className="py-3.5 px-4"><Skeleton className="h-4 w-24" /></td>
                      <td className="py-3.5 px-4"><Skeleton className="h-4 w-20" /></td>
                      <td className="py-3.5 px-4"><Skeleton className="h-4 w-12" /></td>
                      <td className="py-3.5 px-4"><Skeleton className="h-4 w-16" /></td>
                      <td className="py-3.5 px-4 text-right"><Skeleton className="h-4 w-24 ml-auto" /></td>
                    </tr>
                  ))
                ) : isError ? (
                  <tr>
                    <td colSpan={7} className="py-12 text-center text-rose-600">
                      <p className="font-semibold">Unable to fetch patient records.</p>
                      <button
                        onClick={() => void refetch()}
                        className="mt-2 text-xs text-teal-700 underline"
                      >
                        Try again
                      </button>
                    </td>
                  </tr>
                ) : data && data.items.length > 0 ? (
                  data.items.map((patient) => {
                    const fullName = [
                      patient.first_name,
                      patient.middle_name,
                      patient.last_name,
                    ]
                      .filter(Boolean)
                      .join(" ");

                    const isArchived = Boolean(patient.deleted_at);

                    return (
                      <tr
                        key={patient.id}
                        className="hover:bg-slate-50/70 transition-colors"
                      >
                        <td className="py-3.5 px-4 font-mono font-medium text-teal-700">
                          <Link
                            href={`/patients/${patient.id}`}
                            className="hover:underline flex items-center gap-1.5"
                          >
                            {patient.patient_number}
                          </Link>
                        </td>
                        <td className="py-3.5 px-4 font-medium text-slate-900">
                          <Link href={`/patients/${patient.id}`} className="hover:underline">
                            {fullName}
                          </Link>
                          {patient.email && (
                            <span className="block text-[11px] text-slate-400 font-normal">
                              {patient.email}
                            </span>
                          )}
                        </td>
                        <td className="py-3.5 px-4 font-mono">{patient.mobile_number}</td>
                        <td className="py-3.5 px-4">
                          <span>{patient.age} yrs</span>
                          <span className="text-slate-400 mx-1">·</span>
                          <span className="capitalize">
                            {patient.gender.toLowerCase().replaceAll("_", " ")}
                          </span>
                        </td>
                        <td className="py-3.5 px-4">
                          {patient.blood_group ? (
                            <Badge variant="secondary">{patient.blood_group}</Badge>
                          ) : (
                            <span className="text-slate-400">—</span>
                          )}
                        </td>
                        <td className="py-3.5 px-4">
                          {isArchived ? (
                            <Badge variant="archived">Archived</Badge>
                          ) : (
                            <Badge variant="active">Active</Badge>
                          )}
                        </td>
                        <td className="py-3.5 px-4 text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            <Link
                              href={`/patients/${patient.id}`}
                              className="p-1.5 text-slate-500 hover:text-teal-700 hover:bg-slate-100 rounded"
                              title="View Patient Profile"
                            >
                              <Eye size={15} />
                            </Link>
                            {!isArchived && (
                              <Link
                                href={`/patients/${patient.id}/edit`}
                                className="p-1.5 text-slate-500 hover:text-blue-700 hover:bg-slate-100 rounded"
                                title="Edit Patient"
                              >
                                <Edit2 size={15} />
                              </Link>
                            )}
                            {isArchived ? (
                              <button
                                onClick={() => restoreMutation.mutate(patient.id)}
                                disabled={restoreMutation.isPending}
                                className="p-1.5 text-slate-500 hover:text-emerald-700 hover:bg-slate-100 rounded"
                                title="Restore Patient"
                              >
                                <RotateCcw size={15} />
                              </button>
                            ) : (
                              <button
                                onClick={() => setSelectedPatientForArchive(patient)}
                                className="p-1.5 text-slate-500 hover:text-rose-700 hover:bg-slate-100 rounded"
                                title="Archive Patient"
                              >
                                <Archive size={15} />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan={7} className="py-16 text-center text-slate-500">
                      <div className="flex flex-col items-center justify-center gap-2">
                        <Users size={32} className="text-slate-300" />
                        <p className="font-semibold text-slate-700 text-sm">
                          {search || genderFilter || bloodGroupFilter || statusFilter !== "active"
                            ? "No patients match the selected search or filters."
                            : "No patients registered yet."}
                        </p>
                        <p className="text-xs text-slate-400">
                          {search || genderFilter || bloodGroupFilter
                            ? "Try adjusting your query or resetting all filters."
                            : "Get started by registering the clinic's first patient record."}
                        </p>
                        {search || genderFilter || bloodGroupFilter ? (
                          <button
                            onClick={clearFilters}
                            className="mt-2 text-xs font-semibold text-teal-700 hover:underline"
                          >
                            Reset filters
                          </button>
                        ) : (
                          <Link
                            href="/patients/new"
                            className="mt-3 inline-flex items-center gap-1.5 bg-teal-700 hover:bg-teal-800 text-white font-medium text-xs px-3.5 py-2 rounded-md"
                          >
                            <UserPlus size={14} /> Register Patient
                          </Link>
                        )}
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Table Footer & Pagination */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 px-4 py-3 border-t border-slate-200 bg-slate-50/60 text-xs text-slate-600">
            <div>
              {total > 0 ? (
                <span>
                  Showing <strong className="text-slate-800">{startIdx}</strong> to{" "}
                  <strong className="text-slate-800">{endIdx}</strong> of{" "}
                  <strong className="text-slate-800">{total}</strong> registered patients
                </span>
              ) : (
                <span>0 records found</span>
              )}
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0 || isLoading}
                className="inline-flex items-center gap-1 px-3 py-1.5 bg-white border border-slate-200 rounded text-slate-700 font-medium hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronLeft size={14} /> Previous
              </button>
              <span className="font-medium text-slate-700 px-1">
                Page {page + 1} of {Math.max(1, Math.ceil(total / pageSize))}
              </span>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={(page + 1) * pageSize >= total || isLoading}
                className="inline-flex items-center gap-1 px-3 py-1.5 bg-white border border-slate-200 rounded text-slate-700 font-medium hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next <ChevronRight size={14} />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Archive Confirmation Dialog */}
      <Dialog
        open={Boolean(selectedPatientForArchive)}
        onOpenChange={(open) => !open && setSelectedPatientForArchive(null)}
        title="Archive Patient Record"
        description="Are you sure you want to archive this patient?"
      >
        <div className="space-y-4 text-xs text-slate-600">
          <p>
            Archiving will soft-delete{" "}
            <strong className="text-slate-900">
              {selectedPatientForArchive?.first_name} {selectedPatientForArchive?.last_name}
            </strong>{" "}
            ({selectedPatientForArchive?.patient_number}). The record remains stored and can be restored
            at any time from the archived view.
          </p>
          <div className="flex items-center justify-end gap-2.5 pt-2">
            <button
              onClick={() => setSelectedPatientForArchive(null)}
              className="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium rounded-md"
            >
              Cancel
            </button>
            <button
              onClick={() => {
                if (selectedPatientForArchive) {
                  archiveMutation.mutate(selectedPatientForArchive.id);
                }
              }}
              disabled={archiveMutation.isPending}
              className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white font-medium rounded-md shadow-xs disabled:opacity-50"
            >
              {archiveMutation.isPending ? "Archiving..." : "Confirm Archive"}
            </button>
          </div>
        </div>
      </Dialog>
    </main>
  );
}
