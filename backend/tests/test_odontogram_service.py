from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models.identity import Role, User
from app.models.odontogram import (
    COLOR_STANDARDS,
    Tooth,
    ToothCondition,
    ToothSurface,
    ToothSurfaceEnum,
)
from app.models.patient import Patient
from app.schemas.odontogram import (
    ToothProcedureCreate,
    ToothSurfaceUpdate,
    ToothUpdate,
)
from app.services.odontogram_service import OdontogramService


class InMemoryDbService:
    def __init__(self, patient: Patient, teeth: list[Tooth] | None = None):
        self.patient = patient
        self.items: list[object] = [patient] + (teeth or [])
        self.added: list[object] = []

    def add(self, item: object) -> None:
        self.added.append(item)
        if item not in self.items:
            self.items.append(item)

    async def flush(self) -> None:
        pass

    async def commit(self) -> None:
        pass

    async def refresh(self, item: object) -> None:
        pass

    async def get(self, model: type, id_: object) -> object | None:
        for item in self.items:
            if isinstance(item, model) and getattr(item, "id", None) == id_:
                return item
        return None

    async def execute(self, statement: object) -> object:
        text = str(statement).lower()
        from types import SimpleNamespace

        if "count(" in text:
            caries_count = sum(1 for item in self.items if isinstance(item, Tooth) and item.primary_status == ToothCondition.CARIES.value)
            missing_count = sum(1 for item in self.items if isinstance(item, Tooth) and (item.is_missing or item.primary_status == ToothCondition.MISSING.value))
            rct_count = sum(1 for item in self.items if isinstance(item, Tooth) and (item.has_root_canal or item.primary_status == ToothCondition.ROOT_CANAL.value))
            crown_count = sum(1 for item in self.items if isinstance(item, Tooth) and (item.has_crown or item.primary_status == ToothCondition.CROWN.value))
            implant_count = sum(1 for item in self.items if isinstance(item, Tooth) and (item.has_implant or item.primary_status == ToothCondition.IMPLANT.value))
            filling_count = sum(1 for item in self.items if isinstance(item, Tooth) and item.primary_status == ToothCondition.FILLING.value)
            total_count = sum(1 for item in self.items if isinstance(item, Tooth))

            row = SimpleNamespace(
                total=total_count,
                caries=caries_count,
                missing=missing_count,
                root_canals=rct_count,
                crowns=crown_count,
                implants=implant_count,
                restorations=filling_count,
            )
            return SimpleNamespace(one=lambda: row)

        matching = list(self.items)
        if "tooth_surfaces" in text:
            matching = [item for item in self.items if isinstance(item, ToothSurface)]
        elif "teeth" in text:
            matching = [item for item in self.items if isinstance(item, Tooth)]
        elif "tooth_history" in text:
            matching = [item for item in self.items if hasattr(item, "action")]

        return SimpleNamespace(
            scalars=lambda: SimpleNamespace(
                all=lambda: list(matching),
                first=lambda: matching[0] if matching else None,
            ),
            scalar_one_or_none=lambda: matching[0] if matching else None,
        )


def setup_service_fixtures():
    clinic_id = uuid4()
    patient = Patient(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_number="PAT-100",
        first_name="Ravi",
        last_name="Kumar",
        gender="MALE",
        mobile_number="9898989898",
    )
    dentist = User(
        id=uuid4(),
        clinic_id=clinic_id,
        email="dr.ravi@clinic.com",
        first_name="Vikram",
        last_name="Aditya",
        role=Role.DENTIST,
    )
    return clinic_id, patient, dentist


@pytest.mark.asyncio
async def test_odontogram_service_get_auto_initialization():
    clinic_id, patient, dentist = setup_service_fixtures()
    db = InMemoryDbService(patient)
    service = OdontogramService(db)  # type: ignore[arg-type]

    result = await service.get_patient_odontogram(clinic_id, patient.id, "ADULT", dentist.id)
    assert result.patient_id == patient.id
    assert len(result.teeth) == 32
    assert result.stats.total_teeth_charted == 32
    assert result.stats.active_caries == 0


@pytest.mark.asyncio
async def test_odontogram_service_impossible_states_validation():
    clinic_id, patient, dentist = setup_service_fixtures()
    db = InMemoryDbService(patient)
    service = OdontogramService(db)  # type: ignore[arg-type]

    # Initialize teeth
    chart = await service.get_patient_odontogram(clinic_id, patient.id, "ADULT", dentist.id)
    t11_dto = chart.teeth[0]
    t11_model = await db.get(Tooth, t11_dto.id)
    assert t11_model is not None

    # 1. Mark tooth as extracted
    t11_model.is_extracted = True
    t11_model.primary_status = ToothCondition.EXTRACTION.value

    # Test Impossible State: Duplicate extraction -> 400
    with pytest.raises(HTTPException) as exc_info:
        await service.update_tooth(clinic_id, t11_model.id, ToothUpdate(is_extracted=True), dentist)
    assert exc_info.value.status_code == 400
    assert "already extracted" in exc_info.value.detail

    # Test Impossible State: Filling on extracted tooth -> 400
    with pytest.raises(HTTPException) as exc_info:
        await service.update_tooth(clinic_id, t11_model.id, ToothUpdate(primary_status="FILLING"), dentist)
    assert exc_info.value.status_code == 400
    assert "Cannot apply filling to extracted tooth" in exc_info.value.detail

    # Test Impossible State: Crown on extracted tooth without implant -> 400
    with pytest.raises(HTTPException) as exc_info:
        await service.update_tooth(clinic_id, t11_model.id, ToothUpdate(has_crown=True), dentist)
    assert exc_info.value.status_code == 400
    assert "without an implant" in exc_info.value.detail

    # Test Impossible State: Root canal on extracted tooth -> 400
    with pytest.raises(HTTPException) as exc_info:
        await service.update_tooth(clinic_id, t11_model.id, ToothUpdate(has_root_canal=True), dentist)
    assert exc_info.value.status_code == 400
    assert "Cannot perform root canal treatment" in exc_info.value.detail

    # 2. Place implant on extracted tooth -> valid
    await service.update_tooth(clinic_id, t11_model.id, ToothUpdate(has_implant=True), dentist)
    assert t11_model.has_implant is True
    assert t11_model.primary_status == ToothCondition.IMPLANT.value

    # Test Impossible State: Root canal on implant -> 400
    with pytest.raises(HTTPException) as exc_info:
        await service.update_tooth(clinic_id, t11_model.id, ToothUpdate(has_root_canal=True), dentist)
    assert exc_info.value.status_code == 400
    assert "Cannot perform root canal treatment on dental implant" in exc_info.value.detail

    # Test Impossible State: Duplicate implant -> 400
    with pytest.raises(HTTPException) as exc_info:
        await service.update_tooth(clinic_id, t11_model.id, ToothUpdate(has_implant=True), dentist)
    assert exc_info.value.status_code == 400
    assert "already has an implant" in exc_info.value.detail


@pytest.mark.asyncio
async def test_odontogram_service_surface_update_and_procedures():
    clinic_id, patient, dentist = setup_service_fixtures()
    db = InMemoryDbService(patient)
    service = OdontogramService(db)  # type: ignore[arg-type]

    chart = await service.get_patient_odontogram(clinic_id, patient.id, "ADULT", dentist.id)
    t16_dto = next(t for t in chart.teeth if t.tooth_number == "16")
    t16_model = await db.get(Tooth, t16_dto.id)
    assert t16_model is not None

    # Update Occlusal surface condition to Caries
    surf_res = await service.update_surface(
        clinic_id,
        t16_model.id,
        "OCCLUSAL",
        ToothSurfaceUpdate(condition="CARIES"),
        dentist,
    )
    assert surf_res.condition == "CARIES"
    assert surf_res.color == COLOR_STANDARDS[ToothCondition.CARIES]

    # Tooth status should now reflect Caries
    assert t16_model.primary_status == ToothCondition.CARIES.value

    # Apply composite procedure on Occlusal
    proc_res = await service.add_procedure(
        clinic_id,
        t16_model.id,
        ToothProcedureCreate(
            procedure_name="Composite Restoration",
            procedure_type="FILLING",
            surfaces=[ToothSurfaceEnum.OCCLUSAL],
            cost=2500.0,
        ),
        dentist,
    )
    assert proc_res.primary_status == ToothCondition.FILLING.value
    assert proc_res.color == COLOR_STANDARDS[ToothCondition.FILLING]
