export type AIProviderType = "MOCK" | "OPENAI" | "ANTHROPIC" | "OLLAMA" | "AZURE_OPENAI";

export interface AIConfigRead {
  id: string;
  clinic_id: string;
  provider_type: AIProviderType;
  model_name: string;
  api_base_url?: string | null;
  temperature: number;
  max_tokens: number;
  clinical_guardrails_enabled: boolean;
  is_active: boolean;
}

export interface AIConfigUpdate {
  provider_type?: AIProviderType;
  model_name?: string;
  api_base_url?: string | null;
  api_key?: string | null;
  temperature?: number;
  max_tokens?: number;
  clinical_guardrails_enabled?: boolean;
  is_active?: boolean;
}

export type RiskSeverity = "HIGH" | "MEDIUM" | "LOW";

export interface RiskAlert {
  category: string;
  severity: RiskSeverity;
  title: string;
  details: string;
}

export interface PatientSummaryResponse {
  patient_id: string;
  patient_name: string;
  summary_text: string;
  risk_alerts: RiskAlert[];
  previous_treatments_summary: string;
  active_prescriptions_summary: string;
  recommended_recall_months: number;
  missing_documentation_alerts: string[];
  generated_at: string;
}

export interface MissingDocAuditResponse {
  patient_id: string;
  missing_items: string[];
  unbilled_procedures: string[];
  unsigned_consents: string[];
}

export interface SOAPNoteDraft {
  subjective: string;
  objective: string;
  assessment: string;
  plan: string;
  safety_disclaimer: string;
}

export interface SOAPSaveRequest {
  treatment_id: string;
  subjective: string;
  objective: string;
  assessment: string;
  plan: string;
}

export type ClinicalDocType =
  | "REFERRAL_LETTER"
  | "MEDICAL_CERTIFICATE"
  | "POST_OP_INSTRUCTIONS"
  | "DISCHARGE_SUMMARY"
  | "TREATMENT_PLAN_PRESENTATION";

export interface ClinicalDocGenerateRequest {
  patient_id: string;
  document_type: ClinicalDocType;
  treatment_id?: string | null;
  recipient_doctor?: string | null;
  custom_notes?: string | null;
}

export interface ClinicalDocResponse {
  document_type: ClinicalDocType;
  title: string;
  formatted_content: string;
  metadata: Record<string, unknown>;
  disclaimer: string;
}

export interface PrescriptionSuggestionItem {
  medicine_name: string;
  generic_name?: string | null;
  dosage: string;
  frequency: string;
  duration: string;
  instructions: string;
  rationale: string;
}

export interface PrescriptionSuggestResponse {
  suggested_items: PrescriptionSuggestionItem[];
  allergy_warnings: string[];
  interaction_warnings: string[];
  disclaimer: string;
}

export interface TreatmentOption {
  title: string;
  procedure_code?: string | null;
  description: string;
  pros: string[];
  cons: string[];
  estimated_visits: number;
  recall_interval_days: number;
}

export interface TreatmentSuggestionResponse {
  primary_recommendation: TreatmentOption;
  alternative_options: TreatmentOption[];
  rationale: string;
}

export interface UnbilledItemSuggestion {
  item_type: string;
  name: string;
  code: string;
  estimated_amount: number;
  source: string;
}

export interface BillingAuditResponse {
  has_unbilled_items: boolean;
  suggestions: UnbilledItemSuggestion[];
  total_unbilled_estimate: number;
}

export interface SchedulingSlotRecommendation {
  recommended_duration_minutes: number;
  dentist_id?: string | null;
  dentist_name?: string | null;
  suggested_dates: string[];
  reason: string;
}

export type AITaskType =
  | "CLINICAL_SUMMARY"
  | "SOAP_NOTE"
  | "PRESCRIPTION_SUGGEST"
  | "TREATMENT_SUGGEST"
  | "DOCUMENT_GENERATE"
  | "BILLING_AUDIT"
  | "SCHEDULING_RECOMMEND"
  | "INVENTORY_FORECAST"
  | "ANALYTICS_INSIGHTS"
  | "NATURAL_LANGUAGE_SEARCH";

export interface InventoryForecastItem {
  item_id?: string;
  item_name: string;
  sku?: string;
  category: string;
  current_stock: number;
  min_stock_level?: number;
  burn_rate_weekly?: number;
  predicted_burn_rate_weekly?: number;
  projected_depletion_date: string;
  recommended_reorder_qty?: number;
  suggested_reorder_quantity?: number;
  estimated_cost?: number;
  urgency?: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "NORMAL";
  reorder_urgency?: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "NORMAL";
}

export interface NLSearchResult {
  patient_id: string;
  patient_name: string;
  age: number;
  gender: string;
  phone: string;
  conditions: string[];
  match_reason: string;
  last_visit: string;
  pending_procedures: string[];
}

export interface InventoryForecastResponse {
  forecasts: InventoryForecastItem[];
  generated_at: string;
}

export interface AIAnalyticsInsightsResponse {
  executive_summary: string;
  revenue_insights: string;
  chair_utilization_insights: string;
  patient_retention_insights: string;
  key_recommendations: string[];
}

export interface AISearchResultItem {
  entity_type: string;
  id: string;
  title: string;
  subtitle: string;
  detail: string;
  link: string;
}

export interface AISearchResponse {
  parsed_intent: string;
  total_count: number;
  results: AISearchResultItem[];
}

export type AIRecommendationStatus = "PENDING_REVIEW" | "APPROVED" | "REJECTED" | "MODIFIED";

export interface AIRecommendationRead {
  id: string;
  clinic_id: string;
  patient_id: string;
  dentist_id: string;
  recommendation_type: string;
  status: AIRecommendationStatus;
  input_context_json: Record<string, unknown>;
  generated_output_json: Record<string, unknown>;
  reviewed_at?: string | null;
  clinician_feedback?: string | null;
  final_content?: string | null;
  created_at: string;
}

export interface AIAuditLogRead {
  id: string;
  clinic_id: string;
  user_id?: string | null;
  patient_id?: string | null;
  task_type: string;
  provider_type: string;
  model_name: string;
  tokens_prompt: number;
  tokens_completion: number;
  latency_ms: number;
  anonymized_prompt_summary?: string | null;
  response_summary?: string | null;
  safety_flags: string[];
  request_id: string;
  created_at: string;
}
