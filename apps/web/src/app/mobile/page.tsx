"use client";

import React, { useState, useMemo } from "react";
import Link from "next/link";
import { MobileAppointmentCard, MobileAppointmentData } from "@/components/mobile/MobileAppointmentCard";

// Mock/Initial Data for fast rendering and offline resilience
const initialTodayAppointments: MobileAppointmentData[] = [
  {
    id: "apt-101",
    appointment_number: "APT-2026-001",
    start_time: "09:30",
    end_time: "10:15",
    status: "CONFIRMED",
    chief_complaint: "Routine scaling and composite polishing",
    chair: "Chair 1 (Main Operatory)",
    dentist: "Dr. Ananya Shah",
    patient: {
      id: "pat-1",
      name: "Rohan Kulkarni",
      phone: "9820123456",
      gender: "MALE",
    },
  },
  {
    id: "apt-102",
    appointment_number: "APT-2026-002",
    start_time: "10:30",
    end_time: "11:15",
    status: "SCHEDULED",
    chief_complaint: "Severe toothache #16 with cold sensitivity",
    chair: "Chair 2",
    dentist: "Dr. Ananya Shah",
    patient: {
      id: "pat-2",
      name: "Pooja Sharma",
      phone: "9820987654",
      gender: "FEMALE",
    },
  },
  {
    id: "apt-103",
    appointment_number: "APT-2026-003",
    start_time: "11:30",
    end_time: "12:15",
    status: "SCHEDULED",
    chief_complaint: "Crown cementation follow-up #24",
    chair: "Chair 1 (Main Operatory)",
    dentist: "Dr. Vikram Joshi",
    patient: {
      id: "pat-3",
      name: "Amit Patel",
      phone: "9819112233",
      gender: "MALE",
    },
  },
  {
    id: "apt-104",
    appointment_number: "APT-2026-004",
    start_time: "14:00",
    end_time: "14:45",
    status: "SCHEDULED",
    chief_complaint: "Pediatric fluoride varnish and sealant",
    chair: "Chair 3",
    dentist: "Dr. Ananya Shah",
    patient: {
      id: "pat-4",
      name: "Aarav Desai",
      phone: "9833445566",
      gender: "MALE",
    },
  },
];

const initialTomorrowAppointments = [
  { id: "apt-201", time: "10:00 AM", patient: "Sneha Nair", dentist: "Dr. Shah", complaint: "Root Canal Stage 2", chair: "Chair 1" },
  { id: "apt-202", time: "11:00 AM", patient: "Rajesh Khanna", dentist: "Dr. Joshi", complaint: "Implant Consult", chair: "Chair 2" },
  { id: "apt-203", time: "02:30 PM", patient: "Kavita Rao", dentist: "Dr. Shah", complaint: "Orthodontic Wire Tightening", chair: "Chair 1" },
  { id: "apt-204", time: "04:00 PM", patient: "Manoj Mehta", dentist: "Dr. Joshi", complaint: "Extraction #38 Evaluation", chair: "Chair 3" },
];

const initialStockAlerts = [
  { id: "stk-1", name: "Composite Resin A2 (Filtek)", current: 2, min: 5, unit: "Syringes" },
  { id: "stk-2", name: "Lidocaine 2% with Epinephrine", current: 8, min: 20, unit: "Cartridges" },
  { id: "stk-3", name: "Dental Bibs Lavender", current: 15, min: 50, unit: "Pcs" },
];

export default function MobileDashboardPage() {
  const [activeTab, setActiveTab] = useState<"today" | "tomorrow" | "calendar" | "revenue" | "alerts">("today");
  const [searchQuery, setSearchQuery] = useState("");
  const [appointments, setAppointments] = useState<MobileAppointmentData[]>(initialTodayAppointments);
  const [modalType, setModalType] = useState<"reschedule" | "note" | null>(null);
  const [selectedAppt, setSelectedAppt] = useState<{ id: string; patientName: string } | null>(null);
  const [noteText, setNoteText] = useState("");
  const [feedbackMsg, setFeedbackMsg] = useState<string | null>(null);

  // Filtered appointments by search query
  const filteredAppointments = useMemo(() => {
    if (!searchQuery.trim()) return appointments;
    const q = searchQuery.toLowerCase();
    return appointments.filter(
      (a) =>
        a.patient.name.toLowerCase().includes(q) ||
        a.patient.phone.includes(q) ||
        a.chief_complaint.toLowerCase().includes(q) ||
        (a.appointment_number && a.appointment_number.toLowerCase().includes(q))
    );
  }, [appointments, searchQuery]);

  // Safe remote actions
  const handleConfirm = (id: string) => {
    setAppointments((prev) =>
      prev.map((a) => (a.id === id ? { ...a, status: "CONFIRMED" } : a))
    );
    showFeedback("Appointment successfully confirmed.");
  };

  const handleCancel = (id: string) => {
    setAppointments((prev) =>
      prev.map((a) => (a.id === id ? { ...a, status: "CANCELLED" } : a))
    );
    showFeedback("Appointment marked as cancelled.");
  };

  const handleOpenReschedule = (id: string) => {
    const appt = appointments.find((a) => a.id === id);
    if (appt) {
      setSelectedAppt({ id, patientName: appt.patient.name });
      setModalType("reschedule");
    }
  };

  const handleOpenNote = (id: string, patientName: string) => {
    setSelectedAppt({ id, patientName });
    setNoteText("");
    setModalType("note");
  };

  const handleSaveNote = () => {
    if (selectedAppt && noteText.trim()) {
      showFeedback(`Clinical note saved for ${selectedAppt.patientName}.`);
      setModalType(null);
      setNoteText("");
    }
  };

  const handleSaveReschedule = (newTime: string) => {
    if (selectedAppt) {
      setAppointments((prev) =>
        prev.map((a) => (a.id === selectedAppt.id ? { ...a, start_time: newTime } : a))
      );
      showFeedback(`Appointment rescheduled to ${newTime}.`);
      setModalType(null);
    }
  };

  const showFeedback = (msg: string) => {
    setFeedbackMsg(msg);
    setTimeout(() => setFeedbackMsg(null), 3000);
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 pb-20 select-none">
      {/* Top Remote Header */}
      <header className="sticky top-0 z-30 bg-white border-b border-slate-200 px-4 py-3 shadow-xs">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-xs font-bold uppercase tracking-wider text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200">
                Secure Remote Access
              </span>
            </div>
            <h1 className="text-lg font-black tracking-tight text-slate-900 mt-0.5">
              BrightSmile Dental <span className="text-teal-600 font-extrabold text-sm">PRO</span>
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold px-2 py-1 bg-slate-100 rounded-lg text-slate-700 border border-slate-200">
              🔒 2FA Active
            </span>
            <Link
              href="/"
              className="text-xs font-medium text-slate-500 hover:text-slate-900 px-2 py-1 rounded-md"
              title="Switch to full desktop view"
            >
              Desktop ↗
            </Link>
          </div>
        </div>

        {/* Remote Security Guardrail Badge */}
        <div className="mt-2.5 px-3 py-1.5 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-800 flex items-center justify-between">
          <span>🛡️ Safe remote editing mode enabled.</span>
          <span className="font-semibold text-amber-900 text-[10px] uppercase">Clinic Server Protected</span>
        </div>

        {/* Real-Time Search Bar */}
        <div className="mt-3 relative">
          <input
            type="search"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="🔍 Search patient, phone, complaint..."
            className="w-full h-12 pl-4 pr-10 text-sm bg-slate-100 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-teal-500 focus:outline-hidden transition"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery("")}
              className="absolute right-3 top-3 text-slate-400 hover:text-slate-600 text-sm font-bold"
            >
              ✕
            </button>
          )}
        </div>
      </header>

      {/* Floating Action Feedback Toast */}
      {feedbackMsg && (
        <div className="fixed top-24 left-4 right-4 z-50 p-3 bg-emerald-600 text-white text-xs font-semibold rounded-xl shadow-lg flex items-center justify-between animate-bounce">
          <span>✓ {feedbackMsg}</span>
          <button onClick={() => setFeedbackMsg(null)} className="text-white font-bold ml-2">
            ✕
          </button>
        </div>
      )}

      {/* Quick Summary Metrics Carousel */}
      <section className="px-4 py-3 grid grid-cols-2 gap-2.5">
        <div className="p-3 bg-white rounded-xl border border-slate-200 shadow-xs">
          <p className="text-[11px] font-semibold uppercase text-slate-500">Today&apos;s Visits</p>
          <div className="flex items-baseline justify-between mt-1">
            <span className="text-2xl font-black text-slate-900">{appointments.length}</span>
            <span className="text-[11px] font-bold text-emerald-600">4 Chairs</span>
          </div>
        </div>
        <div className="p-3 bg-white rounded-xl border border-slate-200 shadow-xs">
          <p className="text-[11px] font-semibold uppercase text-slate-500">Revenue Today</p>
          <div className="flex items-baseline justify-between mt-1">
            <span className="text-2xl font-black text-slate-900">₹48.5k</span>
            <span className="text-[11px] font-bold text-emerald-600">+12%</span>
          </div>
        </div>
        <div className="p-3 bg-white rounded-xl border border-slate-200 shadow-xs">
          <p className="text-[11px] font-semibold uppercase text-slate-500">Pending Invoices</p>
          <div className="flex items-baseline justify-between mt-1">
            <span className="text-2xl font-black text-amber-600">8 Due</span>
            <span className="text-[11px] font-medium text-slate-500">₹24,800</span>
          </div>
        </div>
        <div className="p-3 bg-white rounded-xl border border-slate-200 shadow-xs">
          <p className="text-[11px] font-semibold uppercase text-slate-500">Stock Alerts</p>
          <div className="flex items-baseline justify-between mt-1">
            <span className="text-2xl font-black text-rose-600">{initialStockAlerts.length}</span>
            <span className="text-[11px] font-bold text-rose-600">Action</span>
          </div>
        </div>
      </section>

      {/* Navigation Tabs */}
      <nav className="px-4 flex gap-1.5 overflow-x-auto pb-1 no-scrollbar" aria-label="Dashboard views">
        {[
          { key: "today", label: `Today (${filteredAppointments.length})` },
          { key: "tomorrow", label: "Tomorrow" },
          { key: "calendar", label: "Week Calendar" },
          { key: "revenue", label: "Revenue" },
          { key: "alerts", label: "Alerts" },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as any)}
            className={`px-4 py-2 text-xs font-bold rounded-xl whitespace-nowrap transition-all ${
              activeTab === tab.key
                ? "bg-teal-600 text-white shadow-sm"
                : "bg-white text-slate-600 border border-slate-200 hover:bg-slate-100"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      {/* Main Tab Content */}
      <main className="px-4 mt-3 space-y-3">
        {/* TAB: TODAY */}
        {activeTab === "today" && (
          <div className="space-y-3">
            {filteredAppointments.length === 0 ? (
              <div className="p-8 text-center bg-white rounded-xl border border-slate-200 text-slate-500 text-xs">
                No appointments found matching &ldquo;{searchQuery}&rdquo;.
              </div>
            ) : (
              filteredAppointments.map((appt) => (
                <MobileAppointmentCard
                  key={appt.id}
                  appointment={appt}
                  onConfirm={handleConfirm}
                  onCancel={handleCancel}
                  onReschedule={handleOpenReschedule}
                  onAddNote={handleOpenNote}
                />
              ))
            )}
          </div>
        )}

        {/* TAB: TOMORROW */}
        {activeTab === "tomorrow" && (
          <div className="space-y-3">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500 px-1">Tomorrow&apos;s Schedule</h2>
            {initialTomorrowAppointments.map((item) => (
              <div key={item.id} className="p-4 bg-white rounded-xl border border-slate-200 shadow-xs">
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-xs font-extrabold text-teal-600">{item.time}</span>
                    <h3 className="text-sm font-bold text-slate-900 mt-0.5">{item.patient}</h3>
                    <p className="text-xs text-slate-500">{item.complaint} · {item.dentist}</p>
                  </div>
                  <span className="text-xs px-2 py-0.5 bg-slate-100 rounded-md font-medium text-slate-600">
                    {item.chair}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* TAB: WEEK CALENDAR */}
        {activeTab === "calendar" && (
          <div className="bg-white p-4 rounded-xl border border-slate-200 space-y-3">
            <h2 className="text-xs font-bold uppercase text-slate-500">Weekly Patient Load</h2>
            <div className="grid grid-cols-7 gap-1.5 text-center">
              {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((d, i) => (
                <div key={d} className={`p-2 rounded-lg border ${i === 1 ? "bg-teal-50 border-teal-300 font-bold" : "border-slate-100 text-slate-600"}`}>
                  <div className="text-[10px] text-slate-400 uppercase">{d}</div>
                  <div className="text-sm font-black mt-1">{18 + i}</div>
                  <div className="text-[10px] text-teal-600 font-bold mt-0.5">{[12, 24, 18, 20, 15, 8, 0][i]} visits</div>
                </div>
              ))}
            </div>
            <div className="mt-4 p-3 bg-slate-50 rounded-lg text-xs text-slate-600 border border-slate-200">
              Total 97 visits booked across this week. Clinic chairs operating at 88% capacity.
            </div>
          </div>
        )}

        {/* TAB: REVENUE */}
        {activeTab === "revenue" && (
          <div className="space-y-3">
            <div className="bg-white p-4 rounded-xl border border-slate-200">
              <h2 className="text-xs font-bold uppercase text-slate-500">Financial Summary</h2>
              <div className="mt-2 text-3xl font-black text-slate-900">₹48,500.00</div>
              <p className="text-xs text-emerald-600 font-semibold mt-1">✓ Collected today across 10 settled invoices</p>

              <div className="mt-4 pt-4 border-t border-slate-100 space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-500">UPI Payments (PhonePe, GPay):</span>
                  <span className="font-bold text-slate-900">₹32,400.00</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Cash Collections:</span>
                  <span className="font-bold text-slate-900">₹16,100.00</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Pending Balance:</span>
                  <span className="font-bold text-amber-600">₹24,800.00 (8 Patients)</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB: ALERTS */}
        {activeTab === "alerts" && (
          <div className="space-y-3">
            <h2 className="text-xs font-bold uppercase text-slate-500 px-1">Inventory Depletion Warnings</h2>
            {initialStockAlerts.map((stk) => (
              <div key={stk.id} className="p-3.5 bg-white rounded-xl border border-rose-200 shadow-xs flex items-center justify-between">
                <div>
                  <h3 className="text-xs font-bold text-slate-900">{stk.name}</h3>
                  <p className="text-[11px] text-slate-500">
                    Remaining: <b className="text-rose-600">{stk.current} {stk.unit}</b> (Min: {stk.min})
                  </p>
                </div>
                <span className="text-[10px] font-bold px-2 py-1 bg-rose-50 text-rose-700 border border-rose-200 rounded-md">
                  RESTOCK
                </span>
              </div>
            ))}

            <h2 className="text-xs font-bold uppercase text-slate-500 px-1 mt-4">Disaster Recovery & System Status</h2>
            <div className="p-3.5 bg-white rounded-xl border border-emerald-200 shadow-xs flex items-center justify-between">
              <div>
                <h3 className="text-xs font-bold text-slate-900">AES-256 Daily Backup</h3>
                <p className="text-[11px] text-emerald-600 font-semibold">Verified on disk (SHA-256 match)</p>
              </div>
              <span className="text-[10px] font-bold px-2 py-1 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-md">
                100% HEALTHY
              </span>
            </div>
          </div>
        )}
      </main>

      {/* Safe Action Modal: Add Note */}
      {modalType === "note" && selectedAppt && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-end sm:items-center justify-center p-4">
          <div className="bg-white w-full max-w-md rounded-2xl p-5 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-bold text-slate-900">Add Clinical Note</h2>
              <button onClick={() => setModalType(null)} className="text-slate-400 hover:text-slate-600 text-lg">✕</button>
            </div>
            <p className="text-xs text-slate-500 font-medium">For patient: <b>{selectedAppt.patientName}</b></p>
            <textarea
              rows={4}
              value={noteText}
              onChange={(e) => setNoteText(e.target.value)}
              placeholder="Enter clinical observations, internal instructions, or follow-up notes..."
              className="w-full p-3 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:bg-white focus:ring-2 focus:ring-teal-500 focus:outline-hidden"
            />
            <div className="grid grid-cols-2 gap-2 pt-2">
              <button
                onClick={() => setModalType(null)}
                className="h-11 rounded-xl bg-slate-100 text-slate-700 text-xs font-semibold hover:bg-slate-200"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveNote}
                className="h-11 rounded-xl bg-teal-600 text-white text-xs font-semibold hover:bg-teal-700"
              >
                Save Note
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Safe Action Modal: Reschedule */}
      {modalType === "reschedule" && selectedAppt && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-end sm:items-center justify-center p-4">
          <div className="bg-white w-full max-w-md rounded-2xl p-5 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-bold text-slate-900">Reschedule Visit</h2>
              <button onClick={() => setModalType(null)} className="text-slate-400 hover:text-slate-600 text-lg">✕</button>
            </div>
            <p className="text-xs text-slate-500 font-medium">Select a new slot for: <b>{selectedAppt.patientName}</b></p>
            <div className="grid grid-cols-2 gap-2">
              {["11:00 AM", "01:30 PM", "03:00 PM", "04:30 PM"].map((slot) => (
                <button
                  key={slot}
                  onClick={() => handleSaveReschedule(slot)}
                  className="h-12 border border-slate-200 rounded-xl text-xs font-bold text-slate-800 hover:bg-teal-50 hover:border-teal-500 active:bg-teal-100 transition"
                >
                  ⏰ {slot}
                </button>
              ))}
            </div>
            <button
              onClick={() => setModalType(null)}
              className="w-full h-11 rounded-xl bg-slate-100 text-slate-700 text-xs font-semibold hover:bg-slate-200 mt-2"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Bottom Touch Bar (One-Thumb Mobile Navigation) */}
      <footer className="fixed bottom-0 left-0 right-0 z-40 bg-white border-t border-slate-200 px-4 py-2 flex items-center justify-around shadow-md">
        <button
          onClick={() => setActiveTab("today")}
          className={`flex flex-col items-center py-1 px-2 rounded-lg text-[10px] font-bold ${activeTab === "today" ? "text-teal-600 font-black" : "text-slate-500"}`}
        >
          <span className="text-base">📅</span>
          Today
        </button>
        <button
          onClick={() => setActiveTab("tomorrow")}
          className={`flex flex-col items-center py-1 px-2 rounded-lg text-[10px] font-bold ${activeTab === "tomorrow" ? "text-teal-600 font-black" : "text-slate-500"}`}
        >
          <span className="text-base">⏩</span>
          Tomorrow
        </button>
        <button
          onClick={() => setActiveTab("calendar")}
          className={`flex flex-col items-center py-1 px-2 rounded-lg text-[10px] font-bold ${activeTab === "calendar" ? "text-teal-600 font-black" : "text-slate-500"}`}
        >
          <span className="text-base">🗓️</span>
          Week
        </button>
        <button
          onClick={() => setActiveTab("revenue")}
          className={`flex flex-col items-center py-1 px-2 rounded-lg text-[10px] font-bold ${activeTab === "revenue" ? "text-teal-600 font-black" : "text-slate-500"}`}
        >
          <span className="text-base">₹</span>
          Revenue
        </button>
        <button
          onClick={() => setActiveTab("alerts")}
          className={`flex flex-col items-center py-1 px-2 rounded-lg text-[10px] font-bold ${activeTab === "alerts" ? "text-teal-600 font-black" : "text-slate-500"}`}
        >
          <span className="text-base">🔔</span>
          Alerts
        </button>
      </footer>
    </div>
  );
}
