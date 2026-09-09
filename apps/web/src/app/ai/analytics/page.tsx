"use client";

import Link from "next/link";
import { useState } from "react";
import type { InventoryForecastItem } from "../types";

const MOCK_INVENTORY: InventoryForecastItem[] = [
  {
    item_id: "INV-101",
    item_name: "Composite Resin Syringes (A2 Shade)",
    sku: "RES-A2-3G",
    category: "Restorative Consumables",
    current_stock: 4,
    min_stock_level: 10,
    burn_rate_weekly: 6,
    projected_depletion_date: "2026-09-13",
    reorder_urgency: "CRITICAL",
    suggested_reorder_quantity: 25,
    estimated_cost: 12500,
  },
  {
    item_id: "INV-102",
    item_name: "2% Lignocaine with 1:80,000 Adrenaline Cartridges",
    sku: "LA-LIG-18ML",
    category: "Anesthetics",
    current_stock: 22,
    min_stock_level: 50,
    burn_rate_weekly: 45,
    projected_depletion_date: "2026-09-12",
    reorder_urgency: "HIGH",
    suggested_reorder_quantity: 100,
    estimated_cost: 4500,
  },
  {
    item_id: "INV-103",
    item_name: "Examination Nitrile Gloves (Medium)",
    sku: "GLV-NIT-MED",
    category: "PPE & Infection Control",
    current_stock: 12,
    min_stock_level: 20,
    burn_rate_weekly: 15,
    projected_depletion_date: "2026-09-14",
    reorder_urgency: "HIGH",
    suggested_reorder_quantity: 40,
    estimated_cost: 8000,
  },
  {
    item_id: "INV-104",
    item_name: "Gutta-Percha Points (0.04 Taper Assorted)",
    sku: "ENDO-GP-04",
    category: "Endodontics",
    current_stock: 8,
    min_stock_level: 5,
    burn_rate_weekly: 2,
    projected_depletion_date: "2026-10-06",
    reorder_urgency: "MEDIUM",
    suggested_reorder_quantity: 10,
    estimated_cost: 3200,
  },
  {
    item_id: "INV-105",
    item_name: "3% Sodium Hypochlorite Canal Irrigant (500ml)",
    sku: "IRR-NAOCL-500",
    category: "Endodontics",
    current_stock: 15,
    min_stock_level: 5,
    burn_rate_weekly: 1,
    projected_depletion_date: "2026-12-20",
    reorder_urgency: "NORMAL",
    suggested_reorder_quantity: 5,
    estimated_cost: 950,
  },
];

export default function AIAnalyticsPage() {
  const [inventory, setInventory] = useState<InventoryForecastItem[]>(MOCK_INVENTORY);
  const [reorderedId, setReorderedId] = useState<string | null>(null);

  const handleReorder = (itemId: string) => {
    setReorderedId(itemId);
    setTimeout(() => {
      setReorderedId(null);
    }, 2500);
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-4 md:p-8">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div>
            <div className="flex items-center gap-2 text-sm text-slate-400 mb-1">
              <Link href="/" className="hover:text-cyan-400">Dashboard</Link>
              <span>/</span>
              <Link href="/ai" className="hover:text-cyan-400">AI Hub</Link>
              <span>/</span>
              <span className="text-slate-200">Practice Analytics</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white flex items-center gap-3">
              📈 Practice Analytics & AI Stock Forecasting
            </h1>
          </div>

          <Link
            href="/ai"
            className="px-3 py-1.5 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 transition"
          >
            Back to AI Hub
          </Link>
        </div>

        {/* Natural Language Executive Insights */}
        <div className="bg-gradient-to-r from-blue-950/60 to-cyan-950/60 border border-cyan-800/50 rounded-xl p-5 space-y-3 shadow-lg">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-cyan-300 flex items-center gap-2">
              <span>💡</span> AI Executive Summary & Clinical Operations Pulse
            </h2>
            <span className="text-[11px] text-cyan-400 font-mono">Updated: Today, 08:30 AM</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-slate-300">
            <div className="bg-slate-900/60 rounded-lg p-3 border border-slate-800 space-y-1">
              <p className="font-semibold text-emerald-400">Revenue Trajectory</p>
              <p>Practice is trending at <strong>₹1,84,500/mo (+16% vs forecast)</strong>. High-value restorative procedures (crowns and endodontics) accounted for 62% of revenue.</p>
            </div>
            <div className="bg-slate-900/60 rounded-lg p-3 border border-slate-800 space-y-1">
              <p className="font-semibold text-amber-400">Chair Efficiency</p>
              <p>Chair 1 utilization is optimal at <strong>84%</strong>. Chair 3 experiences a 28% vacancy dip on Tuesday & Thursday afternoons. AI scheduling recommends slot compaction.</p>
            </div>
            <div className="bg-slate-900/60 rounded-lg p-3 border border-slate-800 space-y-1">
              <p className="font-semibold text-rose-400">Stock Depletion Alert</p>
              <p><strong>Composite Resin A2</strong> and <strong>2% Lignocaine</strong> will deplete within 5 days based on 4-week moving average usage. Auto-reorder recommended.</p>
            </div>
          </div>
        </div>

        {/* KPIs */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="bg-slate-800/80 border border-slate-700/70 rounded-xl p-4">
            <p className="text-xs text-slate-400 font-medium">Chair Occupancy</p>
            <p className="text-2xl font-bold text-white mt-1">79.4%</p>
            <span className="text-[11px] text-emerald-400">Optimal (Target 75-85%)</span>
          </div>
          <div className="bg-slate-800/80 border border-slate-700/70 rounded-xl p-4">
            <p className="text-xs text-slate-400 font-medium">Recall Adherence</p>
            <p className="text-2xl font-bold text-white mt-1">82.1%</p>
            <span className="text-[11px] text-emerald-400">+5.3% since Phase 10 Portal</span>
          </div>
          <div className="bg-slate-800/80 border border-slate-700/70 rounded-xl p-4">
            <p className="text-xs text-slate-400 font-medium">Cancellation Rate</p>
            <p className="text-2xl font-bold text-white mt-1">4.2%</p>
            <span className="text-[11px] text-emerald-400">Industry avg: 11%</span>
          </div>
          <div className="bg-slate-800/80 border border-slate-700/70 rounded-xl p-4">
            <p className="text-xs text-slate-400 font-medium">Proc. Duration Accuracy</p>
            <p className="text-2xl font-bold text-white mt-1">94.8%</p>
            <span className="text-[11px] text-cyan-400">Variance: ±3.8 mins</span>
          </div>
        </div>

        {/* Predictive Inventory Depletion Table */}
        <div className="bg-slate-800/80 border border-slate-700/70 rounded-xl p-5 space-y-4 shadow-lg">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-700/60 pb-3">
            <div>
              <h2 className="text-base font-semibold text-slate-200">
                📦 AI Inventory Burn-Rate & Depletion Forecast
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                Projections calculated from appointment procedure logs and historical consumable usage rates
              </p>
            </div>
            <Link
              href="/inventory/purchase-orders/new"
              className="px-3 py-1.5 text-xs font-semibold bg-cyan-600 hover:bg-cyan-500 text-white rounded shadow transition"
            >
              + Create Purchase Order
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-200">
              <thead className="bg-slate-900/60 text-slate-400 uppercase tracking-wider text-[11px]">
                <tr>
                  <th className="p-3">Item / SKU</th>
                  <th className="p-3">Category</th>
                  <th className="p-3">Current Stock</th>
                  <th className="p-3">Burn Rate</th>
                  <th className="p-3">Depletion Date</th>
                  <th className="p-3">Urgency</th>
                  <th className="p-3">Suggested Order</th>
                  <th className="p-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/50 font-sans">
                {inventory.map((item) => (
                  <tr key={item.item_id ?? item.item_name} className="hover:bg-slate-700/30 transition">
                    <td className="p-3">
                      <p className="font-semibold text-white">{item.item_name}</p>
                      <p className="text-[11px] font-mono text-slate-400">{item.sku ?? "SKU-AUTO"}</p>
                    </td>
                    <td className="p-3 text-slate-300">{item.category}</td>
                    <td className="p-3 font-medium">
                      <span className={item.current_stock <= (item.min_stock_level ?? 0) ? "text-rose-400 font-bold" : "text-slate-200"}>
                        {item.current_stock} units
                      </span>
                      <span className="text-[10px] text-slate-500 block">Min: {item.min_stock_level ?? 0}</span>
                    </td>
                    <td className="p-3 text-slate-300">{item.burn_rate_weekly ?? item.predicted_burn_rate_weekly ?? 0} / wk</td>
                    <td className="p-3 font-mono text-slate-200">{item.projected_depletion_date}</td>
                    <td className="p-3">
                      <span
                        className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                          item.reorder_urgency === "CRITICAL"
                            ? "bg-rose-950 text-rose-300 border border-rose-700"
                            : item.reorder_urgency === "HIGH"
                            ? "bg-amber-950 text-amber-300 border border-amber-700"
                            : item.reorder_urgency === "MEDIUM"
                            ? "bg-blue-950 text-blue-300 border border-blue-700"
                            : "bg-slate-800 text-slate-400 border border-slate-700"
                        }`}
                      >
                        {item.reorder_urgency ?? item.urgency ?? "NORMAL"}
                      </span>
                    </td>
                    <td className="p-3">
                      <p className="font-medium text-white">{item.suggested_reorder_quantity ?? item.recommended_reorder_qty ?? 0} units</p>
                      <p className="text-[10px] text-slate-400">Est. ₹{(item.estimated_cost ?? 0).toLocaleString()}</p>
                    </td>
                    <td className="p-3 text-right">
                      {item.item_id && reorderedId === item.item_id ? (
                        <span className="text-xs text-emerald-400 font-medium">✓ PO Created</span>
                      ) : (
                        <button
                          type="button"
                          onClick={() => handleReorder(item.item_id ?? item.item_name)}
                          className="px-2.5 py-1 bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs rounded transition"
                        >
                          Reorder
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
