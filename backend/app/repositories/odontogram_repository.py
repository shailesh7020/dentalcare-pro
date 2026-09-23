from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.odontogram import (
    COLOR_STANDARDS,
    DentitionType,
    Tooth,
    ToothArch,
    ToothCondition,
    ToothHistory,
    ToothSurface,
    ToothSurfaceEnum,
    ToothType,
)

# Canonical Adult Dentition Catalog (32 teeth)
ADULT_TEETH_CATALOG = [
    # Upper Right (Quadrant 1)
    {"number": "18", "universal": "1", "palmer": "UR8", "name": "Maxillary Right Third Molar", "arch": ToothArch.UPPER, "quadrant": 1, "type": ToothType.MOLAR, "center": ToothSurfaceEnum.OCCLUSAL},
    {"number": "17", "universal": "2", "palmer": "UR7", "name": "Maxillary Right Second Molar", "arch": ToothArch.UPPER, "quadrant": 1, "type": ToothType.MOLAR, "center": ToothSurfaceEnum.OCCLUSAL},
    {"number": "16", "universal": "3", "palmer": "UR6", "name": "Maxillary Right First Molar", "arch": ToothArch.UPPER, "quadrant": 1, "type": ToothType.MOLAR, "center": ToothSurfaceEnum.OCCLUSAL},
    {"number": "15", "universal": "4", "palmer": "UR5", "name": "Maxillary Right Second Premolar", "arch": ToothArch.UPPER, "quadrant": 1, "type": ToothType.PREMOLAR, "center": ToothSurfaceEnum.OCCLUSAL},
    {"number": "14", "universal": "5", "palmer": "UR4", "name": "Maxillary Right First Premolar", "arch": ToothArch.UPPER, "quadrant": 1, "type": ToothType.PREMOLAR, "center": ToothSurfaceEnum.OCCLUSAL},
    {"number": "13", "universal": "6", "palmer": "UR3", "name": "Maxillary Right Canine", "arch": ToothArch.UPPER, "quadrant": 1, "type": ToothType.CANINE, "center": ToothSurfaceEnum.INCISAL},
    {"number": "12", "universal": "7", "palmer": "UR2", "name": "Maxillary Right Lateral Incisor", "arch": ToothArch.UPPER, "quadrant": 1, "type": ToothType.INCISOR, "center": ToothSurfaceEnum.INCISAL},
    {"number": "11", "universal": "8", "palmer": "UR1", "name": "Maxillary Right Central Incisor", "arch": ToothArch.UPPER, "quadrant": 1, "type": ToothType.INCISOR, "center": ToothSurfaceEnum.INCISAL},
    # Upper Left (Quadrant 2)
    {"number": "21", "universal": "9", "palmer": "UL1", "name": "Maxillary Left Central Incisor", "arch": ToothArch.UPPER, "quadrant": 2, "type": ToothType.INCISOR, "center": ToothSurfaceEnum.INCISAL},
    {"number": "22", "universal": "10", "palmer": "UL2", "name": "Maxillary Left Lateral Incisor", "arch": ToothArch.UPPER, "quadrant": 2, "type": ToothType.INCISOR, "center": ToothSurfaceEnum.INCISAL},
    {"number": "23", "universal": "11", "palmer": "UL3", "name": "Maxillary Left Canine", "arch": ToothArch.UPPER, "quadrant": 2, "type": ToothType.CANINE, "center": ToothSurfaceEnum.INCISAL},
    {"number": "24", "universal": "12", "palmer": "UL4", "name": "Maxillary Left First Premolar", "arch": ToothArch.UPPER, "quadrant": 2, "type": ToothType.PREMOLAR, "center": ToothSurfaceEnum.OCCLUSAL},
    {"number": "25", "universal": "13", "palmer": "UL5", "name": "Maxillary Left Second Premolar", "arch": ToothArch.UPPER, "quadrant": 2, "type": ToothType.PREMOLAR, "center": ToothSurfaceEnum.OCCLUSAL},
    {"number": "26", "universal": "14", "palmer": "UL6", "name": "Maxillary Left First Molar", "arch": ToothArch.UPPER, "quadrant": 2, "type": ToothType.MOLAR, "center": ToothSurfaceEnum.OCCLUSAL},
    {"number": "27", "universal": "15", "palmer": "UL7", "name": "Maxillary Left Second Molar", "arch": ToothArch.UPPER, "quadrant": 2, "type": ToothType.MOLAR, "center": ToothSurfaceEnum.OCCLUSAL},
    {"number": "28", "universal": "16", "palmer": "UL8", "name": "Maxillary Left Third Molar", "arch": ToothArch.UPPER, "quadrant": 2, "type": ToothType.MOLAR, "center": ToothSurfaceEnum.OCCLUSAL},
    # Lower Left (Quadrant 3)
    {"number": "38", "universal": "17", "palmer": "LL8", "name": "Mandibular Left Third Molar", "arch": ToothArch.LOWER, "quadrant": 3, "type": ToothType.MOLAR, "center": ToothSurfaceEnum.OCCLUSAL},
    {"number": "37", "universal": "18", "palmer": "LL7", "name": "Mandibular Left Second Molar", "arch": ToothArch.LOWER, "quadrant": 3, "type": ToothType.MOLAR, "center": ToothSurfaceEnum.OCCLUSAL},
    {"number": "36", "universal": "19", "palmer": "LL6", "name": "Mandibular Left First Molar", "arch": ToothArch.LOWER, "quadrant": 3, "type": ToothType.MOLAR, "center": ToothSurfaceEnum.OCCLUSAL},
    {"number": "35", "universal": "20", "palmer": "LL5", "name": "Mandibular Left Second Premolar", "arch": ToothArch.LOWER, "quadrant": 3, "type": ToothType.PREMOLAR, "center": ToothSurfaceEnum.OCCLUSAL},
    {"number": "34", "universal": "21", "palmer": "LL4", "name": "Mandibular Left First Premolar", "arch": ToothArch.LOWER, "quadrant": 3, "type": ToothType.PREMOLAR, "center": ToothSurfaceEnum.OCCLUSAL},
    {"number": "33", "universal": "22", "palmer": "LL3", "name": "Mandibular Left Canine", "arch": ToothArch.LOWER, "quadrant": 3, "type": ToothType.CANINE, "center": ToothSurfaceEnum.INCISAL},
    {"number": "32", "universal": "23", "palmer": "LL2", "name": "Mandibular Left Lateral Incisor", "arch": ToothArch.LOWER, "quadrant": 3, "type": ToothType.INCISOR, "center": ToothSurfaceEnum.INCISAL},
    {"number": "31", "universal": "24", "palmer": "LL1", "name": "Mandibular Left Central Incisor", "arch": ToothArch.LOWER, "quadrant": 3, "type": ToothType.INCISOR, "center": ToothSurfaceEnum.INCISAL},
    # Lower Right (Quadrant 4)
    {"number": "41", "universal": "25", "palmer": "LR1", "name": "Mandibular Right Central Incisor", "arch": ToothArch.LOWER, "quadrant": 4, "type": ToothType.INCISOR, "center": ToothSurfaceEnum.INCISAL},
    {"number": "42", "universal": "26", "palmer": "LR2", "name": "Mandibular Right Lateral Incisor", "arch": ToothArch.LOWER, "quadrant": 4, "type": ToothType.INCISOR, "center": ToothSurfaceEnum.INCISAL},
    {"number": "43", "universal": "27", "palmer": "LR3", "name": "Mandibular Right Canine", "arch": ToothArch.LOWER, "quadrant": 4, "type": ToothType.CANINE, "center": ToothSurfaceEnum.INCISAL},
    {"number": "44", "universal": "28", "palmer": "LR4", "name": "Mandibular Right First Premolar", "arch": ToothArch.LOWER, "quadrant": 4, "type": ToothType.PREMOLAR, "center": ToothSurfaceEnum.OCCLUSAL},
    {"number": "45", "universal": "29", "palmer": "LR5", "name": "Mandibular Right Second Premolar", "arch": ToothArch.LOWER, "quadrant": 4, "type": ToothType.PREMOLAR, "center": ToothSurfaceEnum.OCCLUSAL},
    {"number": "46", "universal": "30", "palmer": "LR6", "name": "Mandibular Right First Molar", "arch": ToothArch.LOWER, "quadrant": 4, "type": ToothType.MOLAR, "center": ToothSurfaceEnum.OCCLUSAL},
    {"number": "47", "universal": "31", "palmer": "LR7", "name": "Mandibular Right Second Molar", "arch": ToothArch.LOWER, "quadrant": 4, "type": ToothType.MOLAR, "center": ToothSurfaceEnum.OCCLUSAL},
    {"number": "48", "universal": "32", "palmer": "LR8", "name": "Mandibular Right Third Molar", "arch": ToothArch.LOWER, "quadrant": 4, "type": ToothType.MOLAR, "center": ToothSurfaceEnum.OCCLUSAL},
]

# Canonical Primary Dentition Catalog (20 teeth)
PRIMARY_TEETH_CATALOG = [
    # Upper Right (Quadrant 5)
    {"number": "55", "universal": "A", "palmer": "URE", "name": "Primary Maxillary Right Second Molar", "arch": ToothArch.UPPER, "quadrant": 5, "type": ToothType.MOLAR, "center": ToothSurfaceEnum.OCCLUSAL},
    {"number": "54", "universal": "B", "palmer": "URD", "name": "Primary Maxillary Right First Molar", "arch": ToothArch.UPPER, "quadrant": 5, "type": ToothType.MOLAR, "center": ToothSurfaceEnum.OCCLUSAL},
    {"number": "53", "universal": "C", "palmer": "URC", "name": "Primary Maxillary Right Canine", "arch": ToothArch.UPPER, "quadrant": 5, "type": ToothType.CANINE, "center": ToothSurfaceEnum.INCISAL},
    {"number": "52", "universal": "D", "palmer": "URB", "name": "Primary Maxillary Right Lateral Incisor", "arch": ToothArch.UPPER, "quadrant": 5, "type": ToothType.INCISOR, "center": ToothSurfaceEnum.INCISAL},
    {"number": "51", "universal": "E", "palmer": "URA", "name": "Primary Maxillary Right Central Incisor", "arch": ToothArch.UPPER, "quadrant": 5, "type": ToothType.INCISOR, "center": ToothSurfaceEnum.INCISAL},
    # Upper Left (Quadrant 6)
    {"number": "61", "universal": "F", "palmer": "ULA", "name": "Primary Maxillary Left Central Incisor", "arch": ToothArch.UPPER, "quadrant": 6, "type": ToothType.INCISOR, "center": ToothSurfaceEnum.INCISAL},
    {"number": "62", "universal": "G", "palmer": "ULB", "name": "Primary Maxillary Left Lateral Incisor", "arch": ToothArch.UPPER, "quadrant": 6, "type": ToothType.INCISOR, "center": ToothSurfaceEnum.INCISAL},
    {"number": "63", "universal": "H", "palmer": "ULC", "name": "Primary Maxillary Left Canine", "arch": ToothArch.UPPER, "quadrant": 6, "type": ToothType.CANINE, "center": ToothSurfaceEnum.INCISAL},
    {"number": "64", "universal": "I", "palmer": "ULD", "name": "Primary Maxillary Left First Molar", "arch": ToothArch.UPPER, "quadrant": 6, "type": ToothType.MOLAR, "center": ToothSurfaceEnum.OCCLUSAL},
    {"number": "65", "universal": "J", "palmer": "ULE", "name": "Primary Maxillary Left Second Molar", "arch": ToothArch.UPPER, "quadrant": 6, "type": ToothType.MOLAR, "center": ToothSurfaceEnum.OCCLUSAL},
    # Lower Left (Quadrant 7)
    {"number": "75", "universal": "K", "palmer": "LLE", "name": "Primary Mandibular Left Second Molar", "arch": ToothArch.LOWER, "quadrant": 7, "type": ToothType.MOLAR, "center": ToothSurfaceEnum.OCCLUSAL},
    {"number": "74", "universal": "L", "palmer": "LLD", "name": "Primary Mandibular Left First Molar", "arch": ToothArch.LOWER, "quadrant": 7, "type": ToothType.MOLAR, "center": ToothSurfaceEnum.OCCLUSAL},
    {"number": "73", "universal": "M", "palmer": "LLC", "name": "Primary Mandibular Left Canine", "arch": ToothArch.LOWER, "quadrant": 7, "type": ToothType.CANINE, "center": ToothSurfaceEnum.INCISAL},
    {"number": "72", "universal": "N", "palmer": "LLB", "name": "Primary Mandibular Left Lateral Incisor", "arch": ToothArch.LOWER, "quadrant": 7, "type": ToothType.INCISOR, "center": ToothSurfaceEnum.INCISAL},
    {"number": "71", "universal": "O", "palmer": "LLA", "name": "Primary Mandibular Left Central Incisor", "arch": ToothArch.LOWER, "quadrant": 7, "type": ToothType.INCISOR, "center": ToothSurfaceEnum.INCISAL},
    # Lower Right (Quadrant 8)
    {"number": "81", "universal": "P", "palmer": "LRA", "name": "Primary Mandibular Right Central Incisor", "arch": ToothArch.LOWER, "quadrant": 8, "type": ToothType.INCISOR, "center": ToothSurfaceEnum.INCISAL},
    {"number": "82", "universal": "Q", "palmer": "LRB", "name": "Primary Mandibular Right Lateral Incisor", "arch": ToothArch.LOWER, "quadrant": 8, "type": ToothType.INCISOR, "center": ToothSurfaceEnum.INCISAL},
    {"number": "83", "universal": "R", "palmer": "LRC", "name": "Primary Mandibular Right Canine", "arch": ToothArch.LOWER, "quadrant": 8, "type": ToothType.CANINE, "center": ToothSurfaceEnum.INCISAL},
    {"number": "84", "universal": "S", "palmer": "LRD", "name": "Primary Mandibular Right First Molar", "arch": ToothArch.LOWER, "quadrant": 8, "type": ToothType.MOLAR, "center": ToothSurfaceEnum.OCCLUSAL},
    {"number": "85", "universal": "T", "palmer": "LRE", "name": "Primary Mandibular Right Second Molar", "arch": ToothArch.LOWER, "quadrant": 8, "type": ToothType.MOLAR, "center": ToothSurfaceEnum.OCCLUSAL},
]


class OdontogramRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_teeth_by_patient(
        self, clinic_id: UUID, patient_id: UUID, dentition_type: str = "ADULT"
    ) -> list[Tooth]:
        dentition_str = (
            dentition_type.value
            if hasattr(dentition_type, "value")
            else str(dentition_type)
        ).upper()
        query = (
            select(Tooth)
            .where(
                Tooth.clinic_id == clinic_id,
                Tooth.patient_id == patient_id,
                Tooth.dentition_type == dentition_str,
                Tooth.deleted_at.is_(None),
            )
            .options(
                selectinload(Tooth.surfaces),
            )
            .order_by(Tooth.quadrant.asc(), Tooth.tooth_number.asc())
        )
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def get_or_initialize_odontogram(
        self,
        clinic_id: UUID,
        patient_id: UUID,
        dentition_type: str = "ADULT",
        user_id: UUID | None = None,
    ) -> list[Tooth]:
        dentition_str = (
            dentition_type.value
            if hasattr(dentition_type, "value")
            else str(dentition_type)
        ).upper()

        catalog = (
            ADULT_TEETH_CATALOG
            if dentition_str == DentitionType.ADULT.value
            else PRIMARY_TEETH_CATALOG
        )

        catalog_map = {entry["number"]: entry for entry in catalog}
        existing_teeth = await self.get_teeth_by_patient(clinic_id, patient_id, dentition_str)
        existing_by_num = {t.tooth_number: t for t in existing_teeth}

        modified = False

        # 1. Normalize and repair any existing teeth
        for t_num, tooth in existing_by_num.items():
            if t_num in catalog_map:
                entry = catalog_map[t_num]
                c_arch = entry["arch"].value if hasattr(entry["arch"], "value") else str(entry["arch"])
                c_quad = entry["quadrant"]
                c_type = entry["type"].value if hasattr(entry["type"], "value") else str(entry["type"])

                if tooth.arch != c_arch:
                    tooth.arch = c_arch
                    modified = True
                if tooth.quadrant != c_quad:
                    tooth.quadrant = c_quad
                    modified = True
                if tooth.tooth_type != c_type:
                    tooth.tooth_type = c_type
                    modified = True
                if not tooth.universal_number or tooth.universal_number != entry["universal"]:
                    tooth.universal_number = entry["universal"]
                    modified = True
                if not tooth.palmer_notation or tooth.palmer_notation != entry["palmer"]:
                    tooth.palmer_notation = entry["palmer"]
                    modified = True
                if not tooth.name or tooth.name != entry["name"]:
                    tooth.name = entry["name"]
                    modified = True

                # Check if tooth has surfaces; if not, initialize them
                tooth_surfs = getattr(tooth, "surfaces", None)
                if not tooth_surfs:
                    surfaces_to_create = [
                        ToothSurfaceEnum.MESIAL,
                        ToothSurfaceEnum.DISTAL,
                        ToothSurfaceEnum.BUCCAL,
                        ToothSurfaceEnum.LINGUAL,
                        entry["center"],
                        ToothSurfaceEnum.CERVICAL,
                        ToothSurfaceEnum.ROOT,
                    ]
                    if tooth.surfaces is None:
                        tooth.surfaces = []
                    for s in surfaces_to_create:
                        surf_name = s.value if hasattr(s, "value") else str(s)
                        surf = ToothSurface(
                            id=uuid4(),
                            clinic_id=clinic_id,
                            tooth_id=tooth.id,
                            surface=surf_name,
                            condition=ToothCondition.HEALTHY.value,
                            treatment="NONE",
                            color=COLOR_STANDARDS[ToothCondition.HEALTHY],
                            last_modified_at=datetime.now(UTC),
                            created_by=user_id,
                            updated_by=user_id,
                        )
                        tooth.surfaces.append(surf)
                        self.db.add(surf)
                    modified = True

        # 2. Check for missing teeth from catalog and create them
        missing_entries = [entry for entry in catalog if entry["number"] not in existing_by_num]
        if missing_entries:
            modified = True
            for entry in missing_entries:
                tooth = Tooth(
                    id=uuid4(),
                    clinic_id=clinic_id,
                    patient_id=patient_id,
                    tooth_number=entry["number"],
                    universal_number=entry["universal"],
                    palmer_notation=entry["palmer"],
                    name=entry["name"],
                    dentition_type=dentition_str,
                    arch=entry["arch"].value if hasattr(entry["arch"], "value") else str(entry["arch"]),
                    quadrant=entry["quadrant"],
                    tooth_type=entry["type"].value if hasattr(entry["type"], "value") else str(entry["type"]),
                    primary_status=ToothCondition.HEALTHY.value,
                    color=COLOR_STANDARDS[ToothCondition.HEALTHY],
                    is_missing=False,
                    is_extracted=False,
                    is_impacted=False,
                    has_root_canal=False,
                    has_crown=False,
                    has_implant=False,
                    has_bridge=False,
                    mobility_grade=0,
                    created_by=user_id,
                    updated_by=user_id,
                )

                surfaces_to_create = [
                    ToothSurfaceEnum.MESIAL,
                    ToothSurfaceEnum.DISTAL,
                    ToothSurfaceEnum.BUCCAL,
                    ToothSurfaceEnum.LINGUAL,
                    entry["center"],
                    ToothSurfaceEnum.CERVICAL,
                    ToothSurfaceEnum.ROOT,
                ]

                for s in surfaces_to_create:
                    surf_name = s.value if hasattr(s, "value") else str(s)
                    surf = ToothSurface(
                        id=uuid4(),
                        clinic_id=clinic_id,
                        tooth_id=tooth.id,
                        surface=surf_name,
                        condition=ToothCondition.HEALTHY.value,
                        treatment="NONE",
                        color=COLOR_STANDARDS[ToothCondition.HEALTHY],
                        last_modified_at=datetime.now(UTC),
                        created_by=user_id,
                        updated_by=user_id,
                    )
                    tooth.surfaces.append(surf)

                tooth.history.append(
                    ToothHistory(
                        id=uuid4(),
                        clinic_id=clinic_id,
                        patient_id=patient_id,
                        tooth_id=tooth.id,
                        action="INITIALIZED",
                        description=f"Initialized tooth #{entry['number']} as healthy {dentition_str.lower()} dentition.",
                        previous_state=None,
                        new_state=json.dumps({"primary_status": ToothCondition.HEALTHY.value, "surfaces": "ALL_HEALTHY"}),
                        created_at=datetime.now(UTC),
                        created_by=user_id,
                    )
                )

                self.db.add(tooth)
                existing_by_num[entry["number"]] = tooth

        if modified:
            await self.db.flush()
            if hasattr(self.db, "commit"):
                await self.db.commit()

        # Re-fetch or return complete sorted teeth
        all_teeth = await self.get_teeth_by_patient(clinic_id, patient_id, dentition_str)
        if not all_teeth:
            all_teeth = list(existing_by_num.values())
        return all_teeth

    async def get_tooth_by_id(self, clinic_id: UUID, tooth_id: UUID) -> Tooth | None:
        tooth = await self.db.get(Tooth, tooth_id)
        if tooth and getattr(tooth, "clinic_id", None) == clinic_id and getattr(tooth, "deleted_at", None) is None:
            return tooth

        query = (
            select(Tooth)
            .where(
                Tooth.id == tooth_id,
                Tooth.clinic_id == clinic_id,
                Tooth.deleted_at.is_(None),
            )
            .options(
                selectinload(Tooth.surfaces),
                selectinload(Tooth.history),
            )
        )
        res = await self.db.execute(query)
        scalars = getattr(res, "scalars", lambda: None)()
        if scalars and hasattr(scalars, "first"):
            item = scalars.first()
            if isinstance(item, Tooth) and item.id == tooth_id:
                return item
        return getattr(res, "scalar_one_or_none", lambda: None)()

    async def get_tooth_by_number(
        self, clinic_id: UUID, patient_id: UUID, tooth_number: str
    ) -> Tooth | None:
        # Standardize number (strip #, whitespace)
        clean_num = tooth_number.strip().replace("#", "").upper()
        query = (
            select(Tooth)
            .where(
                Tooth.clinic_id == clinic_id,
                Tooth.patient_id == patient_id,
                (
                    (Tooth.tooth_number == clean_num)
                    | (Tooth.universal_number == clean_num)
                    | (Tooth.palmer_notation == clean_num)
                ),
                Tooth.deleted_at.is_(None),
            )
            .options(
                selectinload(Tooth.surfaces),
                selectinload(Tooth.history),
            )
        )
        res = await self.db.execute(query)
        scalars = res.scalars()
        if hasattr(scalars, "first"):
            item = scalars.first()
        elif hasattr(scalars, "all"):
            items = scalars.all()
            item = items[0] if items else None
        else:
            item = None
        return item if isinstance(item, Tooth) else None

    async def get_surface(
        self, clinic_id: UUID, tooth_id: UUID, surface_name: str
    ) -> ToothSurface | None:
        tooth = await self.get_tooth_by_id(clinic_id, tooth_id)
        if tooth and tooth.surfaces:
            for s in tooth.surfaces:
                if s.surface.upper() == surface_name.upper():
                    return s

        query = select(ToothSurface).where(
            ToothSurface.clinic_id == clinic_id,
            ToothSurface.tooth_id == tooth_id,
            ToothSurface.surface == surface_name.upper(),
        )
        res = await self.db.execute(query)
        scalars = getattr(res, "scalars", lambda: None)()
        if scalars and hasattr(scalars, "first"):
            return scalars.first()
        return getattr(res, "scalar_one_or_none", lambda: None)()

    async def get_tooth_history(
        self, clinic_id: UUID, tooth_id: UUID
    ) -> list[ToothHistory]:
        query = (
            select(ToothHistory)
            .where(
                ToothHistory.clinic_id == clinic_id,
                ToothHistory.tooth_id == tooth_id,
            )
            .order_by(ToothHistory.created_at.desc())
        )
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def get_patient_tooth_history(
        self, clinic_id: UUID, patient_id: UUID
    ) -> list[ToothHistory]:
        query = (
            select(ToothHistory)
            .where(
                ToothHistory.clinic_id == clinic_id,
                ToothHistory.patient_id == patient_id,
            )
            .order_by(ToothHistory.created_at.desc())
        )
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def append_history(
        self,
        clinic_id: UUID,
        patient_id: UUID,
        tooth_id: UUID,
        action: str,
        description: str,
        previous_state: dict[str, Any] | None = None,
        new_state: dict[str, Any] | None = None,
        affected_surfaces: str | None = None,
        treatment_id: UUID | None = None,
        treatment_procedure_id: UUID | None = None,
        appointment_id: UUID | None = None,
        dentist_id: UUID | None = None,
        user_id: UUID | None = None,
    ) -> ToothHistory:
        entry = ToothHistory(
            id=uuid4(),
            clinic_id=clinic_id,
            patient_id=patient_id,
            tooth_id=tooth_id,
            action=action,
            description=description,
            previous_state=json.dumps(previous_state) if previous_state else None,
            new_state=json.dumps(new_state) if new_state else None,
            affected_surfaces=affected_surfaces,
            treatment_id=treatment_id,
            treatment_procedure_id=treatment_procedure_id,
            appointment_id=appointment_id,
            dentist_id=dentist_id,
            created_at=datetime.now(UTC),
            created_by=user_id,
        )
        self.db.add(entry)
        await self.db.flush()
        return entry

    async def get_dashboard_stats(
        self, clinic_id: UUID, patient_id: UUID | None = None
    ) -> dict[str, int]:
        filters = [Tooth.clinic_id == clinic_id, Tooth.deleted_at.is_(None)]
        if patient_id:
            filters.append(Tooth.patient_id == patient_id)

        query = (
            select(
                func.count(Tooth.id).label("total"),
                func.count().filter(Tooth.primary_status == ToothCondition.CARIES.value).label("caries"),
                func.count().filter(Tooth.is_missing.is_(True) | (Tooth.primary_status == ToothCondition.MISSING.value)).label("missing"),
                func.count().filter(Tooth.has_root_canal.is_(True) | (Tooth.primary_status == ToothCondition.ROOT_CANAL.value)).label("root_canals"),
                func.count().filter(Tooth.has_crown.is_(True) | (Tooth.primary_status == ToothCondition.CROWN.value)).label("crowns"),
                func.count().filter(Tooth.has_implant.is_(True) | (Tooth.primary_status == ToothCondition.IMPLANT.value)).label("implants"),
                func.count().filter(Tooth.primary_status == ToothCondition.FILLING.value).label("restorations"),
            )
            .where(*filters)
        )
        res = await self.db.execute(query)
        if hasattr(res, "one"):
            row = res.one()
        elif hasattr(res, "scalar_one"):
            row = res.scalar_one()
        else:
            row = getattr(res, "scalar", lambda: None)()
        return {
            "total_teeth_charted": getattr(row, "total", 0) or 0,
            "active_caries": getattr(row, "caries", 0) or 0,
            "missing_teeth": getattr(row, "missing", 0) or 0,
            "root_canals": getattr(row, "root_canals", 0) or 0,
            "crowns": getattr(row, "crowns", 0) or 0,
            "implants": getattr(row, "implants", 0) or 0,
            "restorations": getattr(row, "restorations", 0) or 0,
        }
