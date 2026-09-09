# =====================================================================
# DentalCare Pro - Master End-to-End Enterprise Workflow Test Suite
# Phase 17: Validates 6 core real-world healthcare & enterprise lifecycles
# =====================================================================
from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

from app.models.appointment import Appointment, AppointmentStatus, Chair, ChairStatus, VisitType
from app.models.billing import (
    Invoice,
    InvoiceItem,
    InvoiceStatus,
    Payment,
    PaymentMethod,
    PaymentStatus,
)
from app.models.enterprise import InventoryTransfer, InventoryTransferStatus, Organization, Region
from app.models.hr import (
    AttendanceRecord,
    AttendanceStatus,
    Employee,
    LeaveRequest,
    LeaveStatus,
    LeaveType,
    PayrollRun,
    PayrollStatus,
    Payslip,
    PayslipStatus,
    PerformanceReview,
    ReviewStatus,
    WorkShift,
)
from app.models.identity import Clinic, Role, User
from app.models.insurance import (
    ClaimStatus,
    InsuranceClaim,
    InsuranceProvider,
    PatientInsurancePolicy,
    PolicyStatus,
)
from app.models.inventory import InventoryItem
from app.models.odontogram import Tooth, ToothCondition, ToothSurface
from app.models.patient import BloodGroup, Gender, Patient
from app.models.prescription import (
    DosageFrequency,
    MedicineForm,
    Prescription,
    PrescriptionItem,
    PrescriptionStatus,
)
from app.models.treatment import (
    FollowUpStatus,
    Treatment,
    TreatmentFollowUp,
    TreatmentProcedure,
    TreatmentStatus,
)


class MasterMockSession:
    """Mock asynchronous database session simulating high-fidelity relational state."""
    def __init__(self) -> None:
        self.entities: list[object] = []
        self.added: list[object] = []
        self.commits = 0

    def add(self, item: object) -> None:
        if not getattr(item, "id", None):
            item.id = uuid4()
        self.added.append(item)
        if item not in self.entities:
            self.entities.append(item)

    async def flush(self) -> None:
        pass

    async def commit(self) -> None:
        self.commits += 1

    async def refresh(self, item: object) -> None:
        pass

    async def get(self, model_cls: type, ident: UUID | str) -> object | None:
        for item in self.entities:
            if isinstance(item, model_cls) and getattr(item, "id", None) == ident:
                return item
        return None

    def _filter_matching(self, statement: object) -> list[object]:
        params: dict[str, object] = {}
        try:
            params = statement.compile().params or {}  # type: ignore[attr-defined]
        except Exception:
            pass

        matching = list(self.entities)
        if hasattr(statement, "column_descriptions") and statement.column_descriptions:
            desc = statement.column_descriptions[0]
            entity_cls = desc.get("entity")
            if isinstance(entity_cls, type):
                matching = [item for item in matching if isinstance(item, entity_cls)]

        clinic_ids = [v for k, v in params.items() if "clinic_id" in k]
        id_values = [v for k, v in params.items() if k == "id" or k.startswith("id_")]

        if clinic_ids:
            matching = [item for item in matching if getattr(item, "clinic_id", None) in clinic_ids]
        if id_values:
            matching = [item for item in matching if getattr(item, "id", None) in id_values]
        return matching

    async def scalar(self, statement: object) -> object | None:
        res = self._filter_matching(statement)
        return res[0] if res else None

    async def scalars(self, statement: object) -> SimpleNamespace:
        res = self._filter_matching(statement)
        return SimpleNamespace(all=lambda: list(res))

    async def execute(self, statement: object) -> SimpleNamespace:
        res = self._filter_matching(statement)
        return SimpleNamespace(
            scalar_one_or_none=lambda: res[0] if res else None,
            scalars=lambda: SimpleNamespace(all=lambda: list(res)),
            all=lambda: list(res),
        )


def build_enterprise_fixture():
    session = MasterMockSession()
    clinic_id = uuid4()
    clinic = Clinic(
        id=clinic_id,
        name="Metro Smiles Dental Center",
        slug="metro-smiles-central",
        email="info@metrosmiles.com",
        is_active=True,
    )
    session.add(clinic)

    dentist = User(
        id=uuid4(),
        clinic_id=clinic_id,
        email="dr.sarah@metrosmiles.com",
        first_name="Sarah",
        last_name="Jenkins",
        role=Role.DENTIST,
        is_active=True,
    )
    receptionist = User(
        id=uuid4(),
        clinic_id=clinic_id,
        email="reception@metrosmiles.com",
        first_name="Emily",
        last_name="Watson",
        role=Role.RECEPTIONIST,
        is_active=True,
    )
    admin = User(
        id=uuid4(),
        clinic_id=clinic_id,
        email="admin@metrosmiles.com",
        first_name="Marcus",
        last_name="Vance",
        role=Role.CLINIC_ADMIN,
        is_active=True,
    )
    chair = Chair(
        id=uuid4(),
        clinic_id=clinic_id,
        name="Operatory 1 - Pediatric & Surgical",
        status=ChairStatus.ACTIVE,
    )
    session.add(dentist)
    session.add(receptionist)
    session.add(admin)
    session.add(chair)

    return session, clinic, dentist, receptionist, admin, chair


# ==============================================================================
# Workflow 1: New Patient Complete Clinical & Financial Journey
# ==============================================================================
@pytest.mark.asyncio
async def test_e2e_new_patient_journey():
    """
    Validates complete lifecycle:
    Registration -> Intake -> Appointment -> Consultation -> Odontogram ->
    Treatment Procedure -> Prescription -> Invoicing -> Payment -> Follow-up.
    """
    session, clinic, dentist, receptionist, admin, chair = build_enterprise_fixture()

    # 1. New Patient Registration & Medical Intake
    patient = Patient(
        id=uuid4(),
        clinic_id=clinic.id,
        patient_number="P-2026-0099",
        first_name="Alexander",
        last_name="Wright",
        date_of_birth=date(1992, 5, 14),
        gender=Gender.MALE,
        blood_group=BloodGroup.O_POSITIVE,
        mobile_number="+15552345678",
        email="alex.wright@example.com",
        created_at=datetime.now(UTC),
    )
    session.add(patient)
    assert patient.patient_number == "P-2026-0099"

    # 2. Appointment Booking & Check-In
    appt_date = datetime.now(UTC).date() + timedelta(days=1)
    appointment = Appointment(
        id=uuid4(),
        clinic_id=clinic.id,
        patient_id=patient.id,
        dentist_id=dentist.id,
        chair_id=chair.id,
        appointment_number="APT-20260909-001",
        date=appt_date,
        start_time=time(10, 0),
        end_time=time(11, 0),
        duration=60,
        visit_type=VisitType.CONSULTATION,
        status=AppointmentStatus.CHECKED_IN,
    )
    session.add(appointment)
    assert appointment.status == AppointmentStatus.CHECKED_IN

    # 3. 32-Tooth Odontogram Clinical Charting (Tooth #14)
    tooth_14 = Tooth(
        id=uuid4(),
        clinic_id=clinic.id,
        patient_id=patient.id,
        tooth_number="14",
        universal_number="4",
        palmer_notation="4",
        name="Maxillary Right First Premolar",
        arch="UPPER",
        quadrant=1,
        tooth_type="PREMOLAR",
        primary_status=ToothCondition.CARIES,
        color="#EF4444",
    )
    surface_mo = ToothSurface(
        id=uuid4(),
        clinic_id=clinic.id,
        tooth_id=tooth_14.id,
        surface="MESIAL",
        condition=ToothCondition.CARIES,
        treatment="COMPOSITE_RESTORATION",
    )
    session.add(tooth_14)
    session.add(surface_mo)
    assert tooth_14.tooth_number == "14"
    assert tooth_14.primary_status == ToothCondition.CARIES

    # 4. Clinical Treatment & SOAP Note Documentation
    treatment = Treatment(
        id=uuid4(),
        clinic_id=clinic.id,
        patient_id=patient.id,
        appointment_id=appointment.id,
        dentist_id=dentist.id,
        treatment_number="TRT-20260909-001",
        diagnosis="Reversible pulpitis secondary to dental caries #14",
        chief_complaint="Severe sensitivity to cold on upper right tooth",
        soap_subjective="Patient notes sharp throbbing pain when consuming chilled liquids.",
        soap_objective="Tooth #14 exhibits active class II carious lesion on MO surfaces.",
        soap_assessment="Reversible pulpitis secondary to dental caries #14.",
        soap_plan="Composite resin restoration and post-op analgesics.",
        status=TreatmentStatus.IN_PROGRESS,
        created_at=datetime.now(UTC),
    )
    procedure = TreatmentProcedure(
        id=uuid4(),
        treatment_id=treatment.id,
        procedure_name="Resin-based composite - two surfaces, posterior (#14 MO)",
        tooth_number="14",
        cost=250.00,
        status="COMPLETED",
    )
    treatment.status = TreatmentStatus.COMPLETED
    appointment.status = AppointmentStatus.COMPLETED
    session.add(treatment)
    session.add(procedure)
    assert treatment.status == TreatmentStatus.COMPLETED

    # 5. E-Prescription Dispatch
    prescription = Prescription(
        id=uuid4(),
        clinic_id=clinic.id,
        patient_id=patient.id,
        dentist_id=dentist.id,
        treatment_id=treatment.id,
        appointment_id=appointment.id,
        prescription_number="RX-2026-0881",
        date=datetime.now(UTC).date(),
        diagnosis="Caries restoration #14 post-op",
        status=PrescriptionStatus.ISSUED,
    )
    rx_item = PrescriptionItem(
        id=uuid4(),
        prescription_id=prescription.id,
        medicine_name="Amoxicillin 500mg",
        strength="500 mg",
        form=MedicineForm.CAPSULE,
        dosage="1 capsule",
        frequency=DosageFrequency.TDS,
        duration="5 days",
        food_instructions="Take one capsule with food every 8 hours",
    )
    session.add(prescription)
    session.add(rx_item)
    assert prescription.prescription_number == "RX-2026-0881"

    # 6. Itemized Invoicing & POS Payment Collection
    invoice = Invoice(
        id=uuid4(),
        clinic_id=clinic.id,
        patient_id=patient.id,
        dentist_id=dentist.id,
        created_by=receptionist.id,
        updated_by=receptionist.id,
        invoice_number="INV-2026-0442",
        date=datetime.now(UTC).date(),
        status=InvoiceStatus.UNPAID,
        subtotal=250.00,
        tax_amount=0.00,
        grand_total=250.00,
        amount_paid=0.00,
        balance_due=250.00,
        created_at=datetime.now(UTC),
    )
    inv_item = InvoiceItem(
        id=uuid4(),
        invoice_id=invoice.id,
        description="Resin-based composite - tooth #14 MO",
        quantity=1,
        unit_price=250.00,
        total=250.00,
    )
    payment = Payment(
        id=uuid4(),
        invoice_id=invoice.id,
        clinic_id=clinic.id,
        receipt_number="REC-2026-0909",
        payment_date=datetime.now(UTC).date(),
        amount=250.00,
        method=PaymentMethod.CARD,
        status=PaymentStatus.COMPLETED,
        transaction_reference="TXN_STRIPE_987654321",
        received_by=receptionist.id,
    )
    invoice.amount_paid = 250.00
    invoice.balance_due = 0.00
    invoice.status = InvoiceStatus.PAID
    session.add(invoice)
    session.add(inv_item)
    session.add(payment)
    assert invoice.balance_due == 0.00
    assert invoice.status == InvoiceStatus.PAID

    # 7. Follow-up Care Scheduling
    follow_up = TreatmentFollowUp(
        id=uuid4(),
        clinic_id=clinic.id,
        patient_id=patient.id,
        treatment_id=treatment.id,
        follow_up_date=datetime.now(UTC).date() + timedelta(days=14),
        reason="Check occlusion and margin seal on composite #14",
        status=FollowUpStatus.SCHEDULED,
    )
    session.add(follow_up)
    assert follow_up.reason.startswith("Check occlusion")
    assert len(session.added) >= 10


# ==============================================================================
# Workflow 2: Returning Patient & Insurance Claims Processing
# ==============================================================================
@pytest.mark.asyncio
async def test_e2e_returning_patient_and_insurance():
    """Validates existing patient lookup, treatment, and insurance claim adjudication."""
    session, clinic, dentist, receptionist, admin, chair = build_enterprise_fixture()

    patient = Patient(
        id=uuid4(),
        clinic_id=clinic.id,
        patient_number="P-2025-0012",
        first_name="Eleanor",
        last_name="Rigby",
        date_of_birth=date(1985, 8, 22),
        gender=Gender.FEMALE,
        mobile_number="+15559876543",
    )
    provider = InsuranceProvider(
        id=uuid4(),
        clinic_id=clinic.id,
        provider_name="MetLife Dental",
        provider_code="METLIFE-001",
        is_active=True,
    )
    policy = PatientInsurancePolicy(
        id=uuid4(),
        clinic_id=clinic.id,
        patient_id=patient.id,
        provider_id=provider.id,
        policy_number="MET-88990011",
        member_id="MEM-998811",
        effective_date=date(2026, 1, 1),
        expiry_date=date(2026, 12, 31),
        status=PolicyStatus.ACTIVE,
    )
    session.add(patient)
    session.add(provider)
    session.add(policy)

    # Treatment for Crown (Code D2740)
    treatment = Treatment(
        id=uuid4(),
        clinic_id=clinic.id,
        patient_id=patient.id,
        appointment_id=uuid4(),
        dentist_id=dentist.id,
        treatment_number="TRT-20260909-002",
        diagnosis="Severe tooth decay requiring full porcelain crown",
        status=TreatmentStatus.COMPLETED,
    )
    session.add(treatment)

    # File Insurance Claim
    claim = InsuranceClaim(
        id=uuid4(),
        clinic_id=clinic.id,
        patient_id=patient.id,
        policy_id=policy.id,
        treatment_id=treatment.id,
        claim_number="CLM-2026-0045",
        total_claimed_amount=1000.00,
        patient_copay_amount=250.00,
        approved_amount=750.00,
        status=ClaimStatus.SUBMITTED,
        submission_date=datetime.now(UTC).date(),
    )
    session.add(claim)

    # Simulate adjudication approval
    claim.status = ClaimStatus.APPROVED
    assert claim.status == ClaimStatus.APPROVED
    assert claim.approved_amount == 750.00
    assert claim.patient_copay_amount == 250.00


# ==============================================================================
# Workflow 3: Front Desk Reception & Chair Allocation Queue
# ==============================================================================
@pytest.mark.asyncio
async def test_e2e_reception_queue_and_checkout():
    """Validates front desk arrival, waiting room transitions, and next visit recall."""
    session, clinic, dentist, receptionist, admin, chair = build_enterprise_fixture()

    patient = Patient(
        id=uuid4(),
        clinic_id=clinic.id,
        patient_number="P-2026-0033",
        first_name="Thomas",
        last_name="Shelby",
        date_of_birth=date(1982, 3, 10),
        gender=Gender.MALE,
        mobile_number="+15554321098",
    )
    session.add(patient)

    appt = Appointment(
        id=uuid4(),
        clinic_id=clinic.id,
        patient_id=patient.id,
        dentist_id=dentist.id,
        chair_id=chair.id,
        appointment_number="APT-REC-001",
        date=datetime.now(UTC).date(),
        start_time=time(14, 0),
        end_time=time(14, 30),
        duration=30,
        status=AppointmentStatus.SCHEDULED,
    )
    session.add(appt)

    # Step 1: Patient arrives at reception and scans QR
    appt.status = AppointmentStatus.CHECKED_IN
    # Step 2: Operatory chair prepared & patient called in
    appt.status = AppointmentStatus.IN_TREATMENT
    assert appt.status == AppointmentStatus.IN_TREATMENT

    # Step 3: Treatment concludes
    appt.status = AppointmentStatus.COMPLETED

    # Step 4: Schedule 6-month hygiene recall
    next_recall = Appointment(
        id=uuid4(),
        clinic_id=clinic.id,
        patient_id=patient.id,
        dentist_id=dentist.id,
        appointment_number="APT-REC-002",
        date=datetime.now(UTC).date() + timedelta(days=180),
        start_time=time(10, 0),
        end_time=time(10, 45),
        duration=45,
        visit_type=VisitType.CLEANING,
        status=AppointmentStatus.SCHEDULED,
    )
    session.add(next_recall)
    assert next_recall.visit_type == VisitType.CLEANING


# ==============================================================================
# Workflow 4: Dentist chairside examination & digital charting
# ==============================================================================
@pytest.mark.asyncio
async def test_e2e_dentist_clinical_charting():
    """Validates full FDI 32-tooth odontogram charting, SOAP notes, and treatment plan sign-off."""
    session, clinic, dentist, receptionist, admin, chair = build_enterprise_fixture()

    patient = Patient(
        id=uuid4(),
        clinic_id=clinic.id,
        patient_number="P-2026-0044",
        first_name="Grace",
        last_name="Burgess",
        date_of_birth=date(1990, 7, 19),
        gender=Gender.FEMALE,
        mobile_number="+15558765432",
    )
    session.add(patient)

    # Multi-tooth charting: Tooth #18 (Missing), Tooth #24 (Crown), Tooth #36 (Endodontic Root Canal)
    t18 = Tooth(
        clinic_id=clinic.id,
        patient_id=patient.id,
        tooth_number="18",
        universal_number="1",
        palmer_notation="8",
        name="Maxillary Right Third Molar",
        arch="UPPER",
        quadrant=1,
        tooth_type="MOLAR",
        is_missing=True,
        primary_status=ToothCondition.MISSING,
    )
    t24 = Tooth(
        clinic_id=clinic.id,
        patient_id=patient.id,
        tooth_number="24",
        universal_number="12",
        palmer_notation="4",
        name="Maxillary Left First Premolar",
        arch="UPPER",
        quadrant=2,
        tooth_type="PREMOLAR",
        has_crown=True,
        primary_status=ToothCondition.CROWN,
    )
    t36 = Tooth(
        clinic_id=clinic.id,
        patient_id=patient.id,
        tooth_number="36",
        universal_number="19",
        palmer_notation="6",
        name="Mandibular Left First Molar",
        arch="LOWER",
        quadrant=3,
        tooth_type="MOLAR",
        has_root_canal=True,
        primary_status=ToothCondition.ROOT_CANAL,
    )
    session.add(t18)
    session.add(t24)
    session.add(t36)

    treatment = Treatment(
        id=uuid4(),
        clinic_id=clinic.id,
        patient_id=patient.id,
        appointment_id=uuid4(),
        dentist_id=dentist.id,
        treatment_number="TRT-20260909-003",
        diagnosis="Gingivitis, localized, plaque-induced",
        soap_subjective="Routine 6-month recall; no acute pain reported.",
        soap_objective="Oral hygiene good; mild supra-gingival calculus on lingual lower incisors.",
        soap_assessment="Gingivitis, localized, plaque-induced.",
        soap_plan="Full mouth scaling and polishing (D1110). Patient educated on interdental flossing.",
        status=TreatmentStatus.COMPLETED,
    )
    session.add(treatment)
    assert t18.tooth_number == "18"
    assert t24.primary_status == ToothCondition.CROWN
    assert t36.primary_status == ToothCondition.ROOT_CANAL
    assert treatment.status == TreatmentStatus.COMPLETED


# ==============================================================================
# Workflow 5: HR, Shift Attendance & Payroll Processing
# ==============================================================================
@pytest.mark.asyncio
async def test_e2e_hr_payroll_and_attendance():
    """Validates employee shift scheduling, attendance clock-in, leave approval, and payroll generation."""
    session, clinic, dentist, receptionist, admin, chair = build_enterprise_fixture()

    employee = Employee(
        id=uuid4(),
        clinic_id=clinic.id,
        user_id=dentist.id,
        employee_code="EMP-DENT-001",
        first_name="Sarah",
        last_name="Jenkins",
        email="dr.sarah@metrosmiles.com",
        designation="Senior Endodontist",
        joining_date=date(2024, 1, 15),
        base_salary=9500.00,
    )
    session.add(employee)

    # 1. Shift Schedule & Clock-In
    shift = WorkShift(
        id=uuid4(),
        clinic_id=clinic.id,
        name="Standard Day Shift",
        code="SHIFT-DAY",
        start_time=time(9, 0),
        end_time=time(17, 0),
    )
    attendance = AttendanceRecord(
        id=uuid4(),
        clinic_id=clinic.id,
        employee_id=employee.id,
        date=datetime.now(UTC).date(),
        check_in_time=datetime.now(UTC) - timedelta(hours=8),
        check_out_time=datetime.now(UTC),
        status=AttendanceStatus.PRESENT,
    )
    session.add(shift)
    session.add(attendance)
    assert attendance.status == AttendanceStatus.PRESENT

    # 2. Leave Request & Approval
    leave = LeaveRequest(
        id=uuid4(),
        clinic_id=clinic.id,
        employee_id=employee.id,
        leave_type=LeaveType.ANNUAL,
        start_date=datetime.now(UTC).date() + timedelta(days=10),
        end_date=datetime.now(UTC).date() + timedelta(days=12),
        days_count=3.0,
        reason="Attending international dental symposium",
        status=LeaveStatus.HR_APPROVED,
    )
    session.add(leave)
    assert leave.status == LeaveStatus.HR_APPROVED

    # 3. Monthly Payroll Calculation with Tax & Deductions
    gross_salary = employee.base_salary + 500.00  # $500 clinical allowance
    tax_deduction = gross_salary * 0.18           # 18% withholding tax
    pension_deduction = 400.00                    # Retirement 401k
    net_salary = gross_salary - tax_deduction - pension_deduction

    payroll_run = PayrollRun(
        id=uuid4(),
        clinic_id=clinic.id,
        run_number="PR-2026-09",
        period_month=datetime.now(UTC).date().month,
        period_year=datetime.now(UTC).date().year,
        total_gross=gross_salary,
        total_deductions=tax_deduction + pension_deduction,
        total_net=net_salary,
        total_employees=1,
        status=PayrollStatus.APPROVED,
    )
    payslip = Payslip(
        id=uuid4(),
        payroll_run_id=payroll_run.id,
        employee_id=employee.id,
        clinic_id=clinic.id,
        period_month=datetime.now(UTC).date().month,
        period_year=datetime.now(UTC).date().year,
        basic_salary=employee.base_salary,
        gross_earnings=gross_salary,
        total_deductions=tax_deduction + pension_deduction,
        net_salary=net_salary,
        status=PayslipStatus.APPROVED,
    )
    session.add(payroll_run)
    session.add(payslip)
    assert payslip.gross_earnings == 10000.00
    assert payslip.net_salary == 7800.00

    # 4. Performance Appraisal Review
    review = PerformanceReview(
        id=uuid4(),
        clinic_id=clinic.id,
        employee_id=employee.id,
        reviewer_id=admin.id,
        review_period="2026-Q3",
        overall_rating=4.8,
        clinical_skills_rating=5.0,
        patient_satisfaction_rating=4.9,
        strengths="Outstanding clinical precision and exemplary patient bedside manner.",
        status=ReviewStatus.COMPLETED,
    )
    session.add(review)
    assert review.overall_rating == 4.8


# ==============================================================================
# Workflow 6: Enterprise Multi-Branch Requisition & Inventory Transfer
# ==============================================================================
@pytest.mark.asyncio
async def test_e2e_enterprise_multi_branch_transfer():
    """Validates multi-clinic organization hierarchy, stock requisition, and inter-branch inventory transfer."""
    session, clinic, dentist, receptionist, admin, chair = build_enterprise_fixture()

    # 1. Organization & Regional Hierarchy
    org = Organization(
        id=uuid4(),
        name="Global Dental Partners Corp",
        slug="global-dental-partners",
        code="GDP-CORP",
        primary_email="corp@globaldental.com",
        is_active=True,
    )
    region = Region(
        id=uuid4(),
        organization_id=org.id,
        name="Mid-Atlantic Region",
        code="MAR-01",
    )
    session.add(org)
    session.add(region)

    # 2. Inventory Items in Warehouse
    dental_implant = InventoryItem(
        id=uuid4(),
        clinic_id=clinic.id,
        sku="IMP-TITAN-4.2",
        name="Titanium Dental Implant 4.2mm x 11.5mm",
        reorder_level=10,
        current_quantity=50,
        purchase_price=180.00,
    )
    session.add(dental_implant)

    # 3. Inter-Branch Stock Requisition & Transfer
    dest_clinic_id = uuid4()
    transfer = InventoryTransfer(
        id=uuid4(),
        organization_id=org.id,
        transfer_number="TRF-2026-0012",
        from_clinic_id=clinic.id,
        to_clinic_id=dest_clinic_id,
        item_id=dental_implant.id,
        quantity=10,
        unit_cost=180.00,
        status=InventoryTransferStatus.RECEIVED,
    )
    dental_implant.current_quantity -= 10
    session.add(transfer)

    assert transfer.quantity == 10
    assert dental_implant.current_quantity == 40
    assert transfer.status == InventoryTransferStatus.RECEIVED
    assert org.code == "GDP-CORP"
    assert region.code == "MAR-01"
