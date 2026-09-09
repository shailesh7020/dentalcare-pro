from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.identity import User
from app.models.patient import Patient
from app.models.prescription import (
    DosageFrequency,
    MedicineCatalog,
    MedicineForm,
    Prescription,
    PrescriptionItem,
    PrescriptionStatus,
    PrescriptionTemplate,
    TemplateCategory,
)
from app.models.treatment import Treatment
from app.schemas.prescription import (
    MedicineCatalogCreate,
    PrescriptionCreate,
    PrescriptionDashboardStats,
    PrescriptionDetail,
    PrescriptionItemRead,
    PrescriptionTemplateCreate,
    PrescriptionUpdate,
)

STANDARD_MEDICINES: list[dict[str, Any]] = [
    {
        "generic_name": "Amoxicillin",
        "brand_name": "Amoxil 500",
        "strength": "500 mg",
        "form": MedicineForm.CAPSULE,
        "category": "Antibiotic",
        "standard_dosage": "500 mg TID for 5 days",
        "default_route": "Oral",
        "default_frequency": DosageFrequency.TDS,
        "default_duration": "5 days",
        "default_instructions": "After food",
        "notes": "First-line dental antibacterial prophylaxis and treatment.",
    },
    {
        "generic_name": "Amoxicillin + Potassium Clavulanate",
        "brand_name": "Augmentin 625 Duo",
        "strength": "625 mg",
        "form": MedicineForm.TABLET,
        "category": "Antibiotic",
        "standard_dosage": "625 mg BID for 5 days",
        "default_route": "Oral",
        "default_frequency": DosageFrequency.BD,
        "default_duration": "5 days",
        "default_instructions": "With food / immediately after food",
        "notes": "Broad-spectrum beta-lactamase inhibitor for resistant odontogenic infections.",
    },
    {
        "generic_name": "Metronidazole",
        "brand_name": "Flagyl 400",
        "strength": "400 mg",
        "form": MedicineForm.TABLET,
        "category": "Antibiotic / Antiprotozoal",
        "standard_dosage": "400 mg TID for 5 days",
        "default_route": "Oral",
        "default_frequency": DosageFrequency.TDS,
        "default_duration": "5 days",
        "default_instructions": "After food",
        "notes": "Anaerobic coverage for periodontal abscesses and pericoronitis. Avoid alcohol.",
    },
    {
        "generic_name": "Ibuprofen",
        "brand_name": "Brufen 400",
        "strength": "400 mg",
        "form": MedicineForm.TABLET,
        "category": "Analgesic / NSAID",
        "standard_dosage": "400 mg TID as needed",
        "default_route": "Oral",
        "default_frequency": DosageFrequency.TDS,
        "default_duration": "3 days",
        "default_instructions": "Strictly after meals",
        "notes": "Anti-inflammatory and dental pain relief.",
    },
    {
        "generic_name": "Paracetamol",
        "brand_name": "Dolo 650",
        "strength": "650 mg",
        "form": MedicineForm.TABLET,
        "category": "Analgesic / Antipyretic",
        "standard_dosage": "650 mg TID as needed",
        "default_route": "Oral",
        "default_frequency": DosageFrequency.TDS,
        "default_duration": "3 days",
        "default_instructions": "After food",
        "notes": "Mild-to-moderate dental pain relief and antipyretic.",
    },
    {
        "generic_name": "Aceclofenac + Paracetamol",
        "brand_name": "Zerodol-P",
        "strength": "100 mg + 325 mg",
        "form": MedicineForm.TABLET,
        "category": "Analgesic / NSAID",
        "standard_dosage": "1 tablet BID for 3 days",
        "default_route": "Oral",
        "default_frequency": DosageFrequency.BD,
        "default_duration": "3 days",
        "default_instructions": "After food",
        "notes": "Acute dental pain and post-extraction inflammation.",
    },
    {
        "generic_name": "Ketorolac Tromethamine",
        "brand_name": "Ketorol DT",
        "strength": "10 mg",
        "form": MedicineForm.TABLET,
        "category": "Analgesic / NSAID",
        "standard_dosage": "10 mg sublingual/dispersible SOS",
        "default_route": "Oral",
        "default_frequency": DosageFrequency.SOS,
        "default_duration": "2 days",
        "default_instructions": "Disperse in water or swallow after food",
        "notes": "Potent emergency NSAID for severe acute dental pain. Short term only.",
    },
    {
        "generic_name": "Diclofenac Potassium",
        "brand_name": "Voveran 50",
        "strength": "50 mg",
        "form": MedicineForm.TABLET,
        "category": "Analgesic / NSAID",
        "standard_dosage": "50 mg BID for 3 days",
        "default_route": "Oral",
        "default_frequency": DosageFrequency.BD,
        "default_duration": "3 days",
        "default_instructions": "After food",
        "notes": "Rapid onset post-surgical and odontogenic analgesia.",
    },
    {
        "generic_name": "Azithromycin",
        "brand_name": "Azee 500",
        "strength": "500 mg",
        "form": MedicineForm.TABLET,
        "category": "Antibiotic",
        "standard_dosage": "500 mg once daily for 3 days",
        "default_route": "Oral",
        "default_frequency": DosageFrequency.OD,
        "default_duration": "3 days",
        "default_instructions": "1 hour before or 2 hours after food",
        "notes": "Macrolide antibiotic alternative for penicillin-allergic patients.",
    },
    {
        "generic_name": "Clindamycin",
        "brand_name": "Dalacin C 300",
        "strength": "300 mg",
        "form": MedicineForm.CAPSULE,
        "category": "Antibiotic",
        "standard_dosage": "300 mg TID for 5 days",
        "default_route": "Oral",
        "default_frequency": DosageFrequency.TDS,
        "default_duration": "5 days",
        "default_instructions": "Take with a full glass of water",
        "notes": "High alveolar bone penetration for deep periapical infections.",
    },
    {
        "generic_name": "Chlorhexidine Gluconate 0.2%",
        "brand_name": "Hexidine Mouthwash",
        "strength": "0.2% w/v",
        "form": MedicineForm.MOUTHWASH,
        "category": "Antiseptic",
        "standard_dosage": "10 ml rinse twice daily for 14 days",
        "default_route": "Topical",
        "default_frequency": DosageFrequency.BD,
        "default_duration": "14 days",
        "default_instructions": "Swish for 60 seconds undiluted, do not swallow",
        "notes": "Anti-plaque antiseptic rinse for gingivitis and post-surgical hygiene.",
    },
    {
        "generic_name": "Moxifloxacin",
        "brand_name": "Avelox 400",
        "strength": "400 mg",
        "form": MedicineForm.TABLET,
        "category": "Antibiotic",
        "standard_dosage": "400 mg once daily for 5 days",
        "default_route": "Oral",
        "default_frequency": DosageFrequency.OD,
        "default_duration": "5 days",
        "default_instructions": "After food",
        "notes": "Advanced broad spectrum for complicated maxillofacial spaces.",
    },
    {
        "generic_name": "Doxycycline",
        "brand_name": "Doxicip 100",
        "strength": "100 mg",
        "form": MedicineForm.CAPSULE,
        "category": "Antibiotic / Host Modulator",
        "standard_dosage": "100 mg once daily for 14 days",
        "default_route": "Oral",
        "default_frequency": DosageFrequency.OD,
        "default_duration": "14 days",
        "default_instructions": "After food, remain upright for 30 minutes",
        "notes": "Periodontal host modulation and collagenase enzyme inhibition.",
    },
    {
        "generic_name": "Etoricoxib",
        "brand_name": "Nucoxia 90",
        "strength": "90 mg",
        "form": MedicineForm.TABLET,
        "category": "Analgesic / COX-2 Inhibitor",
        "standard_dosage": "90 mg once daily for 3 days",
        "default_route": "Oral",
        "default_frequency": DosageFrequency.OD,
        "default_duration": "3 days",
        "default_instructions": "After food",
        "notes": "Selective COX-2 anti-inflammatory with favorable gastric tolerance.",
    },
    {
        "generic_name": "Pantoprazole",
        "brand_name": "Pan 40",
        "strength": "40 mg",
        "form": MedicineForm.TABLET,
        "category": "Proton Pump Inhibitor",
        "standard_dosage": "40 mg once daily before breakfast",
        "default_route": "Oral",
        "default_frequency": DosageFrequency.OD,
        "default_duration": "5 days",
        "default_instructions": "Morning 30 minutes before breakfast",
        "notes": "Gastric mucosal protection prescribed alongside NSAID therapy.",
    },
    {
        "generic_name": "Choline Salicylate + Lignocaine",
        "brand_name": "Zytee Dental Gel",
        "strength": "8.7% + 2.0%",
        "form": MedicineForm.GEL,
        "category": "Topical Analgesic",
        "standard_dosage": "Apply thin film TID on ulcerated area",
        "default_route": "Topical",
        "default_frequency": DosageFrequency.TDS,
        "default_duration": "5 days",
        "default_instructions": "Apply clean finger, avoid eating for 15 minutes",
        "notes": "Mucosal anesthetic for aphthous ulcers, denture irritation, and braces.",
    },
    {
        "generic_name": "Triamcinolone Acetonide",
        "brand_name": "Kenacort 0.1% Oral Paste",
        "strength": "0.1% w/w",
        "form": MedicineForm.DENTAL_PASTE,
        "category": "Corticosteroid",
        "standard_dosage": "Dab small ribbon at bedtime",
        "default_route": "Topical",
        "default_frequency": DosageFrequency.BD,
        "default_duration": "5 days",
        "default_instructions": "Dab without rubbing to form adherent protective film",
        "notes": "Topical corticosteroid for non-infectious inflammatory oral ulcers.",
    },
]

STANDARD_TEMPLATES: list[dict[str, Any]] = [
    {
        "name": "Extraction Regimen (Post-Exodontia)",
        "category": TemplateCategory.EXTRACTION,
        "description": "Standard prophylactic antibiotic, NSAID, and gastroprotective protocol following tooth extraction.",
        "diagnosis_template": "Status post dental extraction. Suture placed, primary hemostasis achieved.",
        "instructions_template": "1. Do not spit, rinse, or use a straw for 24 hours.\n2. Keep cotton gauze pressed firmly for 45 minutes.\n3. Take soft, cold foods only. Avoid hot liquids and smoking.\n4. From tomorrow, rinse with warm saline or chlorhexidine mouthwash twice daily.",
        "default_items": [
            {
                "medicine_name": "Augmentin 625 Duo",
                "generic_name": "Amoxicillin + Potassium Clavulanate",
                "strength": "625 mg",
                "form": "TABLET",
                "dosage": "1 tablet",
                "route": "Oral",
                "frequency": "BD",
                "duration": "5 days",
                "quantity": 10,
                "timing": "Morning - Night",
                "food_instructions": "After food",
                "notes": "Complete the full 5-day course.",
            },
            {
                "medicine_name": "Zerodol-P",
                "generic_name": "Aceclofenac + Paracetamol",
                "strength": "100 mg + 325 mg",
                "form": "TABLET",
                "dosage": "1 tablet",
                "route": "Oral",
                "frequency": "BD",
                "duration": "3 days",
                "quantity": 6,
                "timing": "Morning - Night",
                "food_instructions": "Strictly after food",
                "notes": "For pain and swelling.",
            },
            {
                "medicine_name": "Pan 40",
                "generic_name": "Pantoprazole",
                "strength": "40 mg",
                "form": "TABLET",
                "dosage": "1 tablet",
                "route": "Oral",
                "frequency": "OD",
                "duration": "5 days",
                "quantity": 5,
                "timing": "Morning",
                "food_instructions": "30 mins before breakfast",
                "notes": "Gastric protection.",
            },
            {
                "medicine_name": "Hexidine Mouthwash",
                "generic_name": "Chlorhexidine Gluconate 0.2%",
                "strength": "0.2% w/v",
                "form": "MOUTHWASH",
                "dosage": "10 ml",
                "route": "Topical",
                "frequency": "BD",
                "duration": "7 days",
                "quantity": 1,
                "timing": "Morning - Night",
                "food_instructions": "After brushing",
                "notes": "Start 24 hours after extraction. Swish gently.",
            },
        ],
    },
    {
        "name": "Root Canal Therapy (Acute Pulpitis / Abscess)",
        "category": TemplateCategory.ROOT_CANAL,
        "description": "Endodontic infection control with dual coverage (aerobic + anaerobic) and analgesia.",
        "diagnosis_template": "Acute irreversible pulpitis / symptomatic apical periodontitis.",
        "instructions_template": "1. Avoid chewing hard foods on the treated side until the tooth is permanently restored.\n2. Mild soreness on biting is expected for 48 hours.\n3. Return immediately if swelling develops.",
        "default_items": [
            {
                "medicine_name": "Augmentin 625 Duo",
                "generic_name": "Amoxicillin + Potassium Clavulanate",
                "strength": "625 mg",
                "form": "TABLET",
                "dosage": "1 tablet",
                "route": "Oral",
                "frequency": "BD",
                "duration": "5 days",
                "quantity": 10,
                "timing": "Morning - Night",
                "food_instructions": "After food",
                "notes": "Take full antibiotic course.",
            },
            {
                "medicine_name": "Flagyl 400",
                "generic_name": "Metronidazole",
                "strength": "400 mg",
                "form": "TABLET",
                "dosage": "1 tablet",
                "route": "Oral",
                "frequency": "TDS",
                "duration": "5 days",
                "quantity": 15,
                "timing": "Morning - Afternoon - Night",
                "food_instructions": "After food",
                "notes": "Anaerobic coverage. Strictly avoid alcohol.",
            },
            {
                "medicine_name": "Brufen 400",
                "generic_name": "Ibuprofen",
                "strength": "400 mg",
                "form": "TABLET",
                "dosage": "1 tablet",
                "route": "Oral",
                "frequency": "TDS",
                "duration": "3 days",
                "quantity": 9,
                "timing": "Morning - Afternoon - Night",
                "food_instructions": "After food",
                "notes": "Anti-inflammatory pain relief.",
            },
            {
                "medicine_name": "Pan 40",
                "generic_name": "Pantoprazole",
                "strength": "40 mg",
                "form": "TABLET",
                "dosage": "1 tablet",
                "route": "Oral",
                "frequency": "OD",
                "duration": "5 days",
                "quantity": 5,
                "timing": "Morning",
                "food_instructions": "Before breakfast",
                "notes": "Antacid protection.",
            },
        ],
    },
    {
        "name": "Dental Implant Surgery",
        "category": TemplateCategory.IMPLANT,
        "description": "Post-surgical antibiotic and anti-inflammatory coverage following fixture placement.",
        "diagnosis_template": "Status post endosteal implant placement. Good primary stability achieved.",
        "instructions_template": "1. Soft diet for 10-14 days. Avoid chewing directly on implant site.\n2. Keep ice pack applied externally for first 6 hours (15 mins on, 15 mins off).\n3. Meticulous oral rinse with chlorhexidine.",
        "default_items": [
            {
                "medicine_name": "Augmentin 625 Duo",
                "generic_name": "Amoxicillin + Potassium Clavulanate",
                "strength": "625 mg",
                "form": "TABLET",
                "dosage": "1 tablet",
                "route": "Oral",
                "frequency": "BD",
                "duration": "5 days",
                "quantity": 10,
                "timing": "Morning - Night",
                "food_instructions": "With food",
                "notes": "Prophylactic antibiotic.",
            },
            {
                "medicine_name": "Nucoxia 90",
                "generic_name": "Etoricoxib",
                "strength": "90 mg",
                "form": "TABLET",
                "dosage": "1 tablet",
                "route": "Oral",
                "frequency": "OD",
                "duration": "3 days",
                "quantity": 3,
                "timing": "Night",
                "food_instructions": "After dinner",
                "notes": "Once-daily COX-2 pain and swelling control.",
            },
            {
                "medicine_name": "Hexidine Mouthwash",
                "generic_name": "Chlorhexidine Gluconate 0.2%",
                "strength": "0.2% w/v",
                "form": "MOUTHWASH",
                "dosage": "10 ml",
                "route": "Topical",
                "frequency": "BD",
                "duration": "14 days",
                "quantity": 1,
                "timing": "Morning - Night",
                "food_instructions": "After brushing",
                "notes": "Start next morning. Swish gently without vigorous spitting.",
            },
        ],
    },
    {
        "name": "Periodontal Deep Scaling & Curettage",
        "category": TemplateCategory.SCALING,
        "description": "Therapeutic antiseptic and mild analgesic protocol after subgingival debridement.",
        "diagnosis_template": "Generalized chronic periodontitis. Completed ultrasonic scaling and root planing.",
        "instructions_template": "1. Mild sensitivity to hot and cold is normal for a few days.\n2. Use a soft toothbrush with gentle circular motions.\n3. Rinse with warm salt water after 24 hours.",
        "default_items": [
            {
                "medicine_name": "Hexidine Mouthwash",
                "generic_name": "Chlorhexidine Gluconate 0.2%",
                "strength": "0.2% w/v",
                "form": "MOUTHWASH",
                "dosage": "10 ml",
                "route": "Topical",
                "frequency": "BD",
                "duration": "14 days",
                "quantity": 1,
                "timing": "Morning - Night",
                "food_instructions": "After brushing",
                "notes": "Swish for 1 minute undiluted.",
            },
            {
                "medicine_name": "Dolo 650",
                "generic_name": "Paracetamol",
                "strength": "650 mg",
                "form": "TABLET",
                "dosage": "1 tablet",
                "route": "Oral",
                "frequency": "SOS",
                "duration": "2 days",
                "quantity": 4,
                "timing": "When required",
                "food_instructions": "After food",
                "notes": "Take only if soreness occurs.",
            },
        ],
    },
    {
        "name": "Emergency Acute Odontalgia (Severe Dental Pain)",
        "category": TemplateCategory.EMERGENCY,
        "description": "Rapid pain relief protocol for patients awaiting definitive endodontic or surgical appointments.",
        "diagnosis_template": "Acute severe odontogenic pain / symptomatic pulpitis.",
        "instructions_template": "1. Take dispersible Ketorol DT in 1 teaspoon of water for immediate emergency pain relief.\n2. Do not exceed 3 tablets per day.\n3. Return for clinical appointment as scheduled.",
        "default_items": [
            {
                "medicine_name": "Ketorol DT",
                "generic_name": "Ketorolac Tromethamine",
                "strength": "10 mg",
                "form": "TABLET",
                "dosage": "1 tablet",
                "route": "Oral",
                "frequency": "SOS",
                "duration": "2 days",
                "quantity": 4,
                "timing": "As needed (min 6h interval)",
                "food_instructions": "Disperse in water",
                "notes": "Maximum 3 tablets in 24 hours. Short term only.",
            },
            {
                "medicine_name": "Pan 40",
                "generic_name": "Pantoprazole",
                "strength": "40 mg",
                "form": "TABLET",
                "dosage": "1 tablet",
                "route": "Oral",
                "frequency": "OD",
                "duration": "3 days",
                "quantity": 3,
                "timing": "Morning",
                "food_instructions": "Before food",
                "notes": "Gastric shield.",
            },
        ],
    },
]


class PrescriptionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _base_query(self, clinic_id: UUID):
        return (
            select(Prescription)
            .where(
                Prescription.clinic_id == clinic_id,
                Prescription.deleted_at.is_(None),
            )
            .options(
                selectinload(Prescription.items),
                selectinload(Prescription.patient).selectinload(Patient.medical_history),
                selectinload(Prescription.treatment),
                selectinload(Prescription.appointment),
                selectinload(Prescription.dentist),
                selectinload(Prescription.clinic),
            )
        )

    async def generate_prescription_number(
        self, clinic_id: UUID, target_date: date | None = None
    ) -> str:
        d = target_date or datetime.now(UTC).date()
        prefix = f"RX-{d.strftime('%Y%m%d')}"
        query = select(func.count(Prescription.id)).where(
            Prescription.clinic_id == clinic_id,
            Prescription.prescription_number.like(f"{prefix}-%"),
        )
        res = await self.db.execute(query)
        count = res.scalar_one() or 0
        return f"{prefix}-{count + 1:04d}"

    async def get_by_id(self, clinic_id: UUID, prescription_id: UUID) -> Prescription | None:
        rx = await self.db.get(Prescription, prescription_id)
        if rx and rx.clinic_id == clinic_id and rx.deleted_at is None:
            if not getattr(rx, "patient", None) and getattr(rx, "patient_id", None):
                rx.patient = await self.db.get(Patient, rx.patient_id)
            if not getattr(rx, "dentist", None) and getattr(rx, "dentist_id", None):
                rx.dentist = await self.db.get(User, rx.dentist_id)
            if not getattr(rx, "treatment", None) and getattr(rx, "treatment_id", None):
                rx.treatment = await self.db.get(Treatment, rx.treatment_id)
            return rx
        query = self._base_query(clinic_id).where(Prescription.id == prescription_id)
        res = await self.db.execute(query)
        rx = res.scalar_one_or_none()
        if rx:
            if not getattr(rx, "patient", None) and getattr(rx, "patient_id", None):
                rx.patient = await self.db.get(Patient, rx.patient_id)
            if not getattr(rx, "dentist", None) and getattr(rx, "dentist_id", None):
                rx.dentist = await self.db.get(User, rx.dentist_id)
            if not getattr(rx, "treatment", None) and getattr(rx, "treatment_id", None):
                rx.treatment = await self.db.get(Treatment, rx.treatment_id)
        return rx

    async def get_by_number(self, clinic_id: UUID, rx_number: str) -> Prescription | None:
        query = self._base_query(clinic_id).where(
            Prescription.prescription_number == rx_number
        )
        res = await self.db.execute(query)
        return res.scalar_one_or_none()

    async def get_by_treatment(
        self, clinic_id: UUID, treatment_id: UUID
    ) -> list[Prescription]:
        query = (
            self._base_query(clinic_id)
            .where(Prescription.treatment_id == treatment_id)
            .order_by(Prescription.created_at.desc())
        )
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def get_by_appointment(
        self, clinic_id: UUID, appointment_id: UUID
    ) -> list[Prescription]:
        query = (
            self._base_query(clinic_id)
            .where(Prescription.appointment_id == appointment_id)
            .order_by(Prescription.created_at.desc())
        )
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def get_by_patient(
        self, clinic_id: UUID, patient_id: UUID
    ) -> list[Prescription]:
        query = (
            self._base_query(clinic_id)
            .where(Prescription.patient_id == patient_id)
            .order_by(Prescription.created_at.desc())
        )
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def list_prescriptions(
        self,
        clinic_id: UUID,
        patient_id: UUID | None = None,
        treatment_id: UUID | None = None,
        dentist_id: UUID | None = None,
        status: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Prescription]:
        query = self._base_query(clinic_id)

        if patient_id:
            query = query.where(Prescription.patient_id == patient_id)
        if treatment_id:
            query = query.where(Prescription.treatment_id == treatment_id)
        if dentist_id:
            query = query.where(Prescription.dentist_id == dentist_id)
        if status:
            query = query.where(Prescription.status == status)
        if date_from:
            query = query.where(Prescription.date >= date_from)
        if date_to:
            query = query.where(Prescription.date <= date_to)
        if search:
            query = query.join(Prescription.patient).where(
                or_(
                    Prescription.prescription_number.ilike(f"%{search}%"),
                    Prescription.diagnosis.ilike(f"%{search}%"),
                    Patient.first_name.ilike(f"%{search}%"),
                    Patient.last_name.ilike(f"%{search}%"),
                    Patient.patient_number.ilike(f"%{search}%"),
                )
            )

        query = query.order_by(Prescription.created_at.desc()).limit(limit).offset(offset)
        res = await self.db.execute(query)
        return list(res.scalars().all())

    async def create(
        self,
        clinic_id: UUID,
        payload: PrescriptionCreate,
        actor: User,
        prescription_number: str,
    ) -> Prescription:
        rx_date = payload.date or datetime.now(UTC).date()
        rx_status = (
            PrescriptionStatus.ISSUED
            if payload.issue_immediately and payload.items
            else PrescriptionStatus.DRAFT
        )
        issued_at = datetime.now(UTC) if rx_status == PrescriptionStatus.ISSUED else None

        rx = Prescription(
            clinic_id=clinic_id,
            patient_id=payload.patient_id,
            treatment_id=payload.treatment_id,
            appointment_id=payload.appointment_id,
            dentist_id=payload.dentist_id,
            prescription_number=prescription_number,
            date=rx_date,
            diagnosis=payload.diagnosis,
            notes=payload.notes,
            instructions=payload.instructions,
            follow_up_date=payload.follow_up_date,
            status=rx_status,
            issued_at=issued_at,
            created_by=actor.id,
            updated_by=actor.id,
            version=1,
        )
        self.db.add(rx)
        await self.db.flush()

        for item_data in payload.items:
            item = PrescriptionItem(
                prescription=rx,
                prescription_id=rx.id,
                medicine_name=item_data.medicine_name,
                generic_name=item_data.generic_name,
                brand_name=item_data.brand_name,
                strength=item_data.strength,
                form=item_data.form,
                dosage=item_data.dosage,
                route=item_data.route,
                frequency=item_data.frequency,
                duration=item_data.duration,
                quantity=item_data.quantity,
                timing=item_data.timing,
                food_instructions=item_data.food_instructions,
                notes=item_data.notes,
                created_by=actor.id,
                updated_by=actor.id,
                version=1,
            )
            self.db.add(item)

        await self.db.flush()
        return rx

    async def update(
        self,
        prescription: Prescription,
        payload: PrescriptionUpdate,
        actor: User,
    ) -> Prescription:
        if payload.diagnosis is not None:
            prescription.diagnosis = payload.diagnosis
        if payload.notes is not None:
            prescription.notes = payload.notes
        if payload.instructions is not None:
            prescription.instructions = payload.instructions
        if payload.follow_up_date is not None:
            prescription.follow_up_date = payload.follow_up_date

        if payload.items is not None:
            # Delete existing items and replace with updated set
            for item in list(prescription.items):
                await self.db.delete(item)
            prescription.items.clear()
            await self.db.flush()

            for item_data in payload.items:
                item = PrescriptionItem(
                    prescription=prescription,
                    prescription_id=prescription.id,
                    medicine_name=item_data.medicine_name,
                    generic_name=item_data.generic_name,
                    brand_name=item_data.brand_name,
                    strength=item_data.strength,
                    form=item_data.form,
                    dosage=item_data.dosage,
                    route=item_data.route,
                    frequency=item_data.frequency,
                    duration=item_data.duration,
                    quantity=item_data.quantity,
                    timing=item_data.timing,
                    food_instructions=item_data.food_instructions,
                    notes=item_data.notes,
                    created_by=actor.id,
                    updated_by=actor.id,
                    version=1,
                )
                self.db.add(item)

        prescription.updated_by = actor.id
        prescription.updated_at = datetime.now(UTC)
        prescription.version = (prescription.version or 1) + 1
        await self.db.flush()
        return prescription

    async def issue(self, prescription: Prescription, actor: User) -> Prescription:
        prescription.status = PrescriptionStatus.ISSUED
        prescription.issued_at = datetime.now(UTC)
        prescription.updated_by = actor.id
        prescription.updated_at = datetime.now(UTC)
        prescription.version = (prescription.version or 1) + 1
        await self.db.flush()
        return prescription

    async def cancel(
        self, prescription: Prescription, reason: str, actor: User
    ) -> Prescription:
        prescription.status = PrescriptionStatus.CANCELLED
        prescription.cancellation_reason = reason
        prescription.updated_by = actor.id
        prescription.updated_at = datetime.now(UTC)
        prescription.version = (prescription.version or 1) + 1
        await self.db.flush()
        return prescription

    async def soft_delete(self, prescription: Prescription, actor: User) -> None:
        now = datetime.now(UTC)
        prescription.deleted_at = now
        prescription.updated_by = actor.id
        for item in prescription.items:
            item.deleted_at = now
            item.updated_by = actor.id
        await self.db.flush()

    # --- Medicine Catalog ---
    async def seed_standard_medicines(self) -> int:
        seeded_count = 0
        for med in STANDARD_MEDICINES:
            q = select(MedicineCatalog).where(
                MedicineCatalog.brand_name == med["brand_name"],
                MedicineCatalog.clinic_id.is_(None),
            )
            res = await self.db.execute(q)
            if res.scalar_one_or_none() is None:
                record = MedicineCatalog(
                    clinic_id=None,
                    generic_name=med["generic_name"],
                    brand_name=med["brand_name"],
                    strength=med["strength"],
                    form=med["form"],
                    category=med["category"],
                    standard_dosage=med["standard_dosage"],
                    default_route=med["default_route"],
                    default_frequency=med["default_frequency"],
                    default_duration=med["default_duration"],
                    default_instructions=med["default_instructions"],
                    notes=med["notes"],
                    is_active=True,
                    version=1,
                )
                self.db.add(record)
                seeded_count += 1

        if seeded_count > 0:
            await self.db.flush()
        return seeded_count

    async def search_medicines(
        self,
        clinic_id: UUID | None = None,
        query: str | None = None,
        category: str | None = None,
        form: str | None = None,
        limit: int = 30,
    ) -> list[MedicineCatalog]:
        await self.seed_standard_medicines()

        q = select(MedicineCatalog).where(
            MedicineCatalog.deleted_at.is_(None),
            MedicineCatalog.is_active.is_(True),
        )

        if clinic_id:
            q = q.where(
                or_(
                    MedicineCatalog.clinic_id.is_(None),
                    MedicineCatalog.clinic_id == clinic_id,
                )
            )
        else:
            q = q.where(MedicineCatalog.clinic_id.is_(None))

        if query:
            clean_q = f"%{query}%"
            q = q.where(
                or_(
                    MedicineCatalog.brand_name.ilike(clean_q),
                    MedicineCatalog.generic_name.ilike(clean_q),
                    MedicineCatalog.category.ilike(clean_q),
                )
            )

        if category:
            q = q.where(MedicineCatalog.category.ilike(f"%{category}%"))
        if form:
            q = q.where(MedicineCatalog.form == form)

        q = q.order_by(MedicineCatalog.brand_name.asc()).limit(limit)
        res = await self.db.execute(q)
        return list(res.scalars().all())

    async def create_medicine(
        self, clinic_id: UUID, payload: MedicineCatalogCreate, actor: User
    ) -> MedicineCatalog:
        med = MedicineCatalog(
            clinic_id=clinic_id,
            generic_name=payload.generic_name,
            brand_name=payload.brand_name,
            strength=payload.strength,
            form=payload.form,
            category=payload.category,
            standard_dosage=payload.standard_dosage,
            default_route=payload.default_route,
            default_frequency=payload.default_frequency,
            default_duration=payload.default_duration,
            default_instructions=payload.default_instructions,
            notes=payload.notes,
            created_by=actor.id,
            updated_by=actor.id,
            version=1,
        )
        self.db.add(med)
        await self.db.flush()
        return med

    # --- Prescription Templates ---
    async def seed_standard_templates(self) -> int:
        seeded_count = 0
        for tmpl in STANDARD_TEMPLATES:
            q = select(PrescriptionTemplate).where(
                PrescriptionTemplate.name == tmpl["name"],
                PrescriptionTemplate.clinic_id.is_(None),
            )
            res = await self.db.execute(q)
            if res.scalar_one_or_none() is None:
                record = PrescriptionTemplate(
                    clinic_id=None,
                    name=tmpl["name"],
                    category=tmpl["category"],
                    description=tmpl["description"],
                    diagnosis_template=tmpl["diagnosis_template"],
                    instructions_template=tmpl["instructions_template"],
                    default_items=tmpl["default_items"],
                    is_active=True,
                    version=1,
                )
                self.db.add(record)
                seeded_count += 1

        if seeded_count > 0:
            await self.db.flush()
        return seeded_count

    async def list_templates(
        self, clinic_id: UUID | None = None, category: str | None = None
    ) -> list[PrescriptionTemplate]:
        await self.seed_standard_templates()

        q = select(PrescriptionTemplate).where(
            PrescriptionTemplate.deleted_at.is_(None),
            PrescriptionTemplate.is_active.is_(True),
        )

        if clinic_id:
            q = q.where(
                or_(
                    PrescriptionTemplate.clinic_id.is_(None),
                    PrescriptionTemplate.clinic_id == clinic_id,
                )
            )
        else:
            q = q.where(PrescriptionTemplate.clinic_id.is_(None))

        if category:
            q = q.where(PrescriptionTemplate.category == category)

        q = q.order_by(PrescriptionTemplate.name.asc())
        res = await self.db.execute(q)
        return list(res.scalars().all())

    async def create_template(
        self, clinic_id: UUID, payload: PrescriptionTemplateCreate, actor: User
    ) -> PrescriptionTemplate:
        template = PrescriptionTemplate(
            clinic_id=clinic_id,
            name=payload.name,
            category=payload.category,
            description=payload.description,
            diagnosis_template=payload.diagnosis_template,
            instructions_template=payload.instructions_template,
            default_items=[item.model_dump() for item in payload.default_items],
            created_by=actor.id,
            updated_by=actor.id,
            version=1,
        )
        self.db.add(template)
        await self.db.flush()
        return template

    # --- Dashboard Stats ---
    async def get_dashboard_stats(self, clinic_id: UUID) -> PrescriptionDashboardStats:
        today = datetime.now(UTC).date()

        total_q = select(func.count(Prescription.id)).where(
            Prescription.clinic_id == clinic_id,
            Prescription.deleted_at.is_(None),
        )
        today_q = select(func.count(Prescription.id)).where(
            Prescription.clinic_id == clinic_id,
            Prescription.date == today,
            Prescription.deleted_at.is_(None),
        )
        issued_q = select(func.count(Prescription.id)).where(
            Prescription.clinic_id == clinic_id,
            Prescription.status == PrescriptionStatus.ISSUED,
            Prescription.deleted_at.is_(None),
        )
        draft_q = select(func.count(Prescription.id)).where(
            Prescription.clinic_id == clinic_id,
            Prescription.status == PrescriptionStatus.DRAFT,
            Prescription.deleted_at.is_(None),
        )
        cancelled_q = select(func.count(Prescription.id)).where(
            Prescription.clinic_id == clinic_id,
            Prescription.status == PrescriptionStatus.CANCELLED,
            Prescription.deleted_at.is_(None),
        )
        follow_up_q = select(func.count(Prescription.id)).where(
            Prescription.clinic_id == clinic_id,
            Prescription.follow_up_date >= today,
            Prescription.status == PrescriptionStatus.ISSUED,
            Prescription.deleted_at.is_(None),
        )

        total_res = await self.db.execute(total_q)
        today_res = await self.db.execute(today_q)
        issued_res = await self.db.execute(issued_q)
        draft_res = await self.db.execute(draft_q)
        cancelled_res = await self.db.execute(cancelled_q)
        follow_up_res = await self.db.execute(follow_up_q)

        return PrescriptionDashboardStats(
            total_prescriptions=total_res.scalar_one() or 0,
            today_prescriptions=today_res.scalar_one() or 0,
            issued_prescriptions=issued_res.scalar_one() or 0,
            draft_prescriptions=draft_res.scalar_one() or 0,
            cancelled_prescriptions=cancelled_res.scalar_one() or 0,
            follow_ups_due=follow_up_res.scalar_one() or 0,
        )

    def to_detail_schema(self, rx: Prescription) -> PrescriptionDetail:
        items_read = [
            PrescriptionItemRead(
                id=item.id,
                prescription_id=item.prescription_id,
                medicine_name=item.medicine_name,
                generic_name=item.generic_name,
                brand_name=item.brand_name,
                strength=item.strength,
                form=item.form or MedicineForm.TABLET,
                dosage=item.dosage,
                route=item.route or "Oral",
                frequency=item.frequency or DosageFrequency.BD,
                duration=item.duration,
                quantity=item.quantity or 10,
                timing=item.timing,
                food_instructions=item.food_instructions,
                notes=item.notes,
                created_at=item.created_at or datetime.now(UTC),
                updated_at=item.updated_at or datetime.now(UTC),
            )
            for item in (rx.items or [])
            if item.deleted_at is None
        ]

        patient_name = (
            f"{rx.patient.first_name} {rx.patient.last_name}" if rx.patient else None
        )
        patient_number = rx.patient.patient_number if rx.patient else None
        patient_age = rx.patient.age if rx.patient else None
        patient_gender = str(rx.patient.gender) if rx.patient else None

        alerts: list[str] = []
        if rx.patient and rx.patient.medical_history:
            mh = rx.patient.medical_history
            if mh.allergies:
                alerts.append(f"ALLERGY: {mh.allergies}")
            if mh.cardiac_disease:
                alerts.append("Cardiac Condition")
            if mh.diabetes:
                alerts.append("Diabetic")
            if mh.hypertension:
                alerts.append("Hypertensive")
            if mh.asthma:
                alerts.append("Asthma")
            if mh.pregnancy:
                alerts.append("Pregnancy")

        dentist_name = (
            f"Dr. {rx.dentist.first_name} {rx.dentist.last_name}" if rx.dentist else None
        )
        treatment_num = rx.treatment.treatment_number if rx.treatment else None

        return PrescriptionDetail(
            id=rx.id,
            clinic_id=rx.clinic_id,
            patient_id=rx.patient_id,
            treatment_id=rx.treatment_id,
            appointment_id=rx.appointment_id,
            dentist_id=rx.dentist_id,
            prescription_number=rx.prescription_number,
            date=rx.date,
            diagnosis=rx.diagnosis,
            notes=rx.notes,
            instructions=rx.instructions,
            follow_up_date=rx.follow_up_date,
            status=rx.status,
            cancellation_reason=rx.cancellation_reason,
            issued_at=rx.issued_at,
            items_count=len(items_read),
            created_at=rx.created_at or datetime.now(UTC),
            updated_at=rx.updated_at or datetime.now(UTC),
            items=items_read,
            patient_name=patient_name,
            patient_number=patient_number,
            patient_age=patient_age,
            patient_gender=patient_gender,
            patient_alerts=alerts,
            dentist_name=dentist_name,
            dentist_registration="DCI-REG-" + str(rx.dentist_id)[:8].upper() if rx.dentist_id else None,
            treatment_number=treatment_num,
            clinic_name=rx.clinic.name if rx.clinic else None,
            clinic_phone=rx.clinic.phone if rx.clinic else None,
            clinic_email=rx.clinic.email if rx.clinic else None,
        )
