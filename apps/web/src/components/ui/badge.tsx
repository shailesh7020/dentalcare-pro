import React from "react";

export type BadgeVariant =
  | "default"
  | "active"
  | "archived"
  | "critical"
  | "destructive"
  | "success"
  | "warning"
  | "info"
  | "secondary"
  | "outline";

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
}

const variantStyles: Record<BadgeVariant, string> = {
  default: "bg-teal-50 text-teal-700 border-teal-200",
  active: "bg-emerald-50 text-emerald-700 border-emerald-200",
  success: "bg-emerald-50 text-emerald-700 border-emerald-200",
  archived: "bg-slate-100 text-slate-600 border-slate-200",
  critical: "bg-rose-50 text-rose-700 border-rose-200 font-semibold",
  destructive: "bg-rose-50 text-rose-700 border-rose-200 font-semibold",
  warning: "bg-amber-50 text-amber-700 border-amber-200",
  info: "bg-sky-50 text-sky-700 border-sky-200",
  secondary: "bg-slate-50 text-slate-700 border-slate-200",
  outline: "bg-transparent text-slate-600 border-slate-300",
};

export function Badge({
  className = "",
  variant = "default",
  children,
  ...props
}: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${variantStyles[variant]} ${className}`}
      {...props}
    >
      {children}
    </span>
  );
}
