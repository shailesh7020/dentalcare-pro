"use client";

import React from "react";

export function DataTable({
  className = "",
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={`w-full overflow-hidden bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-xs ${className}`}
      {...props}
    >
      <div className="w-full overflow-x-auto">
        <table className="w-full text-left text-sm border-collapse">
          {children}
        </table>
      </div>
    </div>
  );
}

export function TableHeader({
  className = "",
  children,
  ...props
}: React.HTMLAttributes<HTMLTableSectionElement>) {
  return (
    <thead
      className={`sticky top-0 z-10 bg-slate-50 dark:bg-slate-800 border-b border-slate-200 dark:border-slate-800 text-xs font-semibold text-slate-600 dark:text-slate-300 uppercase tracking-wider ${className}`}
      {...props}
    >
      {children}
    </thead>
  );
}

export function TableBody({
  className = "",
  children,
  ...props
}: React.HTMLAttributes<HTMLTableSectionElement>) {
  return (
    <tbody
      className={`divide-y divide-slate-100 dark:divide-slate-800/60 text-slate-800 dark:text-slate-200 ${className}`}
      {...props}
    >
      {children}
    </tbody>
  );
}

export function TableRow({
  className = "",
  children,
  ...props
}: React.HTMLAttributes<HTMLTableRowElement>) {
  return (
    <tr
      className={`transition-colors duration-150 hover:bg-slate-50/80 dark:hover:bg-slate-800/50 ${className}`}
      {...props}
    >
      {children}
    </tr>
  );
}

export function TableHead({
  className = "",
  children,
  ...props
}: React.ThHTMLAttributes<HTMLTableCellElement>) {
  return (
    <th className={`px-4 py-3.5 select-none font-semibold ${className}`} {...props}>
      {children}
    </th>
  );
}

export function TableCell({
  className = "",
  children,
  ...props
}: React.TdHTMLAttributes<HTMLTableCellElement>) {
  return (
    <td className={`px-4 py-3.5 align-middle ${className}`} {...props}>
      {children}
    </td>
  );
}

export function TableEmpty({
  title = "No records found",
  description = "There are no entries to display matching your criteria.",
  icon,
  action,
}: {
  title?: string;
  description?: string;
  icon?: React.ReactNode;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center">
      {icon && <div className="mb-3 text-slate-400 dark:text-slate-500">{icon}</div>}
      <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200">
        {title}
      </h4>
      <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 max-w-sm">
        {description}
      </p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
