"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Building2,
  CheckCircle2,
  Edit,
  Mail,
  Phone,
  Plus,
  RefreshCw,
  Search,
  Star,
  Users,
  X,
} from "lucide-react";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import type { Supplier, SupplierCreate, SupplierUpdate } from "../types";

export default function SuppliersDirectoryPage() {
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState("");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingSupplier, setEditingSupplier] = useState<Supplier | null>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isModalOpen) {
        setIsModalOpen(false);
        setEditingSupplier(null);
        setFormError(null);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isModalOpen]);

  // Form fields
  const [name, setName] = useState("");
  const [contactPerson, setContactPerson] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [address, setAddress] = useState("");
  const [taxId, setTaxId] = useState("");
  const [paymentTerms, setPaymentTerms] = useState("Net 30");
  const [notes, setNotes] = useState("");
  const [rating, setRating] = useState<number>(4.5);
  const [formError, setFormError] = useState<string | null>(null);

  const suppliersQuery = useQuery({
    queryKey: ["inventory-suppliers-full-list"],
    queryFn: async () => {
      const res = await api.get<Supplier[]>("/inventory/suppliers");
      return res.data;
    },
  });

  const createMutation = useMutation({
    mutationFn: async (payload: SupplierCreate) => {
      const res = await api.post("/inventory/suppliers", payload);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inventory-suppliers-full-list"] });
      closeModal();
    },
    onError: (err: any) => {
      setFormError(err.response?.data?.detail || "Failed to create supplier.");
    },
  });

  const updateMutation = useMutation({
    mutationFn: async ({ id, payload }: { id: string; payload: SupplierUpdate }) => {
      const res = await api.patch(`/inventory/suppliers/${id}`, payload);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inventory-suppliers-full-list"] });
      closeModal();
    },
    onError: (err: any) => {
      setFormError(err.response?.data?.detail || "Failed to update supplier.");
    },
  });

  const openCreateModal = () => {
    setEditingSupplier(null);
    setName("");
    setContactPerson("");
    setPhone("");
    setEmail("");
    setAddress("");
    setTaxId("");
    setPaymentTerms("Net 30");
    setNotes("");
    setRating(4.5);
    setFormError(null);
    setIsModalOpen(true);
  };

  const openEditModal = (s: Supplier) => {
    setEditingSupplier(s);
    setName(s.name);
    setContactPerson(s.contact_person || "");
    setPhone(s.phone || "");
    setEmail(s.email || "");
    setAddress(s.address || "");
    setTaxId(s.tax_id || "");
    setPaymentTerms(s.payment_terms || "Net 30");
    setNotes(s.notes || "");
    setRating(s.rating || 4.5);
    setFormError(null);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingSupplier(null);
    setFormError(null);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setFormError("Supplier name is required.");
      return;
    }
    setFormError(null);

    if (editingSupplier) {
      updateMutation.mutate({
        id: editingSupplier.id,
        payload: {
          name: name.trim(),
          contact_person: contactPerson.trim() || undefined,
          phone: phone.trim() || undefined,
          email: email.trim() || undefined,
          address: address.trim() || undefined,
          tax_id: taxId.trim() || undefined,
          payment_terms: paymentTerms.trim() || undefined,
          notes: notes.trim() || undefined,
          rating: Number(rating),
        },
      });
    } else {
      createMutation.mutate({
        name: name.trim(),
        contact_person: contactPerson.trim() || undefined,
        phone: phone.trim() || undefined,
        email: email.trim() || undefined,
        address: address.trim() || undefined,
        tax_id: taxId.trim() || undefined,
        payment_terms: paymentTerms.trim() || undefined,
        notes: notes.trim() || undefined,
        rating: Number(rating),
      });
    }
  };

  const suppliers = suppliersQuery.data || [];
  const filtered = suppliers.filter((s) => {
    if (!searchTerm.trim()) return true;
    const term = searchTerm.toLowerCase();
    return (
      s.name.toLowerCase().includes(term) ||
      (s.contact_person || "").toLowerCase().includes(term) ||
      (s.phone || "").toLowerCase().includes(term) ||
      (s.email || "").toLowerCase().includes(term)
    );
  });

  const activeCount = suppliers.filter((s) => s.is_active).length;
  const avgRating =
    suppliers.length > 0
      ? (suppliers.reduce((acc, s) => acc + (s.rating || 0), 0) / suppliers.length).toFixed(1)
      : "0.0";

  return (
    <div className="space-y-6 pb-16">
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link href="/inventory" className="hover:text-slate-900 dark:hover:text-slate-100 flex items-center gap-1">
          <ArrowLeft className="h-4 w-4" /> Back to Inventory Hub
        </Link>
      </div>

      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-lg bg-teal-50 text-teal-700 dark:bg-teal-950/50 dark:text-teal-400">
              <Users className="h-6 w-6" />
            </span>
            <div>
              <h1 className="text-2xl font-bold tracking-tight">Suppliers & Vendor Directory</h1>
              <p className="text-sm text-muted-foreground">
                Manage dental material manufacturers, distributors, GSTIN credentials, and payment terms.
              </p>
            </div>
          </div>
        </div>

        <button
          onClick={openCreateModal}
          className="inline-flex items-center gap-1.5 rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-teal-700 transition"
        >
          <Plus className="h-4 w-4" />
          Add Supplier
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <span className="text-xs font-medium text-muted-foreground uppercase">Registered Suppliers</span>
          <div className="mt-1 text-2xl font-bold">{suppliers.length}</div>
          <p className="text-xs text-muted-foreground mt-1">Direct and wholesale distributors</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <span className="text-xs font-medium text-muted-foreground uppercase">Active Vendors</span>
          <div className="mt-1 text-2xl font-bold text-emerald-600 dark:text-emerald-400">{activeCount}</div>
          <p className="text-xs text-muted-foreground mt-1">Ready for purchase orders</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <span className="text-xs font-medium text-muted-foreground uppercase">Average Performance</span>
          <div className="mt-1 text-2xl font-bold text-amber-600 flex items-center gap-1">
            {avgRating} <Star className="h-5 w-5 fill-amber-500 text-amber-500" />
          </div>
          <p className="text-xs text-muted-foreground mt-1">Vendor reliability rating</p>
        </div>
      </div>

      {/* Search & Actions */}
      <div className="flex items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search suppliers by name, phone, contact person..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full rounded-lg border border-slate-300 bg-white py-2 pl-9 pr-3 text-sm focus:border-teal-500 focus:outline-none dark:border-slate-700 dark:bg-slate-900"
          />
        </div>

        <button
          onClick={() => suppliersQuery.refetch()}
          className="p-2 rounded-lg border border-slate-300 bg-white text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
        >
          <RefreshCw className="h-4 w-4" />
        </button>
      </div>

      {/* Suppliers Table */}
      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b bg-slate-50/75 text-xs uppercase font-semibold text-slate-500 dark:bg-slate-800/50">
              <tr>
                <th className="px-4 py-3">Supplier Name</th>
                <th className="px-4 py-3">Contact Person</th>
                <th className="px-4 py-3">Communication</th>
                <th className="px-4 py-3">GSTIN / Tax ID</th>
                <th className="px-4 py-3">Terms</th>
                <th className="px-4 py-3">Rating</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
              {suppliersQuery.isLoading ? (
                Array.from({ length: 4 }).map((_, i) => (
                  <tr key={i}>
                    <td colSpan={8} className="px-4 py-3">
                      <Skeleton className="h-6 w-full" />
                    </td>
                  </tr>
                ))
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-4 py-12 text-center text-muted-foreground">
                    <Building2 className="mx-auto h-8 w-8 text-slate-400 mb-2" />
                    <p className="font-medium">No suppliers found</p>
                    <p className="text-xs mt-1">Add your clinical suppliers and vendors to get started.</p>
                  </td>
                </tr>
              ) : (
                filtered.map((s) => (
                  <tr key={s.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                    <td className="px-4 py-3">
                      <p className="font-semibold text-slate-900 dark:text-slate-100">{s.name}</p>
                      {s.address && <p className="text-xs text-muted-foreground truncate max-w-xs">{s.address}</p>}
                    </td>
                    <td className="px-4 py-3">{s.contact_person || "—"}</td>
                    <td className="px-4 py-3 text-xs space-y-0.5">
                      {s.phone && (
                        <div className="flex items-center gap-1 text-muted-foreground">
                          <Phone className="h-3 w-3" /> {s.phone}
                        </div>
                      )}
                      {s.email && (
                        <div className="flex items-center gap-1 text-muted-foreground">
                          <Mail className="h-3 w-3" /> {s.email}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-muted-foreground">{s.tax_id || "—"}</td>
                    <td className="px-4 py-3 text-xs">{s.payment_terms || "Standard"}</td>
                    <td className="px-4 py-3">
                      <span className="inline-flex items-center gap-0.5 text-xs font-medium text-amber-600">
                        {s.rating?.toFixed(1) || "5.0"} <Star className="h-3 w-3 fill-amber-500" />
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {s.is_active ? (
                        <span className="text-xs px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-medium">Active</span>
                      ) : (
                        <span className="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-medium">Inactive</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => openEditModal(s)}
                        className="rounded p-1 text-slate-500 hover:text-teal-600 hover:bg-slate-100 dark:hover:bg-slate-800"
                        title="Edit Supplier"
                      >
                        <Edit className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Supplier Modal */}
      {isModalOpen && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/75 p-4 overflow-y-auto"
          onClick={(e) => {
            if (e.target === e.currentTarget) closeModal();
          }}
        >
          <div className="w-full max-w-lg rounded-xl bg-white p-6 shadow-2xl dark:bg-slate-900 border border-slate-200 dark:border-slate-800 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="font-semibold text-lg">
                {editingSupplier ? "Edit Supplier" : "Add New Supplier"}
              </h3>
              <button onClick={closeModal}>
                <X className="h-5 w-5" />
              </button>
            </div>

            {formError && (
              <div className="mt-3 rounded-lg bg-rose-50 p-3 text-xs text-rose-700 dark:bg-rose-950/40 dark:text-rose-300">
                {formError}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4 mt-4">
              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Supplier / Vendor Name *
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Dentsply Sirona India Pvt Ltd"
                  className="w-full rounded-lg border border-slate-300 bg-white py-2 px-3 text-sm dark:border-slate-700 dark:bg-slate-800"
                  required
                />
              </div>

              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Contact Person
                  </label>
                  <input
                    type="text"
                    value={contactPerson}
                    onChange={(e) => setContactPerson(e.target.value)}
                    placeholder="e.g. Rajesh Sharma"
                    className="w-full rounded-lg border border-slate-300 bg-white py-2 px-3 text-sm dark:border-slate-700 dark:bg-slate-800"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Phone Number
                  </label>
                  <input
                    type="text"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="e.g. +91 98200 12345"
                    className="w-full rounded-lg border border-slate-300 bg-white py-2 px-3 text-sm dark:border-slate-700 dark:bg-slate-800"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Email Address
                  </label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="e.g. orders@dentsply.in"
                    className="w-full rounded-lg border border-slate-300 bg-white py-2 px-3 text-sm dark:border-slate-700 dark:bg-slate-800"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    GSTIN / Tax ID
                  </label>
                  <input
                    type="text"
                    value={taxId}
                    onChange={(e) => setTaxId(e.target.value)}
                    placeholder="e.g. 27AAAAA0000A1Z5"
                    className="w-full rounded-lg border border-slate-300 bg-white py-2 px-3 text-sm dark:border-slate-700 dark:bg-slate-800"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Payment Terms
                  </label>
                  <input
                    type="text"
                    value={paymentTerms}
                    onChange={(e) => setPaymentTerms(e.target.value)}
                    placeholder="e.g. Net 30, COD, Net 15"
                    className="w-full rounded-lg border border-slate-300 bg-white py-2 px-3 text-sm dark:border-slate-700 dark:bg-slate-800"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                    Vendor Rating (1 to 5)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="1"
                    max="5"
                    value={rating}
                    onChange={(e) => setRating(parseFloat(e.target.value) || 5)}
                    className="w-full rounded-lg border border-slate-300 bg-white py-2 px-3 text-sm dark:border-slate-700 dark:bg-slate-800"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Postal Address
                </label>
                <textarea
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  placeholder="Street, City, Pin code"
                  rows={2}
                  className="w-full rounded-lg border border-slate-300 bg-white py-1.5 px-3 text-sm dark:border-slate-700 dark:bg-slate-800"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t">
                <button
                  type="button"
                  onClick={closeModal}
                  className="rounded-lg border px-4 py-2 text-sm font-medium hover:bg-slate-50 dark:hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending || updateMutation.isPending}
                  className="rounded-lg bg-teal-600 px-5 py-2 text-sm font-medium text-white hover:bg-teal-700 disabled:opacity-50"
                >
                  {createMutation.isPending || updateMutation.isPending
                    ? "Saving..."
                    : editingSupplier
                    ? "Update Supplier"
                    : "Create Supplier"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
