from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ai import AIAuditLog, AITaskType
from app.models.billing import Invoice, InvoiceStatus
from app.models.patient import Patient
from app.models.treatment import Treatment
from app.schemas.ai import (
    BillingAuditRequest,
    BillingAuditResponse,
    UnbilledItemSuggestion,
)


class AIBillingAssistantService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def audit_unbilled_items(
        self, clinic_id: UUID, payload: BillingAuditRequest, user_id: UUID
    ) -> BillingAuditResponse:
        patient = await self.db.get(Patient, payload.patient_id)
        if not patient or patient.clinic_id != clinic_id:
            raise HTTPException(status_code=404, detail="Patient not found.")

        # 1. Fetch completed or in-progress treatments
        stmt_trt = (
            select(Treatment)
            .options(selectinload(Treatment.procedures))
            .where(
                Treatment.patient_id == payload.patient_id,
                Treatment.clinic_id == clinic_id,
                Treatment.deleted_at.is_(None),
            )
        )
        if payload.treatment_id:
            stmt_trt = stmt_trt.where(Treatment.id == payload.treatment_id)

        treatments = list((await self.db.execute(stmt_trt)).scalars().all())

        # 2. Fetch existing invoices
        stmt_inv = (
            select(Invoice)
            .options(selectinload(Invoice.items))
            .where(
                Invoice.patient_id == payload.patient_id,
                Invoice.clinic_id == clinic_id,
                Invoice.status.in_([InvoiceStatus.PAID, InvoiceStatus.PARTIALLY_PAID, InvoiceStatus.UNPAID]),
                Invoice.deleted_at.is_(None),
            )
        )
        invoices = list((await self.db.execute(stmt_inv)).scalars().all())

        billed_descriptions = set()
        for inv in invoices:
            for item in inv.items:
                billed_descriptions.add(item.description.lower().strip())

        suggestions: list[UnbilledItemSuggestion] = []

        for trt in treatments:
            for proc in trt.procedures:
                proc_name = proc.procedure_name.strip()
                # Check if this procedure appears in billed items
                if not any(proc_name.lower() in b for b in billed_descriptions):
                    cost = float(proc.cost) if getattr(proc, "cost", None) else 1500.0
                    plan_name = getattr(trt, "treatment_plan", None) or getattr(trt, "diagnosis", "Treatment")
                    suggestions.append(
                        UnbilledItemSuggestion(
                            item_type="PROCEDURE",
                            name=proc_name,
                            code=f"PROC-{proc.procedure_type if hasattr(proc, 'procedure_type') else 'DNT'}",
                            estimated_amount=cost,
                            source=f"Completed in {plan_name}",
                        )
                    )

        # Audit log
        total_unbilled = sum(s.estimated_amount for s in suggestions)
        audit = AIAuditLog(
            id=uuid4(),
            clinic_id=clinic_id,
            user_id=user_id,
            patient_id=patient.id,
            task_type=AITaskType.BILLING_AUDIT,
            provider_type="LOCAL_RULE_ENGINE",
            model_name="dentalcare-billing-auditor",
            tokens_prompt=50,
            tokens_completion=50,
            latency_ms=10,
            anonymized_prompt_summary="Unbilled procedure audit",
            response_summary=f"{len(suggestions)} unbilled items flagged",
            safety_flags=["UNBILLED_PROCEDURES_FOUND"] if suggestions else [],
            request_id=f"AI-BIL-{uuid4().hex[:8]}",
            created_by=user_id,
            updated_by=user_id,
        )
        self.db.add(audit)
        await self.db.commit()

        return BillingAuditResponse(
            has_unbilled_items=len(suggestions) > 0,
            suggestions=suggestions,
            total_unbilled_estimate=total_unbilled,
        )
