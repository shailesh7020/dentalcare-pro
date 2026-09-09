"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertCircle,
  Calendar,
  CheckCircle2,
  Clock,
  ExternalLink,
  Layers,
  Phone,
  Play,
  RefreshCw,
  Sparkles,
  Stethoscope,
  User,
  UserCheck,
  Users,
} from "lucide-react";
import { api } from "@/lib/api";
import { Appointment, AppointmentQueueItem, AppointmentStatus, VisitType } from "../types";

interface QueueViewProps {
  onSelectAppointment: (appointment: Appointment) => void;
  onNewBooking: (opts: { date?: string }) => void;
}

export function QueueView({ onSelectAppointment, onNewBooking }: QueueViewProps) {
  const queryClient = useQueryClient();
  const [selectedDate, setSelectedDate] = useState<string>(
    new Date().toISOString().split("T")[0]
  );
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [actionError, setActionError] = useState<string | null>(null);

  // Queue query
  const queueQuery = useQuery({
    queryKey: ["appointment-queue", selectedDate],
    queryFn: async () => {
      const res = await api.get<AppointmentQueueItem[]>("/appointments/queue", {
        params: { target_date: selectedDate },
      });
      return res.data;
    },
    refetchInterval: autoRefresh ? 15000 : false,
  });

  const invalidateAll = () => {
    void queryClient.invalidateQueries({ queryKey: ["appointment-queue"] });
    void queryClient.invalidateQueries({ queryKey: ["calendar-day"] });
    void queryClient.invalidateQueries({ queryKey: ["calendar-week"] });
    void queryClient.invalidateQueries({ queryKey: ["calendar-month"] });
    void queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });
    void queryClient.invalidateQueries({ queryKey: ["appointments"] });
  };

  // State transitions mutations
  const checkinMutation = useMutation({
    mutationFn: async (appointmentId: string) => {
      setActionError(null);
      const res = await api.post(`/appointments/${appointmentId}/checkin`);
      return res.data;
    },
    onSuccess: () => invalidateAll(),
    onError: (err: any) => {
      setActionError(err.response?.data?.detail || "Failed to check in patient.");
    },
  });

  const startMutation = useMutation({
    mutationFn: async (appointmentId: string) => {
      setActionError(null);
      const res = await api.post(`/appointments/${appointmentId}/start`);
      return res.data;
    },
    onSuccess: () => invalidateAll(),
    onError: (err: any) => {
      setActionError(err.response?.data?.detail || "Failed to start treatment.");
    },
  });

  const completeMutation = useMutation({
    mutationFn: async (appointmentId: string) => {
      setActionError(null);
      const res = await api.post(`/appointments/${appointmentId}/complete`);
      return res.data;
    },
    onSuccess: () => invalidateAll(),
    onError: (err: any) => {
      setActionError(err.response?.data?.detail || "Failed to complete appointment.");
    },
  });

  const queueItems = queueQuery.data ?? [];

  // Group queue items by stages
  const waitingItems = queueItems.filter((i) => i.status === "CHECKED_IN");
  const inTreatmentItems = queueItems.filter((i) => i.status === "IN_CHAIR");
  const scheduledItems = queueItems.filter(
    (i) => i.status === "SCHEDULED" || i.status === "CONFIRMED"
  );
  const completedItems = queueItems.filter((i) => i.status === "COMPLETED");

  const convertQueueToAppointment = (item: AppointmentQueueItem): Appointment => {
    return {
      id: item.id,
      clinic_id: "",
      patient_id: item.patient_id,
      dentist_id: item.dentist_id,
      chair_id: item.chair_id,
      appointment_number: item.appointment_number,
      date: selectedDate,
      start_time: item.scheduled_time,
      end_time: "",
      duration: item.duration,
      status: item.status,
      visit_type: item.visit_type,
      priority: item.priority,
      is_emergency_override: false,
      created_at: "",
      updated_at: "",
      patient_name: item.patient_name,
      patient_number: item.patient_number,
      patient_phone: item.patient_phone,
      dentist_name: item.dentist_name,
      chair_name: item.chair_name,
    };
  };

  const getVisitBadge = (type: VisitType) => {
    switch (type) {
      case "EMERGENCY":
        return "bg-rose-100 text-rose-800 border-rose-300 font-bold";
      case "SURGERY":
        return "bg-red-50 text-red-700 border-red-200";
      case "PROCEDURE":
        return "bg-blue-50 text-blue-700 border-blue-200";
      case "CLEANING":
        return "bg-teal-50 text-teal-700 border-teal-200";
      default:
        return "bg-slate-100 text-slate-700 border-slate-200";
    }
  };

  return (
    <div className="space-y-4">
      {/* Header & Controls Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Users size={18} className="text-teal-600" />
            Live Reception & Operatory Flow
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Real-time patient lobby tracker, chair assignments, and clinical status transitions.
          </p>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          {/* Date Picker */}
          <div className="flex items-center gap-1.5 text-xs">
            <Calendar size={13} className="text-slate-400" />
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="px-2.5 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs font-medium text-slate-700 focus:outline-teal-600"
              aria-label="Filter queue by date"
            />
          </div>

          {/* Auto Refresh Toggle */}
          <label className="flex items-center gap-1.5 text-xs text-slate-600 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded border-slate-300 text-teal-600 focus:ring-teal-500"
            />
            <span>Auto-refresh (15s)</span>
          </label>

          {/* Manual Refresh Button */}
          <button
            onClick={() => void queueQuery.refetch()}
            disabled={queueQuery.isFetching}
            className="p-1.5 border border-slate-200 rounded-lg text-slate-600 hover:bg-slate-50 transition-colors"
            title="Refresh Queue"
            aria-label="Refresh Queue"
          >
            <RefreshCw
              size={15}
              className={queueQuery.isFetching ? "animate-spin text-teal-600" : ""}
            />
          </button>
        </div>
      </div>

      {/* Error alert if any action failed */}
      {actionError && (
        <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 rounded-lg text-xs flex items-center gap-2">
          <AlertCircle size={15} className="text-rose-600 shrink-0" />
          <span>{actionError}</span>
        </div>
      )}

      {/* 4-Stage Operational Columns Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        {/* Stage 1: Waiting in Lobby */}
        <div className="bg-amber-50/40 border border-amber-200 rounded-xl p-4 flex flex-col min-h-[500px]">
          <div className="flex items-center justify-between pb-3 border-b border-amber-200/80 mb-3">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500 animate-pulse" />
              <h3 className="text-xs font-bold text-amber-950 uppercase tracking-wider">
                Waiting in Lobby
              </h3>
            </div>
            <span className="text-xs font-bold bg-amber-100 text-amber-900 px-2 py-0.5 rounded-full border border-amber-300">
              {waitingItems.length}
            </span>
          </div>

          <div className="space-y-3 flex-1 overflow-y-auto">
            {waitingItems.length === 0 ? (
              <div className="h-40 flex flex-col items-center justify-center text-center text-slate-400 text-xs">
                <Users size={24} className="mb-2 text-slate-300" />
                No patients waiting in lobby
              </div>
            ) : (
              waitingItems.map((item) => (
                <div
                  key={item.id}
                  className="bg-white p-3.5 rounded-lg border border-amber-200/90 shadow-2xs hover:shadow-xs transition-all"
                >
                  <div className="flex items-start justify-between gap-2 mb-1.5">
                    <div>
                      <h4 className="font-bold text-xs text-slate-900">{item.patient_name}</h4>
                      <p className="text-[11px] font-mono text-slate-500">
                        {item.patient_number}
                      </p>
                    </div>
                    <span
                      className={`text-[9px] uppercase px-1.5 py-0.5 rounded border ${getVisitBadge(
                        item.visit_type
                      )}`}
                    >
                      {item.visit_type}
                    </span>
                  </div>

                  {/* Wait Duration Indicator */}
                  <div className="flex items-center gap-1.5 text-xs text-amber-800 bg-amber-50/80 px-2 py-1 rounded border border-amber-100 mb-2.5">
                    <Clock size={12} className="text-amber-600" />
                    <span className="font-bold font-mono">
                      {item.wait_minutes ?? 0}m wait
                    </span>
                    <span className="text-[11px] text-amber-700">
                      (Arrived {item.checked_in_at ? new Date(item.checked_in_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : "Recently"})
                    </span>
                  </div>

                  <div className="text-[11px] text-slate-600 space-y-0.5 mb-3">
                    <div className="flex items-center gap-1">
                      <Stethoscope size={11} className="text-slate-400" />
                      <span>{item.dentist_name}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Layers size={11} className="text-slate-400" />
                      <span>{item.chair_name}</span>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex items-center gap-2 pt-2 border-t border-slate-100">
                    <button
                      onClick={() => startMutation.mutate(item.id)}
                      disabled={startMutation.isPending}
                      className="flex-1 inline-flex items-center justify-center gap-1.5 px-2.5 py-1.5 bg-purple-700 hover:bg-purple-800 text-white rounded-md text-xs font-semibold shadow-2xs transition-colors disabled:opacity-50"
                    >
                      <Play size={12} /> Call In / Start
                    </button>
                    <button
                      onClick={() => onSelectAppointment(convertQueueToAppointment(item))}
                      className="p-1.5 border border-slate-200 text-slate-600 hover:bg-slate-50 rounded-md transition-colors"
                      title="View Details"
                      aria-label="View Details"
                    >
                      <ExternalLink size={13} />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Stage 2: In Treatment (In Chair) */}
        <div className="bg-purple-50/40 border border-purple-200 rounded-xl p-4 flex flex-col min-h-[500px]">
          <div className="flex items-center justify-between pb-3 border-b border-purple-200/80 mb-3">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-purple-600 animate-pulse" />
              <h3 className="text-xs font-bold text-purple-950 uppercase tracking-wider">
                In Treatment (Operatory)
              </h3>
            </div>
            <span className="text-xs font-bold bg-purple-100 text-purple-900 px-2 py-0.5 rounded-full border border-purple-300">
              {inTreatmentItems.length}
            </span>
          </div>

          <div className="space-y-3 flex-1 overflow-y-auto">
            {inTreatmentItems.length === 0 ? (
              <div className="h-40 flex flex-col items-center justify-center text-center text-slate-400 text-xs">
                <Layers size={24} className="mb-2 text-slate-300" />
                All operatories currently free
              </div>
            ) : (
              inTreatmentItems.map((item) => (
                <div
                  key={item.id}
                  className="bg-white p-3.5 rounded-lg border border-purple-200 shadow-2xs hover:shadow-xs transition-all"
                >
                  <div className="flex items-start justify-between gap-2 mb-1.5">
                    <div>
                      <h4 className="font-bold text-xs text-slate-900">{item.patient_name}</h4>
                      <p className="text-[11px] font-mono text-slate-500">
                        {item.patient_number}
                      </p>
                    </div>
                    <span
                      className={`text-[9px] uppercase px-1.5 py-0.5 rounded border ${getVisitBadge(
                        item.visit_type
                      )}`}
                    >
                      {item.visit_type}
                    </span>
                  </div>

                  <div className="p-2 bg-purple-50 rounded border border-purple-100 text-xs text-purple-900 mb-2.5 flex items-center justify-between">
                    <span className="font-bold">{item.chair_name}</span>
                    <span className="text-[11px] font-mono">
                      Started {item.treatment_started_at ? new Date(item.treatment_started_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : "Active"}
                    </span>
                  </div>

                  <div className="text-[11px] text-slate-600 space-y-0.5 mb-3">
                    <div className="flex items-center gap-1">
                      <Stethoscope size={11} className="text-slate-400" />
                      <span>{item.dentist_name}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Clock size={11} className="text-slate-400" />
                      <span>Planned duration: {item.duration} min</span>
                    </div>
                  </div>

                  {/* Complete Action Button */}
                  <div className="flex items-center gap-2 pt-2 border-t border-slate-100">
                    <button
                      onClick={() => completeMutation.mutate(item.id)}
                      disabled={completeMutation.isPending}
                      className="flex-1 inline-flex items-center justify-center gap-1.5 px-2.5 py-1.5 bg-emerald-700 hover:bg-emerald-800 text-white rounded-md text-xs font-semibold shadow-2xs transition-colors disabled:opacity-50"
                    >
                      <CheckCircle2 size={12} /> Complete Visit
                    </button>
                    <button
                      onClick={() => onSelectAppointment(convertQueueToAppointment(item))}
                      className="p-1.5 border border-slate-200 text-slate-600 hover:bg-slate-50 rounded-md transition-colors"
                      title="View Details"
                      aria-label="View Details"
                    >
                      <ExternalLink size={13} />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Stage 3: Scheduled / Expected Today */}
        <div className="bg-slate-50/80 border border-slate-200 rounded-xl p-4 flex flex-col min-h-[500px]">
          <div className="flex items-center justify-between pb-3 border-b border-slate-200 mb-3">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-sky-500" />
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                Scheduled Today
              </h3>
            </div>
            <span className="text-xs font-bold bg-slate-200 text-slate-800 px-2 py-0.5 rounded-full">
              {scheduledItems.length}
            </span>
          </div>

          <div className="space-y-3 flex-1 overflow-y-auto">
            {scheduledItems.length === 0 ? (
              <div className="h-40 flex flex-col items-center justify-center text-center text-slate-400 text-xs">
                <Calendar size={24} className="mb-2 text-slate-300" />
                No more upcoming arrivals for this date
              </div>
            ) : (
              scheduledItems.map((item) => (
                <div
                  key={item.id}
                  className="bg-white p-3.5 rounded-lg border border-slate-200 shadow-2xs hover:shadow-xs transition-all"
                >
                  <div className="flex items-start justify-between gap-2 mb-1.5">
                    <div>
                      <h4 className="font-bold text-xs text-slate-900">{item.patient_name}</h4>
                      <p className="text-[11px] font-mono text-slate-500">
                        {item.patient_number}
                      </p>
                    </div>
                    <span className="text-xs font-mono font-bold text-teal-800 bg-teal-50 px-2 py-0.5 rounded border border-teal-200">
                      {item.scheduled_time.slice(0, 5)}
                    </span>
                  </div>

                  <div className="text-[11px] text-slate-600 space-y-0.5 mb-3">
                    <div className="flex items-center gap-1">
                      <Stethoscope size={11} className="text-slate-400" />
                      <span>{item.dentist_name}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Layers size={11} className="text-slate-400" />
                      <span>{item.chair_name}</span>
                    </div>
                  </div>

                  {/* Check-In Action Button */}
                  <div className="flex items-center gap-2 pt-2 border-t border-slate-100">
                    <button
                      onClick={() => checkinMutation.mutate(item.id)}
                      disabled={checkinMutation.isPending}
                      className="flex-1 inline-flex items-center justify-center gap-1.5 px-2.5 py-1.5 bg-amber-600 hover:bg-amber-700 text-white rounded-md text-xs font-semibold shadow-2xs transition-colors disabled:opacity-50"
                    >
                      <UserCheck size={12} /> Check In Patient
                    </button>
                    <button
                      onClick={() => onSelectAppointment(convertQueueToAppointment(item))}
                      className="p-1.5 border border-slate-200 text-slate-600 hover:bg-slate-50 rounded-md transition-colors"
                      title="View Details"
                      aria-label="View Details"
                    >
                      <ExternalLink size={13} />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Stage 4: Completed Today */}
        <div className="bg-emerald-50/30 border border-emerald-200 rounded-xl p-4 flex flex-col min-h-[500px]">
          <div className="flex items-center justify-between pb-3 border-b border-emerald-200/80 mb-3">
            <div className="flex items-center gap-2">
              <CheckCircle2 size={14} className="text-emerald-600" />
              <h3 className="text-xs font-bold text-emerald-950 uppercase tracking-wider">
                Completed Today
              </h3>
            </div>
            <span className="text-xs font-bold bg-emerald-100 text-emerald-900 px-2 py-0.5 rounded-full border border-emerald-300">
              {completedItems.length}
            </span>
          </div>

          <div className="space-y-3 flex-1 overflow-y-auto">
            {completedItems.length === 0 ? (
              <div className="h-40 flex flex-col items-center justify-center text-center text-slate-400 text-xs">
                <CheckCircle2 size={24} className="mb-2 text-slate-300" />
                No completed appointments yet today
              </div>
            ) : (
              completedItems.map((item) => (
                <div
                  key={item.id}
                  className="bg-white p-3 rounded-lg border border-emerald-200 shadow-2xs"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-xs text-slate-900">{item.patient_name}</span>
                    <span className="text-[10px] text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200 font-semibold">
                      Completed
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-500 flex items-center justify-between">
                    <span>{item.dentist_name}</span>
                    <span className="font-mono">{item.scheduled_time.slice(0, 5)}</span>
                  </div>
                  <button
                    onClick={() => onSelectAppointment(convertQueueToAppointment(item))}
                    className="w-full mt-2 text-center text-[11px] font-semibold text-teal-700 hover:text-teal-900 transition-colors pt-1.5 border-t border-slate-100"
                  >
                    View Clinical Record →
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
