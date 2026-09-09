"use client";

import React, { useState } from "react";
import {
  COLOR_STANDARDS,
  getToothLabel,
  NumberingSystem,
  Tooth,
  ToothSurface,
  ToothSurfaceEnum,
} from "@/app/patients/[id]/odontogram/types";
import { Badge } from "@/components/ui/badge";
import { X, Clock, ShieldAlert, Sparkles, Activity } from "lucide-react";

interface ToothDetailPanelProps {
  tooth: Tooth | null;
  numberingSystem: NumberingSystem;
  onClose: () => void;
  onUpdateStatus: (status: string, notes?: string) => Promise<void>;
  onUpdateSurface: (surface: ToothSurfaceEnum, condition: string, treatment: string) => Promise<void>;
}

export function ToothDetailPanel({
  tooth,
  numberingSystem,
  onClose,
  onUpdateStatus,
  onUpdateSurface,
}: ToothDetailPanelProps) {
  const [activeTab, setActiveTab] = useState<"surfaces" | "history" | "actions">("surfaces");
  const [selectedSurface, setSelectedSurface] = useState<ToothSurface | null>(null);
  const [surfaceCondition, setSurfaceCondition] = useState("HEALTHY");
  const [surfaceTreatment, setSurfaceTreatment] = useState("NONE");
  const [statusNotes, setStatusNotes] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  if (!tooth) return null;

  const handleStatusSubmit = async (status: string) => {
    setErrorMessage(null);
    setIsSubmitting(true);
    try {
      await onUpdateStatus(status, statusNotes);
      setStatusNotes("");
    } catch (err: unknown) {
      const errorMsg =
        typeof err === "object" && err !== null && "message" in err
          ? String((err as { message: unknown }).message)
          : "Clinical validation error.";
      setErrorMessage(errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSurfaceSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSurface) return;
    setErrorMessage(null);
    setIsSubmitting(true);
    try {
      await onUpdateSurface(selectedSurface.surface, surfaceCondition, surfaceTreatment);
      setSelectedSurface(null);
    } catch (err: unknown) {
      const errorMsg =
        typeof err === "object" && err !== null && "message" in err
          ? String((err as { message: unknown }).message)
          : "Failed to update tooth surface.";
      setErrorMessage(errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-lg shadow-md flex flex-col h-full max-h-[720px] overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-slate-100 flex items-start justify-between bg-slate-50/50">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xl font-bold font-mono text-slate-900">
              #{getToothLabel(tooth, numberingSystem)}
            </span>
            <span className="text-xs text-slate-400 font-mono">
              ({numberingSystem} · FDI: {tooth.tooth_number} · Univ: {tooth.universal_number} · Palmer: {tooth.palmer_notation})
            </span>
            <span
              className="px-2 py-0.5 rounded text-[11px] font-bold text-white uppercase tracking-wider"
              style={{
                backgroundColor:
                  COLOR_STANDARDS[tooth.primary_status] || "#10B981",
              }}
            >
              {tooth.primary_status.replaceAll("_", " ")}
            </span>
          </div>
          <h3 className="text-xs font-semibold text-slate-700 mt-1">
            {tooth.name} · {tooth.arch} Arch (Quad {tooth.quadrant})
          </h3>
        </div>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-slate-600 p-1 rounded-md hover:bg-slate-100 transition-colors"
        >
          <X size={16} />
        </button>
      </div>

      {/* Error Alert if any */}
      {errorMessage && (
        <div className="mx-4 mt-3 p-2.5 bg-rose-50 border border-rose-200 rounded-md text-xs text-rose-800 flex items-start gap-2">
          <ShieldAlert size={15} className="shrink-0 text-rose-600 mt-0.5" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Navigation Subtabs */}
      <div className="flex border-b border-slate-200 px-4 bg-white text-xs font-medium text-slate-600">
        <button
          onClick={() => setActiveTab("surfaces")}
          className={`py-2.5 px-3 border-b-2 font-semibold transition-colors ${
            activeTab === "surfaces"
              ? "border-teal-600 text-teal-700"
              : "border-transparent hover:text-slate-900"
          }`}
        >
          Surfaces ({tooth.surfaces.length})
        </button>
        <button
          onClick={() => setActiveTab("history")}
          className={`py-2.5 px-3 border-b-2 font-semibold transition-colors ${
            activeTab === "history"
              ? "border-teal-600 text-teal-700"
              : "border-transparent hover:text-slate-900"
          }`}
        >
          History & Audit
        </button>
        <button
          onClick={() => setActiveTab("actions")}
          className={`py-2.5 px-3 border-b-2 font-semibold transition-colors ${
            activeTab === "actions"
              ? "border-teal-600 text-teal-700"
              : "border-transparent hover:text-slate-900"
          }`}
        >
          Quick Actions
        </button>
      </div>

      {/* Body Content */}
      <div className="p-4 overflow-y-auto flex-1 text-xs">
        {/* TAB 1: Surfaces */}
        {activeTab === "surfaces" && (
          <div className="space-y-3">
            <p className="text-slate-500">
              Independent 8-surface clinical charting. Click any surface to inspect or update condition and restorations:
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {tooth.surfaces.map((surf) => (
                <div
                  key={surf.surface}
                  onClick={() => {
                    setSelectedSurface(surf);
                    setSurfaceCondition(surf.condition);
                    setSurfaceTreatment(surf.treatment);
                  }}
                  className={`p-2.5 rounded-md border transition-all cursor-pointer ${
                    selectedSurface?.surface === surf.surface
                      ? "border-teal-600 bg-teal-50/50 shadow-xs"
                      : "border-slate-200 hover:border-slate-300 bg-white"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-800 flex items-center gap-1.5">
                      <span
                        className="w-2.5 h-2.5 rounded-full"
                        style={{ backgroundColor: surf.color || "#10B981" }}
                      />
                      {surf.surface}
                    </span>
                    <Badge variant="outline" className="text-[10px] font-mono">
                      {surf.condition}
                    </Badge>
                  </div>
                  {surf.treatment !== "NONE" && (
                    <div className="mt-1 text-[11px] text-teal-800 font-medium">
                      Treatment: {surf.treatment}
                    </div>
                  )}
                  {surf.last_modified_at && (
                    <div className="mt-1 text-[10px] text-slate-400">
                      Modified: {new Date(surf.last_modified_at).toLocaleDateString()}
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Surface Edit Modal / Box */}
            {selectedSurface && (
              <form
                onSubmit={handleSurfaceSubmit}
                className="mt-4 p-3 bg-slate-50 border border-slate-200 rounded-md space-y-2.5"
              >
                <div className="flex items-center justify-between font-bold text-slate-800">
                  <span>Edit Surface: {selectedSurface.surface}</span>
                  <button
                    type="button"
                    onClick={() => setSelectedSurface(null)}
                    className="text-slate-400 hover:text-slate-600"
                  >
                    Cancel
                  </button>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-[10px] font-bold uppercase text-slate-500 mb-1">
                      Condition
                    </label>
                    <select
                      value={surfaceCondition}
                      onChange={(e) => setSurfaceCondition(e.target.value)}
                      className="w-full bg-white border border-slate-300 rounded px-2 py-1 text-xs"
                    >
                      <option value="HEALTHY">HEALTHY</option>
                      <option value="CARIES">CARIES</option>
                      <option value="FRACTURE">FRACTURE</option>
                      <option value="OBSERVATION">OBSERVATION</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold uppercase text-slate-500 mb-1">
                      Restoration
                    </label>
                    <select
                      value={surfaceTreatment}
                      onChange={(e) => setSurfaceTreatment(e.target.value)}
                      className="w-full bg-white border border-slate-300 rounded px-2 py-1 text-xs"
                    >
                      <option value="NONE">NONE</option>
                      <option value="COMPOSITE">COMPOSITE</option>
                      <option value="AMALGAM">AMALGAM</option>
                      <option value="GLASS_IONOMER">GIC</option>
                      <option value="SEALANT">SEALANT</option>
                    </select>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full py-1.5 bg-teal-600 hover:bg-teal-700 text-white font-semibold rounded text-xs transition-colors disabled:opacity-50"
                >
                  {isSubmitting ? "Saving..." : "Save Surface Changes"}
                </button>
              </form>
            )}
          </div>
        )}

        {/* TAB 2: History Timeline */}
        {activeTab === "history" && (
          <div className="space-y-3">
            <p className="text-slate-500">
              Immutable clinical audit stream. Every diagnosis, surface modification, and treatment synchronization is permanently recorded:
            </p>

            {tooth.history && tooth.history.length > 0 ? (
              <div className="relative pl-5 space-y-3.5 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
                {tooth.history.map((h) => (
                  <div key={h.id} className="relative group">
                    <span className="absolute -left-5 top-1 w-2.5 h-2.5 rounded-full bg-teal-500 ring-4 ring-white" />
                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-bold text-slate-800 font-mono text-[11px]">
                          {h.action}
                        </span>
                        <span className="text-[10px] text-slate-400 flex items-center gap-1 font-mono">
                          <Clock size={10} />
                          {new Date(h.created_at).toLocaleString()}
                        </span>
                      </div>
                      <p className="text-slate-600 mt-0.5">{h.description}</p>
                      {h.affected_surfaces && (
                        <span className="inline-block mt-1 px-1.5 py-0.5 bg-slate-100 text-slate-600 rounded text-[10px] font-mono">
                          Surfaces: {h.affected_surfaces}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-6 text-slate-400">
                <Clock size={24} className="mx-auto mb-1 text-slate-300" />
                No history entries recorded yet.
              </div>
            )}
          </div>
        )}

        {/* TAB 3: Quick Actions */}
        {activeTab === "actions" && (
          <div className="space-y-3">
            <p className="text-slate-500">
              Apply structural changes to tooth #{tooth.tooth_number}. All changes adhere to clinical safety invariants:
            </p>

            <div className="space-y-2">
              <button
                type="button"
                onClick={() => handleStatusSubmit("HEALTHY")}
                disabled={isSubmitting}
                className="w-full flex items-center justify-between p-2.5 bg-emerald-50 hover:bg-emerald-100/80 border border-emerald-200 text-emerald-800 rounded-md font-semibold text-xs transition-colors"
              >
                <span>Reset to Healthy</span>
                <Sparkles size={14} />
              </button>

              <button
                type="button"
                onClick={() => handleStatusSubmit("EXTRACTION")}
                disabled={isSubmitting || tooth.is_extracted}
                className="w-full flex items-center justify-between p-2.5 bg-rose-50 hover:bg-rose-100/80 border border-rose-200 text-rose-800 rounded-md font-semibold text-xs transition-colors disabled:opacity-50"
              >
                <span>Mark as Extracted</span>
                <Activity size={14} />
              </button>

              <button
                type="button"
                onClick={() => handleStatusSubmit("IMPLANT")}
                disabled={isSubmitting || tooth.has_implant}
                className="w-full flex items-center justify-between p-2.5 bg-slate-100 hover:bg-slate-200 border border-slate-300 text-slate-800 rounded-md font-semibold text-xs transition-colors disabled:opacity-50"
              >
                <span>Record Dental Implant</span>
                <Activity size={14} />
              </button>

              <button
                type="button"
                onClick={() => handleStatusSubmit("CROWN")}
                disabled={isSubmitting}
                className="w-full flex items-center justify-between p-2.5 bg-amber-50 hover:bg-amber-100/80 border border-amber-200 text-amber-800 rounded-md font-semibold text-xs transition-colors disabled:opacity-50"
              >
                <span>Place Permanent Crown</span>
                <Activity size={14} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
