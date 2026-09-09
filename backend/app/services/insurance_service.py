from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.insurance import ClaimStatus
from app.repositories.insurance_repository import InsuranceRepository
from app.schemas.insurance import (
    ClaimCreate,
    ClaimDetail,
    ClaimRead,
    ClaimsReportResponse,
    ClaimStatusUpdate,
    InsuranceDashboardStats,
    InsurancePlanCreate,
    InsurancePlanRead,
    InsurancePlanUpdate,
    InsuranceProviderCreate,
    InsuranceProviderDetail,
    InsuranceProviderRead,
    InsuranceProviderUpdate,
    PatientInsurancePolicyCreate,
    PatientInsurancePolicyRead,
    PatientInsurancePolicyUpdate,
    PaymentReconciliationCreate,
    PaymentReconciliationRead,
    PolicyVerificationRequest,
    PreAuthCreate,
    PreAuthRead,
    PreAuthStatusUpdate,
    ProviderPerformanceResponse,
)


class InsuranceService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = InsuranceRepository(db)

    # -----------------------------------------------------------------------
    # Providers
    # -----------------------------------------------------------------------
    async def list_providers(
        self, clinic_id: UUID, is_active: bool | None = None, search: str | None = None, limit: int = 50, offset: int = 0
    ) -> list[InsuranceProviderRead]:
        return await self.repo.list_providers(clinic_id, is_active, search, limit, offset)

    async def get_provider(self, clinic_id: UUID, provider_id: UUID) -> InsuranceProviderDetail:
        p = await self.repo.get_provider(clinic_id, provider_id)
        if not p:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insurance provider not found")
        return p

    async def create_provider(
        self, clinic_id: UUID, data: InsuranceProviderCreate, created_by: UUID | None = None
    ) -> InsuranceProviderRead:
        return await self.repo.create_provider(clinic_id, data, created_by)

    async def update_provider(
        self, clinic_id: UUID, provider_id: UUID, data: InsuranceProviderUpdate, updated_by: UUID | None = None
    ) -> InsuranceProviderRead:
        p = await self.repo.update_provider(clinic_id, provider_id, data, updated_by)
        if not p:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insurance provider not found")
        return p

    # -----------------------------------------------------------------------
    # Plans
    # -----------------------------------------------------------------------
    async def list_plans(
        self, clinic_id: UUID, provider_id: UUID | None = None, is_active: bool | None = None, limit: int = 50, offset: int = 0
    ) -> list[InsurancePlanRead]:
        return await self.repo.list_plans(clinic_id, provider_id, is_active, limit, offset)

    async def get_plan(self, clinic_id: UUID, plan_id: UUID) -> InsurancePlanRead:
        pl = await self.repo.get_plan(clinic_id, plan_id)
        if not pl:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insurance plan not found")
        return pl

    async def create_plan(
        self, clinic_id: UUID, data: InsurancePlanCreate, created_by: UUID | None = None
    ) -> InsurancePlanRead:
        # Verify provider exists
        await self.get_provider(clinic_id, data.provider_id)
        return await self.repo.create_plan(clinic_id, data, created_by)

    async def update_plan(
        self, clinic_id: UUID, plan_id: UUID, data: InsurancePlanUpdate, updated_by: UUID | None = None
    ) -> InsurancePlanRead:
        pl = await self.repo.update_plan(clinic_id, plan_id, data, updated_by)
        if not pl:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insurance plan not found")
        return pl

    # -----------------------------------------------------------------------
    # Coverage Calculation Logic
    # -----------------------------------------------------------------------
    async def calculate_procedure_coverage(
        self,
        clinic_id: UUID,
        plan_id: UUID,
        procedure_cost: float,
        procedure_code: str,
    ) -> tuple[float, float, float]:
        """Calculates covered amount, patient responsibility, and insurance responsibility based on plan rules."""
        plan = await self.get_plan(clinic_id, plan_id)
        rules = await self.repo.list_coverage_rules(clinic_id, plan_id)

        # Check for specific procedure rule
        matching_rule = next((r for r in rules if r.procedure_code == procedure_code), None)
        coverage_pct = float(matching_rule.coverage_percentage) if matching_rule else float(plan.coverage_percentage)

        covered_amt = round(procedure_cost * (coverage_pct / 100.0), 2)
        ins_resp = min(covered_amt, float(plan.annual_limit))
        patient_resp = round(procedure_cost - ins_resp, 2)

        return covered_amt, patient_resp, ins_resp

    # -----------------------------------------------------------------------
    # Policies
    # -----------------------------------------------------------------------
    async def list_patient_policies(
        self, clinic_id: UUID, patient_id: UUID | None = None, status: str | None = None, limit: int = 50, offset: int = 0
    ) -> list[PatientInsurancePolicyRead]:
        return await self.repo.list_patient_policies(clinic_id, patient_id, status, limit, offset)  # type: ignore

    async def get_policy(self, clinic_id: UUID, policy_id: UUID) -> PatientInsurancePolicyRead:
        pol = await self.repo.get_policy(clinic_id, policy_id)
        if not pol:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient policy not found")
        return pol

    async def create_policy(
        self, clinic_id: UUID, data: PatientInsurancePolicyCreate, created_by: UUID | None = None
    ) -> PatientInsurancePolicyRead:
        return await self.repo.create_policy(clinic_id, data, created_by)

    async def update_policy(
        self, clinic_id: UUID, policy_id: UUID, data: PatientInsurancePolicyUpdate, updated_by: UUID | None = None
    ) -> PatientInsurancePolicyRead:
        pol = await self.repo.update_policy(clinic_id, policy_id, data, updated_by)
        if not pol:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient policy not found")
        return pol

    async def verify_policy(
        self, clinic_id: UUID, policy_id: UUID, data: PolicyVerificationRequest
    ) -> PatientInsurancePolicyRead:
        pol = await self.repo.verify_policy(clinic_id, policy_id, data.verified_by, data.notes)
        if not pol:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient policy not found")
        return pol

    # -----------------------------------------------------------------------
    # Pre-Authorizations
    # -----------------------------------------------------------------------
    async def list_preauths(
        self, clinic_id: UUID, patient_id: UUID | None = None, status: str | None = None, limit: int = 50, offset: int = 0
    ) -> list[PreAuthRead]:
        return await self.repo.list_preauths(clinic_id, patient_id, status, limit, offset)  # type: ignore

    async def get_preauth(self, clinic_id: UUID, preauth_id: UUID) -> PreAuthRead:
        pa = await self.repo.get_preauth(clinic_id, preauth_id)
        if not pa:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pre-authorization not found")
        return pa

    async def create_preauth(
        self, clinic_id: UUID, data: PreAuthCreate, created_by: UUID | None = None
    ) -> PreAuthRead:
        return await self.repo.create_preauth(clinic_id, data, created_by)

    async def update_preauth_status(
        self, clinic_id: UUID, preauth_id: UUID, data: PreAuthStatusUpdate, updated_by: UUID | None = None
    ) -> PreAuthRead:
        pa = await self.repo.update_preauth_status(clinic_id, preauth_id, data, updated_by)
        if not pa:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pre-authorization not found")
        return pa

    # -----------------------------------------------------------------------
    # Claims
    # -----------------------------------------------------------------------
    async def list_claims(
        self,
        clinic_id: UUID,
        patient_id: UUID | None = None,
        status: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ClaimRead]:
        return await self.repo.list_claims(clinic_id, patient_id, status, search, limit, offset)  # type: ignore

    async def get_claim(self, clinic_id: UUID, claim_id: UUID) -> ClaimDetail:
        c = await self.repo.get_claim_detail(clinic_id, claim_id)
        if not c:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insurance claim not found")
        return c

    async def create_claim(
        self, clinic_id: UUID, data: ClaimCreate, created_by: UUID | None = None
    ) -> ClaimDetail:
        return await self.repo.create_claim(clinic_id, data, created_by)

    async def update_claim_status(
        self, clinic_id: UUID, claim_id: UUID, data: ClaimStatusUpdate, updated_by: UUID | None = None
    ) -> ClaimDetail:
        # Validate state machine
        current = await self.get_claim(clinic_id, claim_id)
        valid_transitions = {
            ClaimStatus.DRAFT: [ClaimStatus.SUBMITTED, ClaimStatus.REJECTED],
            ClaimStatus.SUBMITTED: [ClaimStatus.PENDING, ClaimStatus.ADDITIONAL_INFO_REQUESTED, ClaimStatus.APPROVED, ClaimStatus.REJECTED],
            ClaimStatus.PENDING: [ClaimStatus.ADDITIONAL_INFO_REQUESTED, ClaimStatus.APPROVED, ClaimStatus.PARTIALLY_APPROVED, ClaimStatus.REJECTED],
            ClaimStatus.ADDITIONAL_INFO_REQUESTED: [ClaimStatus.SUBMITTED, ClaimStatus.PENDING, ClaimStatus.REJECTED],
            ClaimStatus.APPROVED: [ClaimStatus.PAID, ClaimStatus.CLOSED],
            ClaimStatus.PARTIALLY_APPROVED: [ClaimStatus.PAID, ClaimStatus.CLOSED],
            ClaimStatus.REJECTED: [ClaimStatus.DRAFT, ClaimStatus.CLOSED],
            ClaimStatus.PAID: [ClaimStatus.CLOSED],
            ClaimStatus.CLOSED: [],
        }

        allowed = valid_transitions.get(current.status, [])
        if data.status not in allowed and data.status != current.status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid claim status transition from {current.status} to {data.status}. Allowed: {allowed}",
            )

        updated = await self.repo.update_claim_status(clinic_id, claim_id, data, updated_by)
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insurance claim not found")
        return updated

    # -----------------------------------------------------------------------
    # Reconciliations
    # -----------------------------------------------------------------------
    async def list_reconciliations(
        self, clinic_id: UUID, claim_id: UUID | None = None, limit: int = 50, offset: int = 0
    ) -> list[PaymentReconciliationRead]:
        return await self.repo.list_reconciliations(clinic_id, claim_id, limit, offset)

    async def create_reconciliation(
        self, clinic_id: UUID, data: PaymentReconciliationCreate, created_by: UUID | None = None
    ) -> PaymentReconciliationRead:
        return await self.repo.create_reconciliation(clinic_id, data, created_by)

    # -----------------------------------------------------------------------
    # Dashboard & Reports
    # -----------------------------------------------------------------------
    async def get_dashboard_stats(self, clinic_id: UUID) -> InsuranceDashboardStats:
        return await self.repo.get_dashboard_stats(clinic_id)

    async def generate_claims_report(
        self, clinic_id: UUID, start_date: date | None = None, end_date: date | None = None, status: str | None = None
    ) -> ClaimsReportResponse:
        return await self.repo.generate_claims_report(clinic_id, start_date, end_date, status)  # type: ignore

    async def generate_provider_performance_report(self, clinic_id: UUID) -> ProviderPerformanceResponse:
        return await self.repo.generate_provider_performance_report(clinic_id)
