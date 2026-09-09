from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.v1 import odontogram as o_api
from app.models.identity import Role, User
from app.models.odontogram import (
    Tooth,
    ToothCondition,
    ToothHistory,
    ToothSurface,
    ToothSurfaceEnum,
)
from app.models.patient import Patient
from app.schemas.odontogram import (
    ToothConditionCreate,
    ToothProcedureCreate,
    ToothSurfaceUpdate,
    ToothUpdate,
)


class InMemoryDbApi:
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
            matching = [item for item in self.items if isinstance(item, ToothHistory)]

        return SimpleNamespace(
            scalars=lambda: SimpleNamespace(
                all=lambda: list(matching),
                first=lambda: matching[0] if matching else None,
            ),
            scalar_one_or_none=lambda: matching[0] if matching else None,
        )


def setup_api_fixtures():
    clinic_id = uuid4()
    patient = Patient(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_number="PAT-200",
        first_name="Deepa",
        last_name="Shah",
        gender="FEMALE",
        mobile_number="9777777777",
    )
    dentist = User(
        id=uuid4(),
        clinic_id=clinic_id,
        email="dr.deepa@clinic.com",
        first_name="Pooja",
        last_name="Nair",
        role=Role.DENTIST,
    )
    return clinic_id, patient, dentist


@pytest.mark.asyncio
async def test_odontogram_api_full_flow():
    clinic_id, patient, dentist = setup_api_fixtures()
    db = InMemoryDbApi(patient)

    # 1. Get Patient Odontogram (auto-init)
    odontogram_read = await o_api.get_patient_odontogram(
        id=patient.id, dentition="ADULT", actor=dentist, db=db  # type: ignore[arg-type]
    )
    assert odontogram_read.patient_id == patient.id
    assert len(odontogram_read.teeth) == 32
    t11 = next(t for t in odontogram_read.teeth if t.tooth_number == "11")
    t11_id = t11.id

    # 2. Get Single Tooth
    tooth_detail = await o_api.get_tooth(id=t11_id, actor=dentist, db=db)  # type: ignore[arg-type]
    assert tooth_detail.id == t11_id
    assert tooth_detail.primary_status == ToothCondition.HEALTHY.value

    # 3. Patch Tooth Status
    updated_tooth = await o_api.update_tooth(
        id=t11_id,
        payload=ToothUpdate(notes="Mild attrition on incisal edge"),
        actor=dentist,
        db=db,  # type: ignore[arg-type]
    )
    assert updated_tooth.notes == "Mild attrition on incisal edge"

    # 4. Patch Surface
    surf_res = await o_api.update_tooth_surface(
        id=t11_id,
        surface="INCISAL",
        payload=ToothSurfaceUpdate(condition="OBSERVATION"),
        actor=dentist,
        db=db,  # type: ignore[arg-type]
    )
    assert surf_res.surface == "INCISAL"

    # 5. Add Condition
    cond_res = await o_api.add_tooth_condition(
        id=t11_id,
        payload=ToothConditionCreate(
            condition="CARIES",
            surfaces=[ToothSurfaceEnum.INCISAL],
        ),
        actor=dentist,
        db=db,  # type: ignore[arg-type]
    )
    assert cond_res.primary_status == "CARIES"

    # 6. Add Procedure
    proc_res = await o_api.add_tooth_procedure(
        id=t11_id,
        payload=ToothProcedureCreate(
            procedure_name="Composite Restoration",
            procedure_type="FILLING",
            surfaces=[ToothSurfaceEnum.INCISAL],
            cost=1800.0,
        ),
        actor=dentist,
        db=db,  # type: ignore[arg-type]
    )
    assert proc_res.primary_status == "FILLING"

    # 7. Get Tooth History
    history = await o_api.get_tooth_history(id=t11_id, actor=dentist, db=db)  # type: ignore[arg-type]
    assert len(history) >= 1

    # 8. Get Patient Tooth History
    pat_history = await o_api.get_patient_tooth_history(id=patient.id, actor=dentist, db=db)  # type: ignore[arg-type]
    assert len(pat_history) >= 1

    # 9. Get Dashboard Stats
    stats = await o_api.get_odontogram_dashboard_stats(actor=dentist, db=db)  # type: ignore[arg-type]
    assert stats.total_teeth_charted >= 32


@pytest.mark.asyncio
async def test_odontogram_api_tenant_isolation_idor():
    clinic_a_id = uuid4()
    clinic_b_id = uuid4()

    patient_b = Patient(
        id=uuid4(),
        clinic_id=clinic_b_id,
        patient_number="PAT-B-001",
        first_name="Foreign",
        last_name="Patient",
        gender="MALE",
        mobile_number="9111111111",
    )

    dentist_a = User(
        id=uuid4(),
        clinic_id=clinic_a_id,
        email="dr.a@clinica.com",
        first_name="Alice",
        last_name="Dentist",
        role=Role.DENTIST,
    )

    db = InMemoryDbApi(patient_b)

    # Clinician from Clinic A attempting to access Patient from Clinic B -> 404
    with pytest.raises(HTTPException) as exc_info:
        await o_api.get_patient_odontogram(
            id=patient_b.id, dentition="ADULT", actor=dentist_a, db=db  # type: ignore[arg-type]
        )
    assert exc_info.value.status_code == 404
    assert "not found in this clinic" in exc_info.value.detail
