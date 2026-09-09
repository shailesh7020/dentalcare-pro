export interface PortalDashboardSummary {
  patient_id: string;
  patient_name: string;
  patient_number: string;
  clinic_name: string;
  next_appointment?: {
    id: string;
    appointment_number: string;
    date: string;
    time: string;
    dentist_name: string;
    visit_type: string;
    status: string;
  } | null;
  active_prescriptions_count: number;
  total_balance_due: number;
  unread_messages_count: number;
  pending_forms_count: number;
}

export interface PortalAppointmentRead {
  id: string;
  appointment_number: string;
  date: string;
  start_time: string;
  duration_minutes: number;
  status: string;
  visit_type: string;
  reason?: string;
  notes?: string;
  dentist_name?: string;
}

export interface PortalPrescriptionItemRead {
  id: string;
  medicine_name: string;
  dosage: string;
  frequency: string;
  duration: string;
  instructions?: string;
}

export interface PortalPrescriptionRead {
  id: string;
  prescription_number: string;
  date: string;
  dentist_name?: string;
  diagnosis?: string;
  notes?: string;
  items: PortalPrescriptionItemRead[];
}

export interface PortalInvoiceRead {
  id: string;
  invoice_number: string;
  date: string;
  total_amount: number;
  discount_amount: number;
  tax_amount: number;
  final_amount: number;
  paid_amount: number;
  balance_due: number;
  status: string;
}

export interface PortalTreatmentRead {
  id: string;
  treatment_plan_name: string;
  status: string;
  start_date?: string;
  completion_date?: string;
  dentist_name?: string;
  notes?: string;
}

export interface PortalToothRead {
  tooth_number: string;
  condition: string;
  color?: string;
  surface_details?: Record<string, any>;
  notes?: string;
}

export interface PortalDocumentRead {
  id: string;
  file_name: string;
  document_type: string;
  created_at: string;
  download_url?: string;
}

export interface PortalPatientProfile {
  id: string;
  patient_number: string;
  first_name: string;
  last_name: string;
  email: string;
  mobile_number: string;
  date_of_birth?: string;
  gender?: string;
  blood_group?: string;
  address?: string;
  allergies?: string[];
  medical_history?: string[];
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
}
