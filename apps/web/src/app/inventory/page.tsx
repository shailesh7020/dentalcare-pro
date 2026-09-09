"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  ArrowRight,
  Boxes,
  CheckCircle2,
  DollarSign,
  FileSpreadsheet,
  Filter,
  IndianRupee,
  Layers,
  Package,
  PackagePlus,
  Plus,
  RefreshCw,
  Search,
  ShoppingCart,
  SlidersHorizontal,
  TrendingDown,
  Truck,
  Users,
  X,
  XCircle,
} from "lucide-react";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import type {
  InventoryAlerts,
  InventoryCategory,
  InventoryDashboardStats,
  InventoryItem,
  InventoryStatus,
  StockAdjustmentCreate,
  StockTransactionType,
} from "./types";

const CATEGORIES: { label: string; value: string }[] = [
  { label: "All Categories", value: "ALL" },
  { label: "Consumables", value: "CONSUMABLES" },
  { label: "Medicines", value: "MEDICINES" },
  { label: "Surgical", value: "SURGICAL" },
  { label: "Endodontic", value: "ENDODONTIC" },
  { label: "Orthodontic", value: "ORTHODONTIC" },
  { label: "Prosthodontic", value: "PROSTHODONTIC" },
  { label: "Instruments", value: "INSTRUMENTS" },
  { label: "Implants", value: "IMPLANTS" },
  { label: "Equipment", value: "EQUIPMENT" },
  { label: "Laboratory", value: "LABORATORY" },
];

export default function InventoryDashboardPage() {
  const queryClient = useQueryClient();
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("ALL");
  const [selectedStatus, setSelectedStatus] = useState<string>("ALL");

  // Adjust Modal state
  const [adjustItem, setAdjustItem] = useState<InventoryItem | null>(null);
  const [adjustType, setAdjustType] = useState<StockTransactionType>("ADJUSTMENT");
  const [adjustQty, setAdjustQty] = useState<number>(0);
  const [adjustReason, setAdjustReason] = useState<string>("");
  const [adjustError, setAdjustError] = useState<string | null>(null);

  // 1. Fetch Dashboard Stats
  const statsQuery = useQuery({
    queryKey: ["inventory-dashboard-stats"],
    queryFn: async () => {
      const res = await api.get<InventoryDashboardStats>("/inventory/dashboard/stats");
      return res.data;
    },
  });

  // 2. Fetch Alerts
  const alertsQuery = useQuery({
    queryKey: ["inventory-alerts"],
    queryFn: async () => {
      const res = await api.get<InventoryAlerts>("/inventory/alerts");
      return res.data;
    },
  });

  // 3. Fetch Items List
  const itemsQuery = useQuery({
    queryKey: ["inventory-items-list", selectedCategory, selectedStatus, searchTerm],
    queryFn: async () => {
      const params: Record<string, string | boolean> = {};
      if (selectedCategory !== "ALL") params.category = selectedCategory;
      if (selectedStatus !== "ALL") params.status = selectedStatus;
      if (searchTerm.trim()) params.search = searchTerm.trim();
      const res = await api.get<{ items: InventoryItem[]; total: number }>("/inventory/items", { params });
      return res.data;
    },
  });

  // Stock Adjustment Mutation
  const adjustMutation = useMutation({
    mutationFn: async (payload: StockAdjustmentCreate) => {
      if (!adjustItem) return;
      const res = await api.post(`/inventory/items/${adjustItem.id}/adjust`, payload);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["inventory-items-list"] });
      queryClient.invalidateQueries({ queryKey: ["inventory-dashboard-stats"] });
      queryClient.invalidateQueries({ queryKey: ["inventory-alerts"] });
      setAdjustItem(null);
      setAdjustQty(0);
      setAdjustReason("");
      setAdjustError(null);
    },
    onError: (err: any) => {
      const detail = err.response?.data?.detail || "Failed to adjust stock.";
      setAdjustError(detail);
    },
  });

  const handleQuickAdjust = (e: React.FormEvent) => {
    e.preventDefault();
    if (!adjustItem) return;
    if (adjustQty === 0) {
      setAdjustError("Quantity delta cannot be zero.");
      return;
    }
    if (adjustQty < 0 && adjustItem.current_quantity + adjustQty < 0) {
      setAdjustError(`Cannot reduce below 0. Maximum reduction is ${adjustItem.current_quantity}.`);
      return;
    }
    if (!adjustReason.trim()) {
      setAdjustError("Please specify a reason for this adjustment.");
      return;
    }
    setAdjustError(null);
    adjustMutation.mutate({
      adjustment_type: adjustType,
      quantity: adjustQty,
      reason: adjustReason.trim(),
    });
  };

  const stats = statsQuery.data;
  const alerts = alertsQuery.data;
  const items = itemsQuery.data?.items || [];
  const totalItems = itemsQuery.data?.total || 0;

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-lg bg-teal-50 text-teal-700 dark:bg-teal-950/50 dark:text-teal-400">
              <Boxes className="h-6 w-6" />
            </span>
            <div>
              <h1 className="text-2xl font-bold tracking-tight">Inventory & Pharmacy Hub</h1>
              <p className="text-sm text-muted-foreground">
                Manage dental supplies, clinical medication catalogs, FIFO batches, and procurement.
              </p>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Link
            href="/inventory/items/new"
            className="inline-flex items-center gap-1.5 rounded-lg bg-teal-600 px-3.5 py-2 text-sm font-medium text-white shadow-sm hover:bg-teal-700 transition"
          >
            <Plus className="h-4 w-4" />
            Add Item
          </Link>
          <Link
            href="/inventory/purchase-orders/new"
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200 transition"
          >
            <ShoppingCart className="h-4 w-4" />
            Create PO
          </Link>
          <Link
            href="/inventory/purchase-orders"
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200 transition"
          >
            <Truck className="h-4 w-4" />
            Purchase Orders
          </Link>
          <Link
            href="/inventory/suppliers"
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200 transition"
          >
            <Users className="h-4 w-4" />
            Suppliers
          </Link>
          <Link
            href="/inventory/reports"
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200 transition"
          >
            <FileSpreadsheet className="h-4 w-4" />
            Reports
          </Link>
        </div>
      </div>

      {/* KPI Metric Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Total Catalog</span>
            <Package className="h-4 w-4 text-slate-500" />
          </div>
          <div className="mt-2 text-2xl font-bold tracking-tight">
            {statsQuery.isLoading ? <Skeleton className="h-8 w-16" /> : (stats?.total_items ?? 0)}
          </div>
          <p className="text-xs text-muted-foreground mt-1">Across 12 categories</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Stock Valuation</span>
            <IndianRupee className="h-4 w-4 text-emerald-500" />
          </div>
          <div className="mt-2 text-2xl font-bold tracking-tight text-emerald-700 dark:text-emerald-400">
            {statsQuery.isLoading ? (
              <Skeleton className="h-8 w-24" />
            ) : (
              `₹${(stats?.total_valuation ?? 0).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
            )}
          </div>
          <p className="text-xs text-muted-foreground mt-1">Warehouse & Operatories</p>
        </div>

        <div className="rounded-xl border border-amber-200 bg-amber-50/50 p-4 shadow-sm dark:border-amber-900/50 dark:bg-amber-950/20">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-amber-800 dark:text-amber-400 uppercase tracking-wider">Low Stock</span>
            <AlertTriangle className="h-4 w-4 text-amber-600" />
          </div>
          <div className="mt-2 text-2xl font-bold tracking-tight text-amber-700 dark:text-amber-400">
            {statsQuery.isLoading ? <Skeleton className="h-8 w-16" /> : (stats?.low_stock_items ?? 0)}
          </div>
          <p className="text-xs text-amber-700/80 dark:text-amber-400/80 mt-1">Below reorder threshold</p>
        </div>

        <div className="rounded-xl border border-rose-200 bg-rose-50/50 p-4 shadow-sm dark:border-rose-900/50 dark:bg-rose-950/20">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-rose-800 dark:text-rose-400 uppercase tracking-wider">Out of Stock</span>
            <XCircle className="h-4 w-4 text-rose-600" />
          </div>
          <div className="mt-2 text-2xl font-bold tracking-tight text-rose-700 dark:text-rose-400">
            {statsQuery.isLoading ? <Skeleton className="h-8 w-16" /> : (stats?.out_of_stock_items ?? 0)}
          </div>
          <p className="text-xs text-rose-700/80 dark:text-rose-400/80 mt-1">Immediate reorder needed</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Pending Orders</span>
            <Truck className="h-4 w-4 text-blue-500" />
          </div>
          <div className="mt-2 text-2xl font-bold tracking-tight text-blue-700 dark:text-blue-400">
            {statsQuery.isLoading ? <Skeleton className="h-8 w-16" /> : (stats?.pending_purchase_orders ?? 0)}
          </div>
          <p className="text-xs text-muted-foreground mt-1">Awaiting goods receipt</p>
        </div>
      </div>

      {/* Critical Alert Banner (if any expired batches or zero stock items) */}
      {alerts && (alerts.expired_batches.length > 0 || alerts.out_of_stock_items.length > 0) && (
        <div className="rounded-lg border border-rose-300 bg-rose-50 p-4 dark:border-rose-900 dark:bg-rose-950/40 text-rose-900 dark:text-rose-200">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-rose-600 shrink-0 mt-0.5" />
            <div className="flex-1 text-sm">
              <span className="font-semibold">Clinical Stock Attention Required:</span>
              <ul className="mt-1 list-disc list-inside space-y-0.5">
                {alerts.expired_batches.length > 0 && (
                  <li>
                    {alerts.expired_batches.length} batch(es) have expired and must be quarantined/disposed.
                  </li>
                )}
                {alerts.out_of_stock_items.length > 0 && (
                  <li>
                    {alerts.out_of_stock_items.length} critical material(s) are completely depleted.
                  </li>
                )}
              </ul>
            </div>
            <Link
              href="/inventory/purchase-orders/new"
              className="text-xs font-medium bg-rose-600 text-white px-3 py-1.5 rounded hover:bg-rose-700 transition"
            >
              Order Now
            </Link>
          </div>
        </div>
      )}

      {/* Controls: Search, Category Tabs, Status Filter */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search by SKU, item name, or generic formula..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full rounded-lg border border-slate-300 bg-white py-2 pl-9 pr-3 text-sm placeholder:text-muted-foreground focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500 dark:border-slate-700 dark:bg-slate-900"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Category Dropdown */}
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="rounded-lg border border-slate-300 bg-white py-2 px-3 text-sm focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500 dark:border-slate-700 dark:bg-slate-900"
          >
            {CATEGORIES.map((cat) => (
              <option key={cat.value} value={cat.value}>
                {cat.label}
              </option>
            ))}
          </select>

          {/* Status Filter */}
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="rounded-lg border border-slate-300 bg-white py-2 px-3 text-sm focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500 dark:border-slate-700 dark:bg-slate-900"
          >
            <option value="ALL">All Statuses</option>
            <option value="IN_STOCK">In Stock</option>
            <option value="LOW_STOCK">Low Stock</option>
            <option value="OUT_OF_STOCK">Out of Stock</option>
          </select>

          <button
            onClick={() => {
              itemsQuery.refetch();
              statsQuery.refetch();
              alertsQuery.refetch();
            }}
            className="p-2 rounded-lg border border-slate-300 bg-white text-slate-600 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
            title="Refresh Inventory"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Items Master Table */}
      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-200 bg-slate-50/75 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:border-slate-800 dark:bg-slate-800/50 dark:text-slate-400">
              <tr>
                <th className="px-4 py-3">SKU / Item Name</th>
                <th className="px-4 py-3">Category</th>
                <th className="px-4 py-3">On Hand</th>
                <th className="px-4 py-3">Reorder Threshold</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Unit Price</th>
                <th className="px-4 py-3">Valuation</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
              {itemsQuery.isLoading ? (
                Array.from({ length: 6 }).map((_, i) => (
                  <tr key={i}>
                    <td colSpan={8} className="px-4 py-3">
                      <Skeleton className="h-6 w-full" />
                    </td>
                  </tr>
                ))
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-4 py-12 text-center text-muted-foreground">
                    <Package className="mx-auto h-8 w-8 text-slate-400 mb-2" />
                    <p className="text-base font-medium">No inventory items found</p>
                    <p className="text-xs mt-1">Try adjusting your filters or add a new stock item.</p>
                  </td>
                </tr>
              ) : (
                items.map((item) => {
                  const valuation = item.current_quantity * item.purchase_price;
                  return (
                    <tr
                      key={item.id}
                      className="hover:bg-slate-50/75 dark:hover:bg-slate-800/50 transition-colors"
                    >
                      <td className="px-4 py-3">
                        <Link
                          href={`/inventory/items/${item.id}`}
                          className="font-medium text-teal-600 hover:text-teal-700 dark:text-teal-400 dark:hover:text-teal-300"
                        >
                          {item.name}
                        </Link>
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                          <span className="font-mono">{item.sku}</span>
                          {item.generic_name && <span>· {item.generic_name}</span>}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className="inline-block rounded bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                          {item.category}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="font-semibold">{item.current_quantity}</span>{" "}
                        <span className="text-xs text-muted-foreground">{item.unit}</span>
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">
                        {item.reorder_level} {item.unit}
                      </td>
                      <td className="px-4 py-3">
                        {item.status === "IN_STOCK" && (
                          <Badge className="bg-emerald-100 text-emerald-800 hover:bg-emerald-100 dark:bg-emerald-950/60 dark:text-emerald-400">
                            In Stock
                          </Badge>
                        )}
                        {item.status === "LOW_STOCK" && (
                          <Badge className="bg-amber-100 text-amber-800 hover:bg-amber-100 dark:bg-amber-950/60 dark:text-amber-400">
                            Low Stock
                          </Badge>
                        )}
                        {item.status === "OUT_OF_STOCK" && (
                          <Badge className="bg-rose-100 text-rose-800 hover:bg-rose-100 dark:bg-rose-950/60 dark:text-rose-400">
                            Out of Stock
                          </Badge>
                        )}
                        {item.status === "DISCONTINUED" && (
                          <Badge className="bg-slate-100 text-slate-800 hover:bg-slate-100 dark:bg-slate-800 dark:text-slate-300">
                            Discontinued
                          </Badge>
                        )}
                      </td>
                      <td className="px-4 py-3">₹{item.purchase_price.toFixed(2)}</td>
                      <td className="px-4 py-3 font-medium">₹{valuation.toFixed(2)}</td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={() => {
                              setAdjustItem(item);
                              setAdjustQty(0);
                              setAdjustReason("");
                              setAdjustError(null);
                            }}
                            className="rounded px-2 py-1 text-xs font-medium text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800 transition"
                            title="Adjust Stock"
                          >
                            Adjust
                          </button>
                          <Link
                            href={`/inventory/items/${item.id}`}
                            className="rounded p-1 text-slate-400 hover:text-teal-600 dark:hover:text-teal-400 transition"
                            title="View Details"
                          >
                            <ArrowRight className="h-4 w-4" />
                          </Link>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
        <div className="flex items-center justify-between border-t border-slate-200 px-4 py-3 text-xs text-muted-foreground dark:border-slate-800">
          <span>Showing {items.length} of {totalItems} items</span>
          <span>DentalCare Pro Inventory Engine</span>
        </div>
      </div>

      {/* Stock Adjustment Modal */}
      {adjustItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl dark:bg-slate-900 border border-slate-200 dark:border-slate-800">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="font-semibold text-lg">Stock Adjustment</h3>
              <button
                onClick={() => setAdjustItem(null)}
                className="text-muted-foreground hover:text-slate-800 dark:hover:text-slate-200"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleQuickAdjust} className="space-y-4 mt-4">
              <div>
                <p className="text-sm font-medium">{adjustItem.name}</p>
                <p className="text-xs text-muted-foreground">
                  SKU: {adjustItem.sku} · On-Hand: <b className="text-slate-800 dark:text-slate-200">{adjustItem.current_quantity} {adjustItem.unit}</b>
                </p>
              </div>

              {adjustError && (
                <div className="rounded-lg bg-rose-50 p-3 text-xs text-rose-700 dark:bg-rose-950/40 dark:text-rose-300">
                  {adjustError}
                </div>
              )}

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Adjustment Type
                </label>
                <select
                  value={adjustType}
                  onChange={(e) => setAdjustType(e.target.value as StockTransactionType)}
                  className="w-full rounded-lg border border-slate-300 bg-white py-2 px-3 text-sm focus:border-teal-500 focus:outline-none dark:border-slate-700 dark:bg-slate-800"
                >
                  <option value="ADJUSTMENT">General Adjustment (Count Correction)</option>
                  <option value="EXPIRY_DISPOSAL">Expiry Disposal</option>
                  <option value="RETURN_TO_SUPPLIER">Return to Supplier</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Quantity Delta (Use negative to deduct, positive to add)
                </label>
                <input
                  type="number"
                  value={adjustQty}
                  onChange={(e) => setAdjustQty(parseInt(e.target.value) || 0)}
                  className="w-full rounded-lg border border-slate-300 bg-white py-2 px-3 text-sm focus:border-teal-500 focus:outline-none dark:border-slate-700 dark:bg-slate-800"
                  placeholder="e.g. -5 to reduce, 10 to add"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Resulting Quantity: <b>{adjustItem.current_quantity + adjustQty} {adjustItem.unit}</b>
                </p>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-700 dark:text-slate-300 mb-1">
                  Reason for Adjustment <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  value={adjustReason}
                  onChange={(e) => setAdjustReason(e.target.value)}
                  placeholder="e.g. Broken packaging, physical inventory audit mismatch"
                  className="w-full rounded-lg border border-slate-300 bg-white py-2 px-3 text-sm focus:border-teal-500 focus:outline-none dark:border-slate-700 dark:bg-slate-800"
                  required
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t">
                <button
                  type="button"
                  onClick={() => setAdjustItem(null)}
                  className="rounded-lg border px-4 py-2 text-sm font-medium hover:bg-slate-50 dark:hover:bg-slate-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={adjustMutation.isPending}
                  className="rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-700 disabled:opacity-50"
                >
                  {adjustMutation.isPending ? "Applying..." : "Save Adjustment"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
