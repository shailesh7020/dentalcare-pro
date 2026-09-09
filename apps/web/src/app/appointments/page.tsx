"use client";

import { Suspense, useMemo, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  Calendar as CalendarIcon,
  CheckCircle2,
  Clock,
  Filter,
  Layers,
  Plus,
  RefreshCw,
  Search,
  Stethoscope,
  User,
  UserCheck,
  Users,
  XCircle,
} from "lucide-react";
import { api } from "@/lib/api";
import { useAuthSession } from "../auth-session";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { BookingModal } from "@/components/appointments/booking-modal";
import { AppointmentDetailDialog } from "@/components/appointments/appointment-detail-dialog";
import { CalendarView } from "./calendar/calendar-view";
import { QueueView } from "./queue/queue-view";
import {
  Appointment,
  AppointmentStatus,
  Chair,
  DashboardStats,
  Dentist,
  VisitType,
} from "./types";

function AppointmentsContent() {
  const { state } = useAuthSession();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();

  // Tab selection: 'calendar' | 'queue' | 'directory'
  const initialTab = (searchParams.get("tab") as "calendar" | "queue" | "directory") || "calendar";
  const [activeTab, setActiveTab] = useState<"calendar" | "queue" | "directory">(initialTab);

  // Booking Modal State
  const initialBook = searchParams.get("book") === "true";
  const [isBookingOpen, setIsBookingOpen] = useState(initialBook);
  const [bookingPrefill, setBookingPrefill] = useState<{
    date?: string;
    time?: string;
    chairId?: string;
  }>({});

  // Detail Modal State
  const [selectedAppointment, setSelectedAppointment] = useState<Appointment | null>(null);

  // Directory Table Filters
  const [dirSearch, setDirSearch] = useState("");
  const [dirStatus, setDirStatus] = useState<string>("ALL");
  const [dirDentistId, setDirDentistId] = useState<string>("ALL");
  const [dirChairId, setDirChairId] = useState<string>("ALL");
  const [dirDate, setDirDate] = useState<string>("");

  // Live Practice Dashboard Stats
  const todayStr = useMemo(() => new Date().toISOString().split("T")[0], []);
  const statsQuery = useQuery({
    queryKey: ["dashboard-stats", todayStr],
    queryFn: async () => {
      const res = await api.get<DashboardStats>("/appointments/dashboard/stats", {
        params: { target_date: todayStr },
      });
      return res.data;
    },
    refetchInterval: 30000,
  });

  // Clinicians and Chairs queries for directory dropdowns
  const dentistsQuery = useQuery({
    queryKey: ["dentists"],
    queryFn: async () => {
      const res = await api.get<Dentist[]>("/dentists");
      return res.data;
    },
  });

  const chairsQuery = useQuery({
    queryKey: ["chairs"],
    queryFn: async () => {
      const res = await api.get<Chair[]>("/chairs");
      return res.data;
    },
  });

  // Directory List Query
  const directoryQuery = useQuery({
    queryKey: [
      "appointments",
      {
        search: dirSearch,
        status: dirStatus,
        dentist_id: dirDentistId,
        chair_id: dirChairId,
        date: dirDate,
      },
    ],
    queryFn: async () => {
      const params: Record<string, string | number> = {
        limit: 100,
        skip: 0,
      };
      if (dirSearch) params.search = dirSearch;
      if (dirStatus !== "ALL") params.status = dirStatus;
      if (dirDentistId !== "ALL") params.dentist_id = dirDentistId;
      if (dirChairId !== "ALL") params.chair_id = dirChairId;
      if (dirDate) params.date = dirDate;

      const res = await api.get<Appointment[]>("/appointments", { params });
      return res.data;
    },
    enabled: activeTab === "directory",
  });

  const handleOpenBooking = (opts?: { date?: string; time?: string; chairId?: string }) => {
    setBookingPrefill(opts ?? {});
    setIsBookingOpen(true);
  };

  const invalidateAll = () => {
    void queryClient.invalidateQueries({ queryKey: ["appointments"] });
    void queryClient.invalidateQueries({ queryKey: ["calendar-day"] });
    void queryClient.invalidateQueries({ queryKey: ["calendar-week"] });
    void queryClient.invalidateQueries({ queryKey: ["calendar-month"] });
    void queryClient.invalidateQueries({ queryKey: ["appointment-queue"] });
    void queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });
  };

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

  const stats = statsQuery.data;
  const dentists = dentistsQuery.data ?? [];
  const chairs = chairsQuery.data ?? [];

  return (
    <main className="min-h-screen bg-slate-50/60 pb-16">
      {/* Top Container */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8">
        {/* Breadcrumb & Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-slate-200">
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-semibold uppercase tracking-wider text-teal-700 bg-teal-50 px-2 py-0.5 rounded">
                Phase 3: Real-Time Scheduling
              </span>
              <span className="text-xs text-slate-400">·</span>
              <span className="text-xs font-medium text-slate-500">Multi-Operatory Engine</span>
            </div>
            <h1 className="text-2xl font-bold text-slate-900 mt-1.5 flex items-center gap-2">
              <CalendarIcon size={24} className="text-teal-700" /> Appointments & Calendar
            </h1>
            <p className="text-sm text-slate-500 mt-0.5">
              Operatory scheduling, double-booking prevention, real-time lobby tracker, and clinician calendars.
            </p>
          </div>

          <div className="flex items-center gap-3 flex-wrap">
            <Link
              href="/patients"
              className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 font-semibold text-xs rounded-lg shadow-2xs transition-colors"
            >
              <Users size={14} /> Patient Directory
            </Link>
            <button
              onClick={() => handleOpenBooking()}
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-teal-700 hover:bg-teal-800 text-white font-semibold text-xs rounded-lg shadow-2xs transition-colors"
            >
              <Plus size={15} /> Book Appointment
            </button>
          </div>
        </div>

        {/* Live Practice Operational Metrics Bar */}
        <section className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5 my-6">
          <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-2xs">
            <p className="text-xs font-medium text-slate-500">Today&apos;s Total</p>
            <strong className="text-xl font-bold text-slate-900 block mt-1">
              {stats?.total_appointments ?? "–"}
            </strong>
            <span className="text-[11px] text-slate-400">Scheduled visits</span>
          </div>

          <div className="bg-white p-4 rounded-xl border border-amber-200/80 shadow-2xs bg-amber-50/20">
            <p className="text-xs font-medium text-amber-800 flex items-center gap-1">
              <UserCheck size={12} className="text-amber-600" /> In Lobby
            </p>
            <strong className="text-xl font-bold text-amber-900 block mt-1">
              {stats?.waiting ?? "–"}
            </strong>
            <span className="text-[11px] text-amber-700 font-medium">Checked in</span>
          </div>

          <div className="bg-white p-4 rounded-xl border border-purple-200/80 shadow-2xs bg-purple-50/20">
            <p className="text-xs font-medium text-purple-800 flex items-center gap-1">
              <Layers size={12} className="text-purple-600" /> In Treatment
            </p>
            <strong className="text-xl font-bold text-purple-900 block mt-1">
              {stats?.in_treatment ?? "–"}
            </strong>
            <span className="text-[11px] text-purple-700 font-medium">Active in chair</span>
          </div>

          <div className="bg-white p-4 rounded-xl border border-emerald-200/80 shadow-2xs bg-emerald-50/20">
            <p className="text-xs font-medium text-emerald-800 flex items-center gap-1">
              <CheckCircle2 size={12} className="text-emerald-600" /> Completed
            </p>
            <strong className="text-xl font-bold text-emerald-900 block mt-1">
              {stats?.completed ?? "–"}
            </strong>
            <span className="text-[11px] text-emerald-700 font-medium">Done today</span>
          </div>

          <div className="bg-white p-4 rounded-xl border border-rose-200/80 shadow-2xs bg-rose-50/20">
            <p className="text-xs font-medium text-rose-800 flex items-center gap-1">
              <XCircle size={12} className="text-rose-600" /> Cancelled
            </p>
            <strong className="text-xl font-bold text-rose-900 block mt-1">
              {stats?.cancelled ?? "–"}
            </strong>
            <span className="text-[11px] text-rose-700 font-medium">No-show / cancelled</span>
          </div>

          <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-2xs">
            <p className="text-xs font-medium text-slate-500 flex items-center gap-1">
              <Clock size={12} className="text-slate-400" /> Follow-ups Due
            </p>
            <strong className="text-xl font-bold text-slate-900 block mt-1">
              {stats?.upcoming_follow_ups ?? "0"}
            </strong>
            <span className="text-[11px] text-slate-400">Next 7 days</span>
          </div>
        </section>

        {/* View Switcher Tabs */}
        <div className="flex border-b border-slate-200 mb-6 bg-white p-1 rounded-t-xl">
          <button
            onClick={() => setActiveTab("calendar")}
            className={`flex items-center gap-2 px-5 py-2.5 text-xs font-bold rounded-lg transition-all ${
              activeTab === "calendar"
                ? "bg-teal-700 text-white shadow-2xs"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
            }`}
          >
            <CalendarIcon size={15} /> Calendar Schedule
          </button>
          <button
            onClick={() => setActiveTab("queue")}
            className={`flex items-center gap-2 px-5 py-2.5 text-xs font-bold rounded-lg transition-all ${
              activeTab === "queue"
                ? "bg-teal-700 text-white shadow-2xs"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
            }`}
          >
            <Users size={15} /> Reception Lobby Queue
            {stats && stats.waiting > 0 && (
              <span className="ml-1 bg-amber-500 text-white text-[10px] px-1.5 py-0.2 rounded-full font-mono">
                {stats.waiting}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab("directory")}
            className={`flex items-center gap-2 px-5 py-2.5 text-xs font-bold rounded-lg transition-all ${
              activeTab === "directory"
                ? "bg-teal-700 text-white shadow-2xs"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
            }`}
          >
            <Clock size={15} /> All Appointments Directory
          </button>
        </div>

        {/* Tab 1: Calendar Schedule */}
        {activeTab === "calendar" && (
          <CalendarView
            onSelectAppointment={(apt) => setSelectedAppointment(apt)}
            onNewBooking={(opts) => handleOpenBooking(opts)}
          />
        )}

        {/* Tab 2: Reception Lobby Queue */}
        {activeTab === "queue" && (
          <QueueView
            onSelectAppointment={(apt) => setSelectedAppointment(apt)}
            onNewBooking={(opts) => handleOpenBooking(opts)}
          />
        )}

        {/* Tab 3: Appointments Directory Table */}
        {activeTab === "directory" && (
          <div className="space-y-4">
            {/* Filter controls */}
            <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-wrap items-center gap-3">
              {/* Search input */}
              <div className="flex-1 min-w-[220px] relative">
                <Search
                  size={14}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
                />
                <input
                  type="text"
                  value={dirSearch}
                  onChange={(e) => setDirSearch(e.target.value)}
                  placeholder="Search patient name, phone, or appointment #..."
                  className="w-full pl-9 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-800 placeholder-slate-400 focus:outline-teal-600"
                />
              </div>

              {/* Status Filter */}
              <select
                value={dirStatus}
                onChange={(e) => setDirStatus(e.target.value)}
                className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-700 focus:outline-teal-600"
                aria-label="Filter directory by status"
              >
                <option value="ALL">All Statuses</option>
                <option value="SCHEDULED">Scheduled</option>
                <option value="CONFIRMED">Confirmed</option>
                <option value="CHECKED_IN">Checked In</option>
                <option value="IN_CHAIR">In Treatment</option>
                <option value="COMPLETED">Completed</option>
                <option value="CANCELLED">Cancelled</option>
                <option value="NO_SHOW">No Show</option>
              </select>

              {/* Date Filter */}
              <input
                type="date"
                value={dirDate}
                onChange={(e) => setDirDate(e.target.value)}
                className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-700 focus:outline-teal-600"
                aria-label="Filter directory by date"
              />

              {/* Dentist Filter */}
              <select
                value={dirDentistId}
                onChange={(e) => setDirDentistId(e.target.value)}
                className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-700 focus:outline-teal-600"
                aria-label="Filter directory by clinician"
              >
                <option value="ALL">All Clinicians</option>
                {dentists.map((d) => (
                  <option key={d.id} value={d.id}>
                    Dr. {d.first_name} {d.last_name}
                  </option>
                ))}
              </select>

              {/* Chair Filter */}
              <select
                value={dirChairId}
                onChange={(e) => setDirChairId(e.target.value)}
                className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-700 focus:outline-teal-600"
                aria-label="Filter directory by chair"
              >
                <option value="ALL">All Chairs</option>
                {chairs.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>

              {/* Reset Filter Button */}
              {(dirSearch || dirStatus !== "ALL" || dirDentistId !== "ALL" || dirChairId !== "ALL" || dirDate) && (
                <button
                  onClick={() => {
                    setDirSearch("");
                    setDirStatus("ALL");
                    setDirDentistId("ALL");
                    setDirChairId("ALL");
                    setDirDate("");
                  }}
                  className="px-3 py-1.5 text-xs text-rose-600 hover:text-rose-800 font-semibold"
                >
                  Clear Filters
                </button>
              )}
            </div>

            {/* Table */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
              {directoryQuery.isLoading ? (
                <div className="p-8 space-y-3">
                  <Skeleton className="h-10 w-full" />
                  <Skeleton className="h-10 w-full" />
                  <Skeleton className="h-10 w-full" />
                </div>
              ) : (directoryQuery.data?.length ?? 0) === 0 ? (
                <div className="p-12 text-center text-slate-500 text-sm">
                  <Clock size={28} className="mx-auto mb-2 text-slate-300" />
                  No appointments found matching your search and filter criteria.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-200">
                      <tr>
                        <th className="py-3 px-4">Appointment #</th>
                        <th className="py-3 px-4">Date & Time</th>
                        <th className="py-3 px-4">Patient</th>
                        <th className="py-3 px-4">Clinician</th>
                        <th className="py-3 px-4">Operatory</th>
                        <th className="py-3 px-4">Visit Type</th>
                        <th className="py-3 px-4">Status</th>
                        <th className="py-3 px-4 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {directoryQuery.data?.map((apt) => (
                        <tr
                          key={apt.id}
                          className="hover:bg-slate-50/70 transition-colors cursor-pointer"
                          onClick={() => setSelectedAppointment(apt)}
                        >
                          <td className="py-3 px-4 font-mono font-semibold text-slate-900">
                            {apt.appointment_number}
                            {apt.is_emergency_override && (
                              <span className="ml-1.5 inline-block text-[10px] text-rose-700 font-bold bg-rose-50 px-1 py-0.5 rounded border border-rose-200">
                                Override
                              </span>
                            )}
                          </td>
                          <td className="py-3 px-4">
                            <div className="font-semibold text-slate-900">{apt.date}</div>
                            <div className="text-[11px] text-slate-500 font-mono">
                              {apt.start_time.slice(0, 5)} - {apt.end_time.slice(0, 5)} (
                              {apt.duration}m)
                            </div>
                          </td>
                          <td className="py-3 px-4">
                            <div className="font-bold text-slate-900">
                              {apt.patient_name || "Patient"}
                            </div>
                            <div className="text-[11px] text-slate-500 font-mono">
                              {apt.patient_number} · {apt.patient_phone || "No phone"}
                            </div>
                          </td>
                          <td className="py-3 px-4 font-medium text-slate-800">
                            {apt.dentist_name ? `Dr. ${apt.dentist_name}` : "Not assigned"}
                          </td>
                          <td className="py-3 px-4 text-slate-700">
                            {apt.chair_name || "Chair"}
                          </td>
                          <td className="py-3 px-4">
                            <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                              {apt.visit_type}
                            </span>
                          </td>
                          <td className="py-3 px-4">
                            <span
                              className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded border ${
                                apt.status === "COMPLETED"
                                  ? "bg-emerald-50 text-emerald-800 border-emerald-200"
                                  : apt.status === "IN_CHAIR"
                                  ? "bg-purple-50 text-purple-800 border-purple-200"
                                  : apt.status === "CHECKED_IN"
                                  ? "bg-amber-50 text-amber-800 border-amber-200"
                                  : apt.status === "CANCELLED"
                                  ? "bg-rose-50 text-rose-800 border-rose-200"
                                  : "bg-sky-50 text-sky-800 border-sky-200"
                              }`}
                            >
                              {apt.status}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-right">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedAppointment(apt);
                              }}
                              className="px-2.5 py-1 bg-white hover:bg-slate-50 border border-slate-200 rounded text-xs font-semibold text-teal-700 transition-colors shadow-2xs"
                            >
                              Manage →
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Booking Modal */}
      <BookingModal
        isOpen={isBookingOpen}
        onClose={() => setIsBookingOpen(false)}
        initialDate={bookingPrefill.date}
        initialTime={bookingPrefill.time}
        initialChairId={bookingPrefill.chairId}
        onSuccess={() => {
          setIsBookingOpen(false);
          invalidateAll();
        }}
      />

      {/* Detail & Quick Actions Dialog */}
      <AppointmentDetailDialog
        appointment={selectedAppointment}
        isOpen={!!selectedAppointment}
        onClose={() => setSelectedAppointment(null)}
        onUpdated={() => {
          setSelectedAppointment(null);
          invalidateAll();
        }}
      />
    </main>
  );
}

export default function AppointmentsPage() {
  return (
    <Suspense
      fallback={
        <div className="p-12 text-center text-slate-500 text-sm">
          Loading appointments...
        </div>
      }
    >
      <AppointmentsContent />
    </Suspense>
  );
}
