"use client";

import React from "react";
import {
  COLOR_STANDARDS,
  Tooth,
  ToothCondition,
  ToothSurfaceEnum,
} from "@/app/patients/[id]/odontogram/types";

export interface ActiveAction {
  category: "CONDITION" | "PROCEDURE";
  code: string;
  label: string;
  color: string;
  procedureType?: string;
}

interface ClinicalToolbarProps {
  selectedTooth: Tooth | null;
  selectedSurfaces: ToothSurfaceEnum[];
  activeAction: ActiveAction | null;
  onSelectAction: (action: ActiveAction | null) => void;
  onToggleSurface: (surface: ToothSurfaceEnum) => void;
  onApplyAction: () => void;
  onClearSelection: () => void;
  isApplying?: boolean;
}

const CONDITIONS: { code: ToothCondition; label: string; color: string }[] = [
  { code: "CARIES", label: "Caries", color: COLOR_STANDARDS.CARIES },
  { code: "FRACTURE", label: "Fracture", color: COLOR_STANDARDS.FRACTURE },
  { code: "OBSERVATION", label: "Observation", color: COLOR_STANDARDS.OBSERVATION },
  { code: "MISSING", label: "Missing", color: COLOR_STANDARDS.MISSING },
];

const PROCEDURES: { code: string; label: string; type: string; color: string }[] = [
  { code: "COMPOSITE", label: "Composite Filling", type: "FILLING", color: COLOR_STANDARDS.FILLING },
  { code: "CROWN", label: "Crown", type: "CROWN", color: COLOR_STANDARDS.CROWN },
  { code: "ROOT_CANAL", label: "Root Canal", type: "ROOT_CANAL", color: COLOR_STANDARDS.ROOT_CANAL },
  { code: "EXTRACTION", label: "Extraction", type: "EXTRACTION", color: COLOR_STANDARDS.EXTRACTION },
  { code: "IMPLANT", label: "Implant", type: "IMPLANT", color: COLOR_STANDARDS.IMPLANT },
  { code: "BRIDGE", label: "Bridge", type: "BRIDGE", color: COLOR_STANDARDS.BRIDGE },
  { code: "SEALANT", label: "Sealant", type: "SEALANT", color: COLOR_STANDARDS.SEALANT },
];

export function ClinicalToolbar({
  selectedTooth,
  selectedSurfaces,
  activeAction,
  onSelectAction,
  onToggleSurface,
  onApplyAction,
  onClearSelection,
  isApplying = false,
}: ClinicalToolbarProps) {
  const isMolarOrPremolar =
    selectedTooth?.tooth_type === "MOLAR" || selectedTooth?.tooth_type === "PREMOLAR";
  const centerSurf: ToothSurfaceEnum = isMolarOrPremolar ? "OCCLUSAL" : "INCISAL";

  const surfacesList: { code: ToothSurfaceEnum; label: string }[] = [
    { code: "MESIAL", label: "M (Mesial)" },
    { code: "OCCLUSAL", label: isMolarOrPremolar ? "O (Occlusal)" : "I (Incisal)" },
    { code: "DISTAL", label: "D (Distal)" },
    { code: "BUCCAL", label: "B (Buccal)" },
    { code: "LINGUAL", label: "L (Lingual)" },
  ];

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-3 shadow-xs flex flex-wrap items-center justify-between gap-3">
      {/* Left: Quick Diagnoses & Procedures */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mr-1">
          Clinical Tools:
        </span>

        {/* Diagnoses */}
        <div className="flex items-center gap-1.5 bg-slate-50 p-1 rounded-md border border-slate-200">
          {CONDITIONS.map((cond) => {
            const isActive =
              activeAction?.category === "CONDITION" && activeAction.code === cond.code;
            return (
              <button
                key={cond.code}
                type="button"
                onClick={() =>
                  onSelectAction(
                    isActive
                      ? null
                      : {
                          category: "CONDITION",
                          code: cond.code,
                          label: cond.label,
                          color: cond.color,
                        }
                  )
                }
                className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-semibold transition-colors ${
                  isActive
                    ? "bg-slate-900 text-white shadow-xs"
                    : "hover:bg-slate-200 text-slate-700"
                }`}
              >
                <span
                  className="w-2.5 h-2.5 rounded-full shrink-0"
                  style={{ backgroundColor: cond.color }}
                />
                {cond.label}
              </button>
            );
          })}
        </div>

        {/* Procedures */}
        <div className="flex items-center gap-1.5 bg-slate-50 p-1 rounded-md border border-slate-200">
          {PROCEDURES.map((proc) => {
            const isActive =
              activeAction?.category === "PROCEDURE" && activeAction.code === proc.code;
            return (
              <button
                key={proc.code}
                type="button"
                onClick={() =>
                  onSelectAction(
                    isActive
                      ? null
                      : {
                          category: "PROCEDURE",
                          code: proc.code,
                          label: proc.label,
                          color: proc.color,
                          procedureType: proc.type,
                        }
                  )
                }
                className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-semibold transition-colors ${
                  isActive
                    ? "bg-teal-700 text-white shadow-xs"
                    : "hover:bg-slate-200 text-slate-700"
                }`}
              >
                <span
                  className="w-2.5 h-2.5 rounded-full shrink-0"
                  style={{ backgroundColor: proc.color }}
                />
                {proc.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Center: Surface Multi-Select Pills (when tooth is selected) */}
      {selectedTooth && (
        <div className="flex items-center gap-1 bg-teal-50/70 p-1 rounded-md border border-teal-200">
          <span className="text-[11px] font-bold text-teal-800 px-1.5">
            Tooth #{selectedTooth.tooth_number} Surfaces:
          </span>
          {surfacesList.map((surf) => {
            const isSelected = selectedSurfaces.includes(
              surf.code === "OCCLUSAL" ? centerSurf : surf.code
            );
            return (
              <button
                key={surf.code}
                type="button"
                onClick={() =>
                  onToggleSurface(surf.code === "OCCLUSAL" ? centerSurf : surf.code)
                }
                className={`px-2 py-0.5 text-xs font-mono font-bold rounded transition-colors ${
                  isSelected
                    ? "bg-teal-700 text-white shadow-xs"
                    : "bg-white text-slate-700 hover:bg-slate-100 border border-slate-200"
                }`}
              >
                {surf.code[0]}
              </button>
            );
          })}
        </div>
      )}

      {/* Right: Apply & Clear Controls */}
      <div className="flex items-center gap-2">
        {activeAction && selectedTooth && (
          <button
            type="button"
            onClick={onApplyAction}
            disabled={isApplying}
            className="inline-flex items-center gap-1 px-3.5 py-1.5 bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold rounded-md shadow-xs transition-colors disabled:opacity-50"
          >
            {isApplying ? "Applying..." : `Apply ${activeAction.label}`}
          </button>
        )}

        {(selectedTooth || activeAction) && (
          <button
            type="button"
            onClick={onClearSelection}
            className="px-2.5 py-1.5 text-xs font-medium text-slate-600 hover:text-slate-900 transition-colors"
          >
            Reset
          </button>
        )}
      </div>
    </div>
  );
}
