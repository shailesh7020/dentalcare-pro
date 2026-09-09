"use client";

import React, { useState } from "react";
import {
  Calendar,
  Clock,
  User,
  Plus,
  X,
  CheckCircle2,
  AlertCircle,
  Ban,
} from "lucide-react";
import { PortalShell } from "../portal-shell";
import type { PortalAppointmentRead } from "../types";

const mockAppointments: PortalAppointmentRead[] = [
  {
    id: "appt-1",
    appointment_number: "APT-2026-0099",
    date: "2026-10-15",
    start_time: "14:00",
    duration_minutes: 45,
    status: "CONFIRMED",
    visit_type: "CONSULTATION",
    reason: "Routine scaling and composite polish review",
    dentist_name: "Dr. David Tennant",
  },
  {
    id: "appt-2",
    appointment_number: "APT-2026-0045",
    date: "2026-09-01",
    start_time: "10:30",
    duration_minutes: 60,
    status: "COMPLETED",
    visit_type: "TREATMENT",
    reason: "Class II Posterior Composite Filling Tooth #14",
    dentist_name: "Dr. David Tennant",
  },
];

export default function PortalAppointmentsPage() {
  const [appointments, setAppointments] = useState(mockAppointments);
  const [isBookModalOpen, setIsBookModalOpen] = useState(false);
  const [cancelTargetId, setCancelTargetId] = useState<string | null>(null);
  const [cancelReason, setCancelReason] = useState("");
  const [notice, setNotice] = useState<string | null>(null);

  // Booking Form State
  const [bookDate, setBookDate] = useState("2026-11-20");
  const [bookTime, setBookTime] = useState("11:00");
  const [bookReason, setBookReason] = useState("");
  const [bookVisitType, setBookVisitType] = useState("CONSULTATION");

  const handleBookAppointment = (e: React.FormEvent) => {
    e.preventDefault();
    const newAppt: PortalAppointmentRead = {
      id: "appt-" + Date.now(),
      appointment_number: "APT-2026-" + Math.floor(1000 + Math.random() * 9000),
      date: bookDate,
      start_time: bookTime,
      duration_minutes: 30,
      status: "SCHEDULED",
      visit_type: bookVisitType,
      reason: bookReason || "Routine Consultation",
      dentist_name: "Dr. David Tennant",
    };
    setAppointments([newAppt, ...appointments]);
    setIsBookModalOpen(false);
    setBookReason("");
    setNotice("Your appointment has been booked! Confirmation notice sent via WhatsApp.");
    setTimeout(() => setNotice(null), 4000);
  };

  const handleCancelAppointment = () => {
    if (!cancelTargetId) return;
    setAppointments(
      appointments.map((a) =>
        a.id === cancelTargetId ? { ...a, status: "CANCELLED", notes: `Cancelled: ${cancelReason}` } : a
      )
    );
    setCancelTargetId(null);
    setCancelReason("");
    setNotice("Appointment cancelled. Notification recorded.");
    setTimeout(() => setNotice(null), 4000);
  };

  return (
    <PortalShell>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Your Appointments</h1>
          <p className="text-xs text-slate-500">View upcoming clinical visits and book convenient time slots</p>
        </div>
        <button
          onClick={() => setIsBookModalOpen(true)}
          className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs rounded-xl shadow-sm transition flex items-center gap-1.5"
        >
          <Plus className="w-4 h-4" /> Book New Appointment
        </button>
      </div>

      {notice && (
        <div className="mb-6 p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs font-semibold flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4" /> {notice}
        </div>
      )}

      {/* Appointments Cards */}
      <div className="space-y-4">
        {appointments.map((a) => {
          const isUpcoming = a.status === "SCHEDULED" || a.status === "CONFIRMED";
          return (
            <div
              key={a.id}
              className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
            >
              <div className="flex items-start gap-4">
                <div className="p-3 bg-teal-50 text-teal-700 rounded-xl text-center min-w-[72px]">
                  <span className="block text-xs font-bold uppercase">{new Date(a.date).toLocaleDateString([], { month: "short" })}</span>
                  <span className="block text-lg font-black">{new Date(a.date).getDate()}</span>
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-bold text-slate-900">{a.reason}</h3>
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${
                        a.status === "CONFIRMED"
                          ? "bg-emerald-100 text-emerald-800"
                          : a.status === "SCHEDULED"
                          ? "bg-blue-100 text-blue-800"
                          : a.status === "COMPLETED"
                          ? "bg-slate-100 text-slate-600"
                          : "bg-rose-100 text-rose-800"
                      }`}
                    >
                      {a.status}
                    </span>
                  </div>
                  <div className="flex items-center gap-4 mt-2 text-xs text-slate-500">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5 text-slate-400" /> {a.start_time} ({a.duration_minutes} min)
                    </span>
                    <span className="flex items-center gap-1">
                      <User className="w-3.5 h-3.5 text-slate-400" /> {a.dentist_name}
                    </span>
                    <span className="font-mono text-slate-400">{a.appointment_number}</span>
                  </div>
                </div>
              </div>

              {isUpcoming && (
                <button
                  onClick={() => setCancelTargetId(a.id)}
                  className="text-xs text-rose-600 font-semibold hover:bg-rose-50 px-3 py-1.5 rounded-lg transition"
                >
                  Cancel Visit
                </button>
              )}
            </div>
          );
        })}
      </div>

      {/* Book Appointment Modal */}
      {isBookModalOpen && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200 animate-scale-up">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-base font-bold text-slate-900">Book Dental Appointment</h3>
              <button onClick={() => setIsBookModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleBookAppointment} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Preferred Date
                </label>
                <input
                  type="date"
                  required
                  value={bookDate}
                  onChange={(e) => setBookDate(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-xl focus:ring-2 focus:ring-teal-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Time Slot
                  </label>
                  <select
                    value={bookTime}
                    onChange={(e) => setBookTime(e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-slate-200 rounded-xl focus:ring-2 focus:ring-teal-500"
                  >
                    <option value="09:00">09:00 AM</option>
                    <option value="10:30">10:30 AM</option>
                    <option value="11:00">11:00 AM</option>
                    <option value="14:00">02:00 PM</option>
                    <option value="15:30">03:30 PM</option>
                    <option value="17:00">05:00 PM</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Visit Reason
                  </label>
                  <select
                    value={bookVisitType}
                    onChange={(e) => setBookVisitType(e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-slate-200 rounded-xl focus:ring-2 focus:ring-teal-500"
                  >
                    <option value="CONSULTATION">Consultation</option>
                    <option value="TREATMENT">Treatment</option>
                    <option value="EMERGENCY">Emergency</option>
                    <option value="FOLLOW_UP">Follow Up</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Chief Complaint / Notes
                </label>
                <textarea
                  rows={3}
                  placeholder="Describe any tooth pain, sensitivity, or checkup request..."
                  value={bookReason}
                  onChange={(e) => setBookReason(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-slate-200 rounded-xl focus:ring-2 focus:ring-teal-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsBookModalOpen(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 text-xs font-bold text-white bg-teal-600 hover:bg-teal-700 rounded-xl shadow-sm transition"
                >
                  Confirm Booking
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Cancel Confirmation Modal */}
      {cancelTargetId && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-sm w-full p-6 shadow-xl border border-slate-200 animate-scale-up">
            <h3 className="text-base font-bold text-slate-900 mb-1">Cancel Appointment?</h3>
            <p className="text-xs text-slate-500 mb-4">Please let us know why you need to cancel this visit.</p>
            <textarea
              rows={3}
              placeholder="e.g. Schedule conflict or travel..."
              value={cancelReason}
              onChange={(e) => setCancelReason(e.target.value)}
              className="w-full p-2.5 text-xs border border-slate-200 rounded-xl mb-4 focus:ring-2 focus:ring-teal-500"
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setCancelTargetId(null)}
                className="px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg transition"
              >
                Keep Visit
              </button>
              <button
                onClick={handleCancelAppointment}
                className="px-4 py-1.5 text-xs font-semibold text-white bg-rose-600 hover:bg-rose-700 rounded-lg transition"
              >
                Yes, Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </PortalShell>
  );
}
