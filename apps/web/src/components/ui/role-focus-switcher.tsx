"use client";

import React, { useEffect, useState } from "react";
import { UserCheck, Stethoscope, ShieldAlert, Sparkles, ChevronDown } from "lucide-react";

export type RoleFocusMode = "all" | "receptionist" | "dentist" | "admin";

interface RoleFocusOption {
  id: RoleFocusMode;
  label: string;
  description: string;
  icon: React.ReactNode;
}

const FOCUS_OPTIONS: RoleFocusOption[] = [
  {
    id: "all",
    label: "Full Practice View",
    description: "Complete clinical and administrative workspace",
    icon: <Sparkles className="w-3.5 h-3.5 text-blue-600" />,
  },
  {
    id: "receptionist",
    label: "Receptionist Mode",
    description: "Prioritize appointments, patient check-in, and billing",
    icon: <UserCheck className="w-3.5 h-3.5 text-teal-600" />,
  },
  {
    id: "dentist",
    label: "Dentist Operatory",
    description: "Focus on dental chart, treatments, and prescriptions",
    icon: <Stethoscope className="w-3.5 h-3.5 text-rose-600" />,
  },
  {
    id: "admin",
    label: "Practice Admin",
    description: "Focus on revenue, staff, supplies, and analytics",
    icon: <ShieldAlert className="w-3.5 h-3.5 text-amber-600" />,
  },
];

export function RoleFocusSwitcher({
  onModeChange,
}: {
  onModeChange?: (mode: RoleFocusMode) => void;
}) {
  const [currentMode, setCurrentMode] = useState<RoleFocusMode>("all");
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem("dentalcare-role-focus") as RoleFocusMode | null;
    if (saved && FOCUS_OPTIONS.some((o) => o.id === saved)) {
      setCurrentMode(saved);
      onModeChange?.(saved);
    }
  }, [onModeChange]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        setIsOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen]);

  const selectMode = (mode: RoleFocusMode) => {
    setCurrentMode(mode);
    localStorage.setItem("dentalcare-role-focus", mode);
    onModeChange?.(mode);
    setIsOpen(false);
  };

  const activeOption = FOCUS_OPTIONS.find((o) => o.id === currentMode) || FOCUS_OPTIONS[0];

  return (
    <div className="relative inline-block text-left">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center gap-2 h-9 px-3 text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-700 border border-slate-200 dark:border-slate-700 rounded-xl transition-colors cursor-pointer"
        aria-expanded={isOpen}
      >
        <span>{activeOption.icon}</span>
        <span className="hidden sm:inline font-semibold">{activeOption.label}</span>
        <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 mt-1.5 w-64 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-xl z-50 p-1.5 animate-in fade-in slide-in-from-top-1 duration-150">
            <div className="px-3 py-2 border-b border-slate-100 dark:border-slate-800 mb-1">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                Workspace Focus Mode
              </p>
            </div>
            {FOCUS_OPTIONS.map((option) => (
              <button
                key={option.id}
                type="button"
                onClick={() => selectMode(option.id)}
                className={`w-full flex items-start gap-2.5 p-2.5 rounded-xl text-left transition-colors cursor-pointer ${
                  currentMode === option.id
                    ? "bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300"
                    : "text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800"
                }`}
              >
                <div className="mt-0.5">{option.icon}</div>
                <div>
                  <p className="text-xs font-semibold leading-tight">{option.label}</p>
                  <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-0.5 leading-snug">
                    {option.description}
                  </p>
                </div>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
