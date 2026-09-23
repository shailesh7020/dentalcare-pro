"use client";

import React from "react";
import {
  COLOR_STANDARDS,
  NumberingSystem,
  Tooth,
  ToothSurfaceEnum,
  getToothLabel,
} from "@/app/patients/[id]/odontogram/types";

export type ToothRenderMode = "ANATOMICAL" | "GEOMETRIC";

interface ToothSVGProps {
  tooth: Tooth;
  numberingSystem: NumberingSystem;
  isSelected: boolean;
  selectedSurface?: ToothSurfaceEnum | null;
  onSelectTooth: (tooth: Tooth) => void;
  onSelectSurface?: (surface: ToothSurfaceEnum, tooth: Tooth) => void;
  renderMode?: ToothRenderMode;
}

// Canonical resolution of tooth type
export const getEffectiveToothType = (tooth: Tooth): "MOLAR" | "PREMOLAR" | "CANINE" | "INCISOR" => {
  if (tooth.tooth_type) {
    const t = tooth.tooth_type.toUpperCase();
    if (t === "MOLAR" || t === "PREMOLAR" || t === "CANINE" || t === "INCISOR") return t as any;
  }
  const num = Number.parseInt(tooth.tooth_number, 10);
  if (!Number.isNaN(num)) {
    const lastDigit = num % 10;
    if (lastDigit === 1 || lastDigit === 2) return "INCISOR";
    if (lastDigit === 3) return "CANINE";
    if (lastDigit === 4 || lastDigit === 5) {
      if (num >= 50) return "MOLAR"; // Primary deciduous 4 & 5 are molars
      return "PREMOLAR";
    }
    if (lastDigit >= 6) return "MOLAR";
  }
  return "MOLAR";
};

export function ToothSVG({
  tooth,
  numberingSystem,
  isSelected,
  selectedSurface,
  onSelectTooth,
  onSelectSurface,
  renderMode = "ANATOMICAL",
}: ToothSVGProps) {
  const isUpper = tooth.arch === "UPPER";
  const isRightQuadrant =
    tooth.quadrant === 1 || tooth.quadrant === 4 || tooth.quadrant === 5 || tooth.quadrant === 8;
  const toothType = getEffectiveToothType(tooth);
  const isMolarOrPremolar = toothType === "MOLAR" || toothType === "PREMOLAR";
  const centerSurfaceName: ToothSurfaceEnum = isMolarOrPremolar ? "OCCLUSAL" : "INCISAL";

  const getSurfaceColor = (surfName: ToothSurfaceEnum): string => {
    if (tooth.is_extracted) return "#1E293B";
    if (tooth.is_missing) return "#CBD5E1";
    if (tooth.has_implant) return "#94A3B8";

    const surf = tooth.surfaces?.find((s) => s.surface === surfName);
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

  const centerColor = getSurfaceColor(centerSurfaceName);
  const buccalColor = getSurfaceColor(buccalName);
  const lingualColor = getSurfaceColor(lingualName);
  const mesialColor = getSurfaceColor(mesialName);
  const distalColor = getSurfaceColor(distalName);

  // In Viewer Left (Quads 1,4,5,8) midline is on the right -> Left is Distal, Right is Mesial.
  // In Viewer Right (Quads 2,3,6,7) midline is on the left -> Left is Mesial, Right is Distal.
  const leftSurfaceName = isRightQuadrant ? distalName : mesialName;
  const rightSurfaceName = isRightQuadrant ? mesialName : distalName;
  const leftColor = isRightQuadrant ? distalColor : mesialColor;
  const rightColor = isRightQuadrant ? mesialColor : distalColor;

  const toothLabel = getToothLabel(tooth, numberingSystem);

  return (
    <div
      onClick={() => onSelectTooth(tooth)}
      className={`relative inline-flex flex-col items-center p-1 rounded-lg transition-all cursor-pointer select-none group ${
        isSelected
          ? "bg-teal-50 dark:bg-teal-950/50 ring-2 ring-teal-500 shadow-sm"
          : "hover:bg-slate-100/70 dark:hover:bg-slate-800/70"
      } ${tooth.is_missing ? "opacity-45" : "opacity-100"}`}
      title={`${tooth.name} (${toothType}, FDI: ${tooth.tooth_number}, Univ: ${tooth.universal_number}) - ${tooth.primary_status}`}
    >
      {/* Top Numbering (Upper Arch) */}
      {isUpper && (
        <span
          className={`text-[11px] font-mono font-bold tracking-tight mb-1 ${
            isSelected ? "text-teal-700 dark:text-teal-400 font-extrabold" : "text-slate-600 dark:text-slate-400"
          }`}
        >
          {toothLabel}
        </span>
      )}

      {/* SVG Canvas */}
      <svg
        viewBox="0 0 54 82"
        className="w-11 h-18 sm:w-12 sm:h-20 transition-transform group-hover:scale-105"
      >
        <defs>
          {/* Subtle Enamel Shading */}
          <linearGradient id={`enamel-grad-${tooth.id}`} x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#FFFFFF" />
            <stop offset="60%" stopColor="#F8FAFC" />
            <stop offset="100%" stopColor="#EDF2F7" />
          </linearGradient>

          {/* Root Shading */}
          <linearGradient id={`root-grad-${tooth.id}`} x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#F8FAFC" />
            <stop offset="50%" stopColor="#E2E8F0" />
            <stop offset="100%" stopColor="#CBD5E1" />
          </linearGradient>

          {/* Titanium Implant Gradient */}
          <linearGradient id={`implant-grad-${tooth.id}`} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#E2E8F0" />
            <stop offset="30%" stopColor="#94A3B8" />
            <stop offset="70%" stopColor="#64748B" />
            <stop offset="100%" stopColor="#475569" />
          </linearGradient>

          {/* Gold / Ceramic Crown Gradient */}
          <linearGradient id={`crown-grad-${tooth.id}`} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#FDE68A" />
            <stop offset="50%" stopColor="#F59E0B" />
            <stop offset="100%" stopColor="#D97706" />
          </linearGradient>
        </defs>

        {/* ========================================================================= */}
        {/* MODE A: REAL ANATOMICAL TOOTH SHAPES                                     */}
        {/* ========================================================================= */}
        {renderMode === "ANATOMICAL" ? (
          <g>
            {/* 1. ANATOMICAL ROOT(S) OR TITANIUM IMPLANT */}
            {tooth.has_implant ? (
              /* Titanium Implant Fixture */
              <g>
                {isUpper ? (
                  /* Upper implant screw pointing UP into maxilla */
                  <g>
                    <path
                      d="M 22,36 L 23,12 C 24,9 30,9 31,12 L 32,36 Z"
                      fill={`url(#implant-grad-${tooth.id})`}
                      stroke="#334155"
                      strokeWidth="1"
                    />
                    {/* Thread Ridges */}
                    {[14, 18, 22, 26, 30, 34].map((y) => (
                      <line key={y} x1="21" y1={y} x2="33" y2={y} stroke="#1E293B" strokeWidth="1.2" />
                    ))}
                    <rect x="20" y="34" width="14" height="3" rx="1" fill="#475569" stroke="#1E293B" strokeWidth="0.8" />
                  </g>
                ) : (
                  /* Lower implant screw pointing DOWN into mandible */
                  <g>
                    <path
                      d="M 22,46 L 23,70 C 24,73 30,73 31,70 L 32,46 Z"
                      fill={`url(#implant-grad-${tooth.id})`}
                      stroke="#334155"
                      strokeWidth="1"
                    />
                    {/* Thread Ridges */}
                    {[48, 52, 56, 60, 64, 68].map((y) => (
                      <line key={y} x1="21" y1={y} x2="33" y2={y} stroke="#1E293B" strokeWidth="1.2" />
                    ))}
                    <rect x="20" y="45" width="14" height="3" rx="1" fill="#475569" stroke="#1E293B" strokeWidth="0.8" />
                  </g>
                )}
              </g>
            ) : (
              /* Biological Roots customized by tooth type */
              <g>
                {isUpper ? (
                  /* UPPER ARCH ROOTS (Pointing Up towards Maxilla) */
                  <g>
                    {toothType === "MOLAR" && (
                      /* Trifurcated Upper Molar (3 roots: Palatal in back, Mesiobuccal & Distobuccal) */
                      <g>
                        {/* Palatal Root (Center/Lingual, reaches highest apex) */}
                        <path
                          d="M 23,36 C 24,20 25,8 27,3 C 29,8 30,20 31,36 Z"
                          fill="#F1F5F9"
                          stroke={tooth.has_root_canal ? "#8B5CF6" : "#94A3B8"}
                          strokeWidth={tooth.has_root_canal ? "1.8" : "1.2"}
                        />
                        {/* Mesiobuccal Root (Left) */}
                        <path
                          d="M 14,36 C 12,24 11,12 16,6 C 19,6 21,17 22,36 Z"
                          fill="#F8FAFC"
                          stroke={tooth.has_root_canal ? "#8B5CF6" : "#94A3B8"}
                          strokeWidth={tooth.has_root_canal ? "1.8" : "1.2"}
                        />
                        {/* Distobuccal Root (Right) */}
                        <path
                          d="M 32,36 C 33,17 35,6 38,6 C 43,12 42,24 40,36 Z"
                          fill="#F8FAFC"
                          stroke={tooth.has_root_canal ? "#8B5CF6" : "#94A3B8"}
                          strokeWidth={tooth.has_root_canal ? "1.8" : "1.2"}
                        />
                        {/* Endodontic Gutta-Percha Canal Obturation */}
                        {tooth.has_root_canal && (
                          <g stroke="#8B5CF6" strokeWidth="1.6" strokeLinecap="round" fill="none">
                            <path d="M 16,8 Q 18,22 22,36" />
                            <line x1="27" y1="5" x2="27" y2="36" />
                            <path d="M 38,8 Q 36,22 32,36" />
                          </g>
                        )}
                      </g>
                    )}

                    {toothType === "PREMOLAR" && (
                      /* Bifurcated / Grooved Upper Premolar Root */
                      <g>
                        <path
                          d="M 19,36 C 17,24 18,12 22,6 C 25,6 26,16 27,24 C 28,16 29,6 32,6 C 36,12 37,24 35,36 Z"
                          fill="#F8FAFC"
                          stroke={tooth.has_root_canal ? "#8B5CF6" : "#94A3B8"}
                          strokeWidth={tooth.has_root_canal ? "1.8" : "1.2"}
                        />
                        {tooth.has_root_canal && (
                          <g stroke="#8B5CF6" strokeWidth="1.6" strokeLinecap="round" fill="none">
                            <path d="M 22,8 Q 24,20 26,36" />
                            <path d="M 32,8 Q 30,20 28,36" />
                          </g>
                        )}
                      </g>
                    )}

                    {toothType === "CANINE" && (
                      /* Sturdy, Prominent Single Root (Longest in mouth) */
                      <g>
                        <path
                          d="M 20,36 C 19,20 22,7 27,3 C 32,7 35,20 34,36 Z"
                          fill="#F8FAFC"
                          stroke={tooth.has_root_canal ? "#8B5CF6" : "#94A3B8"}
                          strokeWidth={tooth.has_root_canal ? "1.8" : "1.2"}
                        />
                        {tooth.has_root_canal && (
                          <line x1="27" y1="5" x2="27" y2="36" stroke="#8B5CF6" strokeWidth="1.8" strokeLinecap="round" />
                        )}
                      </g>
                    )}

                    {toothType === "INCISOR" && (
                      /* Elegant Conical Incisor Root */
                      <g>
                        <path
                          d="M 21,36 C 20,22 22,11 27,5 C 32,11 34,22 33,36 Z"
                          fill="#F8FAFC"
                          stroke={tooth.has_root_canal ? "#8B5CF6" : "#94A3B8"}
                          strokeWidth={tooth.has_root_canal ? "1.8" : "1.2"}
                        />
                        {tooth.has_root_canal && (
                          <line x1="27" y1="6" x2="27" y2="36" stroke="#8B5CF6" strokeWidth="1.8" strokeLinecap="round" />
                        )}
                      </g>
                    )}
                  </g>
                ) : (
                  /* LOWER ARCH ROOTS (Pointing Down towards Mandible) */
                  <g>
                    {toothType === "MOLAR" && (
                      /* Bifurcated Lower Molar (Mesial & Distal curved roots) */
                      <g>
                        {/* Mesial Root (Left) */}
                        <path
                          d="M 14,46 C 12,58 12,72 17,78 C 21,78 23,66 25,46 Z"
                          fill="#F8FAFC"
                          stroke={tooth.has_root_canal ? "#8B5CF6" : "#94A3B8"}
                          strokeWidth={tooth.has_root_canal ? "1.8" : "1.2"}
                        />
                        {/* Furcation Arch between roots */}
                        <path d="M 25,46 C 26,53 28,53 29,46 Z" fill="#E2E8F0" />
                        {/* Distal Root (Right) */}
                        <path
                          d="M 29,46 C 31,66 33,78 37,78 C 42,72 42,58 40,46 Z"
                          fill="#F8FAFC"
                          stroke={tooth.has_root_canal ? "#8B5CF6" : "#94A3B8"}
                          strokeWidth={tooth.has_root_canal ? "1.8" : "1.2"}
                        />
                        {/* Endodontic Gutta-Percha Canal Obturation */}
                        {tooth.has_root_canal && (
                          <g stroke="#8B5CF6" strokeWidth="1.6" strokeLinecap="round" fill="none">
                            <path d="M 20,46 Q 16,62 17,76" />
                            <path d="M 34,46 Q 37,62 37,76" />
                          </g>
                        )}
                      </g>
                    )}

                    {toothType === "PREMOLAR" && (
                      /* Lower Premolar Stout Conical Root */
                      <g>
                        <path
                          d="M 20,46 C 19,58 21,72 27,78 C 33,72 35,58 34,46 Z"
                          fill="#F8FAFC"
                          stroke={tooth.has_root_canal ? "#8B5CF6" : "#94A3B8"}
                          strokeWidth={tooth.has_root_canal ? "1.8" : "1.2"}
                        />
                        {tooth.has_root_canal && (
                          <line x1="27" y1="46" x2="27" y2="76" stroke="#8B5CF6" strokeWidth="1.8" strokeLinecap="round" />
                        )}
                      </g>
                    )}

                    {toothType === "CANINE" && (
                      /* Lower Canine Long Conical Root */
                      <g>
                        <path
                          d="M 20,46 C 19,62 22,75 27,79 C 32,75 35,62 34,46 Z"
                          fill="#F8FAFC"
                          stroke={tooth.has_root_canal ? "#8B5CF6" : "#94A3B8"}
                          strokeWidth={tooth.has_root_canal ? "1.8" : "1.2"}
                        />
                        {tooth.has_root_canal && (
                          <line x1="27" y1="46" x2="27" y2="77" stroke="#8B5CF6" strokeWidth="1.8" strokeLinecap="round" />
                        )}
                      </g>
                    )}

                    {toothType === "INCISOR" && (
                      /* Slender Lower Incisor Root */
                      <g>
                        <path
                          d="M 21,46 C 20,58 22,70 27,77 C 32,70 34,58 33,46 Z"
                          fill="#F8FAFC"
                          stroke={tooth.has_root_canal ? "#8B5CF6" : "#94A3B8"}
                          strokeWidth={tooth.has_root_canal ? "1.8" : "1.2"}
                        />
                        {tooth.has_root_canal && (
                          <line x1="27" y1="46" x2="27" y2="75" stroke="#8B5CF6" strokeWidth="1.8" strokeLinecap="round" />
                        )}
                      </g>
                    )}
                  </g>
                )}
              </g>
            )}

            {/* 2. ANATOMICAL CROWN AND INTERACTIVE SURFACES */}
            {isUpper ? (
              /* UPPER ARCH CROWN (Y=36 to Y=74) */
              <g>
                {toothType === "MOLAR" && (
                  /* Upper Molar Crown: Broad multi-cusped chewing table */
                  <g>
                    {/* Crown Base Outline */}
                    <path
                      d="M 8,36 C 5,44 5,58 7,68 C 11,73 19,74 27,72 C 35,74 43,73 47,68 C 49,58 49,44 46,36 C 38,38 16,38 8,36 Z"
                      fill="#FFFFFF"
                      stroke={tooth.has_crown ? "#F59E0B" : isSelected ? "#0D9488" : "#64748B"}
                      strokeWidth={tooth.has_crown || isSelected ? "2" : "1.2"}
                    />
                    {/* Buccal Surface (Top) */}
                    <path
                      d="M 8,36 C 16,38 38,38 46,36 C 43,42 39,44 36,44 C 31,43 23,43 18,44 C 15,42 11,42 8,36 Z"
                      fill={buccalColor}
                      stroke="#94A3B8"
                      strokeWidth="0.8"
                      onClick={(e) => handleSurfaceClick(e, buccalName)}
                      className={`transition-colors hover:brightness-90 ${
                        selectedSurface === buccalName ? "stroke-teal-600 stroke-[2]" : ""
                      }`}
                    />
                    {/* Lingual Surface (Bottom) */}
                    <path
                      d="M 18,64 C 23,65 31,65 36,64 C 39,66 43,67 47,68 C 43,73 35,74 27,72 C 19,74 11,73 7,68 C 11,67 15,66 18,64 Z"
                      fill={lingualColor}
                      stroke="#94A3B8"
                      strokeWidth="0.8"
                      onClick={(e) => handleSurfaceClick(e, lingualName)}
                      className={`transition-colors hover:brightness-90 ${
                        selectedSurface === lingualName ? "stroke-teal-600 stroke-[2]" : ""
                      }`}
                    />
                    {/* Left Surface (Mesial or Distal) */}
                    <path
                      d="M 8,36 C 11,42 15,42 18,44 C 17,53 17,59 18,64 C 15,66 11,67 7,68 C 5,58 5,44 8,36 Z"
                      fill={leftColor}
                      stroke="#94A3B8"
                      strokeWidth="0.8"
                      onClick={(e) => handleSurfaceClick(e, leftSurfaceName)}
                      className={`transition-colors hover:brightness-90 ${
                        selectedSurface === leftSurfaceName ? "stroke-teal-600 stroke-[2]" : ""
                      }`}
                    />
                    {/* Right Surface (Distal or Mesial) */}
                    <path
                      d="M 46,36 C 43,42 39,44 36,44 C 37,53 37,59 36,64 C 39,66 43,67 47,68 C 49,58 49,44 46,36 Z"
                      fill={rightColor}
                      stroke="#94A3B8"
                      strokeWidth="0.8"
                      onClick={(e) => handleSurfaceClick(e, rightSurfaceName)}
                      className={`transition-colors hover:brightness-90 ${
                        selectedSurface === rightSurfaceName ? "stroke-teal-600 stroke-[2]" : ""
                      }`}
                    />
                    {/* Center Occlusal Table (with anatomical developmental fissure cross) */}
                    <path
                      d="M 18,48 C 18,44 23,43 27,44 C 31,43 36,44 36,48 C 37,53 37,59 36,64 C 31,65 23,65 18,64 C 17,59 17,53 18,48 Z"
                      fill={centerColor}
                      stroke="#94A3B8"
                      strokeWidth="0.8"
                      onClick={(e) => handleSurfaceClick(e, centerSurfaceName)}
                      className={`transition-colors hover:brightness-90 ${
                        selectedSurface === centerSurfaceName ? "stroke-teal-600 stroke-[2]" : ""
                      }`}
                    />
                    <line x1="20" y1="56" x2="34" y2="56" stroke="#94A3B8" strokeWidth="0.8" opacity="0.6" pointerEvents="none" />
                    <line x1="27" y1="46" x2="27" y2="62" stroke="#94A3B8" strokeWidth="0.8" opacity="0.6" pointerEvents="none" />
                  </g>
                )}

                {toothType === "PREMOLAR" && (
                  /* Upper Premolar Crown: Rounded Bicuspid Table */
                  <g>
                    <path
                      d="M 11,36 C 9,43 9,57 11,67 C 15,72 22,73 27,72 C 32,73 39,72 43,67 C 45,57 45,43 43,36 C 37,37 17,37 11,36 Z"
                      fill="#FFFFFF"
                      stroke={tooth.has_crown ? "#F59E0B" : isSelected ? "#0D9488" : "#64748B"}
                      strokeWidth={tooth.has_crown || isSelected ? "2" : "1.2"}
                    />
                    <path
                      d="M 11,36 C 17,37 37,37 43,36 C 41,42 38,45 35,48 C 31,45 23,45 19,48 C 16,45 13,42 11,36 Z"
                      fill={buccalColor}
                      stroke="#94A3B8"
                      strokeWidth="0.8"
                      onClick={(e) => handleSurfaceClick(e, buccalName)}
                      className={`transition-colors hover:brightness-90 ${selectedSurface === buccalName ? "stroke-teal-600 stroke-[2]" : ""}`}
                    />
                    <path
                      d="M 19,64 C 23,66 31,66 35,64 C 38,66 41,66 43,67 C 39,72 32,73 27,72 C 22,73 15,72 11,67 C 13,66 16,66 19,64 Z"
                      fill={lingualColor}
                      stroke="#94A3B8"
                      strokeWidth="0.8"
                      onClick={(e) => handleSurfaceClick(e, lingualName)}
                      className={`transition-colors hover:brightness-90 ${selectedSurface === lingualName ? "stroke-teal-600 stroke-[2]" : ""}`}
                    />
                    <path
                      d="M 11,36 C 13,42 16,45 19,48 C 18,54 18,60 19,64 C 16,66 13,66 11,67 C 9,57 9,43 11,36 Z"
                      fill={leftColor}
                      stroke="#94A3B8"
                      strokeWidth="0.8"
                      onClick={(e) => handleSurfaceClick(e, leftSurfaceName)}
                      className={`transition-colors hover:brightness-90 ${selectedSurface === leftSurfaceName ? "stroke-teal-600 stroke-[2]" : ""}`}
                    />
                    <path
                      d="M 43,36 C 41,42 38,45 35,48 C 36,54 36,60 35,64 C 38,66 41,66 43,67 C 45,57 45,43 43,36 Z"
                      fill={rightColor}
                      stroke="#94A3B8"
                      strokeWidth="0.8"
                      onClick={(e) => handleSurfaceClick(e, rightSurfaceName)}
                      className={`transition-colors hover:brightness-90 ${selectedSurface === rightSurfaceName ? "stroke-teal-600 stroke-[2]" : ""}`}
                    />
                    {/* Oval Bicuspid Occlusal Table */}
                    <path
                      d="M 19,48 C 23,45 31,45 35,48 C 36,54 36,60 35,64 C 31,66 23,66 19,64 C 18,60 18,54 19,48 Z"
                      fill={centerColor}
                      stroke="#94A3B8"
                      strokeWidth="0.8"
                      onClick={(e) => handleSurfaceClick(e, centerSurfaceName)}
                      className={`transition-colors hover:brightness-90 ${selectedSurface === centerSurfaceName ? "stroke-teal-600 stroke-[2]" : ""}`}
                    />
                    <line x1="22" y1="56" x2="32" y2="56" stroke="#94A3B8" strokeWidth="0.8" opacity="0.6" pointerEvents="none" />
                  </g>
                )}

                {toothType === "CANINE" && (
                  /* Upper Canine Crown: Pointed Spearhead Cusp Profile */
                  <g>
                    <path
                      d="M 12,36 C 10,44 10,56 13,64 L 27,73 L 41,64 C 44,56 44,44 42,36 C 36,37 18,37 12,36 Z"
                      fill="#FFFFFF"
                      stroke={tooth.has_crown ? "#F59E0B" : isSelected ? "#0D9488" : "#64748B"}
                      strokeWidth={tooth.has_crown || isSelected ? "2" : "1.2"}
                    />
                    <path
                      d="M 12,36 C 18,37 36,37 42,36 C 40,42 37,47 34,53 L 27,61 L 20,53 C 17,47 14,42 12,36 Z"
                      fill={buccalColor}
                      stroke="#94A3B8"
                      strokeWidth="0.8"
                      onClick={(e) => handleSurfaceClick(e, buccalName)}
                      className={`transition-colors hover:brightness-90 ${selectedSurface === buccalName ? "stroke-teal-600 stroke-[2]" : ""}`}
                    />
                    <path
                      d="M 20,59 L 27,69 L 34,59 L 41,64 L 27,73 L 13,64 Z"
                      fill={lingualColor}
                      stroke="#94A3B8"
                      strokeWidth="0.8"
                      onClick={(e) => handleSurfaceClick(e, lingualName)}
                      className={`transition-colors hover:brightness-90 ${selectedSurface === lingualName ? "stroke-teal-600 stroke-[2]" : ""}`}
                    />
                    <path
                      d="M 12,36 C 14,42 17,47 20,53 L 20,59 L 13,64 C 10,56 10,44 12,36 Z"
                      fill={leftColor}
                      stroke="#94A3B8"
                      strokeWidth="0.8"
                      onClick={(e) => handleSurfaceClick(e, leftSurfaceName)}
                      className={`transition-colors hover:brightness-90 ${selectedSurface === leftSurfaceName ? "stroke-teal-600 stroke-[2]" : ""}`}
                    />
                    <path
                      d="M 42,36 C 40,42 37,47 34,53 L 34,59 L 41,64 C 44,56 44,44 42,36 Z"
                      fill={rightColor}
                      stroke="#94A3B8"
                      strokeWidth="0.8"
                      onClick={(e) => handleSurfaceClick(e, rightSurfaceName)}
                      className={`transition-colors hover:brightness-90 ${selectedSurface === rightSurfaceName ? "stroke-teal-600 stroke-[2]" : ""}`}
                    />
                    {/* Pointed Incisal Cusp Ridge Chevron */}
                    <polygon
                      points="20,53 27,61 34,53 34,59 27,69 20,59"
                      fill={centerColor}
                      stroke="#94A3B8"
                      strokeWidth="0.8"
                      onClick={(e) => handleSurfaceClick(e, centerSurfaceName)}
                      className={`transition-colors hover:brightness-90 ${selectedSurface === centerSurfaceName ? "stroke-teal-600 stroke-[2]" : ""}`}
                    />
                  </g>
                )}

                {toothType === "INCISOR" && (
                  /* Upper Incisor Crown: Flared Chisel Cutting Edge */
                  <g>
                    <path
                      d="M 14,36 C 12,44 10,58 9,70 C 18,72 36,72 45,70 C 44,58 42,44 40,36 C 34,37 20,37 14,36 Z"
                      fill="#FFFFFF"
                      stroke={tooth.has_crown ? "#F59E0B" : isSelected ? "#0D9488" : "#64748B"}
                      strokeWidth={tooth.has_crown || isSelected ? "2" : "1.2"}
                    />
                    <path
                      d="M 14,36 C 20,37 34,37 40,36 C 39,44 38,54 36,60 C 31,61 23,61 18,60 C 16,54 15,44 14,36 Z"
                      fill={buccalColor}
                      stroke="#94A3B8"
                      strokeWidth="0.8"
                      onClick={(e) => handleSurfaceClick(e, buccalName)}
                      className={`transition-colors hover:brightness-90 ${selectedSurface === buccalName ? "stroke-teal-600 stroke-[2]" : ""}`}
                    />
                    <path
                      d="M 18,60 C 23,61 31,61 36,60 L 43,63 C 36,64 18,64 11,63 Z"
                      fill={lingualColor}
                      stroke="#94A3B8"
                      strokeWidth="0.8"
                      onClick={(e) => handleSurfaceClick(e, lingualName)}
                      className={`transition-colors hover:brightness-90 ${selectedSurface === lingualName ? "stroke-teal-600 stroke-[2]" : ""}`}
                    />
                    <path
                      d="M 14,36 C 15,44 16,54 18,60 L 11,63 L 9,70 C 10,58 12,44 14,36 Z"
                      fill={leftColor}
                      stroke="#94A3B8"
                      strokeWidth="0.8"
                      onClick={(e) => handleSurfaceClick(e, leftSurfaceName)}
                      className={`transition-colors hover:brightness-90 ${selectedSurface === leftSurfaceName ? "stroke-teal-600 stroke-[2]" : ""}`}
                    />
                    <path
                      d="M 40,36 C 39,44 38,54 36,60 L 43,63 L 45,70 C 44,58 42,44 40,36 Z"
                      fill={rightColor}
                      stroke="#94A3B8"
                      strokeWidth="0.8"
                      onClick={(e) => handleSurfaceClick(e, rightSurfaceName)}
                      className={`transition-colors hover:brightness-90 ${selectedSurface === rightSurfaceName ? "stroke-teal-600 stroke-[2]" : ""}`}
                    />
                    {/* Incisal Cutting Ribbon Edge */}
                    <path
                      d="M 11,63 C 18,64 36,64 43,63 L 45,70 C 36,72 18,72 9,70 Z"
                      fill={centerColor}
                      stroke="#94A3B8"
                      strokeWidth="0.8"
                      onClick={(e) => handleSurfaceClick(e, centerSurfaceName)}
                      className={`transition-colors hover:brightness-90 ${selectedSurface === centerSurfaceName ? "stroke-teal-600 stroke-[2]" : ""}`}
                    />
                  </g>
                )}
              </g>
            ) : (
              /* LOWER ARCH CROWN (Y=8 to Y=46) */
              <g>
                {toothType === "MOLAR" && (
                  /* Lower Molar Crown: Broad Multi-Cusp Chewing Table */
                  <g>
                    <path
                      d="M 7,14 C 11,9 19,8 27,10 C 35,8 43,9 47,14 C 49,24 49,38 46,46 C 38,44 16,44 8,46 C 5,38 5,24 7,14 Z"
                      fill="#FFFFFF"
                      stroke={tooth.has_crown ? "#F59E0B" : isSelected ? "#0D9488" : "#64748B"}
                      strokeWidth={tooth.has_crown || isSelected ? "2" : "1.2"}
                    />
                    {/* Lingual (Top) */}
                    <path
                      d="M 7,14 C 11,9 19,8 27,10 C 35,8 43,9 47,14 C 43,16 39,17 36,18 C 31,17 23,17 18,18 C 15,17 11,16 7,14 Z"
                      fill={lingualColor}
                      stroke="#94A3B8"
                      strokeWidth="0.8"
                      onClick={(e) => handleSurfaceClick(e, lingualName)}
                      className={`transition-colors hover:brightness-90 ${selectedSurface === lingualName ? "stroke-teal-600 stroke-[2]" : ""}`}
                    />
                    {/* Buccal (Bottom) */}
                    <path
                      d="M 18,34 C 23,35 31,35 36,34 C 39,36 43,40 46,46 C 38,44 16,44 8,46 C 11,40 15,36 18,34 Z"
                      fill={buccalColor}
                      stroke="#94A3B8"
                      strokeWidth="0.8"
                      onClick={(e) => handleSurfaceClick(e, buccalName)}
                      className={`transition-colors hover:brightness-90 ${selectedSurface === buccalName ? "stroke-teal-600 stroke-[2]" : ""}`}
                    />
                    {/* Left Surface */}
                    <path
                      d="M 7,14 C 11,16 15,17 18,18 C 17,23 17,29 18,34 C 15,36 11,40 8,46 C 5,38 5,24 7,14 Z"
                      fill={leftColor}
                      stroke="#94A3B8"
                      strokeWidth="0.8"
                      onClick={(e) => handleSurfaceClick(e, leftSurfaceName)}
                      className={`transition-colors hover:brightness-90 ${selectedSurface === leftSurfaceName ? "stroke-teal-600 stroke-[2]" : ""}`}
                    />
                    {/* Right Surface */}
                    <path
                      d="M 47,14 C 43,16 39,17 36,18 C 37,23 37,29 36,34 C 39,36 43,40 46,46 C 49,38 49,24 47,14 Z"
                      fill={rightColor}
                      stroke="#94A3B8"
                      strokeWidth="0.8"
                      onClick={(e) => handleSurfaceClick(e, rightSurfaceName)}
                      className={`transition-colors hover:brightness-90 ${selectedSurface === rightSurfaceName ? "stroke-teal-600 stroke-[2]" : ""}`}
                    />
                    {/* Center Occlusal Surface */}
                    <path
                      d="M 18,18 C 23,17 31,17 36,18 C 37,23 37,29 36,34 C 31,35 23,35 18,34 C 17,29 17,23 18,18 Z"
                      fill={centerColor}
                      stroke="#94A3B8"
                      strokeWidth="0.8"
                      onClick={(e) => handleSurfaceClick(e, centerSurfaceName)}
                      className={`transition-colors hover:brightness-90 ${selectedSurface === centerSurfaceName ? "stroke-teal-600 stroke-[2]" : ""}`}
                    />
                    <line x1="20" y1="26" x2="34" y2="26" stroke="#94A3B8" strokeWidth="0.8" opacity="0.6" pointerEvents="none" />
                    <line x1="27" y1="19" x2="27" y2="33" stroke="#94A3B8" strokeWidth="0.8" opacity="0.6" pointerEvents="none" />
                  </g>
                )}

                {toothType === "PREMOLAR" && (
                  /* Lower Premolar Crown: Rounded Bicuspid Profile */
                  <g>
                    <path
                      d="M 11,15 C 15,10 22,9 27,10 C 32,9 39,10 43,15 C 45,25 45,39 43,46 C 37,45 17,45 11,46 C 9,39 9,25 11,15 Z"
                      fill="#FFFFFF"
                      stroke={tooth.has_crown ? "#F59E0B" : isSelected ? "#0D9488" : "#64748B"}
                      strokeWidth={tooth.has_crown || isSelected ? "2" : "1.2"}
                    />
                    <path
                      d="M 11,15 C 15,10 22,9 27,10 C 32,9 39,10 43,15 C 41,17 38,18 35,20 C 31,18 23,18 19,20 C 16,18 13,17 11,15 Z"
                      fill={lingualColor}
                      stroke="#94A3B8"
                      strokeWidth="0.8"
                      onClick={(e) => handleSurfaceClick(e, lingualName)}
                      className={`transition-colors hover:brightness-90 ${selectedSurface === lingualName ? "stroke-teal-600 stroke-[2]" : ""}`}
                    />
                    <path
                      d="M 19,36 C 23,38 31,38 35,36 C 38,39 41,42 43,46 C 37,45 17,45 11,46 C 13,42 16,39 19,36 Z"
                      fill={buccalColor}
                      stroke="#94A3B8"
                      strokeWidth="0.8"
                      onClick={(e) => handleSurfaceClick(e, buccalName)}
                      className={`transition-colors hover:brightness-90 ${selectedSurface === buccalName ? "stroke-teal-600 stroke-[2]" : ""}`}
                    />
                    <path
                      d="M 11,15 C 13,17 16,18 19,20 C 18,26 18,32 19,36 C 16,39 13,42 11,46 C 9,39 9,25 11,15 Z"
                      fill={leftColor}
                      stroke="#94A3B8"
                      strokeWidth="0.8"
                      onClick={(e) => handleSurfaceClick(e, leftSurfaceName)}
                      className={`transition-colors hover:brightness-90 ${selectedSurface === leftSurfaceName ? "stroke-teal-600 stroke-[2]" : ""}`}
                    />
                    <path
                      d="M 43,15 C 41,17 38,18 35,20 C 36,26 36,32 35,36 C 38,39 41,42 43,46 C 45,39 45,25 43,15 Z"
                      fill={rightColor}
                      stroke="#94A3B8"
                      strokeWidth="0.8"
                      onClick={(e) => handleSurfaceClick(e, rightSurfaceName)}
                      className={`transition-colors hover:brightness-90 ${selectedSurface === rightSurfaceName ? "stroke-teal-600 stroke-[2]" : ""}`}
                    />
                    <path
                      d="M 19,20 C 23,18 31,18 35,20 C 36,26 36,32 35,36 C 31,38 23,38 19,36 C 18,32 18,26 19,20 Z"
                      fill={centerColor}
                      stroke="#94A3B8"
                      strokeWidth="0.8"
                      onClick={(e) => handleSurfaceClick(e, centerSurfaceName)}
                      className={`transition-colors hover:brightness-90 ${selectedSurface === centerSurfaceName ? "stroke-teal-600 stroke-[2]" : ""}`}
                    />
                    <line x1="22" y1="28" x2="32" y2="28" stroke="#94A3B8" strokeWidth="0.8" opacity="0.6" pointerEvents="none" />
                  </g>
                )}

                {toothType === "CANINE" && (
                  /* Lower Canine Crown: Pointed Cusp Apex at Top */
                  <g>
                    <path
                      d="M 13,18 L 27,9 L 41,18 C 44,26 44,38 42,46 C 36,45 18,45 12,46 C 10,38 10,26 13,18 Z"
                      fill="#FFFFFF"
                      stroke={tooth.has_crown ? "#F59E0B" : isSelected ? "#0D9488" : "#64748B"}
                      strokeWidth={tooth.has_crown || isSelected ? "2" : "1.2"}
                    />
                    <path
                      d="M 20,23 L 27,15 L 34,23 L 41,18 L 27,9 L 13,18 Z"
                      fill={lingualColor}
                      stroke="#94A3B8"
                      strokeWidth="0.8"
                      onClick={(e) => handleSurfaceClick(e, lingualName)}
                      className={`transition-colors hover:brightness-90 ${selectedSurface === lingualName ? "stroke-teal-600 stroke-[2]" : ""}`}
                    />
                    <path
                      d="M 20,29 L 27,21 L 34,29 C 37,35 40,40 42,46 C 36,45 18,45 12,46 C 14,40 17,35 20,29 Z"
                      fill={buccalColor}
                      stroke="#94A3B8"
                      strokeWidth="0.8"
                      onClick={(e) => handleSurfaceClick(e, buccalName)}
                      className={`transition-colors hover:brightness-90 ${selectedSurface === buccalName ? "stroke-teal-600 stroke-[2]" : ""}`}
                    />
                    <path
                      d="M 13,18 L 20,23 L 20,29 C 17,35 14,40 12,46 C 10,38 10,26 13,18 Z"
                      fill={leftColor}
                      stroke="#94A3B8"
                      strokeWidth="0.8"
                      onClick={(e) => handleSurfaceClick(e, leftSurfaceName)}
                      className={`transition-colors hover:brightness-90 ${selectedSurface === leftSurfaceName ? "stroke-teal-600 stroke-[2]" : ""}`}
                    />
                    <path
                      d="M 41,18 L 34,23 L 34,29 C 37,35 40,40 42,46 C 44,38 44,26 41,18 Z"
                      fill={rightColor}
                      stroke="#94A3B8"
                      strokeWidth="0.8"
                      onClick={(e) => handleSurfaceClick(e, rightSurfaceName)}
                      className={`transition-colors hover:brightness-90 ${selectedSurface === rightSurfaceName ? "stroke-teal-600 stroke-[2]" : ""}`}
                    />
                    {/* Pointed Incisal Chevron Ridge */}
                    <polygon
                      points="20,23 27,15 34,23 34,29 27,21 20,29"
                      fill={centerColor}
                      stroke="#94A3B8"
                      strokeWidth="0.8"
                      onClick={(e) => handleSurfaceClick(e, centerSurfaceName)}
                      className={`transition-colors hover:brightness-90 ${selectedSurface === centerSurfaceName ? "stroke-teal-600 stroke-[2]" : ""}`}
                    />
                  </g>
                )}

                {toothType === "INCISOR" && (
                  /* Lower Incisor Crown: Clean Chisel Shape */
                  <g>
                    <path
                      d="M 10,12 C 18,10 36,10 44,12 C 43,24 41,38 39,46 C 33,45 21,45 15,46 C 13,38 11,24 10,12 Z"
                      fill="#FFFFFF"
                      stroke={tooth.has_crown ? "#F59E0B" : isSelected ? "#0D9488" : "#64748B"}
                      strokeWidth={tooth.has_crown || isSelected ? "2" : "1.2"}
                    />
                    <path
                      d="M 12,18 C 18,17 36,17 42,18 L 36,22 C 31,21 23,21 18,22 Z"
                      fill={lingualColor}
                      stroke="#94A3B8"
                      strokeWidth="0.8"
                      onClick={(e) => handleSurfaceClick(e, lingualName)}
                      className={`transition-colors hover:brightness-90 ${selectedSurface === lingualName ? "stroke-teal-600 stroke-[2]" : ""}`}
                    />
                    <path
                      d="M 18,22 C 23,21 31,21 36,22 C 38,28 39,38 39,46 C 33,45 21,45 15,46 C 15,38 16,28 18,22 Z"
                      fill={buccalColor}
                      stroke="#94A3B8"
                      strokeWidth="0.8"
                      onClick={(e) => handleSurfaceClick(e, buccalName)}
                      className={`transition-colors hover:brightness-90 ${selectedSurface === buccalName ? "stroke-teal-600 stroke-[2]" : ""}`}
                    />
                    <path
                      d="M 10,12 L 12,18 L 18,22 C 16,28 15,38 15,46 C 13,38 11,24 10,12 Z"
                      fill={leftColor}
                      stroke="#94A3B8"
                      strokeWidth="0.8"
                      onClick={(e) => handleSurfaceClick(e, leftSurfaceName)}
                      className={`transition-colors hover:brightness-90 ${selectedSurface === leftSurfaceName ? "stroke-teal-600 stroke-[2]" : ""}`}
                    />
                    <path
                      d="M 44,12 L 42,18 L 36,22 C 38,28 39,38 39,46 C 41,38 43,24 44,12 Z"
                      fill={rightColor}
                      stroke="#94A3B8"
                      strokeWidth="0.8"
                      onClick={(e) => handleSurfaceClick(e, rightSurfaceName)}
                      className={`transition-colors hover:brightness-90 ${selectedSurface === rightSurfaceName ? "stroke-teal-600 stroke-[2]" : ""}`}
                    />
                    {/* Incisal Cutting Ribbon Edge */}
                    <path
                      d="M 10,12 C 18,10 36,10 44,12 L 42,18 C 36,17 18,17 12,18 Z"
                      fill={centerColor}
                      stroke="#94A3B8"
                      strokeWidth="0.8"
                      onClick={(e) => handleSurfaceClick(e, centerSurfaceName)}
                      className={`transition-colors hover:brightness-90 ${selectedSurface === centerSurfaceName ? "stroke-teal-600 stroke-[2]" : ""}`}
                    />
                  </g>
                )}
              </g>
            )}
          </g>
        ) : (
          /* ========================================================================= */
          /* MODE B: SCHEMATIC 5-ZONE BOX VIEW                                         */
          /* ========================================================================= */
          <g>
            {/* Root Schematic */}
            {tooth.has_implant ? (
              <g transform={`translate(27, ${isUpper ? 20 : 54})`}>
                <rect x="-4" y="-12" width="8" height="24" rx="2" fill={`url(#implant-grad-${tooth.id})`} stroke="#475569" strokeWidth="1" />
                <line x1="-5" y1="-8" x2="5" y2="-8" stroke="#334155" strokeWidth="1" />
                <line x1="-5" y1="-3" x2="5" y2="-3" stroke="#334155" strokeWidth="1" />
                <line x1="-5" y1="2" x2="5" y2="2" stroke="#334155" strokeWidth="1" />
                <line x1="-5" y1="7" x2="5" y2="7" stroke="#334155" strokeWidth="1" />
              </g>
            ) : (
              <g>
                {isMolarOrPremolar ? (
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
                ) : (
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
                )}
                {tooth.has_root_canal && (
                  <line x1="27" y1={isUpper ? 8 : 66} x2="27" y2={isUpper ? 34 : 40} stroke="#8B5CF6" strokeWidth="1.8" strokeLinecap="round" />
                )}
              </g>
            )}

            {/* Geometric Crown Box */}
            <g transform={`translate(9, ${isUpper ? 34 : 6})`}>
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
              <polygon
                points="0,0 36,0 28,9 8,9"
                fill={buccalColor}
                stroke="#94A3B8"
                strokeWidth="0.8"
                onClick={(e) => handleSurfaceClick(e, buccalName)}
                className={`transition-colors hover:brightness-90 ${selectedSurface === buccalName ? "stroke-teal-600 stroke-[1.8]" : ""}`}
              />
              <polygon
                points="0,34 36,34 28,25 8,25"
                fill={lingualColor}
                stroke="#94A3B8"
                strokeWidth="0.8"
                onClick={(e) => handleSurfaceClick(e, lingualName)}
                className={`transition-colors hover:brightness-90 ${selectedSurface === lingualName ? "stroke-teal-600 stroke-[1.8]" : ""}`}
              />
              <polygon
                points="0,0 8,9 8,25 0,34"
                fill={leftColor}
                stroke="#94A3B8"
                strokeWidth="0.8"
                onClick={(e) => handleSurfaceClick(e, leftSurfaceName)}
                className={`transition-colors hover:brightness-90 ${selectedSurface === leftSurfaceName ? "stroke-teal-600 stroke-[1.8]" : ""}`}
              />
              <polygon
                points="36,0 28,9 28,25 36,34"
                fill={rightColor}
                stroke="#94A3B8"
                strokeWidth="0.8"
                onClick={(e) => handleSurfaceClick(e, rightSurfaceName)}
                className={`transition-colors hover:brightness-90 ${selectedSurface === rightSurfaceName ? "stroke-teal-600 stroke-[1.8]" : ""}`}
              />
              <polygon
                points="8,9 28,9 28,25 8,25"
                fill={centerColor}
                stroke="#94A3B8"
                strokeWidth="0.8"
                onClick={(e) => handleSurfaceClick(e, centerSurfaceName)}
                className={`transition-colors hover:brightness-90 ${selectedSurface === centerSurfaceName ? "stroke-teal-600 stroke-[1.8]" : ""}`}
              />
            </g>
          </g>
        )}

        {/* ========================================================================= */}
        {/* 3. CLINICAL CONDITION OVERLAYS (Crowns, Bridges, Extractions)              */}
        {/* ========================================================================= */}

        {/* Gold / Ceramic Crown Finish Line & Contour Indicator */}
        {tooth.has_crown && (
          <g>
            <path
              d={isUpper ? "M 7,37 L 16,35 L 27,37 L 38,35 L 47,37" : "M 7,45 L 16,47 L 27,45 L 38,47 L 47,45"}
              stroke="#D97706"
              strokeWidth="2.5"
              fill="none"
              strokeLinecap="round"
            />
          </g>
        )}

        {/* Fixed Partial Denture Bridge Connector */}
        {tooth.has_bridge && (
          <rect
            x="4"
            y={isUpper ? 50 : 24}
            width="46"
            height="6"
            rx="2"
            fill="#854D0E"
            opacity="0.85"
            stroke="#78350F"
            strokeWidth="0.8"
          />
        )}

        {/* Surgical Extraction Cross (Bold Red X) */}
        {tooth.is_extracted && (
          <g stroke="#EF4444" strokeWidth="3" strokeLinecap="round">
            <line x1="6" y1="8" x2="48" y2="74" />
            <line x1="48" y1="8" x2="6" y2="74" />
          </g>
        )}

        {/* Missing Tooth Dashed Marker */}
        {tooth.is_missing && !tooth.has_implant && (
          <g stroke="#94A3B8" strokeWidth="1.8" strokeDasharray="3,3">
            <line x1="4" y1="41" x2="50" y2="41" />
          </g>
        )}
      </svg>

      {/* Bottom Numbering (Lower Arch) */}
      {!isUpper && (
        <span
          className={`text-[11px] font-mono font-bold tracking-tight mt-1 ${
            isSelected ? "text-teal-700 dark:text-teal-400 font-extrabold" : "text-slate-600 dark:text-slate-400"
          }`}
        >
          {toothLabel}
        </span>
      )}

      {/* Mobility Badge */}
      {tooth.mobility_grade > 0 && (
        <span className="absolute -top-1 -right-1 px-1 py-0.2 bg-amber-500 text-white rounded text-[8px] font-bold shadow-xs">
          M{tooth.mobility_grade}
        </span>
      )}
    </div>
  );
}
