"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Calendar,
  Users,
  Stethoscope,
  FileText,
  CreditCard,
  TrendingUp,
  Package,
  ShieldCheck,
  Building2,
  Briefcase,
  Sparkles,
  Bell,
  MessageSquare,
  Search,
  Plus,
  Menu,
  X,
  ChevronLeft,
  ChevronRight,
  LogOut,
  History,
  ShieldAlert,
} from "lucide-react";
import { CommandPalette } from "@/components/ui/command-palette";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { RoleFocusSwitcher, RoleFocusMode } from "@/components/ui/role-focus-switcher";
import { AIAssistantDrawer } from "@/components/ai/AIAssistantDrawer";

interface NavGroup {
  name: string;
  items: {
    name: string;
    href: string;
    icon: React.ComponentType<{ className?: string }>;
    badge?: string;
    focusGroups?: RoleFocusMode[];
  }[];
}

const NAVIGATION_GROUPS: NavGroup[] = [
  {
    name: "Clinical Workspace",
    items: [
      { name: "Overview", href: "/", icon: LayoutDashboard },
      {
        name: "Appointments",
        href: "/appointments",
        icon: Calendar,
        focusGroups: ["all", "receptionist", "dentist"],
      },
      {
        name: "Patients",
        href: "/patients",
        icon: Users,
        focusGroups: ["all", "receptionist", "dentist"],
      },
      {
        name: "Treatments",
        href: "/treatments",
        icon: Stethoscope,
        focusGroups: ["all", "dentist"],
      },
      {
        name: "Prescriptions",
        href: "/prescriptions",
        icon: FileText,
        focusGroups: ["all", "dentist"],
      },
      {
        name: "Consent Forms",
        href: "/consents",
        icon: ShieldCheck,
        focusGroups: ["all", "dentist", "receptionist"],
      },
      {
        name: "Recalls & Follow-ups",
        href: "/follow-ups",
        icon: History,
        focusGroups: ["all", "receptionist"],
      },
    ],
  },
  {
    name: "Finance & Operations",
    items: [
      {
        name: "Billing & Invoices",
        href: "/billing",
        icon: CreditCard,
        focusGroups: ["all", "receptionist", "admin"],
      },
      {
        name: "Revenue Reports",
        href: "/billing/reports",
        icon: TrendingUp,
        focusGroups: ["all", "admin"],
      },
      {
        name: "Dental Inventory",
        href: "/inventory",
        icon: Package,
        focusGroups: ["all", "admin"],
      },
      {
        name: "Insurance Claims",
        href: "/insurance",
        icon: ShieldAlert,
        focusGroups: ["all", "admin", "receptionist"],
      },
    ],
  },
  {
    name: "Enterprise & Intelligence",
    items: [
      {
        name: "AI Clinical Studio",
        href: "/ai",
        icon: Sparkles,
        badge: "PRO",
        focusGroups: ["all", "dentist"],
      },
      {
        name: "Clinic Network",
        href: "/enterprise",
        icon: Building2,
        focusGroups: ["all", "admin"],
      },
      {
        name: "Staff & HR",
        href: "/hr",
        icon: Briefcase,
        focusGroups: ["all", "admin"],
      },
      {
        name: "Messages",
        href: "/messages",
        icon: MessageSquare,
      },
      {
        name: "Notifications",
        href: "/notifications",
        icon: Bell,
      },
    ],
  },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [commandOpen, setCommandOpen] = useState(false);
  const [focusMode, setFocusMode] = useState<RoleFocusMode>("all");

  // Close mobile sidebar on route change or Escape
  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && mobileOpen) {
        setMobileOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [mobileOpen]);

  return (
    <div className="min-h-screen flex bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 antialiased selection:bg-blue-500 selection:text-white">
      {/* ----------------------------------------------------------------------
          1. Desktop Dark Sidebar (Slate 900)
          ---------------------------------------------------------------------- */}
      <aside
        className={`hidden md:flex flex-col flex-shrink-0 bg-slate-900 text-slate-300 border-r border-slate-800 transition-all duration-200 z-30 sticky top-0 h-screen ${
          isCollapsed ? "w-[72px]" : "w-[260px]"
        }`}
      >
        {/* Brand Header */}
        <div className="h-16 px-4 flex items-center justify-between border-b border-slate-800/80">
          <Link href="/" className="flex items-center gap-3 overflow-hidden">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-teal-500 flex items-center justify-center text-white font-black text-sm shadow-md flex-shrink-0 tracking-tight">
              DC
            </div>
            {!isCollapsed && (
              <div className="flex flex-col">
                <span className="font-bold text-white tracking-tight text-sm flex items-center gap-1">
                  DentalCare <span className="text-teal-400 font-extrabold text-[11px] bg-teal-950/80 px-1.5 py-0.5 rounded border border-teal-800">PRO</span>
                </span>
                <span className="text-[10px] text-slate-400 font-medium">
                  Enterprise Clinic v20
                </span>
              </div>
            )}
          </Link>
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {isCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
          </button>
        </div>

        {/* Current Clinic Indicator */}
        {!isCollapsed && (
          <div className="mx-3 mt-3 p-2.5 rounded-xl bg-slate-800/60 border border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-2 overflow-hidden">
              <span className="relative flex h-2 w-2 flex-shrink-0">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <div className="truncate">
                <p className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">
                  Clinic Server
                </p>
                <p className="text-xs font-semibold text-white truncate">
                  BrightSmile Dental
                </p>
              </div>
            </div>
            <span className="text-[10px] font-semibold text-emerald-400 bg-emerald-950/60 px-1.5 py-0.5 rounded border border-emerald-800">
              LAN
            </span>
          </div>
        )}

        {/* Navigation Sections */}
        <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
          {NAVIGATION_GROUPS.map((group) => {
            // Filter items based on active focus mode
            const visibleItems = group.items.filter(
              (item) =>
                focusMode === "all" ||
                !item.focusGroups ||
                item.focusGroups.includes(focusMode)
            );

            if (visibleItems.length === 0) return null;

            return (
              <div key={group.name} className="space-y-1">
                {!isCollapsed && (
                  <h4 className="px-3 text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-2">
                    {group.name}
                  </h4>
                )}
                {visibleItems.map((item) => {
                  const isActive =
                    item.href === "/"
                      ? pathname === "/"
                      : pathname.startsWith(item.href);
                  const IconComponent = item.icon;

                  return (
                    <Link
                      key={item.name}
                      href={item.href}
                      title={isCollapsed ? item.name : undefined}
                      className={`flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium transition-all duration-150 ${
                        isActive
                          ? "bg-blue-600 text-white font-semibold shadow-xs"
                          : "text-slate-300 hover:text-white hover:bg-slate-800"
                      } ${isCollapsed ? "justify-center px-2" : ""}`}
                    >
                      <IconComponent
                        className={`w-4 h-4 flex-shrink-0 ${
                          isActive ? "text-white" : "text-slate-400"
                        }`}
                      />
                      {!isCollapsed && (
                        <span className="truncate flex-1">{item.name}</span>
                      )}
                      {!isCollapsed && item.badge && (
                        <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-blue-500/30 text-blue-200 border border-blue-400/30">
                          {item.badge}
                        </span>
                      )}
                    </Link>
                  );
                })}
              </div>
            );
          })}
        </div>

        {/* User Card & Signout Footer */}
        <div className="p-3 border-t border-slate-800/80 bg-slate-950/40">
          <div
            className={`flex items-center gap-3 ${
              isCollapsed ? "justify-center" : "px-2 py-1.5"
            }`}
          >
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-amber-500 to-amber-700 text-white flex items-center justify-center font-bold text-xs flex-shrink-0 shadow-inner">
              AS
            </div>
            {!isCollapsed && (
              <div className="truncate flex-1">
                <p className="text-xs font-semibold text-white truncate">
                  Dr. Ananya Shah
                </p>
                <p className="text-[10px] text-slate-400 truncate">
                  Clinic Administrator
                </p>
              </div>
            )}
            {!isCollapsed && (
              <Link
                href="/login"
                className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-lg transition-colors"
                title="Log out"
              >
                <LogOut size={15} />
              </Link>
            )}
          </div>
        </div>
      </aside>

      {/* ----------------------------------------------------------------------
          2. Mobile Drawer Navigation
          ---------------------------------------------------------------------- */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 flex md:hidden">
          <div
            className="fixed inset-0 bg-slate-950/75"
            onClick={() => setMobileOpen(false)}
          />
          <div className="relative w-72 bg-slate-900 text-slate-300 h-full flex flex-col p-4 shadow-2xl z-10 border-r border-slate-800">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl bg-blue-600 flex items-center justify-center text-white font-bold text-xs">
                  DC
                </div>
                <span className="font-bold text-white text-sm">
                  DentalCare Pro
                </span>
              </div>
              <button
                onClick={() => setMobileOpen(false)}
                className="p-1 text-slate-400 hover:text-white rounded-lg"
              >
                <X size={18} />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto py-4 space-y-4">
              {NAVIGATION_GROUPS.map((group) => (
                <div key={group.name} className="space-y-1">
                  <h4 className="px-2 text-[10px] font-bold uppercase tracking-wider text-slate-500">
                    {group.name}
                  </h4>
                  {group.items.map((item) => {
                    const isActive =
                      item.href === "/"
                        ? pathname === "/"
                        : pathname.startsWith(item.href);
                    const IconComponent = item.icon;
                    return (
                      <Link
                        key={item.name}
                        href={item.href}
                        onClick={() => setMobileOpen(false)}
                        className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-medium ${
                          isActive
                            ? "bg-blue-600 text-white font-semibold"
                            : "text-slate-300 hover:bg-slate-800 hover:text-white"
                        }`}
                      >
                        <IconComponent className="w-4 h-4" />
                        <span>{item.name}</span>
                      </Link>
                    );
                  })}
                </div>
              ))}
            </div>

            <div className="pt-4 border-t border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-full bg-amber-600 text-white flex items-center justify-center font-bold text-xs">
                  AS
                </div>
                <span className="text-xs font-medium text-white">
                  Dr. Shah
                </span>
              </div>
              <ThemeToggle />
            </div>
          </div>
        </div>
      )}

      {/* ----------------------------------------------------------------------
          3. Main Workspace & Top Navigation Bar
          ---------------------------------------------------------------------- */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 sticky top-0 z-20 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 px-4 sm:px-6 lg:px-8 flex items-center justify-between gap-4">
          {/* Left: Mobile hamburger & Search Shortcut */}
          <div className="flex items-center gap-3 flex-1 max-w-lg">
            <button
              onClick={() => setMobileOpen(true)}
              className="md:hidden p-2 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl"
              aria-label="Open menu"
            >
              <Menu size={20} />
            </button>

            {/* Spotlight Search Trigger (Ctrl+K) */}
            <button
              onClick={() => setCommandOpen(true)}
              className="w-full flex items-center justify-between h-10 px-3.5 bg-slate-50 dark:bg-slate-800/80 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-700/80 rounded-xl text-xs text-slate-400 dark:text-slate-400 transition-colors shadow-2xs cursor-pointer"
            >
              <div className="flex items-center gap-2.5">
                <Search className="w-4 h-4 text-slate-400" />
                <span className="hidden sm:inline">Search patients, appointments, actions...</span>
                <span className="sm:hidden">Search...</span>
              </div>
              <kbd className="hidden sm:inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-md bg-white dark:bg-slate-900 text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
                Ctrl K
              </kbd>
            </button>
          </div>

          {/* Right: Role Focus, Quick Actions, Notifications, Theme Toggle */}
          <div className="flex items-center gap-2.5">
            {/* Station Role Focus Mode */}
            <RoleFocusSwitcher onModeChange={setFocusMode} />

            {/* Quick Action Button */}
            <Link
              href="/patients/new"
              className="hidden lg:inline-flex items-center gap-1.5 h-9 px-3.5 text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white rounded-xl shadow-xs transition-colors"
            >
              <Plus size={15} />
              <span>Register Patient</span>
            </Link>

            {/* Notification Bell */}
            <Link
              href="/notifications"
              className="relative p-2 rounded-xl text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              aria-label="Notifications"
            >
              <Bell size={18} />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-rose-500 ring-2 ring-white dark:ring-slate-900" />
            </Link>

            {/* Light / Dark Mode Toggle */}
            <ThemeToggle />
          </div>
        </header>

        {/* Dynamic Page Content */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          {children}
        </main>
      </div>

      {/* Global Command Palette */}
      <CommandPalette open={commandOpen} onOpenChange={setCommandOpen} />

      {/* AI Assistant Drawer */}
      <AIAssistantDrawer />
    </div>
  );
}
