from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enterprise import (
    AnnouncementScope,
    AnnouncementType,
    InventoryTransferStatus,
    PatientSharingMode,
    TransferStatus,
)


# ---------------------------------------------------------------------------
# Base Schema Configuration
# ---------------------------------------------------------------------------
class EnterpriseBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Organization Schemas
# ---------------------------------------------------------------------------
class OrganizationBase(EnterpriseBaseSchema):
    name: str = Field(..., min_length=2, max_length=160)
    code: str = Field(..., min_length=2, max_length=40)
    tax_id: str | None = Field(default=None, max_length=80)
    legal_name: str | None = Field(default=None, max_length=200)
    subscription_tier: str = Field(default="ENTERPRISE", max_length=40)
    logo_url: str | None = Field(default=None, max_length=255)
    theme_color: str = Field(default="#0d9488", max_length=40)
    primary_email: str = Field(..., max_length=255)
    phone: str | None = Field(default=None, max_length=32)
    website: str | None = Field(default=None, max_length=255)
    patient_sharing_mode: PatientSharingMode = PatientSharingMode.SHARED
    settings_json: str | None = None


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(EnterpriseBaseSchema):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    tax_id: str | None = None
    legal_name: str | None = None
    subscription_tier: str | None = None
    is_active: bool | None = None
    logo_url: str | None = None
    theme_color: str | None = None
    primary_email: str | None = None
    phone: str | None = None
    website: str | None = None
    patient_sharing_mode: PatientSharingMode | None = None
    settings_json: str | None = None


class OrganizationResponse(OrganizationBase):
    id: UUID
    slug: str
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Region Schemas
# ---------------------------------------------------------------------------
class RegionBase(EnterpriseBaseSchema):
    name: str = Field(..., min_length=2, max_length=120)
    code: str = Field(..., min_length=2, max_length=40)
    regional_manager_id: UUID | None = None
    description: str | None = None


class RegionCreate(RegionBase):
    organization_id: UUID


class RegionUpdate(EnterpriseBaseSchema):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    code: str | None = None
    regional_manager_id: UUID | None = None
    description: str | None = None
    is_active: bool | None = None


class RegionResponse(RegionBase):
    id: UUID
    organization_id: UUID
    is_active: bool = True
    branch_count: int = 0
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Branch (Clinic) Enterprise Extension Schemas
# ---------------------------------------------------------------------------
class BranchCreate(EnterpriseBaseSchema):
    organization_id: UUID
    region_id: UUID | None = None
    name: str = Field(..., min_length=2, max_length=160)
    branch_code: str = Field(..., min_length=2, max_length=40)
    email: str = Field(..., max_length=255)
    phone: str | None = Field(default=None, max_length=32)
    timezone: str = Field(default="Asia/Kolkata", max_length=64)
    address: str | None = None
    working_hours: str | None = None
    currency: str = Field(default="INR", max_length=10)
    tax_configuration: str | None = None
    is_main_branch: bool = False


class BranchUpdate(EnterpriseBaseSchema):
    region_id: UUID | None = None
    name: str | None = Field(default=None, min_length=2, max_length=160)
    branch_code: str | None = None
    email: str | None = None
    phone: str | None = None
    timezone: str | None = None
    address: str | None = None
    working_hours: str | None = None
    currency: str | None = None
    tax_configuration: str | None = None
    is_main_branch: bool | None = None
    is_active: bool | None = None


class BranchResponse(EnterpriseBaseSchema):
    id: UUID
    organization_id: UUID | None = None
    region_id: UUID | None = None
    name: str
    slug: str
    branch_code: str | None = None
    email: str
    phone: str | None = None
    timezone: str
    address: str | None = None
    working_hours: str | None = None
    currency: str = "INR"
    tax_configuration: str | None = None
    is_main_branch: bool = False
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Department Schemas
# ---------------------------------------------------------------------------
class DepartmentBase(EnterpriseBaseSchema):
    name: str = Field(..., min_length=2, max_length=120)
    code: str = Field(..., min_length=2, max_length=40)
    head_dentist_id: UUID | None = None
    description: str | None = None


class DepartmentCreate(DepartmentBase):
    clinic_id: UUID


class DepartmentUpdate(EnterpriseBaseSchema):
    name: str | None = None
    code: str | None = None
    head_dentist_id: UUID | None = None
    description: str | None = None
    is_active: bool | None = None


class DepartmentResponse(DepartmentBase):
    id: UUID
    clinic_id: UUID
    is_active: bool = True
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Enterprise Roles & Permissions Schemas
# ---------------------------------------------------------------------------
class EnterprisePermissionResponse(EnterpriseBaseSchema):
    id: UUID
    permission_key: str
    module: str
    description: str | None = None


class EnterpriseRoleBase(EnterpriseBaseSchema):
    role_key: str = Field(..., min_length=2, max_length=60)
    name: str = Field(..., min_length=2, max_length=100)
    description: str | None = None


class EnterpriseRoleCreate(EnterpriseRoleBase):
    organization_id: UUID | None = None
    permission_ids: list[UUID] = []


class EnterpriseRoleUpdate(EnterpriseBaseSchema):
    name: str | None = None
    description: str | None = None
    permission_ids: list[UUID] | None = None


class EnterpriseRoleResponse(EnterpriseRoleBase):
    id: UUID
    organization_id: UUID | None = None
    is_system: bool = False
    permissions: list[EnterprisePermissionResponse] = []
    created_at: datetime
    updated_at: datetime


class RolePermissionAssignRequest(EnterpriseBaseSchema):
    permission_ids: list[UUID]


class UserBranchAssignmentCreate(EnterpriseBaseSchema):
    user_id: UUID
    clinic_id: UUID
    role_override: str | None = None
    is_primary: bool = False
    working_days_json: str | None = None


class UserBranchAssignmentResponse(EnterpriseBaseSchema):
    id: UUID
    user_id: UUID
    clinic_id: UUID
    role_override: str | None = None
    is_primary: bool = False
    working_days_json: str | None = None
    is_active: bool = True
    created_at: datetime


class UserPermissionOverrideCreate(EnterpriseBaseSchema):
    user_id: UUID
    permission_id: UUID
    is_granted: bool


class UserPermissionOverrideResponse(EnterpriseBaseSchema):
    user_id: UUID
    permission_id: UUID
    permission_key: str
    is_granted: bool


class EffectiveUserPermissionsResponse(EnterpriseBaseSchema):
    user_id: UUID
    roles: list[str]
    assigned_clinics: list[UUID]
    permissions: list[str]


# ---------------------------------------------------------------------------
# Cross-Branch Patient Transfer & Merge Schemas
# ---------------------------------------------------------------------------
class PatientTransferCreate(EnterpriseBaseSchema):
    patient_id: UUID
    from_clinic_id: UUID
    to_clinic_id: UUID
    transfer_reason: str
    records_included_json: str | None = None
    notes: str | None = None


class PatientTransferActionRequest(EnterpriseBaseSchema):
    status: TransferStatus  # APPROVED or REJECTED
    notes: str | None = None


class PatientTransferResponse(EnterpriseBaseSchema):
    id: UUID
    organization_id: UUID
    patient_id: UUID
    patient_name: str | None = None
    from_clinic_id: UUID
    from_clinic_name: str | None = None
    to_clinic_id: UUID
    to_clinic_name: str | None = None
    initiated_by: UUID | None = None
    approved_by: UUID | None = None
    status: TransferStatus
    transfer_reason: str
    records_included_json: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class PatientMergeRequest(EnterpriseBaseSchema):
    primary_patient_id: UUID
    duplicate_patient_id: UUID
    merge_reason: str | None = None


class PatientMergeResponse(EnterpriseBaseSchema):
    id: UUID
    organization_id: UUID
    primary_patient_id: UUID
    duplicate_patient_id: UUID
    merged_by: UUID | None = None
    merge_reason: str | None = None
    records_migrated: dict[str, int] = {}
    created_at: datetime


class DuplicatePatientMatch(EnterpriseBaseSchema):
    patient_id: UUID
    clinic_id: UUID
    clinic_name: str | None = None
    full_name: str
    phone: str
    email: str | None = None
    date_of_birth: str | None = None
    similarity_score: float
    matched_fields: list[str]


# ---------------------------------------------------------------------------
# Inter-Branch Inventory Transfer Schemas
# ---------------------------------------------------------------------------
class InventoryTransferCreate(EnterpriseBaseSchema):
    from_clinic_id: UUID
    to_clinic_id: UUID
    item_id: UUID
    quantity: int = Field(..., gt=0)
    tracking_number: str | None = None
    notes: str | None = None


class InventoryTransferStatusUpdateRequest(EnterpriseBaseSchema):
    status: InventoryTransferStatus
    tracking_number: str | None = None
    notes: str | None = None


class InventoryTransferResponse(EnterpriseBaseSchema):
    id: UUID
    organization_id: UUID
    transfer_number: str
    from_clinic_id: UUID
    from_clinic_name: str | None = None
    to_clinic_id: UUID
    to_clinic_name: str | None = None
    item_id: UUID
    item_name: str | None = None
    quantity: int
    unit_cost: float = 0.0
    status: InventoryTransferStatus
    dispatched_at: datetime | None = None
    dispatched_by: UUID | None = None
    received_at: datetime | None = None
    received_by: UUID | None = None
    tracking_number: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class ConsolidatedInventoryItem(EnterpriseBaseSchema):
    item_id: UUID
    item_name: str
    category: str
    unit_of_measure: str
    total_stock: int
    total_valuation: float
    clinic_breakdown: list[dict[str, object]]


# ---------------------------------------------------------------------------
# Consolidated Financials Schemas
# ---------------------------------------------------------------------------
class BranchFinancialSummary(EnterpriseBaseSchema):
    clinic_id: UUID
    clinic_name: str
    total_invoiced: float
    total_collected: float
    insurance_collected: float
    outstanding_balance: float
    tax_amount: float
    invoice_count: int


class RegionFinancialSummary(EnterpriseBaseSchema):
    region_id: UUID
    region_name: str
    total_invoiced: float
    total_collected: float
    outstanding_balance: float
    branches: list[BranchFinancialSummary] = []


class ConsolidatedFinancialsResponse(EnterpriseBaseSchema):
    organization_id: UUID
    currency: str
    total_revenue: float
    total_collected: float
    total_outstanding: float
    total_insurance_settled: float
    total_tax: float
    branch_summaries: list[BranchFinancialSummary] = []
    region_summaries: list[RegionFinancialSummary] = []


# ---------------------------------------------------------------------------
# Enterprise Announcements & Audit Logs
# ---------------------------------------------------------------------------
class EnterpriseAnnouncementCreate(EnterpriseBaseSchema):
    title: str = Field(..., min_length=2, max_length=200)
    message: str
    announcement_type: AnnouncementType = AnnouncementType.BROADCAST
    target_scope: AnnouncementScope = AnnouncementScope.ALL
    target_id: UUID | None = None
    expires_at: datetime | None = None


class EnterpriseAnnouncementUpdate(EnterpriseBaseSchema):
    title: str | None = None
    message: str | None = None
    announcement_type: AnnouncementType | None = None
    target_scope: AnnouncementScope | None = None
    target_id: UUID | None = None
    is_active: bool | None = None
    expires_at: datetime | None = None


class EnterpriseAnnouncementResponse(EnterpriseBaseSchema):
    id: UUID
    organization_id: UUID
    title: str
    message: str
    announcement_type: AnnouncementType
    target_scope: AnnouncementScope
    target_id: UUID | None = None
    is_active: bool = True
    expires_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class EnterpriseAuditLogResponse(EnterpriseBaseSchema):
    id: UUID
    organization_id: UUID
    clinic_id: UUID | None = None
    actor_id: UUID | None = None
    action: str
    resource_type: str
    resource_id: str | None = None
    details_json: str | None = None
    ip_address: str | None = None
    created_at: datetime


# ---------------------------------------------------------------------------
# AI Enterprise Analytics Schemas
# ---------------------------------------------------------------------------
class BranchBenchmarkScore(EnterpriseBaseSchema):
    clinic_id: UUID
    clinic_name: str
    overall_score: float = Field(..., ge=0, le=100)
    revenue_score: float = Field(..., ge=0, le=100)
    occupancy_score: float = Field(..., ge=0, le=100)
    patient_satisfaction_score: float = Field(..., ge=0, le=100)
    collection_rate_score: float = Field(..., ge=0, le=100)
    rank: int
    recommendations: list[str] = []


class StaffProductivityMetric(EnterpriseBaseSchema):
    staff_id: UUID
    staff_name: str
    role: str
    branch_name: str
    appointments_completed: int
    revenue_generated: float
    utilization_rate: float
    chairside_hours: float


class RevenueForecastItem(EnterpriseBaseSchema):
    period: str  # Month or Quarter
    forecast_revenue: float
    confidence_lower: float
    confidence_upper: float
    growth_rate_percentage: float


class EnterpriseAIAnalyticsResponse(EnterpriseBaseSchema):
    organization_id: UUID
    generated_at: datetime
    benchmark_scores: list[BranchBenchmarkScore] = []
    top_performing_branches: list[str] = []
    underperforming_branches: list[str] = []
    staff_productivity: list[StaffProductivityMetric] = []
    revenue_forecasts: list[RevenueForecastItem] = []
    network_health_summary: str
    strategic_recommendations: list[str] = []
