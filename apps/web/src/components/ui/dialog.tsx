"use client";

import React, { useEffect } from "react";
import { X } from "lucide-react";

interface DialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title?: string;
  description?: string;
  children: React.ReactNode;
}

export function Dialog({
  open,
  onOpenChange,
  title,
  description,
  children,
}: DialogProps) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && open) {
        onOpenChange(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, onOpenChange]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-in fade-in duration-200">
      {title ? (
        <div
          className="relative w-full max-w-lg bg-white rounded-lg shadow-xl border border-slate-200 overflow-hidden"
          role="dialog"
          aria-modal="true"
        >
          <div className="flex items-center justify-between p-5 border-b border-slate-100">
            <div>
              <h3 className="text-base font-semibold text-slate-900">{title}</h3>
              {description && <p className="text-xs text-slate-500 mt-0.5">{description}</p>}
            </div>
            <button
              onClick={() => onOpenChange(false)}
              className="text-slate-400 hover:text-slate-600 rounded p-1"
              aria-label="Close"
            >
              <X size={18} />
            </button>
          </div>
          <div className="p-5">{children}</div>
        </div>
      ) : (
        children
      )}
    </div>
  );
}

export function DialogContent({
  className,
  children,
}: {
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <div
      role="dialog"
      aria-modal="true"
      className={`relative w-full bg-white rounded-xl shadow-2xl border border-slate-200 overflow-hidden ${
        className || ""
      }`}
    >
      {children}
    </div>
  );
}

export function DialogHeader({
  className,
  children,
}: {
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <div className={`flex flex-col space-y-1.5 pb-4 border-b border-slate-100 ${className || ""}`}>
      {children}
    </div>
  );
}

export function DialogTitle({
  className,
  children,
}: {
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <h3 className={`text-base font-bold text-slate-900 tracking-tight ${className || ""}`}>
      {children}
    </h3>
  );
}
