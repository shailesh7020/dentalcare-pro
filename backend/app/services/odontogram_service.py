from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import AuditEvent, User
from app.models.odontogram import (
    COLOR_STANDARDS,
    DentitionType,
    Tooth,
    ToothCondition,
    ToothSurfaceEnum,
)
from app.models.patient import Patient, PatientTimelineEvent
from app.repositories.odontogram_repository import OdontogramRepository
from app.schemas.odontogram import (
    OdontogramDashboardStats,
    PatientOdontogramRead,
    ToothConditionCreate,
    ToothDetail,
    ToothHistoryRead,
    ToothProcedureCreate,
    ToothRead,
    ToothSurfaceRead,
    ToothSurfaceUpdate,
    ToothUpdate,
)


class OdontogramService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = OdontogramRepository(db)

    async def get_patient_odontogram(
        self,
        clinic_id: UUID,
        patient_id: UUID,
        dentition_type: str = "ADULT",
        user_id: UUID | None = None,
    ) -> PatientOdontogramRead:
        patient = await self.db.get(Patient, patient_id)
        if not patient or patient.clinic_id != clinic_id or patient.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient record not found in this clinic.",
            )

        teeth = await self.repo.get_or_initialize_odontogram(
            clinic_id, patient_id, dentition_type, user_id
        )
        stats_dict = await self.repo.get_dashboard_stats(clinic_id, patient_id)
        stats = OdontogramDashboardStats(**stats_dict)

        patient_name = f"{patient.first_name} {patient.last_name}"
        return PatientOdontogramRead(
            patient_id=patient.id,
            patient_name=patient_name,
            patient_number=patient.patient_number,
            dentition_type=dentition_type,
            teeth=[ToothRead.model_validate(t) for t in teeth],
            stats=stats,
        )

    async def get_tooth(self, clinic_id: UUID, tooth_id: UUID) -> ToothDetail:
        tooth = await self.repo.get_tooth_by_id(clinic_id, tooth_id)
        if not tooth:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tooth record not found.",
            )
        return ToothDetail.model_validate(tooth)

    # Clinical Invariant Validations
    def _validate_filling_possible(self, tooth: Tooth) -> None:
        if tooth.is_extracted or tooth.primary_status == ToothCondition.EXTRACTION.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot apply filling to extracted tooth #{tooth.tooth_number}.",
            )
        if tooth.is_missing or tooth.primary_status == ToothCondition.MISSING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot apply filling to missing tooth #{tooth.tooth_number}.",
            )

    def _validate_crown_possible(self, tooth: Tooth) -> None:
        if (tooth.is_missing or tooth.is_extracted) and not tooth.has_implant:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot place crown on missing or extracted tooth #{tooth.tooth_number} without an implant.",
            )

    def _validate_implant_possible(self, tooth: Tooth) -> None:
        if tooth.has_implant or tooth.primary_status == ToothCondition.IMPLANT.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tooth #{tooth.tooth_number} already has an implant (duplicate implant prohibited).",
            )
        if not (tooth.is_extracted or tooth.is_missing):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot place dental implant on existing natural tooth #{tooth.tooth_number} without prior extraction.",
            )

    def _validate_extraction_possible(self, tooth: Tooth) -> None:
        if tooth.is_extracted or tooth.primary_status == ToothCondition.EXTRACTION.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tooth #{tooth.tooth_number} is already extracted (duplicate extraction prohibited).",
            )
        if tooth.is_missing or tooth.primary_status == ToothCondition.MISSING.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tooth #{tooth.tooth_number} is missing and cannot be extracted.",
            )

    def _validate_root_canal_possible(self, tooth: Tooth) -> None:
        if tooth.has_implant or tooth.primary_status == ToothCondition.IMPLANT.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot perform root canal treatment on dental implant #{tooth.tooth_number}.",
            )
        if tooth.is_extracted or tooth.is_missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot perform root canal treatment on extracted or missing tooth #{tooth.tooth_number}.",
            )

    async def update_tooth(
        self, clinic_id: UUID, tooth_id: UUID, payload: ToothUpdate, actor: User
    ) -> ToothDetail:
        tooth = await self.repo.get_tooth_by_id(clinic_id, tooth_id)
        if not tooth:
            raise HTTPException(status_code=404, detail="Tooth record not found.")

        # Invariant checks if status/flags changed
        if payload.primary_status:
            status_val = payload.primary_status.upper()
            if status_val == ToothCondition.FILLING.value:
                self._validate_filling_possible(tooth)
            elif status_val == ToothCondition.CROWN.value:
                self._validate_crown_possible(tooth)
            elif status_val == ToothCondition.IMPLANT.value:
                self._validate_implant_possible(tooth)
            elif status_val == ToothCondition.EXTRACTION.value:
                self._validate_extraction_possible(tooth)
            elif status_val == ToothCondition.ROOT_CANAL.value:
                self._validate_root_canal_possible(tooth)

        if payload.has_crown is True:
            self._validate_crown_possible(tooth)
        if payload.has_implant is True:
            self._validate_implant_possible(tooth)
        if payload.is_extracted is True:
            self._validate_extraction_possible(tooth)
        if payload.has_root_canal is True:
            self._validate_root_canal_possible(tooth)

        # Snapshot previous state
        prev_state = {
            "primary_status": tooth.primary_status,
            "color": tooth.color,
            "is_missing": tooth.is_missing,
            "is_extracted": tooth.is_extracted,
            "has_root_canal": tooth.has_root_canal,
            "has_crown": tooth.has_crown,
            "has_implant": tooth.has_implant,
            "has_bridge": tooth.has_bridge,
            "mobility_grade": tooth.mobility_grade,
        }

        # Apply updates
        if payload.primary_status is not None:
            tooth.primary_status = payload.primary_status.upper()
            if tooth.primary_status in COLOR_STANDARDS:
                tooth.color = COLOR_STANDARDS[tooth.primary_status]
        if payload.color is not None:
            tooth.color = payload.color
        if payload.is_missing is not None:
            tooth.is_missing = payload.is_missing
            if tooth.is_missing:
                tooth.primary_status = ToothCondition.MISSING.value
                tooth.color = COLOR_STANDARDS[ToothCondition.MISSING]
        if payload.is_extracted is not None:
            tooth.is_extracted = payload.is_extracted
            if tooth.is_extracted:
                tooth.primary_status = ToothCondition.EXTRACTION.value
                tooth.color = COLOR_STANDARDS[ToothCondition.EXTRACTION]
        if payload.is_impacted is not None:
            tooth.is_impacted = payload.is_impacted
        if payload.has_root_canal is not None:
            tooth.has_root_canal = payload.has_root_canal
            if tooth.has_root_canal and tooth.primary_status not in (ToothCondition.CROWN.value, ToothCondition.IMPLANT.value):
                tooth.primary_status = ToothCondition.ROOT_CANAL.value
                tooth.color = COLOR_STANDARDS[ToothCondition.ROOT_CANAL]
        if payload.has_crown is not None:
            tooth.has_crown = payload.has_crown
            if tooth.has_crown:
                tooth.primary_status = ToothCondition.CROWN.value
                tooth.color = COLOR_STANDARDS[ToothCondition.CROWN]
        if payload.has_implant is not None:
            tooth.has_implant = payload.has_implant
            if tooth.has_implant:
                tooth.is_extracted = False
                tooth.is_missing = False
                tooth.primary_status = ToothCondition.IMPLANT.value
                tooth.color = COLOR_STANDARDS[ToothCondition.IMPLANT]
        if payload.has_bridge is not None:
            tooth.has_bridge = payload.has_bridge
        if payload.mobility_grade is not None:
            tooth.mobility_grade = payload.mobility_grade
        if payload.notes is not None:
            tooth.notes = payload.notes

        tooth.updated_by = actor.id

        new_state = {
            "primary_status": tooth.primary_status,
            "color": tooth.color,
            "is_missing": tooth.is_missing,
            "is_extracted": tooth.is_extracted,
            "has_root_canal": tooth.has_root_canal,
            "has_crown": tooth.has_crown,
            "has_implant": tooth.has_implant,
            "has_bridge": tooth.has_bridge,
            "mobility_grade": tooth.mobility_grade,
        }

        # Immutable History Entry
        await self.repo.append_history(
            clinic_id=clinic_id,
            patient_id=tooth.patient_id,
            tooth_id=tooth.id,
            action="STATUS_CHANGE",
            description=f"Tooth #{tooth.tooth_number} status updated to {tooth.primary_status}.",
            previous_state=prev_state,
            new_state=new_state,
            user_id=actor.id,
            dentist_id=actor.id,
        )

        # Audit & Patient Timeline
        self.db.add(
            PatientTimelineEvent(
                patient_id=tooth.patient_id,
                clinic_id=clinic_id,
                event_type="ODONTOGRAM_UPDATED",
                title=f"Tooth #{tooth.tooth_number} Updated",
                description=f"Status changed to {tooth.primary_status}. Recorded by {actor.first_name} {actor.last_name}.",
                actor_id=actor.id,
            )
        )
        self.db.add(
            AuditEvent(
                clinic_id=clinic_id,
                actor_id=actor.id,
                action="UPDATE",
                entity_type="TOOTH",
                entity_id=str(tooth.id),
                metadata_json=json.dumps({"tooth_number": tooth.tooth_number, "status": tooth.primary_status}),
            )
        )

        await self.db.commit()
        return await self.get_tooth(clinic_id, tooth_id)

    async def update_surface(
        self,
        clinic_id: UUID,
        tooth_id: UUID,
        surface_name: str,
        payload: ToothSurfaceUpdate,
        actor: User,
    ) -> ToothSurfaceRead:
        tooth = await self.repo.get_tooth_by_id(clinic_id, tooth_id)
        if not tooth:
            raise HTTPException(status_code=404, detail="Tooth record not found.")

        surface = await self.repo.get_surface(clinic_id, tooth_id, surface_name)
        if not surface:
            raise HTTPException(status_code=404, detail=f"Surface {surface_name} not found on tooth.")

        # Invariant checks
        if payload.condition and payload.condition.upper() == ToothCondition.CARIES.value:
            self._validate_filling_possible(tooth)
        if payload.treatment and payload.treatment.upper() in ("COMPOSITE", "AMALGAM", "GLASS_IONOMER"):
            self._validate_filling_possible(tooth)

        prev_state = {
            "surface": surface.surface,
            "condition": surface.condition,
            "treatment": surface.treatment,
            "color": surface.color,
        }

        if payload.condition is not None:
            surface.condition = payload.condition.upper()
            if surface.condition in COLOR_STANDARDS:
                surface.color = COLOR_STANDARDS[surface.condition]
        if payload.treatment is not None:
            surface.treatment = payload.treatment.upper()
            if surface.treatment in ("COMPOSITE", "AMALGAM", "GLASS_IONOMER", "FILLING"):
                surface.color = COLOR_STANDARDS[ToothCondition.FILLING]
                surface.condition = "RESTORED"
        if payload.color is not None:
            surface.color = payload.color
        if payload.notes is not None:
            surface.notes = payload.notes

        surface.last_modified_at = datetime.now(UTC)
        surface.dentist_id = actor.id
        surface.updated_by = actor.id

        # If surface has caries, update tooth status if currently healthy
        if surface.condition == ToothCondition.CARIES.value and tooth.primary_status == ToothCondition.HEALTHY.value:
            tooth.primary_status = ToothCondition.CARIES.value
            tooth.color = COLOR_STANDARDS[ToothCondition.CARIES]
        # If surface was restored, update tooth status to filling if healthy/caries
        elif surface.treatment in ("COMPOSITE", "AMALGAM", "GLASS_IONOMER", "FILLING") and tooth.primary_status in (ToothCondition.HEALTHY.value, ToothCondition.CARIES.value):
            tooth.primary_status = ToothCondition.FILLING.value
            tooth.color = COLOR_STANDARDS[ToothCondition.FILLING]

        new_state = {
            "surface": surface.surface,
            "condition": surface.condition,
            "treatment": surface.treatment,
            "color": surface.color,
        }

        await self.repo.append_history(
            clinic_id=clinic_id,
            patient_id=tooth.patient_id,
            tooth_id=tooth.id,
            action="SURFACE_UPDATE",
            description=f"Surface {surface.surface} on tooth #{tooth.tooth_number} updated: condition={surface.condition}, treatment={surface.treatment}.",
            previous_state=prev_state,
            new_state=new_state,
            affected_surfaces=surface.surface,
            user_id=actor.id,
            dentist_id=actor.id,
        )

        await self.db.commit()
        await self.db.refresh(surface)
        return ToothSurfaceRead.model_validate(surface)

    async def add_condition(
        self, clinic_id: UUID, tooth_id: UUID, payload: ToothConditionCreate, actor: User
    ) -> ToothDetail:
        tooth = await self.repo.get_tooth_by_id(clinic_id, tooth_id)
        if not tooth:
            raise HTTPException(status_code=404, detail="Tooth record not found.")

        condition_val = payload.condition.upper()

        if condition_val == ToothCondition.CARIES.value:
            self._validate_filling_possible(tooth)
        elif condition_val == ToothCondition.EXTRACTION.value:
            self._validate_extraction_possible(tooth)

        prev_status = tooth.primary_status
        tooth.primary_status = condition_val
        tooth.color = payload.color or COLOR_STANDARDS.get(condition_val, "#EF4444")
        if payload.notes:
            tooth.notes = f"{tooth.notes}\n{payload.notes}".strip() if tooth.notes else payload.notes
        tooth.updated_by = actor.id

        # Affected surfaces
        affected_str = None
        if payload.surfaces:
            surf_names = [s.value if hasattr(s, "value") else str(s) for s in payload.surfaces]
            affected_str = ",".join(surf_names)
            for surf in tooth.surfaces:
                if surf.surface in surf_names:
                    surf.condition = condition_val
                    surf.color = tooth.color
                    surf.last_modified_at = datetime.now(UTC)
                    surf.dentist_id = actor.id

        await self.repo.append_history(
            clinic_id=clinic_id,
            patient_id=tooth.patient_id,
            tooth_id=tooth.id,
            action="CONDITION_ADDED",
            description=f"Diagnosed {condition_val} on tooth #{tooth.tooth_number}." + (f" Surfaces: {affected_str}" if affected_str else ""),
            previous_state={"primary_status": prev_status},
            new_state={"primary_status": condition_val, "affected_surfaces": affected_str},
            affected_surfaces=affected_str,
            user_id=actor.id,
            dentist_id=actor.id,
        )

        self.db.add(
            PatientTimelineEvent(
                patient_id=tooth.patient_id,
                clinic_id=clinic_id,
                event_type="ODONTOGRAM_UPDATED",
                title=f"Condition Diagnosed: Tooth #{tooth.tooth_number}",
                description=f"{condition_val} recorded by Dr. {actor.first_name} {actor.last_name}.",
                actor_id=actor.id,
            )
        )

        await self.db.commit()
        return await self.get_tooth(clinic_id, tooth_id)

    async def add_procedure(
        self, clinic_id: UUID, tooth_id: UUID, payload: ToothProcedureCreate, actor: User
    ) -> ToothDetail:
        tooth = await self.repo.get_tooth_by_id(clinic_id, tooth_id)
        if not tooth:
            raise HTTPException(status_code=404, detail="Tooth record not found.")

        proc_type = payload.procedure_type.upper()

        if proc_type in ("FILLING", "RESTORATION"):
            self._validate_filling_possible(tooth)
            tooth.primary_status = ToothCondition.FILLING.value
            tooth.color = COLOR_STANDARDS[ToothCondition.FILLING]
        elif proc_type in ("CROWN", "CAP"):
            self._validate_crown_possible(tooth)
            tooth.has_crown = True
            tooth.primary_status = ToothCondition.CROWN.value
            tooth.color = COLOR_STANDARDS[ToothCondition.CROWN]
        elif proc_type in ("ROOT_CANAL", "RCT", "ENDODONTIC"):
            self._validate_root_canal_possible(tooth)
            tooth.has_root_canal = True
            tooth.primary_status = ToothCondition.ROOT_CANAL.value
            tooth.color = COLOR_STANDARDS[ToothCondition.ROOT_CANAL]
        elif proc_type in ("EXTRACTION", "EXODONTIA"):
            self._validate_extraction_possible(tooth)
            tooth.is_extracted = True
            tooth.primary_status = ToothCondition.EXTRACTION.value
            tooth.color = COLOR_STANDARDS[ToothCondition.EXTRACTION]
        elif proc_type in ("IMPLANT",):
            self._validate_implant_possible(tooth)
            tooth.has_implant = True
            tooth.is_extracted = False
            tooth.is_missing = False
            tooth.primary_status = ToothCondition.IMPLANT.value
            tooth.color = COLOR_STANDARDS[ToothCondition.IMPLANT]
        elif proc_type in ("BRIDGE",):
            tooth.has_bridge = True
            tooth.primary_status = ToothCondition.BRIDGE.value
            tooth.color = COLOR_STANDARDS[ToothCondition.BRIDGE]
        elif proc_type in ("SEALANT",):
            tooth.primary_status = ToothCondition.SEALANT.value
            tooth.color = COLOR_STANDARDS[ToothCondition.SEALANT]

        affected_str = None
        if payload.surfaces:
            surf_names = [s.value if hasattr(s, "value") else str(s) for s in payload.surfaces]
            affected_str = ",".join(surf_names)
            mat = payload.material or "COMPOSITE"
            for surf in tooth.surfaces:
                if surf.surface in surf_names:
                    surf.treatment = mat
                    surf.condition = "RESTORED"
                    surf.color = tooth.color
                    surf.last_modified_at = datetime.now(UTC)
                    surf.dentist_id = actor.id

        tooth.updated_by = actor.id

        await self.repo.append_history(
            clinic_id=clinic_id,
            patient_id=tooth.patient_id,
            tooth_id=tooth.id,
            action="PROCEDURE_PERFORMED",
            description=f"Performed {payload.procedure_name} ({proc_type}) on tooth #{tooth.tooth_number}." + (f" Surfaces: {affected_str}" if affected_str else ""),
            previous_state=None,
            new_state={"primary_status": tooth.primary_status, "procedure": payload.procedure_name, "cost": payload.cost},
            affected_surfaces=affected_str,
            treatment_id=payload.treatment_id,
            appointment_id=payload.appointment_id,
            user_id=actor.id,
            dentist_id=actor.id,
        )

        self.db.add(
            PatientTimelineEvent(
                patient_id=tooth.patient_id,
                clinic_id=clinic_id,
                event_type="ODONTOGRAM_UPDATED",
                title=f"Procedure: Tooth #{tooth.tooth_number}",
                description=f"{payload.procedure_name} completed by Dr. {actor.first_name} {actor.last_name}.",
                actor_id=actor.id,
            )
        )

        await self.db.commit()
        return await self.get_tooth(clinic_id, tooth_id)

    async def sync_treatment_procedure(
        self,
        clinic_id: UUID,
        patient_id: UUID,
        tooth_number_raw: str,
        procedure_name: str,
        procedure_id: UUID | None,
        treatment_id: UUID,
        appointment_id: UUID,
        actor: User,
    ) -> None:
        """Called automatically when a treatment procedure is added or completed."""
        # Auto-initialize odontogram if not yet initialized
        await self.repo.get_or_initialize_odontogram(
            clinic_id, patient_id, DentitionType.ADULT, actor.id
        )

        tooth = await self.repo.get_tooth_by_number(clinic_id, patient_id, tooth_number_raw)
        if not tooth or not isinstance(tooth, Tooth):
            return  # Raw number didn't match canonical list or mock fallback, skip gracefully

        p_name = procedure_name.lower()
        prev_status = tooth.primary_status

        # Deduce procedure intent
        if "extract" in p_name or "exodontia" in p_name:
            if not tooth.is_extracted and not tooth.is_missing:
                tooth.is_extracted = True
                tooth.primary_status = ToothCondition.EXTRACTION.value
                tooth.color = COLOR_STANDARDS[ToothCondition.EXTRACTION]
        elif "root canal" in p_name or "rct" in p_name or "pulpectomy" in p_name or "endodontic" in p_name:
            if not tooth.has_implant and not tooth.is_extracted and not tooth.is_missing:
                tooth.has_root_canal = True
                tooth.primary_status = ToothCondition.ROOT_CANAL.value
                tooth.color = COLOR_STANDARDS[ToothCondition.ROOT_CANAL]
        elif "implant" in p_name:
            if not tooth.has_implant:
                tooth.has_implant = True
                tooth.is_extracted = False
                tooth.is_missing = False
                tooth.primary_status = ToothCondition.IMPLANT.value
                tooth.color = COLOR_STANDARDS[ToothCondition.IMPLANT]
        elif "crown" in p_name or "cap" in p_name:
            if not tooth.is_extracted and not tooth.is_missing or tooth.has_implant:
                tooth.has_crown = True
                tooth.primary_status = ToothCondition.CROWN.value
                tooth.color = COLOR_STANDARDS[ToothCondition.CROWN]
        elif "bridge" in p_name:
            tooth.has_bridge = True
            tooth.primary_status = ToothCondition.BRIDGE.value
            tooth.color = COLOR_STANDARDS[ToothCondition.BRIDGE]
        elif ("fill" in p_name or "restor" in p_name or "composite" in p_name or "amalgam" in p_name) and not tooth.is_extracted and not tooth.is_missing:
            tooth.primary_status = ToothCondition.FILLING.value
            tooth.color = COLOR_STANDARDS[ToothCondition.FILLING]
            # Default occlusal / incisal surface update
            for s in tooth.surfaces:
                if s.surface in (ToothSurfaceEnum.OCCLUSAL.value, ToothSurfaceEnum.INCISAL.value):
                    s.treatment = "COMPOSITE"
                    s.condition = "RESTORED"
                    s.color = COLOR_STANDARDS[ToothCondition.FILLING]
                    s.last_modified_at = datetime.now(UTC)
                    s.dentist_id = actor.id

        tooth.updated_by = actor.id

        await self.repo.append_history(
            clinic_id=clinic_id,
            patient_id=patient_id,
            tooth_id=tooth.id,
            action="TREATMENT_SYNC",
            description=f"Auto-synchronized from Treatment procedure: {procedure_name}.",
            previous_state={"primary_status": prev_status},
            new_state={"primary_status": tooth.primary_status},
            treatment_id=treatment_id,
            treatment_procedure_id=procedure_id,
            appointment_id=appointment_id,
            user_id=actor.id,
            dentist_id=actor.id,
        )

        self.db.add(
            PatientTimelineEvent(
                patient_id=patient_id,
                clinic_id=clinic_id,
                event_type="ODONTOGRAM_UPDATED",
                title=f"Odontogram Synced: Tooth #{tooth.tooth_number}",
                description=f"Clinical procedure '{procedure_name}' synchronized with dental chart.",
                actor_id=actor.id,
            )
        )

    async def get_patient_history(
        self, clinic_id: UUID, patient_id: UUID
    ) -> list[ToothHistoryRead]:
        history = await self.repo.get_patient_tooth_history(clinic_id, patient_id)
        return [ToothHistoryRead.model_validate(h) for h in history]

    async def get_tooth_history(
        self, clinic_id: UUID, tooth_id: UUID
    ) -> list[ToothHistoryRead]:
        history = await self.repo.get_tooth_history(clinic_id, tooth_id)
        return [ToothHistoryRead.model_validate(h) for h in history]
