"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Building2,
  Search,
  Plus,
  Globe,
  Phone,
  Mail,
  User,
  ShieldCheck,
  ExternalLink,
  CheckCircle2,
  XCircle,
  X,
} from "lucide-react";
import { api } from "@/lib/api";
import { InsuranceNav } from "../nav";
import type { InsuranceProvider, InsuranceProviderType } from "../types";

export default function InsuranceProvidersPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("ALL");
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isModalOpen) {
        setIsModalOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isModalOpen]);

  // Form State
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [providerType, setProviderType] = useState<InsuranceProviderType>("INSURANCE_COMPANY");
  const [tpaName, setTpaName] = useState("");
  const [payerId, setPayerId] = useState("");
  const [contactPerson, setContactPerson] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [portalUrl, setPortalUrl] = useState("");
  const [notes, setNotes] = useState("");

  const { data: providers = [], isLoading } = useQuery<InsuranceProvider[]>({
    queryKey: ["insurance-providers", search],
    queryFn: async () => {
      const res = await api.get<InsuranceProvider[]>("/insurance/providers", {
        params: search ? { search } : undefined,
      });
      return res.data;
    },
  });

  const createMutation = useMutation({
    mutationFn: async () => {
      const payload = {
        provider_name: name,
        provider_code: code,
        provider_type: providerType,
        tpa_name: tpaName || null,
        payer_id: payerId || null,
        contact_person: contactPerson || null,
        email: email || null,
        phone: phone || null,
        portal_url: portalUrl || null,
        notes: notes || null,
        is_active: true,
      };
      await api.post("/insurance/providers", payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["insurance-providers"] });
      setIsModalOpen(false);
      resetForm();
    },
  });

  const resetForm = () => {
    setName("");
    setCode("");
    setProviderType("INSURANCE_COMPANY");
    setTpaName("");
    setPayerId("");
    setContactPerson("");
    setEmail("");
    setPhone("");
    setPortalUrl("");
    setNotes("");
  };

  const filteredProviders = providers.filter((p) => {
    if (typeFilter !== "ALL" && p.provider_type !== typeFilter) return false;
    return true;
  });

  return (
    <div className="min-h-screen bg-slate-50/50">
      <InsuranceNav />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Insurance Providers & TPAs</h1>
            <p className="text-sm text-slate-600 mt-1">
              Master registry of insurance carriers, third-party administrators, payer IDs, and portals.
            </p>
          </div>
          <button
            onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-teal-600 text-white rounded-lg text-sm font-semibold hover:bg-teal-700 shadow-sm transition-colors cursor-pointer"
          >
            <Plus className="w-4 h-4" /> Add Insurance Provider
          </button>
        </div>

        {/* Filter Bar */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-col sm:flex-row gap-3 items-center justify-between">
          <div className="relative w-full sm:w-80">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search provider name, code, or TPA..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 text-xs border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
            />
          </div>
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <label className="text-xs text-slate-500 font-medium">Type:</label>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="text-xs border border-slate-200 rounded-lg px-3 py-2 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-teal-500"
            >
              <option value="ALL">All Types</option>
              <option value="INSURANCE_COMPANY">Insurance Carrier</option>
              <option value="TPA">Third-Party Administrator (TPA)</option>
              <option value="GOVERNMENT_SCHEME">Government Scheme</option>
              <option value="CORPORATE">Corporate Tie-up</option>
            </select>
          </div>
        </div>

        {/* Provider Cards Grid */}
        {isLoading ? (
          <div className="text-center py-12 text-slate-500 text-sm">Loading providers...</div>
        ) : filteredProviders.length === 0 ? (
          <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
            <Building2 className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <h3 className="text-base font-semibold text-slate-800">No insurance providers found</h3>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              Get started by registering your practice's contracted payers or TPAs to enable claim adjudication.
            </p>
            <button
              onClick={() => setIsModalOpen(true)}
              className="mt-4 inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-teal-700 bg-teal-50 border border-teal-200 rounded-lg hover:bg-teal-100"
            >
              <Plus className="w-3.5 h-3.5" /> Add Provider
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {filteredProviders.map((prov) => (
              <div
                key={prov.id}
                className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs hover:border-slate-300 hover:shadow-sm transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <h3 className="font-bold text-slate-900 text-base">{prov.provider_name}</h3>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                          {prov.provider_code}
                        </span>
                        {prov.payer_id && (
                          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-teal-50 text-teal-700 border border-teal-200">
                            Payer: {prov.payer_id}
                          </span>
                        )}
                      </div>
                    </div>
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        prov.is_active
                          ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                          : "bg-slate-100 text-slate-600"
                      }`}
                    >
                      {prov.is_active ? "ACTIVE" : "INACTIVE"}
                    </span>
                  </div>

                  <div className="mt-4 space-y-2 text-xs text-slate-600 border-t border-slate-100 pt-3">
                    <div className="flex items-center justify-between">
                      <span className="text-slate-400">Payer Type:</span>
                      <span className="font-medium text-slate-800">{prov.provider_type.replace(/_/g, " ")}</span>
                    </div>
                    {prov.tpa_name && (
                      <div className="flex items-center justify-between">
                        <span className="text-slate-400">Managed TPA:</span>
                        <span className="font-medium text-purple-700">{prov.tpa_name}</span>
                      </div>
                    )}
                    {prov.contact_person && (
                      <div className="flex items-center gap-1.5 text-slate-600">
                        <User className="w-3.5 h-3.5 text-slate-400" />
                        <span>{prov.contact_person}</span>
                      </div>
                    )}
                    {prov.email && (
                      <div className="flex items-center gap-1.5 text-slate-600">
                        <Mail className="w-3.5 h-3.5 text-slate-400" />
                        <span>{prov.email}</span>
                      </div>
                    )}
                    {prov.phone && (
                      <div className="flex items-center gap-1.5 text-slate-600">
                        <Phone className="w-3.5 h-3.5 text-slate-400" />
                        <span>{prov.phone}</span>
                      </div>
                    )}
                  </div>
                </div>

                {prov.portal_url && (
                  <div className="mt-4 pt-3 border-t border-slate-100">
                    <a
                      href={prov.portal_url.startsWith("http") ? prov.portal_url : `https://${prov.portal_url}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 text-xs font-medium text-teal-700 hover:text-teal-900"
                    >
                      <Globe className="w-3.5 h-3.5" /> Payer Claim Portal <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Create Provider Modal */}
        {isModalOpen && (
          <div 
            className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/75 p-4 overflow-y-auto"
            onClick={(e) => {
              if (e.target === e.currentTarget) setIsModalOpen(false);
            }}
          >
            <div className="bg-white dark:bg-slate-900 rounded-xl shadow-2xl border border-slate-200 dark:border-slate-800 w-full max-w-lg max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-800">
                <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">Register Insurance Provider / TPA</h3>
                <button
                  onClick={() => setIsModalOpen(false)}
                  className="p-1 rounded-md text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="p-6 space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="sm:col-span-2">
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                      Provider / Company Name *
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Star Health Insurance"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                      className="w-full text-xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-md p-2 focus:ring-2 focus:ring-teal-500 focus:outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                      Provider Code *
                    </label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. STAR-01"
                      value={code}
                      onChange={(e) => setCode(e.target.value)}
                      className="w-full text-xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-md p-2 focus:ring-2 focus:ring-teal-500 focus:outline-none uppercase"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Provider Type</label>
                    <select
                      value={providerType}
                      onChange={(e) => setProviderType(e.target.value as InsuranceProviderType)}
                      className="w-full text-xs border border-slate-300 dark:border-slate-700 rounded-md p-2 focus:ring-2 focus:ring-teal-500 focus:outline-none bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100"
                    >
                      <option value="INSURANCE_COMPANY">Insurance Carrier</option>
                      <option value="TPA">TPA Administrator</option>
                      <option value="GOVERNMENT_SCHEME">Government Scheme</option>
                      <option value="CORPORATE">Corporate Tie-up</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Payer ID / EDI</label>
                    <input
                      type="text"
                      placeholder="e.g. 99241"
                      value={payerId}
                      onChange={(e) => setPayerId(e.target.value)}
                      className="w-full text-xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-md p-2 focus:ring-2 focus:ring-teal-500 focus:outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Managed TPA Name</label>
                    <input
                      type="text"
                      placeholder="e.g. Medi Assist / Vidal"
                      value={tpaName}
                      onChange={(e) => setTpaName(e.target.value)}
                      className="w-full text-xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-md p-2 focus:ring-2 focus:ring-teal-500 focus:outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Contact Person</label>
                    <input
                      type="text"
                      placeholder="Claims Desk Officer"
                      value={contactPerson}
                      onChange={(e) => setContactPerson(e.target.value)}
                      className="w-full text-xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-md p-2 focus:ring-2 focus:ring-teal-500 focus:outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Desk Phone</label>
                    <input
                      type="text"
                      placeholder="+91 22 4000 1234"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      className="w-full text-xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-md p-2 focus:ring-2 focus:ring-teal-500 focus:outline-none"
                    />
                  </div>

                  <div className="sm:col-span-2">
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Claims Email</label>
                    <input
                      type="email"
                      placeholder="claims@starhealth.in"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full text-xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-md p-2 focus:ring-2 focus:ring-teal-500 focus:outline-none"
                    />
                  </div>

                  <div className="sm:col-span-2">
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Provider Portal URL</label>
                    <input
                      type="text"
                      placeholder="https://provider.starhealth.in"
                      value={portalUrl}
                      onChange={(e) => setPortalUrl(e.target.value)}
                      className="w-full text-xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-md p-2 focus:ring-2 focus:ring-teal-500 focus:outline-none"
                    />
                  </div>

                  <div className="sm:col-span-2">
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Notes / Instructions</label>
                    <textarea
                      rows={2}
                      placeholder="Special submission requirements or empanelment notes..."
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                      className="w-full text-xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-md p-2 focus:ring-2 focus:ring-teal-500 focus:outline-none"
                    />
                  </div>
                </div>
              </div>

              <div className="px-6 py-3 bg-slate-50 dark:bg-slate-800/60 border-t border-slate-200 dark:border-slate-800 flex justify-end gap-2">
                <button
                  onClick={() => setIsModalOpen(false)}
                  className="px-3 py-1.5 text-xs font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-800 rounded-md transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={() => createMutation.mutate()}
                  disabled={!name || !code || createMutation.isPending}
                  className="px-4 py-1.5 text-xs font-semibold text-white bg-teal-600 hover:bg-teal-700 rounded-md shadow-sm disabled:opacity-50 cursor-pointer transition-colors"
                >
                  {createMutation.isPending ? "Saving..." : "Save Provider"}
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
