"use client";

import { useState } from "react";
import {
  GitBranch,
  Plus,
  Building2,
  MapPin,
  Clock,
  Coins,
  CheckCircle2,
  Star,
  Search,
} from "lucide-react";
import { EnterpriseNav } from "../nav";
import { Branch } from "../types";

const INITIAL_BRANCHES: Branch[] = [
  {
    id: "br-1",
    name: "Central Flagship Clinic",
    slug: "central-flagship-clinic",
    branch_code: "BR-DEL-01",
    email: "central@apollodental.com",
    phone: "+91 11 4100 1100",
    timezone: "Asia/Kolkata",
    address: "Connaught Place, Central Delhi, 110001",
    working_hours: "08:00 - 20:00 (Mon-Sat)",
    currency: "INR",
    tax_configuration: "GST 18%",
    is_main_branch: true,
    is_active: true,
    created_at: "2026-01-15T10:00:00Z",
    updated_at: "2026-09-01T10:00:00Z",
  },
  {
    id: "br-2",
    name: "Indiranagar Dental Lounge",
    slug: "indiranagar-dental-lounge",
    branch_code: "BR-BLR-01",
    email: "indiranagar@apollodental.com",
    phone: "+91 80 4200 2200",
    timezone: "Asia/Kolkata",
    address: "100ft Road, Indiranagar, Bengaluru, 560038",
    working_hours: "09:00 - 21:00 (Mon-Sun)",
    currency: "INR",
    tax_configuration: "GST 18%",
    is_main_branch: false,
    is_active: true,
    created_at: "2026-02-01T11:00:00Z",
    updated_at: "2026-09-01T10:00:00Z",
  },
  {
    id: "br-3",
    name: "Whitefield Specialty Wing",
    slug: "whitefield-specialty-wing",
    branch_code: "BR-BLR-02",
    email: "whitefield@apollodental.com",
    phone: "+91 80 4300 3300",
    timezone: "Asia/Kolkata",
    address: "ITPL Main Road, Whitefield, Bengaluru, 560066",
    working_hours: "08:30 - 19:30 (Mon-Sat)",
    currency: "INR",
    tax_configuration: "GST 18%",
    is_main_branch: false,
    is_active: true,
    created_at: "2026-03-10T12:00:00Z",
    updated_at: "2026-09-01T10:00:00Z",
  },
  {
    id: "br-4",
    name: "Bandra Sea Face Dental Hub",
    slug: "bandra-sea-face-dental-hub",
    branch_code: "BR-BOM-01",
    email: "bandra@apollodental.com",
    phone: "+91 22 2600 4400",
    timezone: "Asia/Kolkata",
    address: "Turner Road, Bandra West, Mumbai, 400050",
    working_hours: "09:00 - 20:00 (Mon-Sat)",
    currency: "INR",
    tax_configuration: "GST 18%",
    is_main_branch: false,
    is_active: true,
    created_at: "2026-04-05T09:30:00Z",
    updated_at: "2026-09-01T10:00:00Z",
  },
];

export default function BranchesPage() {
  const [branches, setBranches] = useState<Branch[]>(INITIAL_BRANCHES);
  const [search, setSearch] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    branch_code: "",
    email: "",
    phone: "",
    address: "",
    working_hours: "09:00 - 20:00 (Mon-Sat)",
    currency: "INR",
    is_main_branch: false,
  });

  const filtered = branches.filter(
    (b) =>
      b.name.toLowerCase().includes(search.toLowerCase()) ||
      b.branch_code?.toLowerCase().includes(search.toLowerCase()) ||
      b.address?.toLowerCase().includes(search.toLowerCase())
  );

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name || !formData.branch_code || !formData.email) return;

    const newBranch: Branch = {
      id: `br-${Date.now()}`,
      name: formData.name,
      slug: formData.name.toLowerCase().replace(/\s+/g, "-"),
      branch_code: formData.branch_code.toUpperCase(),
      email: formData.email,
      phone: formData.phone,
      timezone: "Asia/Kolkata",
      address: formData.address,
      working_hours: formData.working_hours,
      currency: formData.currency,
      is_main_branch: formData.is_main_branch,
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    setBranches([...branches, newBranch]);
    setShowModal(false);
    setFormData({
      name: "",
      branch_code: "",
      email: "",
      phone: "",
      address: "",
      working_hours: "09:00 - 20:00 (Mon-Sat)",
      currency: "INR",
      is_main_branch: false,
    });
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <EnterpriseNav />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Branch Clinics Directory</h1>
            <p className="text-xs text-slate-500 mt-1">
              Manage physical dental branches, address geo-coordinates, working hours, and clinic settings.
            </p>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 shadow-xs transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add Branch Clinic
          </button>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
          <input
            type="text"
            placeholder="Search branches by name, branch code, or city..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-white text-xs border border-slate-200 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        {/* Branch Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {filtered.map((branch) => (
            <div
              key={branch.id}
              className="bg-white rounded-xl border border-slate-200 shadow-xs p-6 space-y-4 hover:border-slate-300 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="font-bold text-slate-900 text-base">{branch.name}</h2>
                    {branch.is_main_branch && (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-semibold bg-amber-50 text-amber-700 rounded-full border border-amber-200">
                        <Star className="w-3 h-3 fill-amber-500" /> Main Headquarters
                      </span>
                    )}
                  </div>
                  <span className="text-xs font-mono font-semibold text-indigo-600">
                    {branch.branch_code}
                  </span>
                </div>
                <span className="px-2 py-0.5 text-[11px] font-medium rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200">
                  Active
                </span>
              </div>

              <div className="space-y-2 text-xs text-slate-600 pt-2 border-t border-slate-100">
                {branch.address && (
                  <div className="flex items-center gap-2">
                    <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span className="truncate">{branch.address}</span>
                  </div>
                )}
                {branch.working_hours && (
                  <div className="flex items-center gap-2">
                    <Clock className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span>{branch.working_hours}</span>
                  </div>
                )}
                <div className="flex items-center gap-2">
                  <Coins className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                  <span>Currency: {branch.currency} (Timezone: {branch.timezone})</span>
                </div>
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                <span className="text-slate-500">{branch.email}</span>
                <span className="text-slate-500">{branch.phone}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Modal */}
        {showModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4">
            <div className="bg-white rounded-xl shadow-xl border border-slate-200 w-full max-w-md p-6 space-y-4">
              <h2 className="text-lg font-bold text-slate-900">Add New Branch Clinic</h2>
              <form onSubmit={handleCreate} className="space-y-3.5 text-xs">
                <div>
                  <label className="block font-medium text-slate-700 mb-1">Branch Name</label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="e.g. Koramangala Dental Suite"
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block font-medium text-slate-700 mb-1">Branch Code</label>
                    <input
                      type="text"
                      required
                      value={formData.branch_code}
                      onChange={(e) => setFormData({ ...formData, branch_code: e.target.value })}
                      placeholder="e.g. BR-BLR-03"
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                  <div>
                    <label className="block font-medium text-slate-700 mb-1">Currency</label>
                    <input
                      type="text"
                      value={formData.currency}
                      onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                    />
                  </div>
                </div>

                <div>
                  <label className="block font-medium text-slate-700 mb-1">Clinic Email</label>
                  <input
                    type="email"
                    required
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    placeholder="koramangala@apollodental.com"
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label className="block font-medium text-slate-700 mb-1">Physical Address</label>
                  <input
                    type="text"
                    value={formData.address}
                    onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                    placeholder="Street, City, Postal Code"
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg"
                  />
                </div>

                <div className="flex items-center gap-2 pt-1">
                  <input
                    type="checkbox"
                    id="is_main"
                    checked={formData.is_main_branch}
                    onChange={(e) => setFormData({ ...formData, is_main_branch: e.target.checked })}
                    className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  <label htmlFor="is_main" className="font-medium text-slate-700">
                    Set as Main Headquarters Branch
                  </label>
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
                    Save Branch
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
