"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Users,
  Clock,
  CalendarDays,
  PlaneTakeoff,
  DollarSign,
  Award,
  GraduationCap,
  Briefcase,
  UserCheck,
  Sparkles,
  LayoutDashboard,
} from "lucide-react";

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

const navItems: NavItem[] = [
  { name: "HR Hub", href: "/hr", icon: LayoutDashboard },
  { name: "Employees", href: "/hr/employees", icon: Users },
  { name: "Attendance", href: "/hr/attendance", icon: Clock },
  { name: "Shift Planner", href: "/hr/shifts", icon: CalendarDays },
  { name: "Leave", href: "/hr/leave", icon: PlaneTakeoff },
  { name: "Payroll", href: "/hr/payroll", icon: DollarSign },
  { name: "Performance", href: "/hr/performance", icon: Award },
  { name: "Credentialing", href: "/hr/training", icon: GraduationCap },
  { name: "Recruitment", href: "/hr/recruitment", icon: Briefcase },
  { name: "Self-Service", href: "/hr/self-service", icon: UserCheck },
  { name: "AI Workforce", href: "/hr/ai", icon: Sparkles },
];

export function HRNav() {
  const pathname = usePathname();

  return (
    <div className="bg-white border-b border-slate-200 sticky top-0 z-20 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-teal-50 text-teal-700 rounded-lg border border-teal-200">
              <Users className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-slate-900 text-lg tracking-tight">Human Resources & Workforce</span>
                <span className="inline-flex items-center gap-1 text-[11px] font-medium bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded-full border border-emerald-200">
                  <Sparkles className="w-3 h-3" /> HRMS & Payroll
                </span>
              </div>
              <p className="text-xs text-slate-500">Employee lifecycle, shift rosters, attendance punches, payroll runs & doctor credentials</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/hr/employees"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-xs font-semibold shadow-xs transition-colors"
            >
              <Users className="w-3.5 h-3.5" /> Directory
            </Link>
            <Link
              href="/hr/self-service"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition-colors"
            >
              <UserCheck className="w-3.5 h-3.5" /> Staff Portal
            </Link>
          </div>
        </div>
      </div>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 border-t border-slate-100">
        <nav className="flex space-x-1 overflow-x-auto py-2 scrollbar-none" aria-label="HR Subsections">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`inline-flex items-center gap-2 px-3 py-1.5 text-xs font-medium rounded-md whitespace-nowrap transition-colors ${
                  isActive
                    ? "bg-teal-50 text-teal-700 font-semibold shadow-2xs border border-teal-200"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? "text-teal-600" : "text-slate-400"}`} />
                {item.name}
              </Link>
            );
          })}
        </nav>
      </div>
    </div>
  );
}
