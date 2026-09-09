"use client";

import Link from "next/link";
import React, { useState } from "react";
import {
  Calendar,
  Pill,
  CreditCard,
  FileSignature,
  MessageSquare,
  Clock,
  ArrowRight,
  AlertCircle,
  CheckCircle2,
  Phone,
  FileText,
  Smile,
  ShieldCheck,
} from "lucide-react";
import { PortalShell } from "./portal-shell";
import type { PortalDashboardSummary } from "./types";

const mockSummary: PortalDashboardSummary = {
  patient_id: "p-1",
  patient_name: "Donna Noble",
  patient_number: "P-4401",
  clinic_name: "City Dental Care",
  next_appointment: {
    id: "appt-1",
    appointment_number: "APT-2026-0099",
    date: "2026-10-15",
    time: "02:00 PM",
    dentist_name: "Dr. David Tennant",
    visit_type: "CONSULTATION",
    status: "CONFIRMED",
  },
  active_prescriptions_count: 2,
  total_balance_due: 272.5,
  unread_messages_count: 1,
  pending_forms_count: 1,
};

export default function PatientPortalDashboard() {
  const [summary] = useState<PortalDashboardSummary>(mockSummary);

  return (
    <PortalShell patientName={summary.patient_name} clinicName={summary.clinic_name}>
      {/* Welcome Banner */}
      <div className="bg-linear-to-r from-teal-700 to-teal-900 text-white p-6 sm:p-8 rounded-3xl shadow-sm mb-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div>
          <span className="text-xs font-semibold bg-teal-800/80 px-3 py-1 rounded-full text-teal-200">
            Patient ID: {summary.patient_number}
          </span>
          <h1 className="text-2xl sm:text-3xl font-black mt-2">Welcome back, {summary.patient_name}</h1>
          <p className="text-xs sm:text-sm text-teal-100 mt-1 max-w-xl">
            Manage your oral health records, upcoming clinic visits, prescriptions, and digital consent forms in one secure portal.
          </p>
        </div>

        <div className="flex gap-2">
          <Link
            href="/portal/appointments"
            className="px-4 py-2 bg-white text-teal-900 font-bold text-xs rounded-xl shadow-sm hover:bg-teal-50 transition flex items-center gap-1.5"
          >
            <Calendar className="w-4 h-4" /> Book Appointment
          </Link>
          <Link
            href="/portal/messages"
            className="px-4 py-2 bg-teal-800 text-white font-semibold text-xs rounded-xl hover:bg-teal-700 transition flex items-center gap-1.5"
          >
            <MessageSquare className="w-4 h-4" /> Message Clinic
          </Link>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {/* Next Appt */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Next Visit</span>
            <Calendar className="w-4 h-4 text-teal-600" />
          </div>
          {summary.next_appointment ? (
            <div>
              <div className="text-base font-bold text-slate-900">{summary.next_appointment.date}</div>
              <div className="text-xs text-teal-700 font-medium">{summary.next_appointment.time}</div>
              <p className="text-xs text-slate-500 mt-1">{summary.next_appointment.dentist_name}</p>
            </div>
          ) : (
            <p className="text-xs text-slate-400 mt-1">No upcoming appointments scheduled</p>
          )}
        </div>

        {/* Balance Due */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Balance Due</span>
            <CreditCard className="w-4 h-4 text-amber-600" />
          </div>
          <div className="text-2xl font-black text-slate-900">
            ₹{summary.total_balance_due.toFixed(2)}
          </div>
          <Link href="/portal/billing" className="text-xs text-teal-600 font-bold hover:underline mt-1 block">
            View Invoices & Pay →
          </Link>
        </div>

        {/* Prescriptions */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Active Prescriptions</span>
            <Pill className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-black text-slate-900">
            {summary.active_prescriptions_count}
          </div>
          <Link href="/portal/prescriptions" className="text-xs text-teal-600 font-bold hover:underline mt-1 block">
            Download Rx PDFs →
          </Link>
        </div>

        {/* Action Items / Forms */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Pending Forms</span>
            <FileSignature className="w-4 h-4 text-rose-500" />
          </div>
          <div className="text-2xl font-black text-rose-600">
            {summary.pending_forms_count}
          </div>
          <Link href="/portal/forms" className="text-xs text-rose-600 font-bold hover:underline mt-1 block">
            Sign Consent Form →
          </Link>
        </div>
      </div>

      {/* Main 2-Column Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Fast Action Cards */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
            <h2 className="text-base font-bold text-slate-900 mb-4">Patient Services & Self-Care</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Link
                href="/portal/appointments"
                className="p-4 rounded-xl border border-slate-100 hover:border-teal-200 hover:bg-teal-50/40 transition group"
              >
                <div className="p-2 bg-teal-100 text-teal-800 rounded-lg w-fit mb-3 group-hover:scale-105 transition">
                  <Calendar className="w-5 h-5" />
                </div>
                <h3 className="text-sm font-bold text-slate-900">Appointments</h3>
                <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                  Schedule new visits, view upcoming dates, or reschedule appointments.
                </p>
              </Link>

              <Link
                href="/portal/prescriptions"
                className="p-4 rounded-xl border border-slate-100 hover:border-teal-200 hover:bg-teal-50/40 transition group"
              >
                <div className="p-2 bg-emerald-100 text-emerald-800 rounded-lg w-fit mb-3 group-hover:scale-105 transition">
                  <Pill className="w-5 h-5" />
                </div>
                <h3 className="text-sm font-bold text-slate-900">Prescriptions & Rx</h3>
                <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                  Access doctor medication orders, dosage schedules, and printable PDFs.
                </p>
              </Link>

              <Link
                href="/portal/treatments"
                className="p-4 rounded-xl border border-slate-100 hover:border-teal-200 hover:bg-teal-50/40 transition group"
              >
                <div className="p-2 bg-blue-100 text-blue-800 rounded-lg w-fit mb-3 group-hover:scale-105 transition">
                  <Smile className="w-5 h-5" />
                </div>
                <h3 className="text-sm font-bold text-slate-900">Interactive Odontogram</h3>
                <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                  View your complete dental tooth chart with healthy, filled, and restored tooth records.
                </p>
              </Link>

              <Link
                href="/portal/forms"
                className="p-4 rounded-xl border border-slate-100 hover:border-teal-200 hover:bg-teal-50/40 transition group"
              >
                <div className="p-2 bg-purple-100 text-purple-800 rounded-lg w-fit mb-3 group-hover:scale-105 transition">
                  <FileSignature className="w-5 h-5" />
                </div>
                <h3 className="text-sm font-bold text-slate-900">Digital Consent Records</h3>
                <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                  Sign informed consent forms with your finger, mouse, or stylus with audit tracking.
                </p>
              </Link>
            </div>
          </div>
        </div>

        {/* Right Column: Contact & Clinic Help */}
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
            <h3 className="text-sm font-bold text-slate-900 mb-2">Need Emergency Dental Advice?</h3>
            <p className="text-xs text-slate-500 leading-relaxed mb-4">
              If you are experiencing severe toothache, acute swelling, or bleeding after a procedure, contact our on-duty team immediately.
            </p>
            <div className="p-3 bg-amber-50 border border-amber-200 text-amber-900 rounded-xl text-xs flex items-center gap-2 mb-4">
              <Phone className="w-4 h-4 text-amber-700 shrink-0" />
              <span>Emergency Hotline: <strong>+91 99000 11223</strong></span>
            </div>
            <Link
              href="/portal/messages"
              className="w-full py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold text-xs rounded-xl transition flex items-center justify-center gap-1.5"
            >
              <MessageSquare className="w-3.5 h-3.5" /> Start Online Chat
            </Link>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs text-xs space-y-3">
            <h4 className="font-bold text-slate-900">Clinic Hours & Location</h4>
            <p className="text-slate-600">BrightSmile & City Dental Care<br />42 Harley Medical Avenue, Suite 4B</p>
            <div className="text-slate-500 space-y-1 pt-2 border-t border-slate-100">
              <p>Mon – Fri: 08:30 AM – 07:00 PM</p>
              <p>Saturday: 09:00 AM – 04:00 PM</p>
              <p>Sunday: Emergency Consultations Only</p>
            </div>
          </div>
        </div>
      </div>
    </PortalShell>
  );
}
