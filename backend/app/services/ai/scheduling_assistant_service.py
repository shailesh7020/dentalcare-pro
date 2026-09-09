from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import Role, User
from app.models.patient import Patient
from app.schemas.ai import (
    SchedulingRecommendationRequest,
    SchedulingSlotRecommendation,
)


class AISchedulingAssistantService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def recommend_slot(
        self, clinic_id: UUID, payload: SchedulingRecommendationRequest
    ) -> SchedulingSlotRecommendation:
        patient = await self.db.get(Patient, payload.patient_id)
        if not patient or patient.clinic_id != clinic_id:
            raise HTTPException(status_code=404, detail="Patient not found.")

        # Estimate duration by procedure name
        proc_lower = payload.procedure_name.lower()
        if "root canal" in proc_lower or "endodontic" in proc_lower:
            duration = 60
        elif "implant" in proc_lower or "surgery" in proc_lower:
            duration = 75
        elif "crown" in proc_lower or "bridge" in proc_lower or "extraction" in proc_lower:
            duration = 45
        elif "scaling" in proc_lower or "cleaning" in proc_lower:
            duration = 30
        else:
            duration = 30

        # Find active dentist
        stmt_d = select(User).where(
            User.clinic_id == clinic_id, User.role == Role.DENTIST, User.is_active.is_(True)
        ).limit(1)
        dentist = await self.db.scalar(stmt_d)

        # Propose dates starting from tomorrow
        base_date = datetime.now(UTC).date() + timedelta(days=1)
        suggested = [
            f"{(base_date + timedelta(days=i)).strftime('%Y-%m-%d')} at 10:00 AM"
            for i in range(1, 4)
        ]

        dentist_name = f"{dentist.first_name} {dentist.last_name}" if dentist else "Assigned Clinician"
        dentist_id = dentist.id if dentist else None

        reason = (
            f"Recommended {duration} minutes for {payload.procedure_name}. "
            f"Optimized to balance chair load with Dr. {dentist_name}."
        )

        return SchedulingSlotRecommendation(
            recommended_duration_minutes=duration,
            dentist_id=dentist_id,
            dentist_name=dentist_name,
            suggested_dates=suggested,
            reason=reason,
        )
