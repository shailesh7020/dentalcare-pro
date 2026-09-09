"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import React from "react";
import {
  Calendar,
  CreditCard,
  FileSignature,
  FileText,
  Home,
  LogOut,
  MessageSquare,
  Pill,
  Smile,
  User,
} from "lucide-react";

interface PortalShellProps {
  children: React.ReactNode;
  patientName?: string;
  clinicName?: string;
}

export function PortalShell({ children, patientName = "Donna Noble", clinicName = "City Dental Care" }: PortalShellProps) {
  const pathname = usePathname();

  const navItems = [
    { name: "Dashboard", href: "/portal", icon: Home },
    { name: "Appointments", href: "/portal/appointments", icon: Calendar },
    { name: "Prescriptions", href: "/portal/prescriptions", icon: Pill },
    { name: "Invoices & Billing", href: "/portal/billing", icon: CreditCard },
    { name: "Treatments & Teeth", href: "/portal/treatments", icon: Smile },
    { name: "Consent Forms", href: "/portal/forms", icon: FileSignature },
    { name: "Messages", href: "/portal/messages", icon: MessageSquare },
  ];

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col">
      {/* Top Navbar */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex items-center justify-between h-16">
          <div className="flex items-center gap-4">
            <Link href="/portal" className="flex items-center gap-2">
              <div className="w-9 h-9 rounded-xl bg-teal-600 text-white flex items-center justify-center font-black text-base shadow-sm">
                DC
              </div>
              <div>
                <span className="font-bold text-slate-900 text-sm sm:text-base">DentalCare Pro</span>
                <span className="text-[10px] block font-semibold text-teal-700 uppercase tracking-wider">Patient Portal</span>
              </div>
            </Link>
            <span className="hidden sm:inline-block text-slate-300">|</span>
            <span className="hidden sm:inline-block text-xs font-semibold text-slate-500 bg-slate-100 px-2.5 py-1 rounded-md">
              {clinicName}
            </span>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-teal-100 text-teal-800 flex items-center justify-center font-bold text-xs">
                {patientName.split(" ").map((n) => n[0]).join("")}
              </div>
              <div className="hidden md:block text-left">
                <p className="text-xs font-bold text-slate-900 leading-tight">{patientName}</p>
                <p className="text-[10px] text-slate-500">P-4401</p>
              </div>
            </div>

            <Link
              href="/portal/login"
              className="p-2 text-slate-400 hover:text-rose-600 hover:bg-slate-100 rounded-lg transition"
              title="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </Link>
          </div>
        </div>

        {/* Secondary Sub-nav Links */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex items-center gap-1 overflow-x-auto border-t border-slate-100 py-1 text-xs">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-medium whitespace-nowrap transition ${
                  isActive
                    ? "bg-teal-50 text-teal-700 font-bold"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? "text-teal-600" : "text-slate-400"}`} />
                {item.name}
              </Link>
            );
          })}
        </div>
      </header>

      {/* Main Body */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-4 text-center text-xs text-slate-400">
        DentalCare Pro Patient Portal &copy; 2026. Certified HIPAA & GDPR Compliant. Emergency dental service: 1-800-DENTAL.
      </footer>
    </div>
  );
}
