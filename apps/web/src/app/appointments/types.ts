export type AppointmentStatus =
  | "SCHEDULED"
  | "CONFIRMED"
  | "CHECKED_IN"
  | "IN_CHAIR"
  | "COMPLETED"
  | "CANCELLED"
  | "NO_SHOW";

export type VisitType =
  | "CONSULTATION"
  | "CHECKUP"
  | "CLEANING"
  | "PROCEDURE"
  | "SURGERY"
  | "FOLLOW_UP"
  | "EMERGENCY";

export interface Chair {
  id: string;
  name: string;
  room_number?: string | null;
  status: "ACTIVE" | "MAINTENANCE" | "INACTIVE";
  notes?: string | null;
  created_at?: string;
}

export interface Dentist {
  id: string;
  first_name: string;
  last_name: string;
  role: string;
}

export interface Appointment {
  id: string;
  clinic_id: string;
  patient_id: string;
  dentist_id: string;
  chair_id: string;
  appointment_number: string;
  date: string;
  start_time: string;
  end_time: string;
  duration: number;
  status: AppointmentStatus;
  visit_type: VisitType;
  priority: string;
  chief_complaint?: string | null;
  notes?: string | null;
  cancellation_reason?: string | null;
  is_emergency_override: boolean;
  created_at: string;
  updated_at: string;

  // Denormalized fields
  patient_name?: string | null;
  patient_number?: string | null;
  patient_phone?: string | null;
  dentist_name?: string | null;
  chair_name?: string | null;
  patient_photo_url?: string | null;
  patient_medical_alerts?: string[];
}

export interface AppointmentQueueItem {
  id: string;
  appointment_number: string;
  patient_id: string;
  patient_name: string;
  patient_number: string;
  patient_phone?: string | null;
  dentist_id: string;
  dentist_name: string;
  chair_id: string;
  chair_name: string;
  scheduled_time: string;
  duration: number;
  status: AppointmentStatus;
  visit_type: VisitType;
  priority: string;
  checked_in_at?: string | null;
  treatment_started_at?: string | null;
  wait_minutes?: number | null;
}

export interface DashboardStats {
  date: string;
  total_appointments: number;
  completed: number;
  cancelled: number;
  no_show: number;
  waiting: number;
  in_treatment: number;
  upcoming_follow_ups: number;
  revenue_placeholder: number;
}

export interface CalendarDayData {
  date: string;
  chairs: Chair[];
  appointments: Appointment[];
}

export interface CalendarWeekData {
  start_date: string;
  end_date: string;
  appointments: Appointment[];
}

export interface CalendarMonthData {
  year: number;
  month: number;
  appointments: Appointment[];
}
