"use client";

import React, { useState } from "react";
import {
  COLOR_STANDARDS,
  DentitionType,
  NumberingSystem,
  Tooth,
  ToothSurfaceEnum,
} from "@/app/patients/[id]/odontogram/types";
import { ToothSVG, ToothRenderMode } from "./tooth-svg";
import { ZoomIn, ZoomOut, RotateCcw } from "lucide-react";

interface OdontogramCanvasProps {
  teeth: Tooth[];
  dentitionType: DentitionType;
  numberingSystem: NumberingSystem;
  selectedTooth: Tooth | null;
  selectedSurface?: ToothSurfaceEnum | null;
  onSelectTooth: (tooth: Tooth) => void;
  onSelectSurface?: (surface: ToothSurfaceEnum, tooth: Tooth) => void;
  onChangeDentition: (dentition: DentitionType) => void;
  onChangeNumberingSystem: (system: NumberingSystem) => void;
}

const resolveArchAndQuadrant = (t: Tooth): { arch: string; quadrant: number } => {
  const num = Number.parseInt(t.tooth_number, 10);
  if (!Number.isNaN(num) && num >= 11 && num <= 85) {
    const quad = Math.floor(num / 10);
    if (quad === 1 || quad === 2 || quad === 5 || quad === 6) {
      return { arch: "UPPER", quadrant: quad };
    }
    if (quad === 3 || quad === 4 || quad === 7 || quad === 8) {
      return { arch: "LOWER", quadrant: quad };
    }
  }
  return { arch: t.arch, quadrant: t.quadrant };
};

export function OdontogramCanvas({
  teeth,
  dentitionType,
  numberingSystem,
  selectedTooth,
  selectedSurface,
  onSelectTooth,
  onSelectSurface,
  onChangeDentition,
  onChangeNumberingSystem,
}: OdontogramCanvasProps) {
  const [zoomLevel, setZoomLevel] = useState(1);
  const [renderMode, setRenderMode] = useState<ToothRenderMode>("ANATOMICAL");

  if (!teeth || teeth.length === 0) {
    return (
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg shadow-xs p-12 text-center flex flex-col items-center justify-center min-h-[380px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600 mb-3" />
        <p className="text-sm font-semibold text-slate-700 dark:text-slate-200">Loading Dental Chart...</p>
        <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">Initializing anatomical odontogram teeth mapping.</p>
      </div>
    );
  }

  // Partition teeth into Upper & Lower Arches with FDI standard resolution
  const upperRightTeeth = teeth
    .filter((t) => {
      const { arch, quadrant } = resolveArchAndQuadrant(t);
      return arch === "UPPER" && (quadrant === 1 || quadrant === 5);
    })
    .sort((a, b) => Number.parseInt(b.tooth_number) - Number.parseInt(a.tooth_number)); // 18 down to 11

  const upperLeftTeeth = teeth
    .filter((t) => {
      const { arch, quadrant } = resolveArchAndQuadrant(t);
      return arch === "UPPER" && (quadrant === 2 || quadrant === 6);
    })
    .sort((a, b) => Number.parseInt(a.tooth_number) - Number.parseInt(b.tooth_number)); // 21 up to 28

  const lowerRightTeeth = teeth
    .filter((t) => {
      const { arch, quadrant } = resolveArchAndQuadrant(t);
      return arch === "LOWER" && (quadrant === 4 || quadrant === 8);
    })
    .sort((a, b) => Number.parseInt(b.tooth_number) - Number.parseInt(a.tooth_number)); // 48 down to 41

  const lowerLeftTeeth = teeth
    .filter((t) => {
      const { arch, quadrant } = resolveArchAndQuadrant(t);
      return arch === "LOWER" && (quadrant === 3 || quadrant === 7);
    })
    .sort((a, b) => Number.parseInt(a.tooth_number) - Number.parseInt(b.tooth_number)); // 31 up to 38

  const handleZoomIn = () => setZoomLevel((prev) => Math.min(prev + 0.15, 1.6));
  const handleZoomOut = () => setZoomLevel((prev) => Math.max(prev - 0.15, 0.75));
  const handleResetZoom = () => setZoomLevel(1);

  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg shadow-xs overflow-hidden flex flex-col">
      {/* Top Chart Header & Controls */}
      <div className="p-3.5 border-b border-slate-100 dark:border-slate-800 flex flex-wrap items-center justify-between gap-3 bg-slate-50/50 dark:bg-slate-800/50">
        {/* Dentition Selector */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Dentition:
          </span>
          <div className="flex items-center bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md p-0.5">
            <button
              type="button"
              onClick={() => onChangeDentition("ADULT")}
              className={`px-3 py-1 text-xs font-semibold rounded transition-colors ${
                dentitionType === "ADULT"
                  ? "bg-teal-700 dark:bg-teal-600 text-white shadow-xs"
                  : "text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white"
              }`}
            >
              Adult (32)
            </button>
            <button
              type="button"
              onClick={() => onChangeDentition("PRIMARY")}
              className={`px-3 py-1 text-xs font-semibold rounded transition-colors ${
                dentitionType === "PRIMARY"
                  ? "bg-teal-700 dark:bg-teal-600 text-white shadow-xs"
                  : "text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white"
              }`}
            >
              Pediatric / Primary (20)
            </button>
          </div>
        </div>

        {/* Numbering System Switcher */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Notation:
          </span>
          <div className="flex items-center bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md p-0.5">
            <button
              type="button"
              onClick={() => onChangeNumberingSystem("FDI")}
              className={`px-2.5 py-1 text-xs font-mono font-semibold rounded transition-colors ${
                numberingSystem === "FDI"
                  ? "bg-slate-900 dark:bg-slate-100 dark:text-slate-900 text-white shadow-xs"
                  : "text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white"
              }`}
            >
              FDI
            </button>
            <button
              type="button"
              onClick={() => onChangeNumberingSystem("UNIVERSAL")}
              className={`px-2.5 py-1 text-xs font-mono font-semibold rounded transition-colors ${
                numberingSystem === "UNIVERSAL"
                  ? "bg-slate-900 dark:bg-slate-100 dark:text-slate-900 text-white shadow-xs"
                  : "text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white"
              }`}
            >
              Universal
            </button>
            <button
              type="button"
              onClick={() => onChangeNumberingSystem("PALMER")}
              className={`px-2.5 py-1 text-xs font-mono font-semibold rounded transition-colors ${
                numberingSystem === "PALMER"
                  ? "bg-slate-900 dark:bg-slate-100 dark:text-slate-900 text-white shadow-xs"
                  : "text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white"
              }`}
            >
              Palmer
            </button>
          </div>
        </div>

        {/* Render Style: Real Tooth (Anatomical) vs Schematic */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Style:
          </span>
          <div className="flex items-center bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md p-0.5">
            <button
              type="button"
              onClick={() => setRenderMode("ANATOMICAL")}
              className={`px-2.5 py-1 text-xs font-semibold rounded transition-colors ${
                renderMode === "ANATOMICAL"
                  ? "bg-teal-700 dark:bg-teal-600 text-white shadow-xs"
                  : "text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white"
              }`}
            >
              Real Tooth
            </button>
            <button
              type="button"
              onClick={() => setRenderMode("GEOMETRIC")}
              className={`px-2.5 py-1 text-xs font-semibold rounded transition-colors ${
                renderMode === "GEOMETRIC"
                  ? "bg-teal-700 dark:bg-teal-600 text-white shadow-xs"
                  : "text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white"
              }`}
            >
              Schematic
            </button>
          </div>
        </div>

        {/* Zoom & Reset Controls */}
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={handleZoomOut}
            className="p-1.5 text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 hover:bg-slate-200/60 dark:hover:bg-slate-700/60 rounded transition-colors"
            title="Zoom Out"
          >
            <ZoomOut size={16} />
          </button>
          <span className="text-xs font-mono text-slate-500 dark:text-slate-400 w-10 text-center">
            {Math.round(zoomLevel * 100)}%
          </span>
          <button
            type="button"
            onClick={handleZoomIn}
            className="p-1.5 text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 hover:bg-slate-200/60 dark:hover:bg-slate-700/60 rounded transition-colors"
            title="Zoom In"
          >
            <ZoomIn size={16} />
          </button>
          <button
            type="button"
            onClick={handleResetZoom}
            className="p-1.5 text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 hover:bg-slate-200/60 dark:hover:bg-slate-700/60 rounded transition-colors ml-1"
            title="Reset Zoom"
          >
            <RotateCcw size={15} />
          </button>
        </div>
      </div>

      {/* Chart Canvas Area */}
      <div className="p-6 overflow-x-auto flex justify-center items-center min-h-[380px] bg-slate-50/25 dark:bg-slate-950/40">
        <div
          className="transition-transform duration-150 origin-center flex flex-col items-center gap-6 w-full max-w-4xl min-w-[760px]"
          style={{ transform: `scale(${zoomLevel})` }}
        >
          {/* Orientation Header */}
          <div className="flex items-center justify-between w-full max-w-4xl text-[11px] font-bold tracking-wider text-slate-400 dark:text-slate-500 uppercase px-2">
            <span>Patient Right (Viewer Left)</span>
            <span>Maxillary (Upper) Arch</span>
            <span>Patient Left (Viewer Right)</span>
          </div>

          {/* Upper Arch (Maxillary) */}
          <div className="flex items-center justify-center gap-3 bg-white dark:bg-slate-900/90 p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-xs w-full max-w-4xl min-w-[740px]">
            {/* Upper Right Quadrant */}
            <div className="flex items-center gap-1">
              {upperRightTeeth.map((tooth) => (
                <ToothSVG
                  key={tooth.id}
                  tooth={tooth}
                  numberingSystem={numberingSystem}
                  isSelected={selectedTooth?.id === tooth.id}
                  selectedSurface={selectedTooth?.id === tooth.id ? selectedSurface : null}
                  onSelectTooth={onSelectTooth}
                  onSelectSurface={onSelectSurface}
                  renderMode={renderMode}
                />
              ))}
            </div>

            {/* Midline Divider */}
            <div className="w-0.5 h-20 bg-teal-500/40 relative flex items-center justify-center">
              <span className="absolute -top-3 text-[9px] font-bold text-teal-600 dark:text-teal-400 bg-teal-50 dark:bg-teal-950/80 px-1 rounded border border-teal-200 dark:border-teal-800">
                MIDLINE
              </span>
            </div>

            {/* Upper Left Quadrant */}
            <div className="flex items-center gap-1">
              {upperLeftTeeth.map((tooth) => (
                <ToothSVG
                  key={tooth.id}
                  tooth={tooth}
                  numberingSystem={numberingSystem}
                  isSelected={selectedTooth?.id === tooth.id}
                  selectedSurface={selectedTooth?.id === tooth.id ? selectedSurface : null}
                  onSelectTooth={onSelectTooth}
                  onSelectSurface={onSelectSurface}
                  renderMode={renderMode}
                />
              ))}
            </div>
          </div>

          {/* Arch Midline Horizontal Separator */}
          <div className="flex items-center justify-between w-full max-w-4xl text-[11px] font-bold tracking-wider text-slate-400 dark:text-slate-500 uppercase px-2">
            <span>Facial / Buccal</span>
            <span className="h-px flex-1 bg-slate-200 dark:bg-slate-700 mx-4" />
            <span>Lingual / Palatal</span>
          </div>

          {/* Lower Arch (Mandibular) */}
          <div className="flex items-center justify-center gap-3 bg-white dark:bg-slate-900/90 p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-xs w-full max-w-4xl min-w-[740px]">
            {/* Lower Right Quadrant */}
            <div className="flex items-center gap-1">
              {lowerRightTeeth.map((tooth) => (
                <ToothSVG
                  key={tooth.id}
                  tooth={tooth}
                  numberingSystem={numberingSystem}
                  isSelected={selectedTooth?.id === tooth.id}
                  selectedSurface={selectedTooth?.id === tooth.id ? selectedSurface : null}
                  onSelectTooth={onSelectTooth}
                  onSelectSurface={onSelectSurface}
                  renderMode={renderMode}
                />
              ))}
            </div>

            {/* Midline Divider */}
            <div className="w-0.5 h-20 bg-teal-500/40 relative flex items-center justify-center">
              <span className="absolute -bottom-3 text-[9px] font-bold text-teal-600 dark:text-teal-400 bg-teal-50 dark:bg-teal-950/80 px-1 rounded border border-teal-200 dark:border-teal-800">
                MIDLINE
              </span>
            </div>

            {/* Lower Left Quadrant */}
            <div className="flex items-center gap-1">
              {lowerLeftTeeth.map((tooth) => (
                <ToothSVG
                  key={tooth.id}
                  tooth={tooth}
                  numberingSystem={numberingSystem}
                  isSelected={selectedTooth?.id === tooth.id}
                  selectedSurface={selectedTooth?.id === tooth.id ? selectedSurface : null}
                  onSelectTooth={onSelectTooth}
                  onSelectSurface={onSelectSurface}
                  renderMode={renderMode}
                />
              ))}
            </div>
          </div>

          {/* Mandibular Orientation Footer */}
          <div className="flex items-center justify-between w-full max-w-4xl text-[11px] font-bold tracking-wider text-slate-400 dark:text-slate-500 uppercase px-2">
            <span>Patient Right</span>
            <span>Mandibular (Lower) Arch</span>
            <span>Patient Left</span>
          </div>
        </div>
      </div>

      {/* Clinical Color Legend Footer */}
      <div className="p-3 border-t border-slate-100 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-900 flex flex-wrap items-center justify-center gap-4 text-xs font-semibold text-slate-600 dark:text-slate-300">
        <span className="text-[10px] font-bold uppercase text-slate-400 dark:text-slate-500">Legend:</span>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COLOR_STANDARDS.HEALTHY }} />
          <span>Healthy</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COLOR_STANDARDS.CARIES }} />
          <span>Caries</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COLOR_STANDARDS.FILLING }} />
          <span>Filling / Restored</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COLOR_STANDARDS.ROOT_CANAL }} />
          <span>Root Canal</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COLOR_STANDARDS.CROWN }} />
          <span>Crown</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COLOR_STANDARDS.IMPLANT }} />
          <span>Implant</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COLOR_STANDARDS.EXTRACTION }} />
          <span>Extracted</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: COLOR_STANDARDS.OBSERVATION }} />
          <span>Observation</span>
        </div>
      </div>
    </div>
  );
}
