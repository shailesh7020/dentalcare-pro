"use client";

import React from "react";
import {
  COLOR_STANDARDS,
  NumberingSystem,
  Tooth,
  ToothSurfaceEnum,
  getToothLabel,
} from "@/app/patients/[id]/odontogram/types";

interface ToothSVGProps {
  tooth: Tooth;
  numberingSystem: NumberingSystem;
  isSelected: boolean;
  selectedSurface?: ToothSurfaceEnum | null;
  onSelectTooth: (tooth: Tooth) => void;
  onSelectSurface?: (surface: ToothSurfaceEnum, tooth: Tooth) => void;
}

export function ToothSVG({
  tooth,
  numberingSystem,
  isSelected,
  selectedSurface,
  onSelectTooth,
  onSelectSurface,
}: ToothSVGProps) {
  const isUpper = tooth.arch === "UPPER";
  // Quadrants 1 and 4 have Mesial on the left from anatomical viewer's perspective (facing patient midline)
  const isRightQuadrant = tooth.quadrant === 1 || tooth.quadrant === 4 || tooth.quadrant === 5 || tooth.quadrant === 8;
  const isMolarOrPremolar = tooth.tooth_type === "MOLAR" || tooth.tooth_type === "PREMOLAR";
  const centerSurfaceName: ToothSurfaceEnum = isMolarOrPremolar ? "OCCLUSAL" : "INCISAL";

  const getSurfaceColor = (surfName: ToothSurfaceEnum): string => {
    if (tooth.is_extracted) return "#1E293B";
    if (tooth.is_missing) return "#CBD5E1";
    if (tooth.has_implant) return "#94A3B8";

    const surf = tooth.surfaces.find((s) => s.surface === surfName);
    if (surf && surf.color && surf.condition !== "HEALTHY") {
      return surf.color;
    }
    if (surf && surf.treatment !== "NONE") {
      return COLOR_STANDARDS.FILLING;
    }
    if (tooth.has_crown) return "#F59E0B";
    if (tooth.primary_status !== "HEALTHY" && COLOR_STANDARDS[tooth.primary_status]) {
      return COLOR_STANDARDS[tooth.primary_status];
    }
    return "#FFFFFF";
  };

  const handleSurfaceClick = (e: React.MouseEvent, surf: ToothSurfaceEnum) => {
    e.stopPropagation();
    if (onSelectSurface) {
      onSelectSurface(surf, tooth);
    } else {
      onSelectTooth(tooth);
    }
  };

  const mesialName: ToothSurfaceEnum = "MESIAL";
  const distalName: ToothSurfaceEnum = "DISTAL";
  const buccalName: ToothSurfaceEnum = "BUCCAL";
  const lingualName: ToothSurfaceEnum = "LINGUAL";

  // Surface colors
  const centerColor = getSurfaceColor(centerSurfaceName);
  const buccalColor = getSurfaceColor(buccalName);
  const lingualColor = getSurfaceColor(lingualName);
  const mesialColor = getSurfaceColor(mesialName);
  const distalColor = getSurfaceColor(distalName);

  // Geometry: 52 x 70 crown/root box
  const crownY = isUpper ? 34 : 6;

  return (
    <div
      onClick={() => onSelectTooth(tooth)}
      className={`relative inline-flex flex-col items-center p-1 rounded-md transition-all cursor-pointer select-none group ${
        isSelected
          ? "bg-teal-50 ring-2 ring-teal-600 shadow-xs"
          : "hover:bg-slate-100/70"
      } ${tooth.is_missing ? "opacity-45" : "opacity-100"}`}
      title={`${tooth.name} (FDI: ${tooth.tooth_number}, Univ: ${tooth.universal_number}, Palmer: ${tooth.palmer_notation}) - ${tooth.primary_status}`}
    >
      {/* Top Numbering (Upper Arch) */}
      {isUpper && (
        <span
          className={`text-[11px] font-mono font-bold tracking-tight mb-0.5 ${
            isSelected ? "text-teal-700 font-extrabold" : "text-slate-600"
          }`}
        >
          {getToothLabel(tooth, numberingSystem)}
        </span>
      )}

      {/* SVG Canvas for Tooth */}
      <svg
        viewBox="0 0 54 76"
        className="w-11 h-16 transition-transform group-hover:scale-105"
      >
        <defs>
          {/* Metallic gradient for implants */}
          <linearGradient id={`implant-grad-${tooth.id}`} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#CBD5E1" />
            <stop offset="50%" stopColor="#94A3B8" />
            <stop offset="100%" stopColor="#64748B" />
          </linearGradient>
        </defs>

        {/* Root Schematic */}
        {tooth.has_implant ? (
          /* Titanium screw implant root */
          <g transform={`translate(27, ${isUpper ? 20 : 54})`}>
            <rect x="-4" y="-12" width="8" height="24" rx="2" fill={`url(#implant-grad-${tooth.id})`} stroke="#475569" strokeWidth="1" />
            <line x1="-5" y1="-8" x2="5" y2="-8" stroke="#334155" strokeWidth="1" />
            <line x1="-5" y1="-3" x2="5" y2="-3" stroke="#334155" strokeWidth="1" />
            <line x1="-5" y1="2" x2="5" y2="2" stroke="#334155" strokeWidth="1" />
            <line x1="-5" y1="7" x2="5" y2="7" stroke="#334155" strokeWidth="1" />
          </g>
        ) : (
          /* Natural roots (Single or Multi-root based on tooth type) */
          <g>
            {tooth.tooth_type === "MOLAR" ? (
              /* Two or three roots */
              <g stroke="#94A3B8" strokeWidth="1.5" fill="none">
                <path
                  d={
                    isUpper
                      ? "M 18,34 Q 16,14 20,6 Q 25,18 27,34 Q 29,18 34,6 Q 38,14 36,34"
                      : "M 18,40 Q 16,60 20,68 Q 25,56 27,40 Q 29,56 34,68 Q 38,60 36,40"
                  }
                  fill="#F8FAFC"
                  stroke={tooth.has_root_canal ? "#8B5CF6" : "#94A3B8"}
                  strokeWidth={tooth.has_root_canal ? "2" : "1.2"}
                />
                {tooth.has_root_canal && (
                  /* Gutta-percha canal fill lines */
                  <g stroke="#8B5CF6" strokeWidth="1.5" strokeLinecap="round">
                    <line x1="20" y1={isUpper ? 8 : 66} x2="21" y2={isUpper ? 34 : 40} />
                    <line x1="34" y1={isUpper ? 8 : 66} x2="33" y2={isUpper ? 34 : 40} />
                  </g>
                )}
              </g>
            ) : (
              /* Single root for incisors, canines, premolars */
              <g>
                <path
                  d={
                    isUpper
                      ? "M 20,34 Q 22,14 27,6 Q 32,14 34,34 Z"
                      : "M 20,40 Q 22,60 27,68 Q 32,60 34,40 Z"
                  }
                  fill="#F8FAFC"
                  stroke={tooth.has_root_canal ? "#8B5CF6" : "#94A3B8"}
                  strokeWidth={tooth.has_root_canal ? "2" : "1.2"}
                />
                {tooth.has_root_canal && (
                  <line
                    x1="27"
                    y1={isUpper ? 8 : 66}
                    x2="27"
                    y2={isUpper ? 34 : 40}
                    stroke="#8B5CF6"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                  />
                )}
              </g>
            )}
          </g>
        )}

        {/* Crown Geometry: 5 Interactive Surfaces */}
        <g transform={`translate(9, ${crownY})`}>
          {/* Crown Base Outline / Border */}
          <rect
            x="0"
            y="0"
            width="36"
            height="34"
            rx="5"
            fill="#FFFFFF"
            stroke={tooth.has_crown ? "#F59E0B" : isSelected ? "#0D9488" : "#64748B"}
            strokeWidth={tooth.has_crown || isSelected ? "2" : "1.2"}
          />

          {/* Buccal / Facial Surface (Top Trapezoid for upper, Bottom for lower) */}
          <polygon
            points="0,0 36,0 28,9 8,9"
            fill={buccalColor}
            stroke="#94A3B8"
            strokeWidth="0.8"
            onClick={(e) => handleSurfaceClick(e, buccalName)}
            className={`transition-colors hover:brightness-90 ${
              selectedSurface === buccalName ? "stroke-teal-600 stroke-[1.8]" : ""
            }`}
          />

          {/* Lingual / Palatal Surface (Bottom Trapezoid for upper, Top for lower) */}
          <polygon
            points="0,34 36,34 28,25 8,25"
            fill={lingualColor}
            stroke="#94A3B8"
            strokeWidth="0.8"
            onClick={(e) => handleSurfaceClick(e, lingualName)}
            className={`transition-colors hover:brightness-90 ${
              selectedSurface === lingualName ? "stroke-teal-600 stroke-[1.8]" : ""
            }`}
          />

          {/* Left Lateral Surface (Mesial or Distal based on Quadrant) */}
          <polygon
            points="0,0 8,9 8,25 0,34"
            fill={isRightQuadrant ? mesialColor : distalColor}
            stroke="#94A3B8"
            strokeWidth="0.8"
            onClick={(e) => handleSurfaceClick(e, isRightQuadrant ? mesialName : distalName)}
            className={`transition-colors hover:brightness-90 ${
              selectedSurface === (isRightQuadrant ? mesialName : distalName)
                ? "stroke-teal-600 stroke-[1.8]"
                : ""
            }`}
          />

          {/* Right Lateral Surface (Distal or Mesial based on Quadrant) */}
          <polygon
            points="36,0 28,9 28,25 36,34"
            fill={isRightQuadrant ? distalColor : mesialColor}
            stroke="#94A3B8"
            strokeWidth="0.8"
            onClick={(e) => handleSurfaceClick(e, isRightQuadrant ? distalName : mesialName)}
            className={`transition-colors hover:brightness-90 ${
              selectedSurface === (isRightQuadrant ? distalName : mesialName)
                ? "stroke-teal-600 stroke-[1.8]"
                : ""
            }`}
          />

          {/* Center Surface: Occlusal (Molar/Premolar) or Incisal (Incisor/Canine) */}
          <polygon
            points="8,9 28,9 28,25 8,25"
            fill={centerColor}
            stroke="#94A3B8"
            strokeWidth="0.8"
            onClick={(e) => handleSurfaceClick(e, centerSurfaceName)}
            className={`transition-colors hover:brightness-90 ${
              selectedSurface === centerSurfaceName ? "stroke-teal-600 stroke-[1.8]" : ""
            }`}
          />

          {/* Gold Crown Indicator */}
          {tooth.has_crown && (
            <path
              d="M 1,3 L 7,1 L 18,4 L 29,1 L 35,3"
              stroke="#D97706"
              strokeWidth="2"
              fill="none"
              strokeLinecap="round"
            />
          )}

          {/* Bridge Abutment Indicator */}
          {tooth.has_bridge && (
            <rect
              x="-2"
              y="14"
              width="40"
              height="6"
              rx="1.5"
              fill="#854D0E"
              opacity="0.85"
            />
          )}

          {/* Extracted Diagonal Cross (X) */}
          {tooth.is_extracted && (
            <g stroke="#EF4444" strokeWidth="2.5" strokeLinecap="round">
              <line x1="2" y1="2" x2="34" y2="32" />
              <line x1="34" y1="2" x2="2" y2="32" />
            </g>
          )}

          {/* Missing Tooth Dashed Overlay */}
          {tooth.is_missing && !tooth.has_implant && (
            <line
              x1="0"
              y1="17"
              x2="36"
              y2="17"
              stroke="#94A3B8"
              strokeWidth="1.5"
              strokeDasharray="3,3"
            />
          )}
        </g>
      </svg>

      {/* Bottom Numbering (Lower Arch) */}
      {!isUpper && (
        <span
          className={`text-[11px] font-mono font-bold tracking-tight mt-0.5 ${
            isSelected ? "text-teal-700 font-extrabold" : "text-slate-600"
          }`}
        >
          {getToothLabel(tooth, numberingSystem)}
        </span>
      )}

      {/* Mobility Badge */}
      {tooth.mobility_grade > 0 && (
        <span className="absolute -top-1 -right-1 px-1 py-0.2 bg-amber-500 text-white rounded text-[8px] font-bold">
          M{tooth.mobility_grade}
        </span>
      )}
    </div>
  );
}
