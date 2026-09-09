export type TreatmentStatus = "PLANNED" | "IN_PROGRESS" | "COMPLETED" | "CANCELLED";

export type FollowUpStatus = "SCHEDULED" | "COMPLETED" | "MISSED" | "CANCELLED";

export interface ProcedureItem {
  id?: string;
  procedure_name: string;
  tooth_number?: string | null;
  quantity: number;
  cost: number;
  duration: number; // in minutes
  notes?: string | null;
  status: string;
  created_at?: string | null;
}

export interface FollowUpItem {
  id?: string;
  treatment_id?: string;
  clinic_id?: string;
  patient_id?: string;
  follow_up_date: string; // YYYY-MM-DD
  reason: string;
  instructions?: string | null;
  status: FollowUpStatus;
  completed_at?: string | null;
  created_at?: string | null;
}

export interface SOAPNotes {
  subjective?: string | null;
  objective?: string | null;
  assessment?: string | null;
  plan?: string | null;
}

export interface TreatmentRead {
  id: string;
  clinic_id: string;
  patient_id: string;
  appointment_id: string;
  dentist_id: string;
  treatment_number: string;
  diagnosis: string;
  chief_complaint?: string | null;
  clinical_findings?: string | null;
  treatment_plan?: string | null;
  procedure_performed?: string | null;
  status: TreatmentStatus;
  is_override: boolean;
  created_at: string;
  completed_at?: string | null;
  patient_name?: string | null;
  patient_number?: string | null;
  patient_phone?: string | null;
  dentist_name?: string | null;
  appointment_number?: string | null;
  appointment_date?: string | null;
  procedures_count: number;
  total_cost: number;
}

export interface TreatmentDetail extends TreatmentRead {
  local_anaesthesia_used?: string | null;
  medicines_used?: string | null;
  clinical_notes?: string | null;
  soap_subjective?: string | null;
  soap_objective?: string | null;
  soap_assessment?: string | null;
  soap_plan?: string | null;
  follow_up_instructions?: string | null;
  cancellation_reason?: string | null;
  procedures: ProcedureItem[];
  follow_ups: FollowUpItem[];
  patient_medical_alerts: string[];
}

export interface TreatmentDashboardStats {
  planned: number;
  in_progress: number;
  completed: number;
  follow_ups_due: number;
  total_treatments: number;
}

export interface TreatmentCreateInput {
  patient_id: string;
  appointment_id: string;
  dentist_id: string;
  diagnosis: string;
  chief_complaint?: string;
  clinical_findings?: string;
  treatment_plan?: string;
  procedure_performed?: string;
  local_anaesthesia_used?: string;
  medicines_used?: string;
  clinical_notes?: string;
  soap?: SOAPNotes;
  follow_up_instructions?: string;
  status: TreatmentStatus;
  is_override?: boolean;
  procedures: {
    procedure_name: string;
    tooth_number?: string;
    quantity: number;
    cost: number;
    duration: number;
    notes?: string;
    status: string;
  }[];
  follow_up?: {
    follow_up_date: string;
    reason: string;
    instructions?: string;
    status: FollowUpStatus;
  } | null;
}

export interface TreatmentUpdateInput {
  diagnosis?: string;
  chief_complaint?: string;
  clinical_findings?: string;
  treatment_plan?: string;
  procedure_performed?: string;
  local_anaesthesia_used?: string;
  medicines_used?: string;
  clinical_notes?: string;
  soap?: SOAPNotes;
  follow_up_instructions?: string;
  status?: TreatmentStatus;
  procedures?: {
    procedure_name: string;
    tooth_number?: string;
    quantity: number;
    cost: number;
    duration: number;
    notes?: string;
    status: string;
  }[];
  follow_up?: {
    follow_up_date: string;
    reason: string;
    instructions?: string;
    status: FollowUpStatus;
  } | null;
}
