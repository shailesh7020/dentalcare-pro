"use client";

import React, { useMemo, useState } from "react";
import Link from "next/link";
import {
  Calendar,
  Users,
  Plus,
  ArrowUpRight,
  TrendingUp,
  CreditCard,
  Package,
  AlertTriangle,
  Clock,
  Sparkles,
  FileText,
  Building2,
  Stethoscope,
  ChevronRight,
  CheckCircle2,
  Activity,
  IndianRupee,
} from "lucide-react";
import { useAuthSession } from "./auth-session";
import { AppShell } from "@/components/layout/AppShell";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

type AppointmentItem = {
  id: string;
  time: string;
  chair: string;
  patient: string;
  procedure: string;
  clinician: string;
  state: "Confirmed" | "In chair" | "Due";
};

const TODAY_APPOINTMENTS: AppointmentItem[] = [
  {
    id: "apt-1",
    time: "09:00 AM",
    chair: "Chair 1",
    patient: "Aarav Mehta",
    procedure: "Routine Dental Check-up",
    clinician: "Dr. N. Shah",
    state: "In chair",
  },
  {
    id: "apt-2",
    time: "10:15 AM",
    chair: "Chair 2",
    patient: "Riya Kapoor",
    procedure: "Root Canal Treatment - Review",
    clinician: "Dr. N. Shah",
    state: "Confirmed",
  },
  {
    id: "apt-3",
    time: "11:30 AM",
    chair: "Chair 1",
    patient: "Arjun Rao",
    procedure: "Titanium Implant Consultation",
    clinician: "Dr. M. Iyer",
    state: "Confirmed",
  },
  {
    id: "apt-4",
    time: "02:00 PM",
    chair: "Chair 3",
    patient: "Isha Verma",
    procedure: "Full Ultrasonic Cleaning",
    clinician: "Dr. M. Iyer",
    state: "Due",
  },
  {
    id: "apt-5",
    time: "03:30 PM",
    chair: "Chair 2",
    patient: "Vikram Malhotra",
    procedure: "Crown Preparation - Tooth #30",
    clinician: "Dr. N. Shah",
    state: "Due",
  },
];

export default function HomePage() {
  const session = useAuthSession();
  const [filterChair, setFilterChair] = useState<string>("ALL");

  const filteredAppointments = useMemo(() => {
    if (filterChair === "ALL") return TODAY_APPOINTMENTS;
    return TODAY_APPOINTMENTS.filter((apt) => apt.chair === filterChair);
  }, [filterChair]);

  if (session.state === "loading") {
    return (
      <main className="session-loading">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin" />
          <p className="text-slate-600 dark:text-slate-400 text-sm font-medium">
            Restoring secure clinic session...
          </p>
        </div>
      </main>
    );
  }

  return (
    <AppShell>
      <div className="space-y-8">
        {/* ------------------------------------------------------------------
            1. Welcome Hero Header Banner
            ------------------------------------------------------------------ */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-2">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[11px] font-bold uppercase tracking-wider text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/60 px-2.5 py-0.5 rounded-full border border-blue-200 dark:border-blue-900/60">
                Tuesday, 2 September 2026
              </span>
              <span className="text-xs text-slate-400 dark:text-slate-500">•</span>
              <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block animate-pulse" />
                Clinic Open (3 Active Chairs)
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
              Good morning, Dr. Shah
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
              Here is what is scheduled for your practice today across all operatory chairs.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Link href="/appointments?tab=calendar">
              <Button variant="outline" size="sm" leftIcon={<Calendar className="w-4 h-4" />}>
                Calendar View
              </Button>
            </Link>
            <Link href="/appointments?book=true">
              <Button variant="primary" size="sm" leftIcon={<Plus className="w-4 h-4" />}>
                Book Appointment
              </Button>
            </Link>
          </div>
        </div>

        {/* ------------------------------------------------------------------
            2. KPI Practice Metrics Cards (4 Columns)
            ------------------------------------------------------------------ */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
          {/* Metric 1: Appointments */}
          <Card className="relative overflow-hidden group hover:border-blue-300 dark:hover:border-blue-800 transition-all">
            <div className="absolute top-0 left-0 right-0 h-1 bg-blue-600" />
            <CardContent className="p-5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  Today&apos;s Appointments
                </span>
                <span className="p-2 rounded-xl bg-blue-50 dark:bg-blue-950/50 text-blue-600 dark:text-blue-400">
                  <Calendar className="w-4 h-4" />
                </span>
              </div>
              <div className="mt-3 flex items-baseline gap-2">
                <span className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">
                  24
                </span>
                <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 flex items-center">
                  <TrendingUp className="w-3 h-3 mr-0.5" /> +4 vs yday
                </span>
              </div>
              <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">
                4 completed · 1 in chair · 19 scheduled
              </p>
            </CardContent>
          </Card>

          {/* Metric 2: Today's Revenue */}
          <Card className="relative overflow-hidden group hover:border-emerald-300 dark:hover:border-emerald-800 transition-all">
            <div className="absolute top-0 left-0 right-0 h-1 bg-emerald-500" />
            <CardContent className="p-5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  Today&apos;s Collections
                </span>
                <span className="p-2 rounded-xl bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400">
                  <IndianRupee className="w-4 h-4" />
                </span>
              </div>
              <div className="mt-3 flex items-baseline gap-2">
                <span className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">
                  ₹48,500
                </span>
                <span className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 flex items-center">
                  <TrendingUp className="w-3 h-3 mr-0.5" /> +12% avg
                </span>
              </div>
              <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">
                Cash: ₹18.5k · UPI: ₹22k · Cards: ₹8k
              </p>
            </CardContent>
          </Card>

          {/* Metric 3: Pending Invoices */}
          <Card className="relative overflow-hidden group hover:border-amber-300 dark:hover:border-amber-800 transition-all">
            <div className="absolute top-0 left-0 right-0 h-1 bg-amber-500" />
            <CardContent className="p-5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  Pending Receivables
                </span>
                <span className="p-2 rounded-xl bg-amber-50 dark:bg-amber-950/50 text-amber-600 dark:text-amber-400">
                  <CreditCard className="w-4 h-4" />
                </span>
              </div>
              <div className="mt-3 flex items-baseline gap-2">
                <span className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">
                  ₹82,700
                </span>
                <span className="text-xs font-semibold text-amber-600 dark:text-amber-400">
                  8 invoices due
                </span>
              </div>
              <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">
                3 overdue (&gt;30 days)
              </p>
            </CardContent>
          </Card>

          {/* Metric 4: New Patients */}
          <Card className="relative overflow-hidden group hover:border-teal-300 dark:hover:border-teal-800 transition-all">
            <div className="absolute top-0 left-0 right-0 h-1 bg-teal-500" />
            <CardContent className="p-5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                  New Patients Registered
                </span>
                <span className="p-2 rounded-xl bg-teal-50 dark:bg-teal-950/50 text-teal-600 dark:text-teal-400">
                  <Users className="w-4 h-4" />
                </span>
              </div>
              <div className="mt-3 flex items-baseline gap-2">
                <span className="text-3xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">
                  6
                </span>
                <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">
                  This week
                </span>
              </div>
              <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">
                Total active patients: 1,428
              </p>
            </CardContent>
          </Card>
        </div>

        {/* ------------------------------------------------------------------
            3. Main Dashboard Grid: Schedule & Right Actions
            ------------------------------------------------------------------ */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-8">
          {/* Left 2 Columns: Live Today's Schedule */}
          <div className="lg:col-span-2 space-y-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-4">
                <div>
                  <CardTitle className="text-base sm:text-lg">
                    Today&apos;s Clinic Schedule
                  </CardTitle>
                  <CardDescription>
                    Live queue & room allocation across all operatory chairs
                  </CardDescription>
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex items-center bg-slate-100 dark:bg-slate-800 p-1 rounded-xl text-xs font-medium">
                    {["ALL", "Chair 1", "Chair 2", "Chair 3"].map((chair) => (
                      <button
                        key={chair}
                        onClick={() => setFilterChair(chair)}
                        className={`px-2.5 py-1 rounded-lg transition-colors cursor-pointer ${
                          filterChair === chair
                            ? "bg-white dark:bg-slate-700 text-slate-900 dark:text-slate-100 font-semibold shadow-2xs"
                            : "text-slate-500 dark:text-slate-400 hover:text-slate-800"
                        }`}
                      >
                        {chair}
                      </button>
                    ))}
                  </div>
                  <Link href="/appointments?tab=calendar">
                    <Button variant="ghost" size="sm">
                      View all <ChevronRight className="w-3.5 h-3.5 ml-1" />
                    </Button>
                  </Link>
                </div>
              </CardHeader>

              <CardContent className="p-0 divide-y divide-slate-100 dark:divide-slate-800/60">
                {filteredAppointments.map((appointment) => {
                  const initials = appointment.patient
                    .split(" ")
                    .map((n) => n[0])
                    .join("");
                  return (
                    <div
                      key={appointment.id}
                      className="p-4 sm:p-5 flex items-center justify-between gap-4 hover:bg-slate-50/70 dark:hover:bg-slate-800/40 transition-colors"
                    >
                      {/* Time & Chair */}
                      <div className="flex items-center gap-3">
                        <div className="flex flex-col items-center justify-center w-16 text-center">
                          <span className="text-xs font-bold text-slate-900 dark:text-slate-100">
                            {appointment.time.split(" ")[0]}
                          </span>
                          <span className="text-[10px] text-slate-400 uppercase">
                            {appointment.time.split(" ")[1]}
                          </span>
                          <span className="text-[10px] font-semibold text-blue-600 dark:text-blue-400 mt-0.5">
                            {appointment.chair}
                          </span>
                        </div>

                        <div className="w-px h-10 bg-slate-200 dark:bg-slate-700 hidden sm:block" />

                        {/* Patient & Procedure */}
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-bold text-xs flex items-center justify-center border border-slate-200 dark:border-slate-700 shadow-2xs">
                            {initials}
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                                {appointment.patient}
                              </h4>
                            </div>
                            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                              {appointment.procedure} ·{" "}
                              <span className="font-medium text-slate-600 dark:text-slate-300">
                                {appointment.clinician}
                              </span>
                            </p>
                          </div>
                        </div>
                      </div>

                      {/* Status Badge & Action */}
                      <div className="flex items-center gap-3">
                        <Badge
                          variant={
                            appointment.state === "Confirmed"
                              ? "confirmed"
                              : appointment.state === "In chair"
                              ? "in-chair"
                              : "due"
                          }
                          dot
                        >
                          {appointment.state}
                        </Badge>
                        <Link
                          href="/appointments"
                          className="p-1.5 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
                        >
                          <ChevronRight className="w-4 h-4" />
                        </Link>
                      </div>
                    </div>
                  );
                })}
              </CardContent>
            </Card>
          </div>

          {/* Right Column: Quick Actions & Alerts */}
          <div className="space-y-6">
            {/* Quick Actions Grid */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">Practice Quick Actions</CardTitle>
                <CardDescription>Direct shortcuts to high-frequency tasks</CardDescription>
              </CardHeader>
              <CardContent className="pt-2">
                <div className="grid grid-cols-2 gap-2.5">
                  <Link
                    href="/patients/new"
                    className="flex flex-col items-start p-3 rounded-xl bg-slate-50 dark:bg-slate-800/80 hover:bg-blue-50 dark:hover:bg-blue-950/40 border border-slate-200/80 dark:border-slate-700 transition-colors group text-left"
                  >
                    <span className="p-2 rounded-lg bg-teal-100 dark:bg-teal-950/60 text-teal-700 dark:text-teal-300 mb-2 group-hover:scale-105 transition-transform">
                      <Plus className="w-4 h-4" />
                    </span>
                    <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                      Add Patient
                    </span>
                    <span className="text-[10px] text-slate-400 mt-0.5">
                      New record
                    </span>
                  </Link>

                  <Link
                    href="/appointments?book=true"
                    className="flex flex-col items-start p-3 rounded-xl bg-slate-50 dark:bg-slate-800/80 hover:bg-blue-50 dark:hover:bg-blue-950/40 border border-slate-200/80 dark:border-slate-700 transition-colors group text-left"
                  >
                    <span className="p-2 rounded-lg bg-blue-100 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 mb-2 group-hover:scale-105 transition-transform">
                      <Calendar className="w-4 h-4" />
                    </span>
                    <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                      Book Visit
                    </span>
                    <span className="text-[10px] text-slate-400 mt-0.5">
                      Chair & doctor
                    </span>
                  </Link>

                  <Link
                    href="/ai"
                    className="flex flex-col items-start p-3 rounded-xl bg-slate-50 dark:bg-slate-800/80 hover:bg-purple-50 dark:hover:bg-purple-950/40 border border-slate-200/80 dark:border-slate-700 transition-colors group text-left"
                  >
                    <span className="p-2 rounded-lg bg-purple-100 dark:bg-purple-950/60 text-purple-700 dark:text-purple-300 mb-2 group-hover:scale-105 transition-transform">
                      <Sparkles className="w-4 h-4" />
                    </span>
                    <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                      AI Studio
                    </span>
                    <span className="text-[10px] text-slate-400 mt-0.5">
                      SOAP notes & RAG
                    </span>
                  </Link>

                  <Link
                    href="/prescriptions/new"
                    className="flex flex-col items-start p-3 rounded-xl bg-slate-50 dark:bg-slate-800/80 hover:bg-emerald-50 dark:hover:bg-emerald-950/40 border border-slate-200/80 dark:border-slate-700 transition-colors group text-left"
                  >
                    <span className="p-2 rounded-lg bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 mb-2 group-hover:scale-105 transition-transform">
                      <FileText className="w-4 h-4" />
                    </span>
                    <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                      Write Rx
                    </span>
                    <span className="text-[10px] text-slate-400 mt-0.5">
                      Prescriptions
                    </span>
                  </Link>

                  <Link
                    href="/billing/new"
                    className="flex flex-col items-start p-3 rounded-xl bg-slate-50 dark:bg-slate-800/80 hover:bg-amber-50 dark:hover:bg-amber-950/40 border border-slate-200/80 dark:border-slate-700 transition-colors group text-left"
                  >
                    <span className="p-2 rounded-lg bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 mb-2 group-hover:scale-105 transition-transform">
                      <CreditCard className="w-4 h-4" />
                    </span>
                    <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                      Create Bill
                    </span>
                    <span className="text-[10px] text-slate-400 mt-0.5">
                      Invoice & GST
                    </span>
                  </Link>

                  <Link
                    href="/inventory"
                    className="flex flex-col items-start p-3 rounded-xl bg-slate-50 dark:bg-slate-800/80 hover:bg-sky-50 dark:hover:bg-sky-950/40 border border-slate-200/80 dark:border-slate-700 transition-colors group text-left"
                  >
                    <span className="p-2 rounded-lg bg-sky-100 dark:bg-sky-950/60 text-sky-700 dark:text-sky-300 mb-2 group-hover:scale-105 transition-transform">
                      <Package className="w-4 h-4" />
                    </span>
                    <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">
                      Supplies
                    </span>
                    <span className="text-[10px] text-slate-400 mt-0.5">
                      Stock inventory
                    </span>
                  </Link>
                </div>
              </CardContent>
            </Card>

            {/* Inventory Alerts Card */}
            <Card className="border-amber-200 dark:border-amber-900/60 bg-amber-50/30 dark:bg-amber-950/20">
              <CardHeader className="pb-2 border-b border-amber-200/60 dark:border-amber-900/40">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="p-1.5 rounded-lg bg-amber-100 dark:bg-amber-950 text-amber-700 dark:text-amber-400">
                      <AlertTriangle className="w-4 h-4" />
                    </span>
                    <CardTitle className="text-sm font-semibold text-amber-900 dark:text-amber-300">
                      Supplies Requiring Attention
                    </CardTitle>
                  </div>
                  <Link
                    href="/inventory"
                    className="text-xs font-semibold text-amber-700 dark:text-amber-400 hover:underline"
                  >
                    View inventory
                  </Link>
                </div>
              </CardHeader>
              <CardContent className="pt-3 space-y-3">
                <div className="flex items-center justify-between text-xs">
                  <div>
                    <p className="font-semibold text-slate-800 dark:text-slate-200">
                      Composite Resin A2 Syringe
                    </p>
                    <p className="text-[11px] text-slate-500">
                      Restorative Consumable
                    </p>
                  </div>
                  <span className="text-xs font-bold text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/60 px-2 py-0.5 rounded-md border border-rose-200 dark:border-rose-900">
                    4 left
                  </span>
                </div>

                <div className="flex items-center justify-between text-xs pt-2 border-t border-amber-200/40 dark:border-amber-900/40">
                  <div>
                    <p className="font-semibold text-slate-800 dark:text-slate-200">
                      Examination Latex Gloves (M)
                    </p>
                    <p className="text-[11px] text-slate-500">
                      General Hygiene Box
                    </p>
                  </div>
                  <span className="text-xs font-bold text-amber-700 dark:text-amber-400 bg-amber-100 dark:bg-amber-950/60 px-2 py-0.5 rounded-md border border-amber-200 dark:border-amber-900">
                    12 boxes
                  </span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
