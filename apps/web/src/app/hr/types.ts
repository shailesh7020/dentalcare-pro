export type EmploymentType = "FULL_TIME" | "PART_TIME" | "CONTRACT" | "CONSULTANT" | "INTERN";
export type EmployeeStatus = "ACTIVE" | "ON_LEAVE" | "SUSPENDED" | "RESIGNED" | "RETIRED";
export type ShiftType = "REGULAR" | "ROTATING" | "SPLIT" | "EMERGENCY";
export type ScheduleStatus = "SCHEDULED" | "CONFIRMED" | "COMPLETED" | "ABSENT" | "CANCELLED";
export type AttendanceMethod = "MANUAL" | "QR_CODE" | "RFID" | "BIOMETRIC";
export type AttendanceStatus = "PRESENT" | "ABSENT" | "HALF_DAY" | "LATE" | "ON_LEAVE";
export type LeaveType = "CASUAL" | "SICK" | "ANNUAL" | "MATERNITY" | "PATERNITY" | "EMERGENCY" | "UNPAID";
export type LeaveStatus = "DRAFT" | "SUBMITTED" | "MANAGER_APPROVED" | "HR_APPROVED" | "REJECTED" | "CANCELLED";
export type PayrollStatus = "DRAFT" | "PROCESSING" | "APPROVED" | "PAID" | "CANCELLED";
export type PayslipStatus = "GENERATED" | "APPROVED" | "PAID";
export type IncentiveCriterion = "TREATMENTS_COMPLETED" | "REVENUE_GENERATED" | "PATIENT_SATISFACTION" | "COLLECTION_TARGETS" | "ATTENDANCE_PERFECT" | "CUSTOM";
export type IncentiveStatus = "PENDING" | "APPROVED" | "INCLUDED_IN_PAYROLL";
export type ReviewCycle = "MONTHLY" | "QUARTERLY" | "YEARLY";
export type ReviewStatus = "DRAFT" | "SUBMITTED" | "ACKNOWLEDGED" | "COMPLETED";
export type CourseType = "CONTINUING_EDUCATION" | "INFECTION_CONTROL" | "CPR_BLS" | "RADIATION_SAFETY" | "CLINICAL_SPECIALTY" | "COMPLIANCE";
export type TrainingRecordStatus = "ENROLLED" | "COMPLETED" | "EXPIRED";
export type JobStatus = "OPEN" | "ON_HOLD" | "CLOSED";
export type ApplicantStage = "APPLIED" | "SCREENING" | "INTERVIEW_SCHEDULED" | "OFFERED" | "HIRED" | "REJECTED";
export type InterviewType = "TECHNICAL" | "CLINICAL_DEMO" | "HR" | "FINAL";
export type InterviewResult = "PENDING" | "RECOMMENDED" | "NOT_RECOMMENDED";
export type DocumentType = "CONTRACT" | "CERTIFICATE" | "DENTAL_LICENSE" | "ID_PROOF" | "TAX_DOCUMENT" | "EDUCATIONAL" | "PERFORMANCE_REPORT";

export interface Employee {
  id: string;
  organization_id?: string | null;
  clinic_id?: string | null;
  user_id?: string | null;
  employee_code: string;
  first_name: string;
  last_name: string;
  email: string;
  phone?: string | null;
  gender: string;
  date_of_birth?: string | null;
  profile_photo_url?: string | null;
  emergency_contact_name?: string | null;
  emergency_contact_phone?: string | null;
  emergency_contact_relation?: string | null;
  address?: string | null;
  qualification?: string | null;
  specialization?: string | null;
  license_number?: string | null;
  license_expiry_date?: string | null;
  department_id?: string | null;
  designation: string;
  employment_type: EmploymentType;
  reporting_manager_id?: string | null;
  joining_date: string;
  exit_date?: string | null;
  status: EmployeeStatus;
  base_salary: number;
  bank_name?: string | null;
  bank_account_number?: string | null;
  bank_ifsc_or_routing?: string | null;
  tax_id_number?: string | null;
  created_at: string;
  updated_at: string;
}

export interface WorkShift {
  id: string;
  organization_id?: string | null;
  clinic_id?: string | null;
  name: string;
  code: string;
  start_time: string;
  end_time: string;
  break_minutes: number;
  shift_type: ShiftType;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface StaffSchedule {
  id: string;
  organization_id?: string | null;
  clinic_id: string;
  employee_id: string;
  shift_id?: string | null;
  chair_id?: string | null;
  schedule_date: string;
  start_time: string;
  end_time: string;
  is_split_shift: boolean;
  split_start_time?: string | null;
  split_end_time?: string | null;
  status: ScheduleStatus;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AttendanceRecord {
  id: string;
  organization_id?: string | null;
  clinic_id: string;
  employee_id: string;
  date: string;
  check_in_time?: string | null;
  check_out_time?: string | null;
  entry_method: AttendanceMethod;
  status: AttendanceStatus;
  break_minutes: number;
  overtime_minutes: number;
  is_late: boolean;
  late_minutes: number;
  is_early_departure: boolean;
  early_departure_minutes: number;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface LeaveAllocation {
  id: string;
  employee_id: string;
  year: number;
  leave_type: LeaveType;
  total_days: number;
  used_days: number;
  pending_days: number;
  created_at: string;
  updated_at: string;
}

export interface LeaveRequest {
  id: string;
  organization_id?: string | null;
  clinic_id: string;
  employee_id: string;
  leave_type: LeaveType;
  start_date: string;
  end_date: string;
  days_count: number;
  reason: string;
  status: LeaveStatus;
  manager_id?: string | null;
  manager_notes?: string | null;
  manager_reviewed_at?: string | null;
  hr_id?: string | null;
  hr_notes?: string | null;
  hr_reviewed_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PayrollRun {
  id: string;
  organization_id?: string | null;
  clinic_id?: string | null;
  run_number: string;
  period_month: number;
  period_year: number;
  status: PayrollStatus;
  total_gross: number;
  total_deductions: number;
  total_net: number;
  total_employees: number;
  approved_by?: string | null;
  approved_at?: string | null;
  paid_at?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Payslip {
  id: string;
  payroll_run_id: string;
  employee_id: string;
  clinic_id: string;
  period_month: number;
  period_year: number;
  basic_salary: number;
  hra_allowance: number;
  special_allowance: number;
  medical_allowance: number;
  other_allowance: number;
  incentive_amount: number;
  overtime_amount: number;
  bonus_amount: number;
  gross_earnings: number;
  pf_deduction: number;
  professional_tax: number;
  tds_tax: number;
  insurance_deduction: number;
  unpaid_leave_deduction: number;
  other_deductions: number;
  total_deductions: number;
  net_salary: number;
  status: PayslipStatus;
  payment_method?: string | null;
  payment_reference?: string | null;
  paid_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface EmployeeIncentive {
  id: string;
  employee_id: string;
  period_month: number;
  period_year: number;
  criterion_type: IncentiveCriterion;
  target_value: number;
  achieved_value: number;
  rate_or_percentage: number;
  calculated_amount: number;
  status: IncentiveStatus;
  approved_by?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PerformanceReview {
  id: string;
  organization_id?: string | null;
  clinic_id: string;
  employee_id: string;
  reviewer_id?: string | null;
  review_cycle: ReviewCycle;
  review_period: string;
  clinical_skills_rating: number;
  patient_satisfaction_rating: number;
  punctuality_rating: number;
  teamwork_rating: number;
  protocol_adherence_rating: number;
  overall_rating: number;
  kpi_details_json?: string | null;
  strengths?: string | null;
  areas_of_improvement?: string | null;
  goals_next_period?: string | null;
  training_needs?: string | null;
  employee_feedback?: string | null;
  status: ReviewStatus;
  created_at: string;
  updated_at: string;
}

export interface TrainingCourse {
  id: string;
  organization_id?: string | null;
  title: string;
  provider: string;
  course_type: CourseType;
  credits_hours: number;
  is_mandatory: boolean;
  validity_months: number;
  description?: string | null;
  created_at: string;
  updated_at: string;
}

export interface EmployeeTrainingRecord {
  id: string;
  employee_id: string;
  course_id?: string | null;
  course_title: string;
  completion_date: string;
  expiry_date?: string | null;
  certificate_number?: string | null;
  certificate_url?: string | null;
  status: TrainingRecordStatus;
  created_at: string;
  updated_at: string;
}

export interface JobOpening {
  id: string;
  organization_id?: string | null;
  clinic_id?: string | null;
  department_id?: string | null;
  title: string;
  employment_type: EmploymentType;
  open_positions: number;
  experience_years_min: number;
  status: JobStatus;
  description: string;
  requirements?: string | null;
  created_at: string;
  updated_at: string;
}

export interface JobApplicant {
  id: string;
  job_opening_id: string;
  full_name: string;
  email: string;
  phone: string;
  resume_url?: string | null;
  qualification?: string | null;
  experience_years: number;
  current_stage: ApplicantStage;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface InterviewSchedule {
  id: string;
  applicant_id: string;
  interviewer_id?: string | null;
  scheduled_at: string;
  interview_type: InterviewType;
  feedback_notes?: string | null;
  rating?: number | null;
  result: InterviewResult;
  created_at: string;
  updated_at: string;
}

export interface EmployeeDocument {
  id: string;
  employee_id: string;
  document_type: DocumentType;
  title: string;
  file_url: string;
  file_size_bytes: number;
  mime_type: string;
  version: number;
  expiry_date?: string | null;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface HRDashboardMetrics {
  total_headcount: number;
  active_employees: number;
  on_leave_employees: number;
  today_scheduled: number;
  today_present: number;
  today_late: number;
  attendance_rate: number;
  pending_leaves: number;
  current_month_payroll_total: number;
  open_job_positions: number;
  licenses_expiring_soon: number;
}
