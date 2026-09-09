"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useAuthSession } from "./auth-session";

import { AIAssistantDrawer } from "@/components/ai/AIAssistantDrawer";

type Appointment = { time: string; patient: string; procedure: string; clinician: string; state: "Confirmed" | "In chair" | "Due" };

const appointments: Appointment[] = [
  { time: "09:00", patient: "Aarav Mehta", procedure: "Routine check-up", clinician: "Dr. N. Shah", state: "In chair" },
  { time: "10:15", patient: "Riya Kapoor", procedure: "Root canal review", clinician: "Dr. N. Shah", state: "Confirmed" },
  { time: "11:30", patient: "Arjun Rao", procedure: "Implant consultation", clinician: "Dr. M. Iyer", state: "Confirmed" },
  { time: "14:00", patient: "Isha Verma", procedure: "Dental cleaning", clinician: "Dr. M. Iyer", state: "Due" },
];
const navigation = [
  { name: "Overview", href: "/" },
  { name: "Appointments", href: "/appointments" },
  { name: "Patients", href: "/patients" },
  { name: "Treatments", href: "/treatments" },
  { name: "Prescriptions", href: "/prescriptions" },
  { name: "Odontogram", href: "#" },
  { name: "Billing", href: "/billing" },
  { name: "Insurance & Claims", href: "/insurance" },
  { name: "Inventory", href: "/inventory" },
  { name: "Reports", href: "/billing/reports" },
  { name: "Notifications", href: "/notifications" },
  { name: "Messages", href: "/messages" },
  { name: "Consent Forms", href: "/consents" },
  { name: "Recalls", href: "/follow-ups" },
  { name: "Patient Portal", href: "/portal" },
  { name: "Enterprise Network", href: "/enterprise" },
  { name: "HR & Workforce", href: "/hr" },
  { name: "AI Studio", href: "/ai" },
];

function Icon({ name }: { name: "grid" | "calendar" | "patient" | "plus" | "search" | "bell" | "arrow" }) {
  const paths = { grid: <><rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" /><rect x="3" y="14" width="7" height="7" /><rect x="14" y="14" width="7" height="7" /></>, calendar: <><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M8 3v4M16 3v4M3 10h18" /></>, patient: <><circle cx="12" cy="8" r="4" /><path d="M4 21c.8-4.2 3.4-6 8-6s7.2 1.8 8 6" /></>, plus: <><path d="M12 5v14M5 12h14" /></>, search: <><circle cx="11" cy="11" r="6" /><path d="m16 16 4 4" /></>, bell: <><path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4" /></>, arrow: <path d="m9 18 6-6-6-6" /> };
  return <svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">{paths[name]}</svg>;
}

export default function Home() {
  const session = useAuthSession();
  const [active, setActive] = useState("Overview");
  const [query, setQuery] = useState("");
  const visible = useMemo(() => appointments.filter((item) => item.patient.toLowerCase().includes(query.toLowerCase())), [query]);
  if (session.state === "loading") return <main className="session-loading">Restoring secure session...</main>;
  return <main className="app-shell">
    <aside className="sidebar"><div className="brand"><span className="brand-mark">DC</span><span>DentalCare <b>Pro</b></span></div><div className="clinic-switch"><span className="clinic-dot" /><span><small>Current clinic</small>BrightSmile Dental</span><span className="chevron">⌄</span></div><nav aria-label="Primary navigation">{navigation.map((item, index) => <Link key={item.name} href={item.href} className={active === item.name ? "nav-item active" : "nav-item"} onClick={() => setActive(item.name)}><span className="nav-icon">{index === 0 ? <Icon name="grid" /> : index === 1 ? <Icon name="calendar" /> : index === 2 ? <Icon name="patient" /> : <span className="nav-bullet" />}</span>{item.name}</Link>)}</nav><div className="sidebar-bottom"><button className="nav-item"><span className="nav-icon">◌</span>Settings</button><div className="user-panel"><div className="avatar">AS</div><span>Dr. Ananya Shah<small>Clinic administrator</small></span><span className="dots">•••</span></div></div></aside>
    <section className="workspace"><header className="topbar"><div className="mobile-brand">DentalCare <b>Pro</b></div><div className="search"><Icon name="search" /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search patients, appointments..." aria-label="Search patients and appointments" /><kbd>Ctrl K</kbd></div><Link href="/notifications" className="icon-button" aria-label="Notifications"><Icon name="bell" /><span className="notification-dot" /></Link><Link href="/patients/new" className="new-button"><Icon name="plus" />New patient</Link></header>
      <div className="content"><div className="page-heading"><div><p className="eyebrow">Tuesday, 2 September</p><h1>Good morning, Dr. Shah</h1><p className="subheading">Here is what needs your attention today.</p></div><Link href="/appointments?tab=calendar" className="date-button"><Icon name="calendar" /> Today <span>⌄</span></Link></div>
        <section className="metrics" aria-label="Today's practice metrics"><article><p>Today&apos;s appointments</p><strong>24</strong><span className="positive">+4 from yesterday</span><div className="metric-bar teal" /></article><article><p>Today&apos;s revenue</p><strong>₹48,500</strong><span className="positive">12% above average</span><div className="metric-bar green" /></article><article><p>Pending payments</p><strong>₹82,700</strong><span className="warning">8 invoices due</span><div className="metric-bar amber" /></article><article><p>New patients</p><strong>6</strong><span className="muted">This week</span><div className="metric-bar blue" /></article></section>
        <div className="dashboard-grid"><section className="schedule-panel"><div className="panel-heading"><div><h2>Today&apos;s schedule</h2><p>{visible.length} appointments across 3 chairs</p></div><Link href="/appointments?tab=calendar" className="text-button">View calendar <Icon name="arrow" /></Link></div><div className="schedule-list">{visible.map((appointment) => <article className="appointment" key={appointment.patient}><time>{appointment.time}</time><div className="appointment-line" /><div className="patient-avatar">{appointment.patient.split(" ").map((name) => name[0]).join("")}</div><div className="appointment-info"><strong>{appointment.patient}</strong><span>{appointment.procedure} · {appointment.clinician}</span></div><span className={`status ${appointment.state.toLowerCase().replace(" ", "-")}`}>{appointment.state}</span><Link href="/appointments" className="row-action" aria-label={`Open ${appointment.patient}`}><Icon name="arrow" /></Link></article>)}</div></section>
          <aside className="right-column"><section className="action-panel"><h2>Quick actions</h2><div className="quick-actions"><Link href="/patients/new" className="button"><span className="quick-icon cyan"><Icon name="plus" /></span>Add patient</Link><Link href="/appointments?book=true" className="button"><span className="quick-icon violet"><Icon name="calendar" /></span>Book visit</Link><Link href="/ai" className="button"><span className="quick-icon cyan">✨</span>AI Studio</Link><Link href="/prescriptions/new" className="button"><span className="quick-icon teal">℞</span>Write Rx</Link><Link href="/inventory" className="button"><span className="quick-icon cyan">📦</span>Inventory</Link><Link href="/billing/new" className="button"><span className="quick-icon amber">₹</span>Create invoice</Link><Link href="/insurance" className="button"><span className="quick-icon teal">🛡️</span>Insurance</Link><Link href="/enterprise" className="button"><span className="quick-icon indigo">🏢</span>Enterprise</Link><Link href="/hr" className="button"><span className="quick-icon teal">👥</span>HR & Staff</Link><Link href="/treatments/new" className="button"><span className="quick-icon rose">⌁</span>Start treatment</Link></div></section><section className="alert-panel"><div className="alert-title"><span className="alert-symbol">!</span><div><h2>Inventory attention</h2><p>3 items need replenishing</p></div><Link href="/inventory" className="row-action" aria-label="Open inventory"><Icon name="arrow" /></Link></div><div className="stock-row"><span>Composite resin A2</span><b>4 left</b></div><div className="stock-row"><span>Examination gloves M</span><b>12 boxes</b></div></section></aside>
        </div></div></section>
      <AIAssistantDrawer />
  </main>;
}
