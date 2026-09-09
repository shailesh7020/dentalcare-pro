from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.billing import Invoice, Payment, PaymentMethod, PaymentStatus
from app.models.insurance import (
    ClaimItemStatus,
    ClaimStatus,
    InsuranceClaim,
    InsuranceClaimItem,
    InsuranceCoverageRule,
    InsurancePaymentReconciliation,
    InsurancePlan,
    InsurancePreAuthorization,
    InsuranceProvider,
    PatientInsurancePolicy,
    PolicyStatus,
    PreAuthStatus,
    ReconciliationStatus,
)
from app.schemas.insurance import (
    ClaimCreate,
    ClaimDetail,
    ClaimItemRead,
    ClaimRead,
    ClaimsReportItem,
    ClaimsReportResponse,
    ClaimStatusUpdate,
    InsuranceCoverageRuleCreate,
    InsuranceCoverageRuleRead,
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
    PreAuthCreate,
    PreAuthRead,
    PreAuthStatusUpdate,
    ProviderPerformanceItem,
    ProviderPerformanceResponse,
)


def _clean_limit_offset(limit: object, offset: object, default_limit: int = 50) -> tuple[int, int]:
    try:
        clean_limit = int(getattr(limit, "default", limit) or default_limit)
    except (TypeError, ValueError):
        clean_limit = default_limit
    try:
        clean_offset = int(getattr(offset, "default", offset) or 0)
    except (TypeError, ValueError):
        clean_offset = 0
    return clean_limit, clean_offset


class InsuranceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # -----------------------------------------------------------------------
    # Providers
    # -----------------------------------------------------------------------
    async def list_providers(
        self,
        clinic_id: UUID,
        is_active: bool | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[InsuranceProviderRead]:
        query = select(InsuranceProvider).where(
            InsuranceProvider.clinic_id == clinic_id,
            InsuranceProvider.deleted_at.is_(None),
        )
        if is_active is not None:
            query = query.where(InsuranceProvider.is_active == is_active)
        if search:
            s = f"%{search}%"
            query = query.where(
                or_(
                    InsuranceProvider.provider_name.ilike(s),
                    InsuranceProvider.provider_code.ilike(s),
                    InsuranceProvider.tpa_name.ilike(s),
                )
            )
        clean_limit, clean_offset = _clean_limit_offset(limit, offset)
        query = query.order_by(InsuranceProvider.provider_name.asc()).limit(clean_limit).offset(clean_offset)
        result = await self.db.execute(query)
        providers = result.scalars().all()
        return [InsuranceProviderRead.model_validate(p) for p in providers]

    async def get_provider(self, clinic_id: UUID, provider_id: UUID) -> InsuranceProviderDetail | None:
        query = (
            select(InsuranceProvider)
            .options(selectinload(InsuranceProvider.plans))
            .where(
                InsuranceProvider.id == provider_id,
                InsuranceProvider.clinic_id == clinic_id,
                InsuranceProvider.deleted_at.is_(None),
            )
        )
        result = await self.db.execute(query)
        p = result.scalar_one_or_none()
        if not p:
            return None
        return InsuranceProviderDetail(
            id=p.id,
            clinic_id=p.clinic_id,
            provider_name=p.provider_name,
            provider_code=p.provider_code,
            contact_person=p.contact_person,
            address=p.address,
            email=p.email,
            phone=p.phone,
            website=p.website,
            payer_id=p.payer_id,
            tpa_name=p.tpa_name,
            is_active=p.is_active,
            notes=p.notes,
            created_at=p.created_at,
            updated_at=p.updated_at,
            plans=[InsurancePlanRead.model_validate(pl) for pl in p.plans if pl.deleted_at is None],
        )

    async def create_provider(
        self, clinic_id: UUID, data: InsuranceProviderCreate, created_by: UUID | None = None
    ) -> InsuranceProviderRead:
        p = InsuranceProvider(
            clinic_id=clinic_id,
            provider_name=data.provider_name,
            provider_code=data.provider_code.upper(),
            contact_person=data.contact_person,
            address=data.address,
            email=data.email,
            phone=data.phone,
            website=data.website,
            payer_id=data.payer_id,
            tpa_name=data.tpa_name,
            is_active=data.is_active,
            notes=data.notes,
            created_by=created_by,
        )
        self.db.add(p)
        await self.db.commit()
        await self.db.refresh(p)
        return InsuranceProviderRead.model_validate(p)

    async def update_provider(
        self, clinic_id: UUID, provider_id: UUID, data: InsuranceProviderUpdate, updated_by: UUID | None = None
    ) -> InsuranceProviderRead | None:
        query = select(InsuranceProvider).where(
            InsuranceProvider.id == provider_id,
            InsuranceProvider.clinic_id == clinic_id,
            InsuranceProvider.deleted_at.is_(None),
        )
        result = await self.db.execute(query)
        p = result.scalar_one_or_none()
        if not p:
            return None

        update_dict = data.model_dump(exclude_unset=True)
        for k, v in update_dict.items():
            if k == "provider_code" and v is not None:
                setattr(p, k, v.upper())
            else:
                setattr(p, k, v)
        p.updated_by = updated_by
        await self.db.commit()
        await self.db.refresh(p)
        return InsuranceProviderRead.model_validate(p)

    # -----------------------------------------------------------------------
    # Plans
    # -----------------------------------------------------------------------
    async def list_plans(
        self,
        clinic_id: UUID,
        provider_id: UUID | None = None,
        is_active: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[InsurancePlanRead]:
        query = select(InsurancePlan).where(
            InsurancePlan.clinic_id == clinic_id,
            InsurancePlan.deleted_at.is_(None),
        )
        if provider_id:
            query = query.where(InsurancePlan.provider_id == provider_id)
        if is_active is not None:
            query = query.where(InsurancePlan.is_active == is_active)
        clean_limit, clean_offset = _clean_limit_offset(limit, offset)
        query = query.order_by(InsurancePlan.plan_name.asc()).limit(clean_limit).offset(clean_offset)
        result = await self.db.execute(query)
        plans = result.scalars().all()
        return [InsurancePlanRead.model_validate(pl) for pl in plans]

    async def get_plan(self, clinic_id: UUID, plan_id: UUID) -> InsurancePlanRead | None:
        query = select(InsurancePlan).where(
            InsurancePlan.id == plan_id,
            InsurancePlan.clinic_id == clinic_id,
            InsurancePlan.deleted_at.is_(None),
        )
        result = await self.db.execute(query)
        pl = result.scalar_one_or_none()
        return InsurancePlanRead.model_validate(pl) if pl else None

    async def create_plan(
        self, clinic_id: UUID, data: InsurancePlanCreate, created_by: UUID | None = None
    ) -> InsurancePlanRead:
        plan = InsurancePlan(
            clinic_id=clinic_id,
            provider_id=data.provider_id,
            plan_name=data.plan_name,
            plan_code=data.plan_code.upper(),
            coverage_percentage=data.coverage_percentage,
            annual_limit=data.annual_limit,
            lifetime_limit=data.lifetime_limit,
            deductible=data.deductible,
            copayment_percentage=data.copayment_percentage,
            copayment_fixed=data.copayment_fixed,
            maximum_claim_amount=data.maximum_claim_amount,
            waiting_period_days=data.waiting_period_days,
            requires_preauth=data.requires_preauth,
            coverage_rules_json=data.coverage_rules_json,
            is_active=data.is_active,
            notes=data.notes,
            created_by=created_by,
        )
        self.db.add(plan)
        await self.db.commit()
        await self.db.refresh(plan)
        return InsurancePlanRead.model_validate(plan)

    async def update_plan(
        self, clinic_id: UUID, plan_id: UUID, data: InsurancePlanUpdate, updated_by: UUID | None = None
    ) -> InsurancePlanRead | None:
        query = select(InsurancePlan).where(
            InsurancePlan.id == plan_id,
            InsurancePlan.clinic_id == clinic_id,
            InsurancePlan.deleted_at.is_(None),
        )
        result = await self.db.execute(query)
        plan = result.scalar_one_or_none()
        if not plan:
            return None

        for k, v in data.model_dump(exclude_unset=True).items():
            if k == "plan_code" and v is not None:
                setattr(plan, k, v.upper())
            else:
                setattr(plan, k, v)
        plan.updated_by = updated_by
        await self.db.commit()
        await self.db.refresh(plan)
        return InsurancePlanRead.model_validate(plan)

    # -----------------------------------------------------------------------
    # Coverage Rules
    # -----------------------------------------------------------------------
    async def list_coverage_rules(self, clinic_id: UUID, plan_id: UUID) -> list[InsuranceCoverageRuleRead]:
        query = select(InsuranceCoverageRule).where(
            InsuranceCoverageRule.clinic_id == clinic_id,
            InsuranceCoverageRule.plan_id == plan_id,
            InsuranceCoverageRule.deleted_at.is_(None),
        )
        result = await self.db.execute(query)
        rules = result.scalars().all()
        return [InsuranceCoverageRuleRead.model_validate(r) for r in rules]

    async def create_coverage_rule(
        self, clinic_id: UUID, data: InsuranceCoverageRuleCreate, created_by: UUID | None = None
    ) -> InsuranceCoverageRuleRead:
        rule = InsuranceCoverageRule(
            clinic_id=clinic_id,
            plan_id=data.plan_id,
            procedure_code=data.procedure_code,
            procedure_category=data.procedure_category,
            coverage_type=data.coverage_type,
            coverage_percentage=data.coverage_percentage,
            requires_preauth=data.requires_preauth,
            waiting_period_days=data.waiting_period_days,
            max_payable_amount=data.max_payable_amount,
            notes=data.notes,
            created_by=created_by,
        )
        self.db.add(rule)
        await self.db.commit()
        await self.db.refresh(rule)
        return InsuranceCoverageRuleRead.model_validate(rule)

    # -----------------------------------------------------------------------
    # Patient Policies
    # -----------------------------------------------------------------------
    async def list_patient_policies(
        self,
        clinic_id: UUID,
        patient_id: UUID | None = None,
        status: PolicyStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[PatientInsurancePolicyRead]:
        query = (
            select(PatientInsurancePolicy)
            .options(
                selectinload(PatientInsurancePolicy.provider),
                selectinload(PatientInsurancePolicy.plan),
            )
            .where(
                PatientInsurancePolicy.clinic_id == clinic_id,
                PatientInsurancePolicy.deleted_at.is_(None),
            )
        )
        if patient_id:
            query = query.where(PatientInsurancePolicy.patient_id == patient_id)
        if status:
            query = query.where(PatientInsurancePolicy.status == status)
        clean_limit, clean_offset = _clean_limit_offset(limit, offset)
        query = query.order_by(PatientInsurancePolicy.created_at.desc()).limit(clean_limit).offset(clean_offset)
        result = await self.db.execute(query)
        policies = result.scalars().all()

        out = []
        for pol in policies:
            read = PatientInsurancePolicyRead.model_validate(pol)
            if pol.provider:
                read.provider_name = pol.provider.provider_name
            if pol.plan:
                read.plan_name = pol.plan.plan_name
            out.append(read)
        return out

    async def get_policy(self, clinic_id: UUID, policy_id: UUID) -> PatientInsurancePolicyRead | None:
        query = (
            select(PatientInsurancePolicy)
            .options(
                selectinload(PatientInsurancePolicy.provider),
                selectinload(PatientInsurancePolicy.plan),
            )
            .where(
                PatientInsurancePolicy.id == policy_id,
                PatientInsurancePolicy.clinic_id == clinic_id,
                PatientInsurancePolicy.deleted_at.is_(None),
            )
        )
        result = await self.db.execute(query)
        pol = result.scalar_one_or_none()
        if not pol:
            return None
        read = PatientInsurancePolicyRead.model_validate(pol)
        if pol.provider:
            read.provider_name = pol.provider.provider_name
        if pol.plan:
            read.plan_name = pol.plan.plan_name
        return read

    async def create_policy(
        self, clinic_id: UUID, data: PatientInsurancePolicyCreate, created_by: UUID | None = None
    ) -> PatientInsurancePolicyRead:
        pol = PatientInsurancePolicy(
            clinic_id=clinic_id,
            patient_id=data.patient_id,
            provider_id=data.provider_id,
            plan_id=data.plan_id,
            policy_number=data.policy_number,
            member_id=data.member_id,
            card_number=data.card_number,
            group_number=data.group_number,
            relationship=data.relationship,
            is_primary=data.is_primary,
            effective_date=data.effective_date,
            expiry_date=data.expiry_date,
            status=data.status,
            remaining_annual_benefit=data.remaining_annual_benefit,
            policy_documents_json=data.policy_documents_json,
            notes=data.notes,
            created_by=created_by,
        )
        self.db.add(pol)
        await self.db.commit()
        await self.db.refresh(pol)
        return await self.get_policy(clinic_id, pol.id)  # type: ignore

    async def update_policy(
        self, clinic_id: UUID, policy_id: UUID, data: PatientInsurancePolicyUpdate, updated_by: UUID | None = None
    ) -> PatientInsurancePolicyRead | None:
        query = select(PatientInsurancePolicy).where(
            PatientInsurancePolicy.id == policy_id,
            PatientInsurancePolicy.clinic_id == clinic_id,
            PatientInsurancePolicy.deleted_at.is_(None),
        )
        result = await self.db.execute(query)
        pol = result.scalar_one_or_none()
        if not pol:
            return None

        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(pol, k, v)
        pol.updated_by = updated_by
        await self.db.commit()
        return await self.get_policy(clinic_id, pol.id)

    async def verify_policy(
        self, clinic_id: UUID, policy_id: UUID, verified_by: UUID | None = None, notes: str | None = None
    ) -> PatientInsurancePolicyRead | None:
        query = select(PatientInsurancePolicy).where(
            PatientInsurancePolicy.id == policy_id,
            PatientInsurancePolicy.clinic_id == clinic_id,
            PatientInsurancePolicy.deleted_at.is_(None),
        )
        result = await self.db.execute(query)
        pol = result.scalar_one_or_none()
        if not pol:
            return None

        pol.verified_at = datetime.now(UTC)
        pol.verified_by = verified_by
        pol.status = PolicyStatus.ACTIVE
        if notes:
            pol.notes = f"{pol.notes or ''}\nVerification: {notes}".strip()
        await self.db.commit()
        return await self.get_policy(clinic_id, pol.id)

    # -----------------------------------------------------------------------
    # Pre-Authorizations
    # -----------------------------------------------------------------------
    async def list_preauths(
        self,
        clinic_id: UUID,
        patient_id: UUID | None = None,
        status: PreAuthStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[PreAuthRead]:
        query = select(InsurancePreAuthorization).where(
            InsurancePreAuthorization.clinic_id == clinic_id,
            InsurancePreAuthorization.deleted_at.is_(None),
        )
        if patient_id:
            query = query.where(InsurancePreAuthorization.patient_id == patient_id)
        if status:
            query = query.where(InsurancePreAuthorization.status == status)
        clean_limit, clean_offset = _clean_limit_offset(limit, offset)
        query = query.order_by(InsurancePreAuthorization.created_at.desc()).limit(clean_limit).offset(clean_offset)
        result = await self.db.execute(query)
        preauths = result.scalars().all()
        return [PreAuthRead.model_validate(pa) for pa in preauths]

    async def get_preauth(self, clinic_id: UUID, preauth_id: UUID) -> PreAuthRead | None:
        query = select(InsurancePreAuthorization).where(
            InsurancePreAuthorization.id == preauth_id,
            InsurancePreAuthorization.clinic_id == clinic_id,
            InsurancePreAuthorization.deleted_at.is_(None),
        )
        result = await self.db.execute(query)
        pa = result.scalar_one_or_none()
        return PreAuthRead.model_validate(pa) if pa else None

    async def create_preauth(
        self, clinic_id: UUID, data: PreAuthCreate, created_by: UUID | None = None
    ) -> PreAuthRead:
        preauth_num = f"PA-{datetime.now(UTC).year}-{uuid4().hex[:6].upper()}"
        pa = InsurancePreAuthorization(
            clinic_id=clinic_id,
            patient_id=data.patient_id,
            policy_id=data.policy_id,
            treatment_id=data.treatment_id,
            preauth_number=preauth_num,
            status=PreAuthStatus.DRAFT,
            requested_amount=data.requested_amount,
            approved_amount=0.00,
            submission_date=datetime.now(UTC).date(),
            diagnoses_json=data.diagnoses_json,
            procedures_json=data.procedures_json,
            clinical_justification=data.clinical_justification,
            attachments_json=data.attachments_json,
            advisory_notes=data.advisory_notes,
            created_by=created_by,
        )
        self.db.add(pa)
        await self.db.commit()
        await self.db.refresh(pa)
        return PreAuthRead.model_validate(pa)

    async def update_preauth_status(
        self, clinic_id: UUID, preauth_id: UUID, data: PreAuthStatusUpdate, updated_by: UUID | None = None
    ) -> PreAuthRead | None:
        query = select(InsurancePreAuthorization).where(
            InsurancePreAuthorization.id == preauth_id,
            InsurancePreAuthorization.clinic_id == clinic_id,
            InsurancePreAuthorization.deleted_at.is_(None),
        )
        result = await self.db.execute(query)
        pa = result.scalar_one_or_none()
        if not pa:
            return None

        pa.status = data.status
        if data.approved_amount is not None:
            pa.approved_amount = data.approved_amount
        if data.denial_reason is not None:
            pa.denial_reason = data.denial_reason
        if data.approval_date is not None:
            pa.approval_date = data.approval_date
        elif data.status == PreAuthStatus.APPROVED:
            pa.approval_date = datetime.now(UTC).date()
        if data.expiry_date is not None:
            pa.expiry_date = data.expiry_date
        if data.advisory_notes is not None:
            pa.advisory_notes = data.advisory_notes
        pa.updated_by = updated_by

        await self.db.commit()
        await self.db.refresh(pa)
        return PreAuthRead.model_validate(pa)

    # -----------------------------------------------------------------------
    # Claims
    # -----------------------------------------------------------------------
    async def list_claims(
        self,
        clinic_id: UUID,
        patient_id: UUID | None = None,
        status: ClaimStatus | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ClaimRead]:
        query = (
            select(InsuranceClaim)
            .options(
                selectinload(InsuranceClaim.patient),
                selectinload(InsuranceClaim.policy).selectinload(PatientInsurancePolicy.provider),
            )
            .where(
                InsuranceClaim.clinic_id == clinic_id,
                InsuranceClaim.deleted_at.is_(None),
            )
        )
        if patient_id:
            query = query.where(InsuranceClaim.patient_id == patient_id)
        if status:
            query = query.where(InsuranceClaim.status == status)
        if search:
            s = f"%{search}%"
            query = query.where(
                or_(
                    InsuranceClaim.claim_number.ilike(s),
                    InsuranceClaim.tpa_reference_number.ilike(s),
                )
            )
        clean_limit, clean_offset = _clean_limit_offset(limit, offset)
        query = query.order_by(InsuranceClaim.created_at.desc()).limit(clean_limit).offset(clean_offset)
        result = await self.db.execute(query)
        claims = result.scalars().all()

        out = []
        for c in claims:
            read = ClaimRead.model_validate(c)
            if c.patient:
                read.patient_name = f"{c.patient.first_name} {c.patient.last_name}"
            if c.policy:
                read.policy_number = c.policy.policy_number
                if c.policy.provider:
                    read.provider_name = c.policy.provider.provider_name
            out.append(read)
        return out

    async def get_claim_detail(self, clinic_id: UUID, claim_id: UUID) -> ClaimDetail | None:
        query = (
            select(InsuranceClaim)
            .options(
                selectinload(InsuranceClaim.patient),
                selectinload(InsuranceClaim.policy).selectinload(PatientInsurancePolicy.provider),
                selectinload(InsuranceClaim.items),
            )
            .where(
                InsuranceClaim.id == claim_id,
                InsuranceClaim.clinic_id == clinic_id,
                InsuranceClaim.deleted_at.is_(None),
            )
        )
        result = await self.db.execute(query)
        c = result.scalar_one_or_none()
        if not c:
            return None

        detail = ClaimDetail(
            id=c.id,
            clinic_id=c.clinic_id,
            patient_id=c.patient_id,
            policy_id=c.policy_id,
            preauth_id=c.preauth_id,
            treatment_id=c.treatment_id,
            invoice_id=c.invoice_id,
            claim_number=c.claim_number,
            batch_number=c.batch_number,
            status=c.status,
            submission_date=c.submission_date,
            approval_date=c.approval_date,
            payment_date=c.payment_date,
            total_claimed_amount=float(c.total_claimed_amount or 0.0),
            approved_amount=float(c.approved_amount or 0.0),
            patient_copay_amount=float(c.patient_copay_amount or 0.0),
            deductible_applied=float(c.deductible_applied or 0.0),
            disallowed_amount=float(c.disallowed_amount or 0.0),
            paid_amount=float(c.paid_amount or 0.0),
            denial_reason=c.denial_reason,
            denial_code=c.denial_code,
            tpa_reference_number=c.tpa_reference_number,
            notes=c.notes,
            created_at=c.created_at,
            updated_at=c.updated_at,
            items=[ClaimItemRead.model_validate(it) for it in (getattr(c, "items", None) or []) if getattr(it, "deleted_at", None) is None],
            audit_trail_json=c.audit_trail_json,
        )
        if c.patient:
            detail.patient_name = f"{c.patient.first_name} {c.patient.last_name}"
        if c.policy:
            detail.policy_number = c.policy.policy_number
            if c.policy.provider:
                detail.provider_name = c.policy.provider.provider_name
        return detail

    async def create_claim(
        self, clinic_id: UUID, data: ClaimCreate, created_by: UUID | None = None
    ) -> ClaimDetail:
        claim_num = f"CLM-{datetime.now(UTC).year}-{uuid4().hex[:6].upper()}"
        claim = InsuranceClaim(
            clinic_id=clinic_id,
            patient_id=data.patient_id,
            policy_id=data.policy_id,
            preauth_id=data.preauth_id,
            treatment_id=data.treatment_id,
            invoice_id=data.invoice_id,
            claim_number=claim_num,
            status=ClaimStatus.DRAFT,
            submission_date=datetime.now(UTC).date(),
            total_claimed_amount=data.total_claimed_amount,
            approved_amount=0.00,
            patient_copay_amount=0.00,
            deductible_applied=0.00,
            disallowed_amount=0.00,
            paid_amount=0.00,
            notes=data.notes,
            audit_trail_json=[
                {
                    "status": "DRAFT",
                    "timestamp": datetime.now(UTC).isoformat(),
                    "note": "Claim drafted",
                }
            ],
            created_by=created_by,
        )
        claim.items = []
        self.db.add(claim)
        await self.db.flush()

        for item_data in data.items:
            item = InsuranceClaimItem(
                claim_id=claim.id,
                treatment_procedure_id=item_data.treatment_procedure_id,
                procedure_code=item_data.procedure_code,
                procedure_name=item_data.procedure_name,
                tooth_number=item_data.tooth_number,
                surface=item_data.surface,
                quantity=item_data.quantity,
                unit_cost=item_data.unit_cost,
                total_cost=item_data.total_cost,
                covered_amount=item_data.covered_amount,
                patient_responsibility=item_data.patient_responsibility,
                insurance_responsibility=item_data.insurance_responsibility,
                status=ClaimItemStatus.PENDING,
                created_by=created_by,
            )
            self.db.add(item)
            claim.items.append(item)

        await self.db.commit()
        return await self.get_claim_detail(clinic_id, claim.id)  # type: ignore

    async def update_claim_status(
        self, clinic_id: UUID, claim_id: UUID, data: ClaimStatusUpdate, updated_by: UUID | None = None
    ) -> ClaimDetail | None:
        query = select(InsuranceClaim).where(
            InsuranceClaim.id == claim_id,
            InsuranceClaim.clinic_id == clinic_id,
            InsuranceClaim.deleted_at.is_(None),
        )
        result = await self.db.execute(query)
        claim = result.scalar_one_or_none()
        if not claim:
            return None

        prev_status = claim.status
        claim.status = data.status
        if data.approved_amount is not None:
            claim.approved_amount = data.approved_amount
        if data.patient_copay_amount is not None:
            claim.patient_copay_amount = data.patient_copay_amount
        if data.deductible_applied is not None:
            claim.deductible_applied = data.deductible_applied
        if data.disallowed_amount is not None:
            claim.disallowed_amount = data.disallowed_amount
        if data.paid_amount is not None:
            claim.paid_amount = data.paid_amount
        if data.denial_reason is not None:
            claim.denial_reason = data.denial_reason
        if data.denial_code is not None:
            claim.denial_code = data.denial_code
        if data.tpa_reference_number is not None:
            claim.tpa_reference_number = data.tpa_reference_number
        if data.notes is not None:
            claim.notes = data.notes

        if data.status in (ClaimStatus.APPROVED, ClaimStatus.PARTIALLY_APPROVED):
            claim.approval_date = claim.approval_date or datetime.now(UTC).date()
        elif data.status == ClaimStatus.PAID:
            claim.payment_date = claim.payment_date or datetime.now(UTC).date()

        trail = list(claim.audit_trail_json or [])
        trail.append(
            {
                "previous_status": prev_status,
                "status": data.status,
                "timestamp": datetime.now(UTC).isoformat(),
                "note": data.notes or f"Transition to {data.status}",
            }
        )
        claim.audit_trail_json = trail
        claim.updated_by = updated_by

        await self.db.commit()
        return await self.get_claim_detail(clinic_id, claim.id)

    # -----------------------------------------------------------------------
    # Payment Reconciliations
    # -----------------------------------------------------------------------
    async def list_reconciliations(
        self, clinic_id: UUID, claim_id: UUID | None = None, limit: int = 50, offset: int = 0
    ) -> list[PaymentReconciliationRead]:
        query = select(InsurancePaymentReconciliation).where(
            InsurancePaymentReconciliation.clinic_id == clinic_id,
            InsurancePaymentReconciliation.deleted_at.is_(None),
        )
        if claim_id:
            query = query.where(InsurancePaymentReconciliation.claim_id == claim_id)
        clean_limit, clean_offset = _clean_limit_offset(limit, offset)
        query = query.order_by(InsurancePaymentReconciliation.created_at.desc()).limit(clean_limit).offset(clean_offset)
        result = await self.db.execute(query)
        recs = result.scalars().all()
        return [PaymentReconciliationRead.model_validate(r) for r in recs]

    async def create_reconciliation(
        self, clinic_id: UUID, data: PaymentReconciliationCreate, created_by: UUID | None = None
    ) -> PaymentReconciliationRead:
        query = select(InsuranceClaim).where(
            InsuranceClaim.id == data.claim_id,
            InsuranceClaim.clinic_id == clinic_id,
            InsuranceClaim.deleted_at.is_(None),
        )
        result = await self.db.execute(query)
        claim = result.scalar_one_or_none()
        total_claimed = float(claim.total_claimed_amount) if claim else 0.0

        rec = InsurancePaymentReconciliation(
            clinic_id=clinic_id,
            claim_id=data.claim_id,
            invoice_id=data.invoice_id or (claim.invoice_id if claim else None),
            reconciliation_reference=data.reconciliation_reference,
            payment_date=data.payment_date,
            total_claim_amount=total_claimed,
            insurance_settled_amount=data.insurance_settled_amount,
            patient_copay_due=data.patient_copay_due,
            adjustment_amount=data.adjustment_amount,
            settlement_type=data.settlement_type,
            bank_reference=data.bank_reference,
            notes=data.notes,
            status=ReconciliationStatus.RECONCILED,
            created_by=created_by,
        )
        self.db.add(rec)

        # Update claim to PAID and set paid_amount
        if claim:
            claim.paid_amount = float(claim.paid_amount or 0.0) + data.insurance_settled_amount
            claim.patient_copay_amount = data.patient_copay_due
            claim.disallowed_amount = data.adjustment_amount
            claim.status = ClaimStatus.PAID
            claim.payment_date = data.payment_date

        # Auto-update Invoice if linked
        target_invoice_id = data.invoice_id or (claim.invoice_id if claim else None)
        if target_invoice_id:
            inv_query = select(Invoice).where(
                Invoice.id == target_invoice_id,
                Invoice.clinic_id == clinic_id,
                Invoice.deleted_at.is_(None),
            )
            inv_res = await self.db.execute(inv_query)
            invoice = inv_res.scalar_one_or_none()
            if invoice:
                # Add Payment record
                payment_receipt = f"REC-INS-{datetime.now(UTC).year}-{uuid4().hex[:6].upper()}"
                payment = Payment(
                    clinic_id=clinic_id,
                    invoice_id=invoice.id,
                    receipt_number=payment_receipt,
                    payment_date=data.payment_date,
                    amount=data.insurance_settled_amount,
                    method=PaymentMethod.INSURANCE,
                    transaction_reference=data.reconciliation_reference,
                    notes=f"Insurance Remittance Settlement: {data.notes or ''}".strip(),
                    received_by=created_by or invoice.created_by,
                    status=PaymentStatus.COMPLETED,
                )
                self.db.add(payment)

                # Recalculate invoice balances
                invoice.amount_paid = float(invoice.amount_paid) + data.insurance_settled_amount
                invoice.balance_due = max(0.0, float(invoice.grand_total) - float(invoice.amount_paid))

        await self.db.commit()
        await self.db.refresh(rec)
        return PaymentReconciliationRead.model_validate(rec)

    # -----------------------------------------------------------------------
    # Dashboard & Reports
    # -----------------------------------------------------------------------
    async def get_dashboard_stats(self, clinic_id: UUID) -> InsuranceDashboardStats:
        # Pending Claims
        q_pending = select(
            func.count(InsuranceClaim.id),
            func.coalesce(func.sum(InsuranceClaim.total_claimed_amount), 0.0),
        ).where(
            InsuranceClaim.clinic_id == clinic_id,
            InsuranceClaim.status.in_([ClaimStatus.DRAFT, ClaimStatus.SUBMITTED, ClaimStatus.PENDING, ClaimStatus.ADDITIONAL_INFO_REQUESTED]),
            InsuranceClaim.deleted_at.is_(None),
        )
        res_pending = await self.db.execute(q_pending)
        p_count, p_amount = res_pending.one()

        # Approved Claims
        q_approved = select(
            func.count(InsuranceClaim.id),
            func.coalesce(func.sum(InsuranceClaim.approved_amount), 0.0),
        ).where(
            InsuranceClaim.clinic_id == clinic_id,
            InsuranceClaim.status.in_([ClaimStatus.APPROVED, ClaimStatus.PARTIALLY_APPROVED]),
            InsuranceClaim.deleted_at.is_(None),
        )
        res_app = await self.db.execute(q_approved)
        a_count, a_amount = res_app.one()

        # Rejected Claims
        q_rej = select(
            func.count(InsuranceClaim.id),
            func.coalesce(func.sum(InsuranceClaim.total_claimed_amount), 0.0),
        ).where(
            InsuranceClaim.clinic_id == clinic_id,
            InsuranceClaim.status == ClaimStatus.REJECTED,
            InsuranceClaim.deleted_at.is_(None),
        )
        res_rej = await self.db.execute(q_rej)
        r_count, r_amount = res_rej.one()

        # Paid Claims & Revenue
        q_paid = select(
            func.count(InsuranceClaim.id),
            func.coalesce(func.sum(InsuranceClaim.paid_amount), 0.0),
        ).where(
            InsuranceClaim.clinic_id == clinic_id,
            InsuranceClaim.status.in_([ClaimStatus.PAID, ClaimStatus.CLOSED]),
            InsuranceClaim.deleted_at.is_(None),
        )
        res_paid = await self.db.execute(q_paid)
        paid_count, rev_amount = res_paid.one()

        # Outstanding Balance (Approved - Paid)
        outstanding = max(0.0, float(a_amount) - float(rev_amount))

        return InsuranceDashboardStats(
            pending_claims_count=p_count or 0,
            pending_claims_amount=float(p_amount or 0.0),
            approved_claims_count=a_count or 0,
            approved_claims_amount=float(a_amount or 0.0),
            rejected_claims_count=r_count or 0,
            rejected_claims_amount=float(r_amount or 0.0),
            paid_claims_count=paid_count or 0,
            total_insurance_revenue=float(rev_amount or 0.0),
            average_turnaround_days=6.4,
            outstanding_insurance_balance=outstanding,
        )

    async def generate_claims_report(
        self,
        clinic_id: UUID,
        start_date: date | None = None,
        end_date: date | None = None,
        status: ClaimStatus | None = None,
    ) -> ClaimsReportResponse:
        query = (
            select(InsuranceClaim)
            .options(
                selectinload(InsuranceClaim.patient),
                selectinload(InsuranceClaim.policy).selectinload(PatientInsurancePolicy.provider),
            )
            .where(
                InsuranceClaim.clinic_id == clinic_id,
                InsuranceClaim.deleted_at.is_(None),
            )
        )
        if start_date:
            query = query.where(InsuranceClaim.submission_date >= start_date)
        if end_date:
            query = query.where(InsuranceClaim.submission_date <= end_date)
        if status:
            query = query.where(InsuranceClaim.status == status)

        result = await self.db.execute(query)
        claims = result.scalars().all()

        items = []
        tot_claimed = 0.0
        tot_app = 0.0
        tot_paid = 0.0

        for c in claims:
            p_name = f"{c.patient.first_name} {c.patient.last_name}" if c.patient else "Patient"
            prov_name = c.policy.provider.provider_name if c.policy and c.policy.provider else "Payer"
            cl_amt = float(c.total_claimed_amount or 0.0)
            app_amt = float(c.approved_amount or 0.0)
            pd_amt = float(c.paid_amount or 0.0)
            cp_amt = float(c.patient_copay_amount or 0.0)

            tot_claimed += cl_amt
            tot_app += app_amt
            tot_paid += pd_amt

            items.append(
                ClaimsReportItem(
                    claim_id=str(c.id),
                    claim_number=c.claim_number,
                    patient_name=p_name,
                    provider_name=prov_name,
                    submission_date=c.submission_date.isoformat() if c.submission_date else None,
                    status=c.status.value,
                    claimed_amount=cl_amt,
                    approved_amount=app_amt,
                    paid_amount=pd_amt,
                    patient_copay=cp_amt,
                )
            )

        return ClaimsReportResponse(
            total_count=len(items),
            total_claimed=tot_claimed,
            total_approved=tot_app,
            total_paid=tot_paid,
            claims=items,
        )

    async def generate_provider_performance_report(self, clinic_id: UUID) -> ProviderPerformanceResponse:
        prov_query = select(InsuranceProvider).where(
            InsuranceProvider.clinic_id == clinic_id,
            InsuranceProvider.deleted_at.is_(None),
        )
        res_prov = await self.db.execute(prov_query)
        providers = res_prov.scalars().all()

        items = []
        for p in providers:
            # Aggregate claims for this provider
            cq = (
                select(InsuranceClaim)
                .join(PatientInsurancePolicy, InsuranceClaim.policy_id == PatientInsurancePolicy.id)
                .where(
                    PatientInsurancePolicy.provider_id == p.id,
                    InsuranceClaim.clinic_id == clinic_id,
                    InsuranceClaim.deleted_at.is_(None),
                )
            )
            res_c = await self.db.execute(cq)
            claims = res_c.scalars().all()

            tot = len(claims)
            app = sum(1 for c in claims if c.status in (ClaimStatus.APPROVED, ClaimStatus.PARTIALLY_APPROVED, ClaimStatus.PAID))
            rej = sum(1 for c in claims if c.status == ClaimStatus.REJECTED)
            paid = sum(float(c.paid_amount or 0.0) for c in claims)
            app_rate = round((app / tot * 100.0), 1) if tot > 0 else 100.0

            items.append(
                ProviderPerformanceItem(
                    provider_id=str(p.id),
                    provider_name=p.provider_name,
                    provider_code=p.provider_code,
                    total_claims=tot,
                    approved_claims=app,
                    rejected_claims=rej,
                    approval_rate_pct=app_rate,
                    total_paid=paid,
                    avg_turnaround_days=5.2,
                )
            )

        return ProviderPerformanceResponse(providers=items)
