export type DentitionType = "ADULT" | "PRIMARY";
export type NumberingSystem = "FDI" | "UNIVERSAL" | "PALMER";

export type ToothCondition =
  | "HEALTHY"
  | "CARIES"
  | "FILLING"
  | "ROOT_CANAL"
  | "CROWN"
  | "IMPLANT"
  | "EXTRACTION"
  | "MISSING"
  | "BRIDGE"
  | "OBSERVATION"
  | "TEMPORARY_CROWN"
  | "TEMPORARY_FILLING"
  | "VENEER"
  | "FRACTURE"
  | "SEALANT"
  | "ORTHODONTIC_BRACKET"
  | "MOBILE_TOOTH"
  | "IMPACTED";

export type ToothSurfaceEnum =
  | "MESIAL"
  | "DISTAL"
  | "BUCCAL"
  | "LINGUAL"
  | "OCCLUSAL"
  | "INCISAL"
  | "CERVICAL"
  | "ROOT";

export const COLOR_STANDARDS: Record<string, string> = {
  HEALTHY: "#10B981",
  CARIES: "#EF4444",
  FILLING: "#3B82F6",
  ROOT_CANAL: "#8B5CF6",
  CROWN: "#F59E0B",
  IMPLANT: "#94A3B8",
  EXTRACTION: "#1E293B",
  MISSING: "#64748B",
  BRIDGE: "#854D0E",
  OBSERVATION: "#EAB308",
  TEMPORARY_CROWN: "#F97316",
  TEMPORARY_FILLING: "#F97316",
  VENEER: "#14B8A6",
  FRACTURE: "#E11D48",
  SEALANT: "#06B6D4",
  ORTHODONTIC_BRACKET: "#6366F1",
  MOBILE_TOOTH: "#D97706",
  IMPACTED: "#7C3AED",
};

export interface ToothSurface {
  id: string;
  surface: ToothSurfaceEnum;
  condition: string;
  treatment: string;
  color: string;
  notes?: string | null;
  last_modified_at: string;
  dentist_id?: string | null;
}

export interface ToothHistory {
  id: string;
  tooth_id: string;
  action: string;
  description: string;
  previous_state?: string | null;
  new_state?: string | null;
  affected_surfaces?: string | null;
  treatment_id?: string | null;
  treatment_procedure_id?: string | null;
  appointment_id?: string | null;
  dentist_id?: string | null;
  created_at: string;
}

export interface Tooth {
  id: string;
  clinic_id: string;
  patient_id: string;
  tooth_number: string;
  universal_number: string;
  palmer_notation: string;
  name: string;
  dentition_type: DentitionType;
  arch: "UPPER" | "LOWER";
  quadrant: number;
  tooth_type: "INCISOR" | "CANINE" | "PREMOLAR" | "MOLAR";
  primary_status: ToothCondition;
  color: string;
  is_missing: boolean;
  is_extracted: boolean;
  is_impacted: boolean;
  has_root_canal: boolean;
  has_crown: boolean;
  has_implant: boolean;
  has_bridge: boolean;
  mobility_grade: number;
  notes?: string | null;
  surfaces: ToothSurface[];
  history?: ToothHistory[];
}

export interface OdontogramStats {
  active_caries: number;
  missing_teeth: number;
  root_canals: number;
  crowns: number;
  implants: number;
  restorations: number;
  total_teeth_charted: number;
}

export interface PatientOdontogram {
  patient_id: string;
  patient_name: string;
  patient_number: string;
  dentition_type: DentitionType;
  preferred_numbering: NumberingSystem;
  teeth: Tooth[];
  stats: OdontogramStats;
}

export function getToothLabel(tooth: Tooth, system: NumberingSystem): string {
  switch (system) {
    case "UNIVERSAL":
      return tooth.universal_number;
    case "PALMER":
      return tooth.palmer_notation;
    case "FDI":
    default:
      return tooth.tooth_number;
  }
}
