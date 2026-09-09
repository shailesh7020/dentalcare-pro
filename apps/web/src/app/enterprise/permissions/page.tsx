"use client";

import { useState } from "react";
import { ShieldCheck, Lock, Check, X, ShieldAlert, Sparkles } from "lucide-react";
import { EnterpriseNav } from "../nav";

interface RoleMatrixItem {
  module: string;
  permissions: Array<{
    key: string;
    description: string;
    roles: Record<string, boolean>;
  }>;
}

const ROLES = [
  "SUPER_ADMIN",
  "ORGANIZATION_ADMIN",
  "REGIONAL_MANAGER",
  "BRANCH_MANAGER",
  "DENTIST",
  "HYGIENIST",
  "RECEPTIONIST",
  "ACCOUNTANT",
  "INVENTORY_MANAGER",
];

const MATRIX_DATA: RoleMatrixItem[] = [
  {
    module: "Enterprise & Hierarchy",
    permissions: [
      {
        key: "enterprise:manage",
        description: "Create organizations, regions, and configure corporate branding",
        roles: { SUPER_ADMIN: true, ORGANIZATION_ADMIN: true },
      },
      {
        key: "branch:manage",
        description: "Open new clinics, configure address, currency, and departments",
        roles: { SUPER_ADMIN: true, ORGANIZATION_ADMIN: true, REGIONAL_MANAGER: true },
      },
      {
        key: "user:assign",
        description: "Assign dentists and staff across multiple branches (roaming)",
        roles: { SUPER_ADMIN: true, ORGANIZATION_ADMIN: true, REGIONAL_MANAGER: true, BRANCH_MANAGER: true },
      },
    ],
  },
  {
    module: "Patient Records & Merges",
    permissions: [
      {
        key: "patient:cross_view",
        description: "Search and view patient medical history across all network branches",
        roles: {
          SUPER_ADMIN: true,
          ORGANIZATION_ADMIN: true,
          REGIONAL_MANAGER: true,
          BRANCH_MANAGER: true,
          DENTIST: true,
          HYGIENIST: true,
        },
      },
      {
        key: "patient:transfer",
        description: "Initiate and approve inter-clinic patient relocation requests",
        roles: { SUPER_ADMIN: true, ORGANIZATION_ADMIN: true, BRANCH_MANAGER: true, RECEPTIONIST: true },
      },
      {
        key: "patient:merge",
        description: "Merge duplicate patient files across clinics with clinical data migration",
        roles: { SUPER_ADMIN: true, ORGANIZATION_ADMIN: true, BRANCH_MANAGER: true },
      },
    ],
  },
  {
    module: "Supply Chain & Financials",
    permissions: [
      {
        key: "inventory:transfer",
        description: "Request, dispatch, and receive inter-branch consumable stock",
        roles: { SUPER_ADMIN: true, ORGANIZATION_ADMIN: true, BRANCH_MANAGER: true, INVENTORY_MANAGER: true },
      },
      {
        key: "financials:consolidated_view",
        description: "Access regional and multi-branch revenue rollups, tax reports",
        roles: { SUPER_ADMIN: true, ORGANIZATION_ADMIN: true, REGIONAL_MANAGER: true, ACCOUNTANT: true },
      },
      {
        key: "announcement:broadcast",
        description: "Publish emergency broadcast alerts to all branches",
        roles: { SUPER_ADMIN: true, ORGANIZATION_ADMIN: true, REGIONAL_MANAGER: true },
      },
    ],
  },
];

export default function PermissionsPage() {
  const [selectedRole, setSelectedRole] = useState<string>("ALL");

  return (
    <div className="min-h-screen bg-slate-50">
      <EnterpriseNav />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Fine-Grained Permission Matrix</h1>
            <p className="text-xs text-slate-500 mt-1">
              Role-Based Access Control (RBAC) across 10 corporate roles, with user-level overrides.
            </p>
          </div>

          {/* Filter by role */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-slate-500">Highlight:</span>
            <select
              value={selectedRole}
              onChange={(e) => setSelectedRole(e.target.value)}
              className="text-xs bg-white border border-slate-200 rounded-lg px-3 py-1.5 font-medium text-slate-700"
            >
              <option value="ALL">All 10 Enterprise Roles</option>
              {ROLES.map((r) => (
                <option key={r} value={r}>
                  {r.replace("_", " ")}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Matrix Table */}
        <div className="space-y-6">
          {MATRIX_DATA.map((group) => (
            <div key={group.module} className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
              <div className="px-6 py-3.5 bg-slate-50/70 border-b border-slate-200">
                <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                  {group.module}
                </h2>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-100 text-slate-500 font-semibold uppercase">
                      <th className="py-3 px-4 w-72">Permission</th>
                      {ROLES.filter((r) => selectedRole === "ALL" || selectedRole === r).map((role) => (
                        <th key={role} className="py-3 px-2 text-center text-[11px] whitespace-nowrap">
                          {role.replace("_", " ")}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {group.permissions.map((perm) => (
                      <tr key={perm.key} className="hover:bg-slate-50/60 transition-colors">
                        <td className="py-3.5 px-4">
                          <div className="font-semibold text-slate-900 font-mono text-[11px]">
                            {perm.key}
                          </div>
                          <div className="text-[11px] text-slate-500 mt-0.5">
                            {perm.description}
                          </div>
                        </td>
                        {ROLES.filter((r) => selectedRole === "ALL" || selectedRole === r).map((role) => {
                          const isGranted = Boolean(perm.roles[role]);
                          return (
                            <td key={role} className="py-3.5 px-2 text-center">
                              {isGranted ? (
                                <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-emerald-50 text-emerald-600 border border-emerald-200">
                                  <Check className="w-3.5 h-3.5 stroke-[2.5]" />
                                </span>
                              ) : (
                                <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-slate-50 text-slate-300">
                                  <X className="w-3.5 h-3.5" />
                                </span>
                              )}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
