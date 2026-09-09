export type PatientSharingMode = "SHARED" | "ISOLATED" | "TRANSFER_ONLY";
export type TransferStatus = "PENDING" | "APPROVED" | "REJECTED" | "COMPLETED" | "CANCELLED";
export type InventoryTransferStatus = "DRAFT" | "DISPATCHED" | "IN_TRANSIT" | "RECEIVED" | "REJECTED" | "CANCELLED";
export type AnnouncementType = "BROADCAST" | "REGIONAL" | "BRANCH_ALERT" | "EMERGENCY";
export type AnnouncementScope = "ALL" | "REGION" | "BRANCH" | "ROLE";

export interface Organization {
  id: string;
  name: string;
  slug: string;
  code: string;
  tax_id?: string;
  legal_name?: string;
  subscription_tier: string;
  is_active: boolean;
  logo_url?: string;
  theme_color: string;
  primary_email: string;
  phone?: string;
  website?: string;
  patient_sharing_mode: PatientSharingMode;
  created_at: string;
  updated_at: string;
}

export interface Region {
  id: string;
  organization_id: string;
  name: string;
  code: string;
  regional_manager_id?: string;
  description?: string;
  is_active: boolean;
  branch_count: number;
  created_at: string;
  updated_at: string;
}

export interface Branch {
  id: string;
  organization_id?: string;
  region_id?: string;
  name: string;
  slug: string;
  branch_code?: string;
  email: string;
  phone?: string;
  timezone: string;
  address?: string;
  working_hours?: string;
  currency: string;
  tax_configuration?: string;
  is_main_branch: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Department {
  id: string;
  clinic_id: string;
  name: string;
  code: string;
  head_dentist_id?: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface EnterprisePermission {
  id: string;
  permission_key: string;
  module: string;
  description?: string;
}

export interface EnterpriseRole {
  id: string;
  organization_id?: string;
  role_key: string;
  name: string;
  description?: string;
  is_system: boolean;
  permissions: EnterprisePermission[];
  created_at: string;
  updated_at: string;
}

export interface UserBranchAssignment {
  id: string;
  user_id: string;
  clinic_id: string;
  role_override?: string;
  is_primary: boolean;
  working_days_json?: string;
  is_active: boolean;
  created_at: string;
}

export interface PatientTransfer {
  id: string;
  organization_id: string;
  patient_id: string;
  patient_name?: string;
  from_clinic_id: string;
  from_clinic_name?: string;
  to_clinic_id: string;
  to_clinic_name?: string;
  initiated_by?: string;
  approved_by?: string;
  status: TransferStatus;
  transfer_reason: string;
  records_included_json?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface DuplicatePatientMatch {
  patient_id: string;
  clinic_id: string;
  clinic_name?: string;
  full_name: string;
  phone: string;
  email?: string;
  date_of_birth?: string;
  similarity_score: number;
  matched_fields: string[];
}

export interface PatientMergeResponse {
  id: string;
  organization_id: string;
  primary_patient_id: string;
  duplicate_patient_id: string;
  merged_by?: string;
  merge_reason?: string;
  records_migrated: Record<string, number>;
  created_at: string;
}

export interface InventoryTransfer {
  id: string;
  organization_id: string;
  transfer_number: string;
  from_clinic_id: string;
  from_clinic_name?: string;
  to_clinic_id: string;
  to_clinic_name?: string;
  item_id: string;
  item_name?: string;
  quantity: number;
  unit_cost: number;
  status: InventoryTransferStatus;
  dispatched_at?: string;
  dispatched_by?: string;
  received_at?: string;
  received_by?: string;
  tracking_number?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface ConsolidatedInventoryItem {
  item_id: string;
  item_name: string;
  category: string;
  unit_of_measure: string;
  total_stock: number;
  total_valuation: number;
  clinic_breakdown: Array<{
    clinic_id: string;
    clinic_name: string;
    stock: number;
    valuation: number;
  }>;
}

export interface BranchFinancialSummary {
  clinic_id: string;
  clinic_name: string;
  total_invoiced: number;
  total_collected: number;
  insurance_collected: number;
  outstanding_balance: number;
  tax_amount: number;
  invoice_count: number;
}

export interface RegionFinancialSummary {
  region_id: string;
  region_name: string;
  total_invoiced: number;
  total_collected: number;
  outstanding_balance: number;
  branches: BranchFinancialSummary[];
}

export interface ConsolidatedFinancials {
  organization_id: string;
  currency: string;
  total_revenue: number;
  total_collected: number;
  total_outstanding: number;
  total_insurance_settled: number;
  total_tax: number;
  branch_summaries: BranchFinancialSummary[];
  region_summaries: RegionFinancialSummary[];
}

export interface BranchBenchmarkScore {
  clinic_id: string;
  clinic_name: string;
  overall_score: number;
  revenue_score: number;
  occupancy_score: number;
  patient_satisfaction_score: number;
  collection_rate_score: number;
  rank: number;
  recommendations: string[];
}

export interface StaffProductivityMetric {
  staff_id: string;
  staff_name: string;
  role: string;
  branch_name: string;
  appointments_completed: number;
  revenue_generated: number;
  utilization_rate: number;
  chairside_hours: number;
}

export interface RevenueForecastItem {
  period: string;
  forecast_revenue: number;
  confidence_lower: number;
  confidence_upper: number;
  growth_rate_percentage: number;
}

export interface EnterpriseAIAnalytics {
  organization_id: string;
  generated_at: string;
  benchmark_scores: BranchBenchmarkScore[];
  top_performing_branches: string[];
  underperforming_branches: string[];
  staff_productivity: StaffProductivityMetric[];
  revenue_forecasts: RevenueForecastItem[];
  network_health_summary: string;
  strategic_recommendations: string[];
}

export interface EnterpriseAnnouncement {
  id: string;
  organization_id: string;
  title: string;
  message: string;
  announcement_type: AnnouncementType;
  target_scope: AnnouncementScope;
  target_id?: string;
  is_active: boolean;
  expires_at?: string;
  created_at: string;
  updated_at: string;
}
