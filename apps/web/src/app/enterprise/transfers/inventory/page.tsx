"use client";

import { useState } from "react";
import {
  Boxes,
  Plus,
  Truck,
  CheckCircle2,
  Clock,
  ArrowRight,
  TrendingUp,
  PackageCheck,
} from "lucide-react";
import { EnterpriseNav } from "../../nav";
import { ConsolidatedInventoryItem, InventoryTransfer, InventoryTransferStatus } from "../../types";

const INITIAL_INV_TRANSFERS: InventoryTransfer[] = [
  {
    id: "inv-tr-1",
    organization_id: "org-1",
    transfer_number: "TRF-20260908-001",
    from_clinic_id: "br-1",
    from_clinic_name: "Central Flagship Clinic",
    to_clinic_id: "br-2",
    to_clinic_name: "Indiranagar Dental Lounge",
    item_id: "item-1",
    item_name: "Composite Resin A2 Syringe",
    quantity: 15,
    unit_cost: 850.0,
    status: "DISPATCHED",
    dispatched_at: "2026-09-08T09:00:00Z",
    tracking_number: "BLUEDART-8822001",
    notes: "Emergency inter-clinic stock balancing",
    created_at: "2026-09-08T08:30:00Z",
    updated_at: "2026-09-08T09:00:00Z",
  },
  {
    id: "inv-tr-2",
    organization_id: "org-1",
    transfer_number: "TRF-20260907-004",
    from_clinic_id: "br-1",
    from_clinic_name: "Central Flagship Clinic",
    to_clinic_id: "br-3",
    to_clinic_name: "Whitefield Specialty Wing",
    item_id: "item-2",
    item_name: "Sterile Dental Implant Fixture 4.0x10mm",
    quantity: 6,
    unit_cost: 6500.0,
    status: "RECEIVED",
    dispatched_at: "2026-09-07T10:00:00Z",
    received_at: "2026-09-07T16:00:00Z",
    tracking_number: "DTDC-443311",
    notes: "Implant replenishment for scheduled surgeries",
    created_at: "2026-09-07T09:30:00Z",
    updated_at: "2026-09-07T16:00:00Z",
  },
];

const CONSOLIDATED_STOCK: ConsolidatedInventoryItem[] = [
  {
    item_id: "item-1",
    item_name: "Composite Resin A2 Syringe",
    category: "CONSUMABLES",
    unit_of_measure: "syringe",
    total_stock: 45,
    total_valuation: 38250.0,
    clinic_breakdown: [
      { clinic_id: "br-1", clinic_name: "Central Flagship Clinic", stock: 25, valuation: 21250.0 },
      { clinic_id: "br-2", clinic_name: "Indiranagar Dental Lounge", stock: 12, valuation: 10200.0 },
      { clinic_id: "br-3", clinic_name: "Whitefield Specialty Wing", stock: 8, valuation: 6800.0 },
    ],
  },
  {
    item_id: "item-2",
    item_name: "Dental Implant Fixture 4.0x10mm",
    category: "IMPLANTS",
    unit_of_measure: "unit",
    total_stock: 18,
    total_valuation: 117000.0,
    clinic_breakdown: [
      { clinic_id: "br-1", clinic_name: "Central Flagship Clinic", stock: 10, valuation: 65000.0 },
      { clinic_id: "br-2", clinic_name: "Indiranagar Dental Lounge", stock: 5, valuation: 32500.0 },
      { clinic_id: "br-3", clinic_name: "Whitefield Specialty Wing", stock: 3, valuation: 19500.0 },
    ],
  },
];

export default function InventoryTransfersPage() {
  const [transfers, setTransfers] = useState<InventoryTransfer[]>(INITIAL_INV_TRANSFERS);
  const [activeTab, setActiveTab] = useState<"transfers" | "consolidated">("transfers");

  const handleReceive = (id: string) => {
    setTransfers(
      transfers.map((t) =>
        t.id === id
          ? { ...t, status: "RECEIVED" as InventoryTransferStatus, received_at: new Date().toISOString() }
          : t
      )
    );
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <EnterpriseNav />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Inter-Branch Inventory Logistics</h1>
            <p className="text-xs text-slate-500 mt-1">
              Transfer supplies between clinics, track stock in-transit, and review consolidated enterprise valuation.
            </p>
          </div>

          <div className="flex items-center gap-1 bg-slate-200/70 p-1 rounded-lg">
            <button
              onClick={() => setActiveTab("transfers")}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${
                activeTab === "transfers" ? "bg-white text-indigo-700 shadow-xs" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Stock Transfers
            </button>
            <button
              onClick={() => setActiveTab("consolidated")}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${
                activeTab === "consolidated" ? "bg-white text-indigo-700 shadow-xs" : "text-slate-600 hover:text-slate-900"
              }`}
            >
              Consolidated Valuation
            </button>
          </div>
        </div>

        {activeTab === "transfers" ? (
          <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-100 text-slate-500 font-semibold uppercase bg-slate-50/70">
                    <th className="py-3 px-4">Transfer #</th>
                    <th className="py-3 px-4">Item</th>
                    <th className="py-3 px-4">From</th>
                    <th className="py-3 px-4">To</th>
                    <th className="py-3 px-4">Quantity</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {transfers.map((t) => (
                    <tr key={t.id} className="hover:bg-slate-50/60 transition-colors">
                      <td className="py-3.5 px-4 font-mono font-bold text-indigo-600">{t.transfer_number}</td>
                      <td className="py-3.5 px-4 font-semibold text-slate-900">{t.item_name}</td>
                      <td className="py-3.5 px-4 text-slate-600">{t.from_clinic_name}</td>
                      <td className="py-3.5 px-4 text-indigo-600 font-medium">{t.to_clinic_name}</td>
                      <td className="py-3.5 px-4 font-bold text-slate-900">{t.quantity} units</td>
                      <td className="py-3.5 px-4">
                        <span
                          className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold border ${
                            t.status === "DISPATCHED"
                              ? "bg-amber-50 text-amber-700 border-amber-200"
                              : t.status === "RECEIVED"
                              ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                              : "bg-slate-50 text-slate-700 border-slate-200"
                          }`}
                        >
                          {t.status === "DISPATCHED" && <Truck className="w-3 h-3" />}
                          {t.status === "RECEIVED" && <CheckCircle2 className="w-3 h-3" />}
                          {t.status}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        {t.status === "DISPATCHED" ? (
                          <button
                            onClick={() => handleReceive(t.id)}
                            className="px-3 py-1 bg-indigo-600 hover:bg-indigo-700 text-white rounded font-medium shadow-xs"
                          >
                            Confirm Receipt
                          </button>
                        ) : (
                          <span className="text-slate-400">Stock Integrated</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
                <span className="text-xs font-medium text-slate-500">Total Consolidated Valuation</span>
                <div className="text-2xl font-bold text-slate-900 mt-2">₹1,55,250.00</div>
                <p className="text-xs text-emerald-600 mt-1 font-medium">All network branches combined</p>
              </div>
              <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
                <span className="text-xs font-medium text-slate-500">Central Consumables Monitored</span>
                <div className="text-2xl font-bold text-slate-900 mt-2">63 Items</div>
                <p className="text-xs text-slate-500 mt-1">Cross-branch automated replenishment active</p>
              </div>
            </div>

            <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
              <div className="px-6 py-4 bg-slate-50/70 border-b border-slate-100">
                <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  Network Stock by Clinic Breakdown
                </h2>
              </div>
              <div className="divide-y divide-slate-100">
                {CONSOLIDATED_STOCK.map((item) => (
                  <div key={item.item_id} className="p-6 space-y-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-bold text-slate-900 text-sm">{item.item_name}</h3>
                        <span className="text-xs text-slate-500 font-mono">Category: {item.category}</span>
                      </div>
                      <div className="text-right">
                        <div className="font-bold text-slate-900 text-sm">₹{item.total_valuation.toLocaleString()}</div>
                        <span className="text-xs text-indigo-600 font-semibold">{item.total_stock} {item.unit_of_measure} total</span>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
                      {item.clinic_breakdown.map((cb) => (
                        <div key={cb.clinic_id} className="p-3 bg-slate-50 rounded-lg border border-slate-100 text-xs">
                          <div className="font-semibold text-slate-900 truncate">{cb.clinic_name}</div>
                          <div className="flex items-center justify-between text-slate-500 mt-1">
                            <span>{cb.stock} {item.unit_of_measure}</span>
                            <span>₹{cb.valuation.toLocaleString()}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
