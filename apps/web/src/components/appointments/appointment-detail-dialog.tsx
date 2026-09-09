"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  Calendar,
  CheckCircle2,
  Clock,
  FileText,
  MapPin,
  Phone,
  Play,
  RotateCcw,
  Stethoscope,
  User,
  UserCheck,
  XCircle,
} from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";

interface AppointmentDetailProps {
  appointment: any | null;
  isOpen: boolean;
  onClose: () => void;
  onUpdated?: () => void;
}

export function AppointmentDetailDialog({
  appointment,
  isOpen,
  onClose,
  onUpdated,
}: AppointmentDetailProps) {
  const queryClient = useQueryClient();
  const [isRescheduling, setIsRescheduling] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);
  const [cancelReason, setCancelReason] = useState("");
  const [newDate, setNewDate] = useState("");
  const [newTime, setNewTime] = useState("");
  const [rescheduleReason, setRescheduleReason] = useState("");
  const [actionError, setActionError] = useState<string | null>(null);

  if (!appointment) return null;

  const invalidateAll = () => {
    void queryClient.invalidateQueries({ queryKey: ["appointments"] });
    void queryClient.invalidateQueries({ queryKey: ["calendar-day"] });
    void queryClient.invalidateQueries({ queryKey: ["calendar-week"] });
    void queryClient.invalidateQueries({ queryKey: ["calendar-month"] });
    void queryClient.invalidateQueries({ queryKey: ["appointment-queue"] });
    void queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] });
    void queryClient.invalidateQueries({ queryKey: ["patient-timeline", appointment.patient_id] });
    if (onUpdated) onUpdated();
  };

  const statusMutation = useMutation({
    mutationFn: async (endpoint: string) => {
      setActionError(null);
      const res = await api.post(`/appointments/${appointment.id}/${endpoint}`);
      return res.data;
    },
    onSuccess: () => {
      invalidateAll();
      onClose();
    },
    onError: (err: any) => {
      setActionError(err.response?.data?.detail || err.message || "Failed to update status.");
    },
  });

  const cancelMutation = useMutation({
    mutationFn: async () => {
      setActionError(null);
      if (!cancelReason.trim()) throw new Error("Please provide a reason for cancellation.");
      const res = await api.post(`/appointments/${appointment.id}/cancel`, {
        reason: cancelReason.trim(),
      });
      return res.data;
    },
    onSuccess: () => {
      setIsCancelling(false);
      setCancelReason("");
      invalidateAll();
      onClose();
    },
    onError: (err: any) => {
      setActionError(err.response?.data?.detail || err.message || "Failed to cancel appointment.");
    },
  });

  const rescheduleMutation = useMutation({
    mutationFn: async () => {
      setActionError(null);
      if (!newDate || !newTime) throw new Error("Please select new date and time.");
      if (!rescheduleReason.trim()) throw new Error("Please provide a reason for rescheduling.");
      const res = await api.post(`/appointments/${appointment.id}/reschedule`, {
        new_date: newDate,
        new_start_time: newTime.length === 5 ? `${newTime}:00` : newTime,
        reason: rescheduleReason.trim(),
      });
      return res.data;
    },
    onSuccess: () => {
      setIsRescheduling(false);
      setNewDate("");
      setNewTime("");
      setRescheduleReason("");
      invalidateAll();
      onClose();
    },
    onError: (err: any) => {
      setActionError(err.response?.data?.detail || err.message || "Failed to reschedule appointment.");
    },
  });

  const isCompleted = appointment.status === "COMPLETED";
  const isCancelled = appointment.status === "CANCELLED";

  const statusBadgeVariant = (status: string) => {
    switch (status) {
      case "COMPLETED":
        return "success";
      case "IN_TREATMENT":
        return "default";
      case "CHECKED_IN":
        return "warning";
      case "CONFIRMED":
        return "secondary";
      case "CANCELLED":
      case "NO_SHOW":
        return "destructive";
      default:
        return "outline";
    }
  };

  const statusFlow = ["SCHEDULED", "CONFIRMED", "CHECKED_IN", "IN_TREATMENT", "COMPLETED"];
  const currentStepIdx = statusFlow.indexOf(appointment.status);

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto p-6 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-2xl">
        <DialogHeader className="border-b border-slate-100 dark:border-slate-800 pb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="font-mono text-xs font-bold text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">
                #{appointment.appointment_number}
              </span>
              <Badge variant={statusBadgeVariant(appointment.status)} className="capitalize">
                {appointment.status.toLowerCase().replace("_", " ")}
              </Badge>
              {appointment.is_emergency_override && (
                <Badge variant="destructive" className="text-[10px]">
                  Emergency Override
                </Badge>
              )}
            </div>
            <span className="text-xs text-slate-400 font-medium">
              {appointment.visit_type.replace("_", " ")}
            </span>
          </div>
          <DialogTitle className="text-base font-bold text-slate-900 mt-2">
            Appointment Overview
          </DialogTitle>
        </DialogHeader>

        {actionError && (
          <div className="p-3 my-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
            <AlertTriangle size={15} className="shrink-0 text-rose-600" />
            <span>{actionError}</span>
          </div>
        )}

        {/* Reschedule Form Sub-view */}
        {isRescheduling ? (
          <div className="my-4 p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
              <RotateCcw size={14} /> Reschedule Appointment
            </h4>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] font-semibold text-slate-600 mb-1">New Date *</label>
                <input
                  type="date"
                  value={newDate}
                  onChange={(e) => setNewDate(e.target.value)}
                  className="w-full text-xs px-3 py-2 bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-600"
                />
              </div>
              <div>
                <label className="block text-[11px] font-semibold text-slate-600 mb-1">New Time *</label>
                <input
                  type="time"
                  value={newTime}
                  onChange={(e) => setNewTime(e.target.value)}
                  className="w-full text-xs px-3 py-2 bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-600"
                />
              </div>
            </div>
            <div>
              <label className="block text-[11px] font-semibold text-slate-600 mb-1">Reason for Rescheduling *</label>
              <input
                type="text"
                placeholder="e.g. Patient requested schedule change"
                value={rescheduleReason}
                onChange={(e) => setRescheduleReason(e.target.value)}
                className="w-full text-xs px-3 py-2 bg-white border border-slate-200 rounded-lg focus:ring-2 focus:ring-teal-600"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setIsRescheduling(false)}
                className="px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-200 rounded-lg"
              >
                Back
              </button>
              <button
                type="button"
                onClick={() => rescheduleMutation.mutate()}
                disabled={rescheduleMutation.isPending || !newDate || !newTime || !rescheduleReason}
                className="px-4 py-1.5 text-xs font-semibold text-white bg-teal-700 hover:bg-teal-800 disabled:opacity-50 rounded-lg"
              >
                {rescheduleMutation.isPending ? "Moving..." : "Confirm Reschedule"}
              </button>
            </div>
          </div>
        ) : isCancelling ? (
          /* Cancel Form Sub-view */
          <div className="my-4 p-4 rounded-xl bg-rose-50 border border-rose-200 space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-rose-800 flex items-center gap-1.5">
              <XCircle size={14} /> Cancel Appointment
            </h4>
            <p className="text-xs text-rose-700">
              Please enter the cancellation reason. This will update the patient timeline and dispatch cancellation records.
            </p>
            <input
              type="text"
              placeholder="e.g. Patient feeling unwell, out of town"
              value={cancelReason}
              onChange={(e) => setCancelReason(e.target.value)}
              className="w-full text-xs px-3 py-2 bg-white border border-rose-300 rounded-lg focus:ring-2 focus:ring-rose-500"
            />
            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setIsCancelling(false)}
                className="px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-200 rounded-lg"
              >
                Back
              </button>
              <button
                type="button"
                onClick={() => cancelMutation.mutate()}
                disabled={cancelMutation.isPending || !cancelReason}
                className="px-4 py-1.5 text-xs font-semibold text-white bg-rose-600 hover:bg-rose-700 disabled:opacity-50 rounded-lg"
              >
                {cancelMutation.isPending ? "Cancelling..." : "Confirm Cancellation"}
              </button>
            </div>
          </div>
        ) : (
          /* Main Overview Content */
          <div className="space-y-6 mt-4">
            {/* Patient Header Card */}
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="w-11 h-11 rounded-full bg-teal-700 text-white font-bold text-sm flex items-center justify-center">
                  {appointment.patient_name
                    ? appointment.patient_name.split(" ").map((n: string) => n[0]).join("")
                    : "P"}
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                    {appointment.patient_name}
                    <Link
                      href={`/patients/${appointment.patient_id}`}
                      className="text-xs text-teal-700 hover:underline font-normal"
                    >
                      (View Profile)
                    </Link>
                  </h3>
                  <div className="flex items-center gap-3 text-xs text-slate-500 mt-0.5">
                    <span>ID: {appointment.patient_number}</span>
                    {appointment.patient_phone && (
                      <span className="flex items-center gap-1">
                        <Phone size={12} /> {appointment.patient_phone}
                      </span>
                    )}
                  </div>
                </div>
              </div>

              {/* Medical Alerts */}
              {appointment.patient_medical_alerts && appointment.patient_medical_alerts.length > 0 && (
                <div className="flex flex-col items-end gap-1">
                  <span className="text-[10px] uppercase font-bold text-rose-700 tracking-wider">
                    Medical Alerts
                  </span>
                  <div className="flex flex-wrap gap-1 justify-end max-w-xs">
                    {appointment.patient_medical_alerts.map((alert: string, idx: number) => (
                      <Badge key={idx} variant="destructive" className="text-[10px] py-0 px-1.5">
                        {alert}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Schedule & Operatory Information */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="p-3 bg-white border border-slate-200 rounded-lg">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block mb-1">
                  Date
                </span>
                <span className="text-xs font-semibold text-slate-900 flex items-center gap-1.5">
                  <Calendar size={13} className="text-teal-600" />
                  {appointment.date}
                </span>
              </div>

              <div className="p-3 bg-white border border-slate-200 rounded-lg">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block mb-1">
                  Time Slot
                </span>
                <span className="text-xs font-semibold text-slate-900 flex items-center gap-1.5">
                  <Clock size={13} className="text-teal-600" />
                  {appointment.start_time.slice(0, 5)} ({appointment.duration}m)
                </span>
              </div>

              <div className="p-3 bg-white border border-slate-200 rounded-lg">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block mb-1">
                  Dentist
                </span>
                <span className="text-xs font-semibold text-slate-900 flex items-center gap-1.5">
                  <Stethoscope size={13} className="text-teal-600" />
                  {appointment.dentist_name || "Doctor"}
                </span>
              </div>

              <div className="p-3 bg-white border border-slate-200 rounded-lg">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block mb-1">
                  Chair / Operatory
                </span>
                <span className="text-xs font-semibold text-slate-900 flex items-center gap-1.5">
                  <MapPin size={13} className="text-teal-600" />
                  {appointment.chair_name || "Operatory"}
                </span>
              </div>
            </div>

            {/* Clinical Complaints & Notes */}
            {(appointment.chief_complaint || appointment.notes || appointment.cancellation_reason) && (
              <div className="space-y-2 p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs">
                {appointment.chief_complaint && (
                  <div>
                    <strong className="text-slate-700">Chief Complaint:</strong>{" "}
                    <span className="text-slate-600">{appointment.chief_complaint}</span>
                  </div>
                )}
                {appointment.notes && (
                  <div>
                    <strong className="text-slate-700">Notes:</strong>{" "}
                    <span className="text-slate-600">{appointment.notes}</span>
                  </div>
                )}
                {appointment.cancellation_reason && (
                  <div>
                    <strong className="text-rose-700">Cancellation Reason:</strong>{" "}
                    <span className="text-rose-600">{appointment.cancellation_reason}</span>
                  </div>
                )}
              </div>
            )}

            {/* Lifecycle Progress Flow */}
            <div>
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
                Lifecycle Progression
              </h4>
              <div className="flex items-center justify-between relative px-2">
                <div className="absolute left-6 right-6 top-3 h-0.5 bg-slate-200 -z-10" />
                {statusFlow.map((s, idx) => {
                  const isPastOrCurrent = currentStepIdx >= idx;
                  const isCurrent = currentStepIdx === idx;
                  return (
                    <div key={s} className="flex flex-col items-center">
                      <div
                        className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold transition-all ${
                          isCurrent
                            ? "bg-teal-700 text-white ring-4 ring-teal-100"
                            : isPastOrCurrent
                            ? "bg-teal-600 text-white"
                            : "bg-white border-2 border-slate-300 text-slate-400"
                        }`}
                      >
                        {idx + 1}
                      </div>
                      <span
                        className={`text-[10px] mt-1.5 font-medium capitalize ${
                          isCurrent ? "text-teal-900 font-bold" : "text-slate-500"
                        }`}
                      >
                        {s.toLowerCase().replace("_", " ")}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Appointment Timeline Events */}
            {appointment.timeline_events && appointment.timeline_events.length > 0 && (
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                  Event Log
                </h4>
                <ol className="relative border-l border-slate-200 ml-2 space-y-3">
                  {appointment.timeline_events.map((evt: any) => (
                    <li key={evt.id} className="ml-4 text-xs">
                      <span className="absolute -left-1.5 mt-1 w-3 h-3 rounded-full bg-teal-600 ring-4 ring-white" />
                      <div className="font-semibold text-slate-800">{evt.title}</div>
                      {evt.notes && <p className="text-slate-500 text-[11px] mt-0.5">{evt.notes}</p>}
                      <time className="text-[10px] text-slate-400 block mt-0.5">
                        {new Date(evt.created_at).toLocaleString()}
                      </time>
                    </li>
                  ))}
                </ol>
              </div>
            )}
          </div>
        )}

        {/* Action Buttons Bar */}
        {!isRescheduling && !isCancelling && (
          <div className="flex items-center justify-between pt-5 border-t border-slate-100 mt-6">
            <div>
              {!isCompleted && !isCancelled && (
                <button
                  type="button"
                  onClick={() => setIsCancelling(true)}
                  className="px-3 py-1.5 text-xs font-semibold text-rose-600 hover:bg-rose-50 rounded-lg"
                >
                  Cancel Visit
                </button>
              )}
            </div>

            <div className="flex items-center gap-2">
              {!isCompleted && !isCancelled && (
                <button
                  type="button"
                  onClick={() => {
                    setNewDate(appointment.date);
                    setNewTime(appointment.start_time.slice(0, 5));
                    setIsRescheduling(true);
                  }}
                  className="px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-100 border border-slate-200 rounded-lg flex items-center gap-1.5"
                >
                  <RotateCcw size={13} /> Reschedule
                </button>
              )}

              {/* Status Transition Action Buttons */}
              {(appointment.status === "SCHEDULED" || appointment.status === "RESCHEDULED") && (
                <>
                  <button
                    type="button"
                    disabled={statusMutation.isPending}
                    onClick={() => statusMutation.mutate("confirm")}
                    className="px-3 py-1.5 text-xs font-semibold text-teal-700 bg-teal-50 hover:bg-teal-100 border border-teal-200 rounded-lg flex items-center gap-1"
                  >
                    <CheckCircle2 size={13} /> Confirm
                  </button>
                  <button
                    type="button"
                    disabled={statusMutation.isPending}
                    onClick={() => statusMutation.mutate("checkin")}
                    className="px-3 py-1.5 text-xs font-semibold text-white bg-amber-600 hover:bg-amber-700 rounded-lg flex items-center gap-1"
                  >
                    <UserCheck size={13} /> Check In
                  </button>
                </>
              )}

              {appointment.status === "CONFIRMED" && (
                <button
                  type="button"
                  disabled={statusMutation.isPending}
                  onClick={() => statusMutation.mutate("checkin")}
                  className="px-3 py-1.5 text-xs font-semibold text-white bg-amber-600 hover:bg-amber-700 rounded-lg flex items-center gap-1"
                >
                  <UserCheck size={13} /> Check In
                </button>
              )}

              {appointment.status === "CHECKED_IN" && (
                <>
                  <button
                    type="button"
                    disabled={statusMutation.isPending}
                    onClick={() => statusMutation.mutate("start")}
                    className="px-3 py-1.5 text-xs font-semibold text-white bg-purple-600 hover:bg-purple-700 rounded-lg flex items-center gap-1"
                  >
                    <Play size={13} /> In Chair
                  </button>
                  <Link
                    href={`/treatments/new?appointment_id=${appointment.id}&patient_id=${appointment.patient_id}`}
                    onClick={onClose}
                    className="px-3 py-1.5 text-xs font-semibold text-teal-700 bg-teal-50 hover:bg-teal-100 border border-teal-200 rounded-lg flex items-center gap-1"
                  >
                    <Stethoscope size={13} /> Start Treatment
                  </Link>
                </>
              )}

              {appointment.status === "IN_TREATMENT" && (
                <>
                  <Link
                    href={`/treatments/new?appointment_id=${appointment.id}&patient_id=${appointment.patient_id}`}
                    onClick={onClose}
                    className="px-3 py-1.5 text-xs font-semibold text-teal-700 bg-teal-50 hover:bg-teal-100 border border-teal-200 rounded-lg flex items-center gap-1"
                  >
                    <Stethoscope size={13} /> Open Clinical Record
                  </Link>
                  <button
                    type="button"
                    disabled={statusMutation.isPending}
                    onClick={() => statusMutation.mutate("complete")}
                    className="px-4 py-1.5 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg flex items-center gap-1"
                  >
                    <CheckCircle2 size={13} /> Complete Visit
                  </button>
                </>
              )}

              {appointment.status === "COMPLETED" && (
                <Link
                  href={`/treatments`}
                  onClick={onClose}
                  className="px-3 py-1.5 text-xs font-semibold text-teal-700 bg-teal-50 hover:bg-teal-100 border border-teal-200 rounded-lg flex items-center gap-1"
                >
                  <Stethoscope size={13} /> Treatments Hub
                </Link>
              )}

              <button
                type="button"
                onClick={onClose}
                className="px-3 py-1.5 text-xs font-semibold text-slate-500 hover:bg-slate-100 rounded-lg ml-2"
              >
                Close
              </button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
