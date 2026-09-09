"use client";

import React, { useEffect, useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import {
  Calendar,
  Users,
  FileText,
  CreditCard,
  Package,
  Sparkles,
  Search,
  Plus,
  Shield,
  Building2,
  Bell,
  Stethoscope,
  Activity,
  History,
  X,
} from "lucide-react";

interface CommandItem {
  id: string;
  title: string;
  category: "Quick Actions" | "Clinical" | "Operations & Finance" | "System";
  icon: React.ReactNode;
  href: string;
  keywords?: string[];
}

const COMMANDS: CommandItem[] = [
  // Quick Actions
  {
    id: "new-patient",
    title: "Register New Patient",
    category: "Quick Actions",
    icon: <Plus className="w-4 h-4 text-teal-600" />,
    href: "/patients/new",
    keywords: ["add", "create", "patient", "register"],
  },
  {
    id: "book-visit",
    title: "Book Appointment",
    category: "Quick Actions",
    icon: <Calendar className="w-4 h-4 text-blue-600" />,
    href: "/appointments?book=true",
    keywords: ["schedule", "appointment", "calendar", "visit"],
  },
  {
    id: "new-invoice",
    title: "Create Invoice / Bill",
    category: "Quick Actions",
    icon: <CreditCard className="w-4 h-4 text-amber-600" />,
    href: "/billing/new",
    keywords: ["billing", "payment", "invoice", "receipt"],
  },
  {
    id: "new-rx",
    title: "Write Prescription",
    category: "Quick Actions",
    icon: <FileText className="w-4 h-4 text-emerald-600" />,
    href: "/prescriptions/new",
    keywords: ["rx", "medicine", "prescription", "drugs"],
  },
  {
    id: "ai-studio",
    title: "AI Clinical Assistant",
    category: "Quick Actions",
    icon: <Sparkles className="w-4 h-4 text-purple-600" />,
    href: "/ai",
    keywords: ["ai", "assistant", "soap", "summary", "intelligence"],
  },

  // Clinical
  {
    id: "nav-patients",
    title: "Patient Electronic Records",
    category: "Clinical",
    icon: <Users className="w-4 h-4 text-teal-600" />,
    href: "/patients",
    keywords: ["patients", "records", "chart", "emr", "directory"],
  },
  {
    id: "nav-appointments",
    title: "Appointments Calendar & Queue",
    category: "Clinical",
    icon: <Calendar className="w-4 h-4 text-blue-600" />,
    href: "/appointments",
    keywords: ["schedule", "appointments", "chairs", "dentists"],
  },
  {
    id: "nav-treatments",
    title: "Treatments & Clinical Plans",
    category: "Clinical",
    icon: <Stethoscope className="w-4 h-4 text-rose-600" />,
    href: "/treatments",
    keywords: ["treatment", "procedures", "plans", "clinical"],
  },
  {
    id: "nav-consents",
    title: "Digital Consent Forms",
    category: "Clinical",
    icon: <Shield className="w-4 h-4 text-sky-600" />,
    href: "/consents",
    keywords: ["consent", "forms", "signature", "legal"],
  },
  {
    id: "nav-recalls",
    title: "Patient Recalls & Follow-ups",
    category: "Clinical",
    icon: <History className="w-4 h-4 text-indigo-600" />,
    href: "/follow-ups",
    keywords: ["recall", "follow-up", "reminder", "checkup"],
  },

  // Operations & Finance
  {
    id: "nav-billing",
    title: "Billing & Invoicing Directory",
    category: "Operations & Finance",
    icon: <CreditCard className="w-4 h-4 text-amber-600" />,
    href: "/billing",
    keywords: ["billing", "payments", "invoices", "gst"],
  },
  {
    id: "nav-reports",
    title: "Revenue & Financial Analytics",
    category: "Operations & Finance",
    icon: <Activity className="w-4 h-4 text-emerald-600" />,
    href: "/billing/reports",
    keywords: ["reports", "revenue", "analytics", "stats"],
  },
  {
    id: "nav-inventory",
    title: "Inventory & Dental Supplies",
    category: "Operations & Finance",
    icon: <Package className="w-4 h-4 text-blue-600" />,
    href: "/inventory",
    keywords: ["inventory", "stock", "supplies", "medicines"],
  },
  {
    id: "nav-enterprise",
    title: "Enterprise Clinic Network",
    category: "Operations & Finance",
    icon: <Building2 className="w-4 h-4 text-indigo-600" />,
    href: "/enterprise",
    keywords: ["enterprise", "branches", "multi-clinic", "network"],
  },

  // System
  {
    id: "nav-notifications",
    title: "System Notifications",
    category: "System",
    icon: <Bell className="w-4 h-4 text-slate-600" />,
    href: "/notifications",
    keywords: ["notifications", "alerts", "bell", "messages"],
  },
];

export function CommandPalette({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);

  // Filter commands
  const filtered = useMemo(() => {
    if (!query.trim()) return COMMANDS;
    const q = query.toLowerCase().trim();
    return COMMANDS.filter(
      (c) =>
        c.title.toLowerCase().includes(q) ||
        c.category.toLowerCase().includes(q) ||
        c.keywords?.some((k) => k.toLowerCase().includes(q))
    );
  }, [query]);

  // Global Ctrl+K shortcut listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        onOpenChange(!open);
      } else if (e.key === "Escape" && open) {
        onOpenChange(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, onOpenChange]);

  // Reset selected index when filtered list changes
  useEffect(() => {
    setSelectedIndex(0);
  }, [filtered.length]);

  // Keyboard navigation within the palette
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % Math.max(1, filtered.length));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) =>
        prev <= 0 ? Math.max(0, filtered.length - 1) : prev - 1
      );
    } else if (e.key === "Enter" && filtered[selectedIndex]) {
      e.preventDefault();
      const item = filtered[selectedIndex];
      onOpenChange(false);
      setQuery("");
      router.push(item.href);
    }
  };

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-20 px-4 bg-slate-950/75 animate-in fade-in duration-150"
      onClick={() => onOpenChange(false)}
    >
      <div
        className="relative w-full max-w-xl bg-white dark:bg-slate-900 rounded-[20px] shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label="Command Palette"
      >
        {/* Search Input */}
        <div className="flex items-center px-4 py-3.5 border-b border-slate-100 dark:border-slate-800">
          <Search className="w-5 h-5 text-slate-400 dark:text-slate-500 mr-3" />
          <input
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a command, patient, or jump to module..."
            className="w-full text-sm bg-transparent text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none"
          />
          <kbd className="hidden sm:inline-flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-slate-700">
            ESC
          </kbd>
          <button
            onClick={() => onOpenChange(false)}
            className="sm:hidden p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 ml-2"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Command Items List */}
        <div className="max-h-80 overflow-y-auto p-2">
          {filtered.length === 0 ? (
            <div className="p-8 text-center text-xs text-slate-500 dark:text-slate-400">
              No matching commands or pages found.
            </div>
          ) : (
            filtered.map((item, index) => {
              const isSelected = index === selectedIndex;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    onOpenChange(false);
                    setQuery("");
                    router.push(item.href);
                  }}
                  onMouseEnter={() => setSelectedIndex(index)}
                  className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-left text-sm transition-colors duration-100 cursor-pointer ${
                    isSelected
                      ? "bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 font-medium"
                      : "text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800"
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span className="p-1.5 rounded-lg bg-slate-100 dark:bg-slate-800">
                      {item.icon}
                    </span>
                    <span>{item.title}</span>
                  </div>
                  <span className="text-[11px] font-medium text-slate-400 dark:text-slate-500">
                    {item.category}
                  </span>
                </button>
              );
            })
          )}
        </div>

        {/* Footer Hint */}
        <div className="px-4 py-2.5 bg-slate-50 dark:bg-slate-800/60 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400">
          <span>Navigate with ↑ ↓ and press Enter</span>
          <span className="font-semibold text-blue-600 dark:text-blue-400">
            DentalCare Pro v20.0
          </span>
        </div>
      </div>
    </div>
  );
}
