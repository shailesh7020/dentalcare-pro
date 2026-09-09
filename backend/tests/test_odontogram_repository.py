from __future__ import annotations

from uuid import uuid4

import pytest

from app.models.odontogram import (
    COLOR_STANDARDS,
    DentitionType,
    Tooth,
    ToothCondition,
    ToothSurfaceEnum,
)
from app.repositories.odontogram_repository import (
    ADULT_TEETH_CATALOG,
    PRIMARY_TEETH_CATALOG,
    OdontogramRepository,
)


class InMemoryDb:
    def __init__(self):
        self.items: list[object] = []
        self.added: list[object] = []
        self.flushes = 0
        self.commits = 0

    def add(self, item: object) -> None:
        self.added.append(item)
        if item not in self.items:
            self.items.append(item)

    async def flush(self) -> None:
        self.flushes += 1

    async def commit(self) -> None:
        self.commits += 1

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

        # Aggregate query
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
            matching = [item for item in self.items if hasattr(item, "surface")]
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


@pytest.mark.asyncio
async def test_odontogram_repository_adult_initialization():
    db = InMemoryDb()
    repo = OdontogramRepository(db)  # type: ignore[arg-type]

    clinic_id = uuid4()
    patient_id = uuid4()
    user_id = uuid4()

    teeth = await repo.get_or_initialize_odontogram(
        clinic_id=clinic_id,
        patient_id=patient_id,
        dentition_type=DentitionType.ADULT,
        user_id=user_id,
    )

    # 32 adult teeth
    assert len(teeth) == 32
    assert len(ADULT_TEETH_CATALOG) == 32

    # Check tooth #11 (Maxillary Right Central Incisor)
    t11 = next(t for t in teeth if t.tooth_number == "11")
    assert t11.universal_number == "8"
    assert t11.palmer_notation == "UR1"
    assert t11.name == "Maxillary Right Central Incisor"
    assert t11.primary_status == ToothCondition.HEALTHY.value
    assert t11.color == COLOR_STANDARDS[ToothCondition.HEALTHY]

    # Verify surfaces (7 surfaces: Mesial, Distal, Buccal, Lingual, Incisal, Cervical, Root)
    assert len(t11.surfaces) == 7
    surf_names = [s.surface for s in t11.surfaces]
    assert ToothSurfaceEnum.INCISAL.value in surf_names
    assert ToothSurfaceEnum.MESIAL.value in surf_names
    assert ToothSurfaceEnum.DISTAL.value in surf_names
    assert ToothSurfaceEnum.BUCCAL.value in surf_names
    assert ToothSurfaceEnum.LINGUAL.value in surf_names

    # Check molar #16 has Occlusal
    t16 = next(t for t in teeth if t.tooth_number == "16")
    molar_surfs = [s.surface for s in t16.surfaces]
    assert ToothSurfaceEnum.OCCLUSAL.value in molar_surfs

    # Verify history
    assert len(t11.history) >= 1
    assert t11.history[0].action == "INITIALIZED"


@pytest.mark.asyncio
async def test_odontogram_repository_primary_initialization():
    db = InMemoryDb()
    repo = OdontogramRepository(db)  # type: ignore[arg-type]

    clinic_id = uuid4()
    patient_id = uuid4()

    teeth = await repo.get_or_initialize_odontogram(
        clinic_id=clinic_id,
        patient_id=patient_id,
        dentition_type=DentitionType.PRIMARY,
    )

    # 20 primary teeth
    assert len(teeth) == 20
    assert len(PRIMARY_TEETH_CATALOG) == 20

    # Tooth #51 (Primary Maxillary Right Central Incisor)
    t51 = next(t for t in teeth if t.tooth_number == "51")
    assert t51.universal_number == "E"
    assert t51.palmer_notation == "URA"


@pytest.mark.asyncio
async def test_odontogram_repository_append_history_and_stats():
    db = InMemoryDb()
    repo = OdontogramRepository(db)  # type: ignore[arg-type]

    clinic_id = uuid4()
    patient_id = uuid4()

    teeth = await repo.get_or_initialize_odontogram(clinic_id, patient_id)
    t11 = teeth[0]

    history_entry = await repo.append_history(
        clinic_id=clinic_id,
        patient_id=patient_id,
        tooth_id=t11.id,
        action="TEST_ACTION",
        description="Repository test history entry",
        previous_state={"primary_status": "HEALTHY"},
        new_state={"primary_status": "CARIES"},
    )
    assert history_entry.id is not None
    assert history_entry.action == "TEST_ACTION"

    stats = await repo.get_dashboard_stats(clinic_id, patient_id)
    assert "total_teeth_charted" in stats
    assert stats["total_teeth_charted"] == 32
