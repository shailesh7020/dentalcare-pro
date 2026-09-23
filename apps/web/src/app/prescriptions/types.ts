export type PrescriptionStatus = "DRAFT" | "ISSUED" | "CANCELLED";

export type MedicineForm =
  | "TABLET"
  | "CAPSULE"
  | "SYRUP"
  | "MOUTHWASH"
  | "DENTAL_PASTE"
  | "GEL"
  | "CREAM"
  | "INJECTION"
  | "DROPS"
  | "POWDER"
  | "OTHER";

export type DosageFrequency =
  | "OD"
  | "BD"
  | "TDS"
  | "QID"
  | "SOS"
  | "STAT"
  | "WEEKLY"
  | "MONTHLY"
  | "CUSTOM";

export type TemplateCategory =
  | "EXTRACTION"
  | "ROOT_CANAL"
  | "IMPLANT"
  | "PERIODONTAL"
  | "EMERGENCY"
  | "GENERAL";

export interface PrescriptionItemRead {
  id: string;
  prescription_id: string;
  medicine_name: string;
  generic_name?: string | null;
  brand_name?: string | null;
  strength?: string | null;
  form: MedicineForm;
  dosage: string;
  route: string;
  frequency: DosageFrequency;
  duration: string;
  quantity: number;
  timing?: string | null;
  food_instructions?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PrescriptionItemCreate {
  medicine_name: string;
  generic_name?: string | null;
  brand_name?: string | null;
  strength?: string | null;
  form?: MedicineForm;
  dosage: string;
  route?: string;
  frequency: DosageFrequency;
  duration: string;
  quantity: number;
  timing?: string | null;
  food_instructions?: string | null;
  notes?: string | null;
}

export interface PrescriptionDetail {
  id: string;
  clinic_id: string;
  patient_id: string;
  treatment_id?: string | null;
  appointment_id?: string | null;
  dentist_id: string;
  prescription_number: string;
  date: string;
  diagnosis: string;
  notes?: string | null;
  instructions?: string | null;
  follow_up_date?: string | null;
  status: PrescriptionStatus;
  cancellation_reason?: string | null;
  issued_at?: string | null;
  items_count: number;
  created_at: string;
  updated_at: string;
  items: PrescriptionItemRead[];
  patient_name?: string | null;
  patient_number?: string | null;
  patient_age?: number | null;
  patient_gender?: string | null;
  patient_alerts?: string[];
  dentist_name?: string | null;
  dentist_registration?: string | null;
  treatment_number?: string | null;
  clinic_name?: string | null;
  clinic_phone?: string | null;
  clinic_email?: string | null;
}

export interface PrescriptionCreate {
  patient_id: string;
  treatment_id?: string | null;
  appointment_id?: string | null;
  dentist_id?: string | null;
  date?: string | null;
  diagnosis: string;
  notes?: string | null;
  instructions?: string | null;
  follow_up_date?: string | null;
  items: PrescriptionItemCreate[];
  issue_immediately: boolean;
}

export interface PrescriptionUpdate {
  diagnosis?: string;
  notes?: string | null;
  instructions?: string | null;
  follow_up_date?: string | null;
  items?: PrescriptionItemCreate[];
}

export interface PrescriptionCancel {
  reason: string;
}

export interface PrescriptionDashboardStats {
  total_prescriptions: number;
  today_prescriptions: number;
  issued_prescriptions: number;
  draft_prescriptions: number;
  cancelled_prescriptions: number;
  follow_ups_due: number;
}

export interface MedicineCatalogItem {
  id: string;
  clinic_id?: string | null;
  generic_name: string;
  brand_name: string;
  strength?: string | null;
  form: MedicineForm;
  category: string;
  standard_dosage?: string | null;
  default_route?: string;
  default_frequency?: DosageFrequency;
  default_duration?: string | null;
  default_instructions?: string | null;
  notes?: string | null;
  is_global: boolean;
  is_active: boolean;
}

export interface PrescriptionTemplateItem {
  id: string;
  clinic_id?: string | null;
  name: string;
  category: TemplateCategory;
  description?: string | null;
  diagnosis_template: string;
  instructions_template: string;
  is_active: boolean;
  default_items: PrescriptionItemCreate[];
}
