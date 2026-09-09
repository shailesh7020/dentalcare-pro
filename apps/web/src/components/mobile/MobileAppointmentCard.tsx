"use client";

import React from "react";

export interface MobileAppointmentData {
  id: string;
  appointment_number?: string;
  start_time: string;
  end_time: string;
  status: string;
  chief_complaint: string;
  chair?: string;
  dentist?: string;
  patient: {
    id: string;
    name: string;
    phone: string;
    gender?: string;
  };
}

interface MobileAppointmentCardProps {
  appointment: MobileAppointmentData;
  onConfirm?: (id: string) => void;
  onCancel?: (id: string) => void;
  onReschedule?: (id: string) => void;
  onAddNote?: (id: string, patientName: string) => void;
}

export function MobileAppointmentCard({
  appointment,
  onConfirm,
  onCancel,
  onReschedule,
  onAddNote,
}: MobileAppointmentCardProps) {
  const { id, start_time, end_time, status, chief_complaint, chair, dentist, patient } = appointment;

  const statusColors: Record<string, { bg: string; text: string; border: string }> = {
    CONFIRMED: { bg: "bg-emerald-50 text-emerald-700", text: "text-emerald-700", border: "border-emerald-200" },
    SCHEDULED: { bg: "bg-sky-50 text-sky-700", text: "text-sky-700", border: "border-sky-200" },
    IN_TREATMENT: { bg: "bg-purple-50 text-purple-700", text: "text-purple-700", border: "border-purple-200" },
    COMPLETED: { bg: "bg-slate-100 text-slate-700", text: "text-slate-700", border: "border-slate-200" },
    CANCELLED: { bg: "bg-rose-50 text-rose-700", text: "text-rose-700", border: "border-rose-200" },
  };

  const style = statusColors[status.toUpperCase()] || {
    bg: "bg-slate-50 text-slate-700",
    text: "text-slate-700",
    border: "border-slate-200",
  };

  const initials = patient.name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <div className={`p-4 bg-white rounded-xl border ${style.border} shadow-sm transition-all hover:shadow-md`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-teal-600 text-white font-bold flex items-center justify-center text-base shrink-0">
            {initials}
          </div>
          <div>
            <h3 className="text-base font-semibold text-slate-900 leading-snug">{patient.name}</h3>
            <p className="text-xs text-slate-500 font-medium">
              📞 {patient.phone} {chair ? `· 💺 ${chair}` : ""}
            </p>
          </div>
        </div>
        <span className={`px-2.5 py-1 text-xs font-semibold rounded-full border ${style.bg} ${style.border}`}>
          {status}
        </span>
      </div>

      <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-600">
        <div>
          <span className="font-semibold text-slate-800">⏰ {start_time} - {end_time}</span>
          {dentist && <span className="text-slate-500 ml-2">· {dentist}</span>}
        </div>
      </div>

      <div className="mt-2 text-xs bg-slate-50 p-2.5 rounded-lg text-slate-700 font-normal">
        <span className="font-semibold text-slate-900">Complaint:</span> {chief_complaint}
      </div>

      {/* Touch-Friendly Action Buttons (Minimum 44px tap targets) */}
      <div className="mt-3 grid grid-cols-4 gap-2">
        {status !== "CONFIRMED" && status !== "COMPLETED" && onConfirm && (
          <button
            onClick={() => onConfirm(id)}
            className="h-11 px-2 flex items-center justify-center rounded-lg bg-emerald-600 text-white text-xs font-semibold active:bg-emerald-700 transition"
            aria-label={`Confirm appointment for ${patient.name}`}
          >
            ✓ Confirm
          </button>
        )}
        {status !== "COMPLETED" && status !== "CANCELLED" && onReschedule && (
          <button
            onClick={() => onReschedule(id)}
            className="h-11 px-2 flex items-center justify-center rounded-lg bg-sky-600 text-white text-xs font-semibold active:bg-sky-700 transition"
            aria-label={`Reschedule appointment for ${patient.name}`}
          >
            📅 Reschedule
          </button>
        )}
        {onAddNote && (
          <button
            onClick={() => onAddNote(id, patient.name)}
            className="h-11 px-2 flex items-center justify-center rounded-lg bg-slate-100 text-slate-700 text-xs font-medium border border-slate-200 active:bg-slate-200 transition"
            aria-label={`Add clinical note for ${patient.name}`}
          >
            📝 Note
          </button>
        )}
        {status !== "CANCELLED" && status !== "COMPLETED" && onCancel && (
          <button
            onClick={() => onCancel(id)}
            className="h-11 px-2 flex items-center justify-center rounded-lg bg-rose-50 text-rose-700 text-xs font-semibold border border-rose-200 active:bg-rose-100 transition"
            aria-label={`Cancel appointment for ${patient.name}`}
          >
            ✕ Cancel
          </button>
        )}
      </div>
    </div>
  );
}
