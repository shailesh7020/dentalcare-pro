export type InsuranceProviderType = 'INSURANCE_COMPANY' | 'TPA' | 'GOVERNMENT_SCHEME' | 'CORPORATE';

export type PolicyStatus = 'ACTIVE' | 'EXPIRED' | 'TERMINATED' | 'PENDING_VERIFICATION' | 'SUSPENDED';

export type PreAuthStatus = 'DRAFT' | 'SUBMITTED' | 'UNDER_REVIEW' | 'APPROVED' | 'REJECTED' | 'EXPIRED' | 'CANCELLED';

export type ClaimStatus =
  | 'DRAFT'
  | 'SUBMITTED'
  | 'PENDING'
  | 'ADDITIONAL_INFO_REQUESTED'
  | 'APPROVED'
  | 'PARTIALLY_APPROVED'
  | 'REJECTED'
  | 'PAID'
  | 'CLOSED'
  | 'APPEALED';

export type ClaimItemStatus = 'PENDING' | 'APPROVED' | 'PARTIALLY_APPROVED' | 'REJECTED' | 'EXCLUDED';

export type SettlementType = 'FULL' | 'PARTIAL' | 'REJECTED_ZERO' | 'OVERPAYMENT';

export type ReconciliationStatus = 'COMPLETED' | 'DISCREPANCY' | 'PENDING_REVIEW';

export interface InsuranceProvider {
  id: string;
  clinic_id: string;
  provider_name: string;
  provider_code: string;
  provider_type: InsuranceProviderType;
  tpa_name?: string | null;
  payer_id?: string | null;
  contact_person?: string | null;
  email?: string | null;
  phone?: string | null;
  portal_url?: string | null;
  notes?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
}

export interface InsuranceProviderDetail extends InsuranceProvider {
  plans: InsurancePlan[];
}

export interface InsurancePlan {
  id: string;
  provider_id: string;
  plan_name: string;
  plan_code: string;
  description?: string | null;
  coverage_percentage: number;
  annual_limit?: number | null;
  lifetime_limit?: number | null;
  deductible: number;
  copay_fixed: number;
  waiting_period_days: number;
  requires_preauth_above?: number | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
  coverage_rules?: InsuranceCoverageRule[];
}

export interface InsuranceCoverageRule {
  id: string;
  plan_id: string;
  procedure_code: string;
  procedure_category?: string | null;
  coverage_status: 'COVERED' | 'PARTIALLY_COVERED' | 'EXCLUDED' | 'PREAUTH_REQUIRED';
  coverage_percentage?: number | null;
  limit_amount?: number | null;
  requires_preauth: boolean;
  waiting_period_days: number;
  notes?: string | null;
  created_at: string;
}

export interface PatientInsurancePolicy {
  id: string;
  clinic_id: string;
  patient_id: string;
  provider_id: string;
  plan_id?: string | null;
  policy_number: string;
  group_number?: string | null;
  member_id: string;
  policy_holder_name?: string | null;
  relationship: string;
  priority: 'PRIMARY' | 'SECONDARY' | 'TERTIARY';
  effective_date: string;
  expiry_date: string;
  status: PolicyStatus;
  verified_at?: string | null;
  verified_by?: string | null;
  verification_notes?: string | null;
  card_front_url?: string | null;
  card_back_url?: string | null;
  created_at: string;
  updated_at: string;
}

export interface InsurancePreAuthorization {
  id: string;
  clinic_id: string;
  patient_id: string;
  policy_id: string;
  treatment_plan_id?: string | null;
  preauth_number?: string | null;
  status: PreAuthStatus;
  requested_amount: number;
  approved_amount?: number | null;
  submission_date?: string | null;
  valid_until?: string | null;
  response_date?: string | null;
  rejection_reason?: string | null;
  denial_code?: string | null;
  clinical_justification?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface InsuranceClaimItem {
  id: string;
  claim_id: string;
  procedure_code: string;
  procedure_name: string;
  tooth_number?: string | null;
  surface?: string | null;
  quantity: number;
  unit_cost: number;
  total_cost: number;
  covered_amount: number;
  patient_responsibility: number;
  insurance_responsibility: number;
  status: ClaimItemStatus;
  denial_reason?: string | null;
  created_at: string;
}

export interface InsuranceClaim {
  id: string;
  clinic_id: string;
  patient_id: string;
  policy_id: string;
  preauth_id?: string | null;
  invoice_id?: string | null;
  claim_number: string;
  status: ClaimStatus;
  submission_date?: string | null;
  adjudication_date?: string | null;
  payment_date?: string | null;
  total_claimed_amount: number;
  approved_amount?: number | null;
  paid_amount?: number | null;
  patient_copay_amount?: number | null;
  patient_coinsurance_amount?: number | null;
  deductible_applied?: number | null;
  denial_code?: string | null;
  denial_reason?: string | null;
  appeal_status?: string | null;
  appeal_date?: string | null;
  tpa_reference_number?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
  items?: InsuranceClaimItem[];
}

export type ClaimDetail = InsuranceClaim;

export interface ClaimItemCreate {
  procedure_code: string;
  procedure_name: string;
  tooth_number?: string | null;
  surface?: string | null;
  quantity?: number;
  unit_cost: number;
  total_cost: number;
  covered_amount?: number;
  patient_responsibility?: number;
  insurance_responsibility?: number;
}

export interface InsurancePaymentReconciliation {
  id: string;
  clinic_id: string;
  claim_id: string;
  invoice_id?: string | null;
  payment_id?: string | null;
  reconciliation_reference: string;
  payment_date: string;
  insurance_settled_amount: number;
  patient_copay_due: number;
  adjustment_amount: number;
  settlement_type: SettlementType;
  status: ReconciliationStatus;
  remittance_advice_url?: string | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
}

export interface InsuranceDashboardStats {
  total_claims_count: number;
  pending_claims_count: number;
  approved_claims_count: number;
  rejected_claims_count: number;
  total_claimed_amount: number;
  total_approved_amount: number;
  total_settled_amount: number;
  total_outstanding_amount: number;
  average_turnaround_days: number;
}

export interface ClaimsReportItem {
  id: string;
  claim_number: string;
  patient_name?: string | null;
  provider_name?: string | null;
  submission_date?: string | null;
  total_claimed_amount: number;
  approved_amount?: number | null;
  paid_amount?: number | null;
  status: string;
}

export interface ClaimsReportResponse {
  claims: ClaimsReportItem[];
  total_claims: number;
  total_claimed_sum: number;
  total_approved_sum: number;
  total_paid_sum: number;
}

export interface ProviderPerformanceItem {
  provider_name: string;
  total_claims: number;
  approved_claims: number;
  rejected_claims: number;
  approval_rate: number;
  average_turnaround_days: number;
  total_settled_amount: number;
}

export interface ProviderPerformanceResponse {
  providers: ProviderPerformanceItem[];
}

export interface AICompletenessAudit {
  claim_id: string;
  completeness_score: number;
  is_audit_passed: boolean;
  missing_requirements: string[];
  recommendations: string[];
  disclaimer: string;
}

export interface AICodingSuggestionItem {
  procedure_description: string;
  suggested_cdt_code: string;
  procedure_name: string;
  category: string;
  confidence: number;
}

export interface AICodingSuggestions {
  suggestions: AICodingSuggestionItem[];
  disclaimer: string;
}

export interface AIRejectionAnalysis {
  claim_id: string;
  denial_code: string;
  denial_reason: string;
  root_cause: string;
  preventative_recommendations: string[];
  suggested_appeal_letter: string;
  appeal_deadline_hint: string;
  disclaimer: string;
}
