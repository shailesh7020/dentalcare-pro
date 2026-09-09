"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useQuery, useMutation } from "@tanstack/react-query";
import { ArrowLeft, Check, PackagePlus, Save } from "lucide-react";
import { api } from "@/lib/api";
import type { InventoryCategory, InventoryItemCreate, Supplier } from "../../types";

const CATEGORIES: InventoryCategory[] = [
  "CONSUMABLES",
  "INSTRUMENTS",
  "EQUIPMENT",
  "IMPLANTS",
  "ORTHODONTIC",
  "ENDODONTIC",
  "PROSTHODONTIC",
  "PERIODONTIC",
  "SURGICAL",
  "MEDICINES",
  "LABORATORY",
  "OFFICE_SUPPLIES",
];

const UNITS = [
  "PCS",
  "PACK",
  "BOX",
  "BOTTLE",
  "KIT",
  "TUBE",
  "VIAL",
  "SYRINGE",
  "GM",
  "ML",
  "PAIR",
  "ROLL",
  "SET",
];

export default function NewInventoryItemPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [genericName, setGenericName] = useState("");
  const [category, setCategory] = useState<InventoryCategory>("CONSUMABLES");
  const [supplierId, setSupplierId] = useState("");
  const [unit, setUnit] = useState("PACK");
  const [minimumStock, setMinimumStock] = useState(5);
  const [reorderLevel, setReorderLevel] = useState(10);
  const [purchasePrice, setPurchasePrice] = useState(100);
  const [sellingPrice, setSellingPrice] = useState<number | "">("");
  const [taxRate, setTaxRate] = useState(18);
  const [storageLocation, setStorageLocation] = useState("");
  const [notes, setNotes] = useState("");

  // Opening stock
  const [initialQty, setInitialQty] = useState(0);
  const [initialBatch, setInitialBatch] = useState("");
  const [initialExpiry, setInitialExpiry] = useState("");

  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Fetch Suppliers
  const suppliersQuery = useQuery({
    queryKey: ["inventory-suppliers-dropdown"],
    queryFn: async () => {
      const res = await api.get<Supplier[]>("/inventory/suppliers");
      return res.data;
    },
  });

  const createMutation = useMutation({
    mutationFn: async (payload: InventoryItemCreate) => {
      const res = await api.post("/inventory/items", payload);
      return res.data;
    },
    onSuccess: (data) => {
      router.push(`/inventory/items/${data.id}`);
    },
    onError: (err: any) => {
      setErrorMsg(err.response?.data?.detail || "Failed to create inventory item.");
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setErrorMsg("Item name is required.");
      return;
    }
    setErrorMsg(null);

    const payload: InventoryItemCreate = {
      name: name.trim(),
      generic_name: genericName.trim() || undefined,
      category,
      supplier_id: supplierId || undefined,
      unit,
      minimum_stock: Number(minimumStock),
      reorder_level: Number(reorderLevel),
      purchase_price: Number(purchasePrice),
      selling_price: sellingPrice !== "" ? Number(sellingPrice) : undefined,
      tax_rate: Number(taxRate),
      storage_location: storageLocation.trim() || undefined,
      notes: notes.trim() || undefined,
      initial_quantity: initialQty > 0 ? Number(initialQty) : undefined,
      initial_batch_number: initialQty > 0 ? initialBatch.trim() || undefined : undefined,
      initial_expiry_date: initialQty > 0 && initialExpiry ? initialExpiry : undefined,
    };

    createMutation.mutate(payload);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-16">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Link href="/inventory" className="hover:text-slate-900 dark:hover:text-slate-100 flex items-center gap-1">
          <ArrowLeft className="h-4 w-4" /> Back to Inventory
        </Link>
      </div>

      <div className="border-b pb-4">
        <h1 className="text-2xl font-bold tracking-tight">Create Inventory Item</h1>
        <p className="text-sm text-muted-foreground">
          Add dental supplies, clinical medication, or prosthetic inventory to your catalog.
        </p>
      </div>

      {errorMsg && (
        <div className="rounded-lg bg-rose-50 p-4 text-sm text-rose-700 dark:bg-rose-950/50 dark:text-rose-300">
          {errorMsg}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Basic Details */}
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900 space-y-4">
          <h2 className="text-base font-semibold border-b pb-2">Item Specifications</h2>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="sm:col-span-2">
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Commercial Item Name <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. 3M ESPE Filtek Z250 Composite Syringe A2"
                className="w-full rounded-lg border border-slate-300 bg-white py-2 px-3 text-sm focus:border-teal-500 focus:outline-none dark:border-slate-700 dark:bg-slate-800"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Generic / Chemical Composition
              </label>
              <input
                type="text"
                value={genericName}
                onChange={(e) => setGenericName(e.target.value)}
                placeholder="e.g. Microhybrid composite restorative resin"
                className="w-full rounded-lg border border-slate-300 bg-white py-2 px-3 text-sm focus:border-teal-500 focus:outline-none dark:border-slate-700 dark:bg-slate-800"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Category <span className="text-rose-500">*</span>
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value as InventoryCategory)}
                className="w-full rounded-lg border border-slate-300 bg-white py-2 px-3 text-sm focus:border-teal-500 focus:outline-none dark:border-slate-700 dark:bg-slate-800"
              >
                {CATEGORIES.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Stock Unit <span className="text-rose-500">*</span>
              </label>
              <select
                value={unit}
                onChange={(e) => setUnit(e.target.value)}
                className="w-full rounded-lg border border-slate-300 bg-white py-2 px-3 text-sm focus:border-teal-500 focus:outline-none dark:border-slate-700 dark:bg-slate-800"
              >
                {UNITS.map((u) => (
                  <option key={u} value={u}>
                    {u}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Preferred Supplier
              </label>
              <select
                value={supplierId}
                onChange={(e) => setSupplierId(e.target.value)}
                className="w-full rounded-lg border border-slate-300 bg-white py-2 px-3 text-sm focus:border-teal-500 focus:outline-none dark:border-slate-700 dark:bg-slate-800"
              >
                <option value="">-- Select Supplier --</option>
                {(suppliersQuery.data || []).map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Storage Location
              </label>
              <input
                type="text"
                value={storageLocation}
                onChange={(e) => setStorageLocation(e.target.value)}
                placeholder="e.g. Cabinet A, Drawer 3"
                className="w-full rounded-lg border border-slate-300 bg-white py-2 px-3 text-sm focus:border-teal-500 focus:outline-none dark:border-slate-700 dark:bg-slate-800"
              />
            </div>
          </div>
        </div>

        {/* Stock Thresholds & Financials */}
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900 space-y-4">
          <h2 className="text-base font-semibold border-b pb-2">Thresholds & Pricing</h2>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Minimum Stock
              </label>
              <input
                type="number"
                min="0"
                value={minimumStock}
                onChange={(e) => setMinimumStock(parseInt(e.target.value) || 0)}
                className="w-full rounded-lg border border-slate-300 bg-white py-2 px-3 text-sm focus:border-teal-500 focus:outline-none dark:border-slate-700 dark:bg-slate-800"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Reorder Threshold Level
              </label>
              <input
                type="number"
                min="1"
                value={reorderLevel}
                onChange={(e) => setReorderLevel(parseInt(e.target.value) || 0)}
                className="w-full rounded-lg border border-slate-300 bg-white py-2 px-3 text-sm focus:border-teal-500 focus:outline-none dark:border-slate-700 dark:bg-slate-800"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                GST / Tax Rate (%)
              </label>
              <input
                type="number"
                min="0"
                value={taxRate}
                onChange={(e) => setTaxRate(parseFloat(e.target.value) || 0)}
                className="w-full rounded-lg border border-slate-300 bg-white py-2 px-3 text-sm focus:border-teal-500 focus:outline-none dark:border-slate-700 dark:bg-slate-800"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Purchase Price (₹ per unit) <span className="text-rose-500">*</span>
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={purchasePrice}
                onChange={(e) => setPurchasePrice(parseFloat(e.target.value) || 0)}
                className="w-full rounded-lg border border-slate-300 bg-white py-2 px-3 text-sm focus:border-teal-500 focus:outline-none dark:border-slate-700 dark:bg-slate-800"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Selling / Patient Charge Price (₹)
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={sellingPrice}
                onChange={(e) => setSellingPrice(e.target.value === "" ? "" : parseFloat(e.target.value))}
                placeholder="Optional"
                className="w-full rounded-lg border border-slate-300 bg-white py-2 px-3 text-sm focus:border-teal-500 focus:outline-none dark:border-slate-700 dark:bg-slate-800"
              />
            </div>
          </div>
        </div>

        {/* Opening Stock (Initial Batch) */}
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900 space-y-4">
          <div className="flex items-center justify-between border-b pb-2">
            <div>
              <h2 className="text-base font-semibold">Opening Stock (Optional Initial Batch)</h2>
              <p className="text-xs text-muted-foreground">
                Enter current warehouse stock on hand if migrating inventory.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Initial Quantity
              </label>
              <input
                type="number"
                min="0"
                value={initialQty}
                onChange={(e) => setInitialQty(parseInt(e.target.value) || 0)}
                className="w-full rounded-lg border border-slate-300 bg-white py-2 px-3 text-sm focus:border-teal-500 focus:outline-none dark:border-slate-700 dark:bg-slate-800"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Batch / Lot Number
              </label>
              <input
                type="text"
                value={initialBatch}
                onChange={(e) => setInitialBatch(e.target.value)}
                placeholder="e.g. B-2026-001"
                className="w-full rounded-lg border border-slate-300 bg-white py-2 px-3 text-sm focus:border-teal-500 focus:outline-none dark:border-slate-700 dark:bg-slate-800"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                Expiry Date
              </label>
              <input
                type="date"
                value={initialExpiry}
                onChange={(e) => setInitialExpiry(e.target.value)}
                className="w-full rounded-lg border border-slate-300 bg-white py-2 px-3 text-sm focus:border-teal-500 focus:outline-none dark:border-slate-700 dark:bg-slate-800"
              />
            </div>
          </div>
        </div>

        {/* Submit */}
        <div className="flex items-center justify-end gap-3">
          <Link
            href="/inventory"
            className="rounded-lg border px-4 py-2 text-sm font-medium hover:bg-slate-50 dark:hover:bg-slate-800"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={createMutation.isPending}
            className="inline-flex items-center gap-1.5 rounded-lg bg-teal-600 px-5 py-2 text-sm font-medium text-white shadow hover:bg-teal-700 disabled:opacity-50 transition"
          >
            <Save className="h-4 w-4" />
            {createMutation.isPending ? "Creating Item..." : "Save Catalog Item"}
          </button>
        </div>
      </form>
    </div>
  );
}
