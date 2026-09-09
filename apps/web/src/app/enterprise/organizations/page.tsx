"use client";

import { useState } from "react";
import {
  Globe2,
  Plus,
  Building2,
  ShieldCheck,
  CheckCircle2,
  Settings,
  Mail,
  Phone,
  ExternalLink,
} from "lucide-react";
import { EnterpriseNav } from "../nav";
import { Organization, PatientSharingMode } from "../types";

const INITIAL_ORGS: Organization[] = [
  {
    id: "org-1",
    name: "Apollo Dental Network",
    slug: "apollo-dental-network",
    code: "APOLLO",
    tax_id: "GSTIN29ABCDE1234F1Z5",
    legal_name: "Apollo Dental Healthcare Private Limited",
    subscription_tier: "ENTERPRISE",
    is_active: true,
    theme_color: "#0d9488",
    primary_email: "admin@apollodental.com",
    phone: "+91 80 4000 5000",
    website: "https://apollodental.example.com",
    patient_sharing_mode: "SHARED",
    created_at: "2026-01-10T10:00:00Z",
    updated_at: "2026-09-01T12:00:00Z",
  },
  {
    id: "org-2",
    name: "Clove Dental Care Systems",
    slug: "clove-dental-care-systems",
    code: "CLOVE",
    tax_id: "GSTIN07XYZAB5678C2Z1",
    legal_name: "Clove Dental Clinics Corp",
    subscription_tier: "ENTERPRISE_PLUS",
    is_active: true,
    theme_color: "#2563eb",
    primary_email: "support@clovedental.com",
    phone: "+91 11 2345 6789",
    website: "https://clovedental.example.com",
    patient_sharing_mode: "TRANSFER_ONLY",
    created_at: "2026-03-15T08:30:00Z",
    updated_at: "2026-08-20T14:15:00Z",
  },
];

export default function OrganizationsPage() {
  const [orgs, setOrgs] = useState<Organization[]>(INITIAL_ORGS);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    code: "",
    legal_name: "",
    primary_email: "",
    phone: "",
    theme_color: "#0d9488",
    patient_sharing_mode: "SHARED" as PatientSharingMode,
  });

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name || !formData.code || !formData.primary_email) return;

    const newOrg: Organization = {
      id: `org-${Date.now()}`,
      name: formData.name,
      slug: formData.code.toLowerCase().replace(/\s+/g, "-"),
      code: formData.code.toUpperCase(),
      legal_name: formData.legal_name,
      subscription_tier: "ENTERPRISE",
      is_active: true,
      theme_color: formData.theme_color,
      primary_email: formData.primary_email,
      phone: formData.phone,
      patient_sharing_mode: formData.patient_sharing_mode,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    setOrgs([...orgs, newOrg]);
    setShowModal(false);
    setFormData({
      name: "",
      code: "",
      legal_name: "",
      primary_email: "",
      phone: "",
      theme_color: "#0d9488",
      patient_sharing_mode: "SHARED",
    });
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <EnterpriseNav />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Corporate Organizations</h1>
            <p className="text-xs text-slate-500 mt-1">
              Manage parent legal entities, brand themes, cross-clinic patient privacy, and subscription tiers.
            </p>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 shadow-xs transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add Organization
          </button>
        </div>

        {/* Organizations Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {orgs.map((org) => (
            <div
              key={org.id}
              className="bg-white rounded-xl border border-slate-200 shadow-xs p-6 space-y-5 hover:border-slate-300 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div
                    className="w-10 h-10 rounded-lg flex items-center justify-center text-white font-bold text-sm shadow-xs"
                    style={{ backgroundColor: org.theme_color }}
                  >
                    {org.code.slice(0, 2)}
                  </div>
                  <div>
                    <h2 className="font-bold text-slate-900 text-base">{org.name}</h2>
                    <p className="text-xs text-slate-500">{org.legal_name || "Enterprise Tenant"}</p>
                  </div>
                </div>
                <span className="px-2 py-0.5 text-[11px] font-semibold rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">
                  {org.subscription_tier}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs pt-3 border-t border-slate-100">
                <div className="flex items-center gap-2 text-slate-600">
                  <Mail className="w-3.5 h-3.5 text-slate-400" />
                  <span className="truncate">{org.primary_email}</span>
                </div>
                {org.phone && (
                  <div className="flex items-center gap-2 text-slate-600">
                    <Phone className="w-3.5 h-3.5 text-slate-400" />
                    <span>{org.phone}</span>
                  </div>
                )}
              </div>

              <div className="flex items-center justify-between pt-3 border-t border-slate-100 text-xs">
                <div>
                  <span className="text-slate-500">Patient Sharing: </span>
                  <span className="font-semibold text-slate-900">{org.patient_sharing_mode}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="inline-flex items-center gap-1 text-emerald-700 font-medium text-[11px]">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Active
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Modal */}
        {showModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4">
            <div className="bg-white rounded-xl shadow-xl border border-slate-200 w-full max-w-md p-6 space-y-4">
              <h2 className="text-lg font-bold text-slate-900">Register New Organization</h2>
              <form onSubmit={handleCreate} className="space-y-3.5 text-xs">
                <div>
                  <label className="block font-medium text-slate-700 mb-1">Organization Name</label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="e.g. Apex Health Dental Care"
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block font-medium text-slate-700 mb-1">Corporate Code</label>
                    <input
                      type="text"
                      required
                      value={formData.code}
                      onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                      placeholder="e.g. APEX"
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                  <div>
                    <label className="block font-medium text-slate-700 mb-1">Brand Theme Color</label>
                    <input
                      type="color"
                      value={formData.theme_color}
                      onChange={(e) => setFormData({ ...formData, theme_color: e.target.value })}
                      className="w-full h-9 p-1 border border-slate-300 rounded-lg cursor-pointer"
                    />
                  </div>
                </div>

                <div>
                  <label className="block font-medium text-slate-700 mb-1">Primary Email</label>
                  <input
                    type="email"
                    required
                    value={formData.primary_email}
                    onChange={(e) => setFormData({ ...formData, primary_email: e.target.value })}
                    placeholder="corporate@apex.com"
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label className="block font-medium text-slate-700 mb-1">Patient Sharing Mode</label>
                  <select
                    value={formData.patient_sharing_mode}
                    onChange={(e) =>
                      setFormData({ ...formData, patient_sharing_mode: e.target.value as PatientSharingMode })
                    }
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="SHARED">SHARED (Seamless across all network branches)</option>
                    <option value="TRANSFER_ONLY">TRANSFER_ONLY (Explicit approval required)</option>
                    <option value="ISOLATED">ISOLATED (Branches cannot see each other)</option>
                  </select>
                </div>

                <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="px-3 py-1.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50 font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-1.5 rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 font-semibold shadow-xs"
                  >
                    Create Organization
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
