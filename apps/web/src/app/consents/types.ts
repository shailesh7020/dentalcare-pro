export type FormStatus = "DRAFT" | "PENDING" | "SUBMITTED" | "REVIEWED" | "APPROVED" | "REJECTED";
export type ConsentType = "PROCEDURE" | "GENERAL_ANESTHESIA" | "COVID_SURVEY" | "FINANCIAL" | "MEDICAL_HISTORY" | "PHOTOGRAPHY";

export interface FormTemplateRead {
  id: string;
  clinic_id: string;
  title: string;
  code: string;
  version: number;
  consent_type: ConsentType;
  description?: string;
  content_markdown: string;
  schema_json: Record<string, any>;
  requires_signature: boolean;
  requires_witness: boolean;
  is_active: boolean;
  created_at: string;
}

export interface PatientFormRead {
  id: string;
  clinic_id: string;
  patient_id: string;
  patient_name?: string;
  template_id: string;
  template_title?: string;
  status: FormStatus;
  responses_json?: Record<string, any>;
  patient_signature?: string;
  submitted_at?: string;
  reviewed_by_name?: string;
  reviewed_at?: string;
  review_notes?: string;
  created_at: string;
}

export interface ConsentRecordRead {
  id: string;
  clinic_id: string;
  patient_id: string;
  patient_name?: string;
  treatment_id?: string;
  consent_type: string;
  title: string;
  legal_text: string;
  signed_by_name: string;
  signature_image?: string;
  signer_relationship: string;
  witness_name?: string;
  witness_signature?: string;
  ip_address?: string;
  audit_hash: string;
  signed_at: string;
  created_at: string;
}
