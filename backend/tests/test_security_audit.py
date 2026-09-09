from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID, uuid4

import jwt
import pytest
from fastapi import HTTPException

from app.api.v1.auth import refresh
from app.core.config import get_settings
from app.dependencies.auth import current_user, require_roles
from app.models.appointment import Appointment, AppointmentStatus, Chair, VisitType
from app.models.identity import RefreshToken, Role, User
from app.models.patient import Patient
from app.models.treatment import Treatment, TreatmentStatus
from app.schemas.appointment import AppointmentCancel, AppointmentReschedule
from app.schemas.auth import RefreshRequest
from app.schemas.patient import PatientUpdate
from app.schemas.treatment import (
    TreatmentCancel,
    TreatmentComplete,
    TreatmentCreate,
    TreatmentUpdate,
)
from app.security.passwords import hash_password
from app.security.tokens import create_access_token, create_refresh_token
from app.services.appointment_service import AppointmentService
from app.services.patient_service import PatientService
from app.services.treatment_service import TreatmentService


class ScalarRows:
    def __init__(self, values: list[object] | None = None) -> None:
        self.values = list(values) if values is not None else []

    def all(self) -> list[object]:
        return self.values

    def first(self) -> object | None:
        return self.values[0] if self.values else None

    def scalars(self) -> ScalarRows:
        return self

    def scalar_one(self) -> object:
        return self.values[0] if self.values else 0

    def scalar_one_or_none(self) -> object | None:
        return self.values[0] if self.values else None


class MockDbSession:
    def __init__(self, entities: list[object] | None = None) -> None:
        self.entities: list[object] = entities or []
        self.added: list[object] = []
        self.commits = 0

    def add(self, item: object) -> None:
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

    def _filter_by_query(self, statement: object) -> list[object]:
        params: dict[str, object] = {}
        try:
            params = statement.compile().params or {}  # type: ignore[attr-defined]
        except Exception:
            pass

        clinic_ids = [v for k, v in params.items() if "clinic_id" in k]
        id_values = [v for k, v in params.items() if k == "id" or k.startswith("id_")]

        matching = list(self.entities)
        if clinic_ids:
            matching = [item for item in matching if getattr(item, "clinic_id", None) in clinic_ids]
        if id_values:
            matching = [item for item in matching if getattr(item, "id", None) in id_values]
        return matching

    async def scalar(self, statement: object) -> object | None:
        matching = self._filter_by_query(statement)
        return matching[0] if matching else None

    async def scalars(self, statement: object) -> ScalarRows:
        matching = self._filter_by_query(statement)
        return ScalarRows(matching)

    async def execute(self, statement: object) -> ScalarRows:
        matching = self._filter_by_query(statement)
        return ScalarRows(matching)


def make_user(clinic_id: UUID, role: Role, email: str | None = None, is_active: bool = True) -> User:
    return User(
        id=uuid4(),
        clinic_id=clinic_id,
        email=email or f"user-{uuid4()}@clinic.com",
        password_hash=hash_password("AuditPassword2026!"),
        first_name="Audit",
        last_name="Tester",
        role=role,
        is_active=is_active,
    )


# ============================================================================
# 1. JWT & TOKEN HARDENING TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_jwt_expired_token_rejection() -> None:
    clinic_id = uuid4()
    dentist = make_user(clinic_id, Role.DENTIST)
    settings = get_settings()

    expired_payload = {
        "sub": str(dentist.id),
        "clinic_id": str(clinic_id),
        "role": dentist.role.value,
        "exp": datetime.now(UTC) - timedelta(minutes=10),
        "nbf": datetime.now(UTC) - timedelta(minutes=20),
    }
    expired_token = jwt.encode(
        expired_payload,
        settings.jwt_secret.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )

    db = MockDbSession([dentist])
    with pytest.raises(HTTPException) as exc_info:
        await current_user(token=expired_token, db=db)  # type: ignore[arg-type]

    assert exc_info.value.status_code == 401
    assert "Invalid authentication credentials" in exc_info.value.detail


@pytest.mark.asyncio
async def test_jwt_tampered_signature_rejection() -> None:
    clinic_id = uuid4()
    dentist = make_user(clinic_id, Role.DENTIST)
    valid_token = create_access_token(str(dentist.id), str(clinic_id), dentist.role.value)

    tampered_token = valid_token[:-6] + "tamper"
    db = MockDbSession([dentist])
    with pytest.raises(HTTPException) as exc_info:
        await current_user(token=tampered_token, db=db)  # type: ignore[arg-type]

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_jwt_inactive_user_token_rejection() -> None:
    clinic_id = uuid4()
    inactive_user = make_user(clinic_id, Role.DENTIST, is_active=False)
    valid_token = create_access_token(str(inactive_user.id), str(clinic_id), inactive_user.role.value)

    db = MockDbSession([inactive_user])
    with pytest.raises(HTTPException) as exc_info:
        await current_user(token=valid_token, db=db)  # type: ignore[arg-type]

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_jwt_soft_deleted_user_token_rejection() -> None:
    clinic_id = uuid4()
    deleted_user = make_user(clinic_id, Role.DENTIST)
    deleted_user.deleted_at = datetime.now(UTC)
    valid_token = create_access_token(str(deleted_user.id), str(clinic_id), deleted_user.role.value)

    class EmptyDbSession(MockDbSession):
        async def scalar(self, statement: object) -> object | None:
            return None

    db = EmptyDbSession()
    with pytest.raises(HTTPException) as exc_info:
        await current_user(token=valid_token, db=db)  # type: ignore[arg-type]

    assert exc_info.value.status_code == 401


# ============================================================================
# 2. REFRESH TOKEN REPLAY DETECTION
# ============================================================================

@pytest.mark.asyncio
async def test_refresh_token_replay_attack_revokes_family() -> None:
    clinic_id = uuid4()
    user = make_user(clinic_id, Role.DENTIST)
    raw_token, digest, _ = create_refresh_token()
    family_id = uuid4()

    revoked_token_record = RefreshToken(
        id=uuid4(),
        user_id=user.id,
        token_hash=digest,
        family_id=family_id,
        expires_at=datetime.now(UTC) + timedelta(days=7),
        revoked_at=datetime.now(UTC) - timedelta(hours=1),
    )

    class ReplayMockSession(MockDbSession):
        def __init__(self) -> None:
            super().__init__([revoked_token_record, user])
            self.scalars_list = [revoked_token_record]

        async def scalar(self, statement: object) -> object | None:
            return self.scalars_list.pop(0) if self.scalars_list else None

    db = ReplayMockSession()

    with pytest.raises(Exception, match="replay"):
        await refresh(RefreshRequest(refresh_token=raw_token), None, db)  # type: ignore[arg-type]

    assert db.commits >= 1


# ============================================================================
# 3. MULTI-TENANT IDOR DATA ISOLATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_idor_cross_tenant_patient_isolation() -> None:
    clinic_a = uuid4()
    clinic_b = uuid4()
    doctor_a = make_user(clinic_a, Role.DENTIST)

    patient_b = Patient(
        id=uuid4(),
        clinic_id=clinic_b,
        patient_number="PAT-B-001",
        first_name="ClinicB",
        last_name="Patient",
        gender="FEMALE",
        date_of_birth=date(1990, 1, 1),
        mobile_number="9123456780",
    )

    db = MockDbSession([patient_b])
    service = PatientService(db, actor=doctor_a)  # type: ignore[arg-type]

    # Clinic A attempts to access Clinic B patient
    with pytest.raises(HTTPException) as exc:
        await service.get(patient_id=patient_b.id)
    assert exc.value.status_code == 404

    # Clinic A attempts to update Clinic B patient
    with pytest.raises(HTTPException) as exc:
        await service.update(
            patient_id=patient_b.id,
            payload=PatientUpdate(first_name="Hacked"),
        )
    assert exc.value.status_code == 404

    # Clinic A attempts to soft-delete Clinic B patient
    with pytest.raises(HTTPException) as exc:
        await service.delete(patient_id=patient_b.id)
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_idor_cross_tenant_appointment_isolation() -> None:
    clinic_a = uuid4()
    clinic_b = uuid4()

    doctor_a = make_user(clinic_a, Role.DENTIST)
    doctor_b = make_user(clinic_b, Role.DENTIST)

    patient_b = Patient(
        id=uuid4(),
        clinic_id=clinic_b,
        patient_number="PAT-B-002",
        first_name="Patient",
        last_name="B",
        gender="MALE",
        date_of_birth=date(1985, 5, 5),
        mobile_number="9876543211",
    )

    chair_b = Chair(id=uuid4(), clinic_id=clinic_b, name="Chair B", is_active=True)

    apt_b = Appointment(
        id=uuid4(),
        clinic_id=clinic_b,
        patient_id=patient_b.id,
        dentist_id=doctor_b.id,
        chair_id=chair_b.id,
        appointment_number="APT-B-001",
        date=date(2026, 9, 9),
        start_time=time(10, 0),
        end_time=time(10, 30),
        duration=30,
        status=AppointmentStatus.CONFIRMED,
        visit_type=VisitType.CONSULTATION,
    )
    apt_b.patient = patient_b
    apt_b.dentist = doctor_b
    apt_b.chair = chair_b
    apt_b.timeline_events = []

    db = MockDbSession([apt_b, patient_b, doctor_b, chair_b, doctor_a])
    service = AppointmentService(db)  # type: ignore[arg-type]

    # Clinic A doctor attempts to access Clinic B appointment
    with pytest.raises(HTTPException) as exc:
        await service.get(clinic_id=clinic_a, appointment_id=apt_b.id)
    assert exc.value.status_code == 404

    # Clinic A attempts to cancel Clinic B appointment
    with pytest.raises(HTTPException) as exc:
        await service.cancel(
            clinic_id=clinic_a,
            appointment_id=apt_b.id,
            payload=AppointmentCancel(reason="Unauthorized cancellation"),
            actor=doctor_a,
        )
    assert exc.value.status_code == 404

    # Clinic A attempts to reschedule Clinic B appointment
    with pytest.raises(HTTPException) as exc:
        await service.reschedule(
            clinic_id=clinic_a,
            appointment_id=apt_b.id,
            payload=AppointmentReschedule(
                new_date=date(2026, 9, 10),
                new_start_time=time(11, 0),
                reason="Unauthorized reschedule",
            ),
            actor=doctor_a,
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_idor_cross_tenant_treatment_isolation() -> None:
    clinic_a = uuid4()
    clinic_b = uuid4()

    doctor_a = make_user(clinic_a, Role.DENTIST)
    doctor_b = make_user(clinic_b, Role.DENTIST)

    patient_b = Patient(
        id=uuid4(),
        clinic_id=clinic_b,
        patient_number="PAT-B-003",
        first_name="Patient",
        last_name="B3",
        gender="FEMALE",
        date_of_birth=date(1992, 4, 12),
        mobile_number="9988776655",
    )

    apt_b = Appointment(
        id=uuid4(),
        clinic_id=clinic_b,
        patient_id=patient_b.id,
        dentist_id=doctor_b.id,
        chair_id=uuid4(),
        appointment_number="APT-B-003",
        date=date(2026, 9, 9),
        start_time=time(14, 0),
        end_time=time(14, 30),
        duration=30,
        status=AppointmentStatus.IN_TREATMENT,
        visit_type=VisitType.CONSULTATION,
    )

    treatment_b = Treatment(
        id=uuid4(),
        clinic_id=clinic_b,
        patient_id=patient_b.id,
        appointment_id=apt_b.id,
        dentist_id=doctor_b.id,
        treatment_number="TRT-20260909-0001",
        diagnosis="Cross Clinic Caries",
        status=TreatmentStatus.IN_PROGRESS,
    )
    treatment_b.patient = patient_b
    treatment_b.dentist = doctor_b
    treatment_b.appointment = apt_b
    treatment_b.procedures = []
    treatment_b.follow_ups = []

    db = MockDbSession([treatment_b, patient_b, apt_b, doctor_b, doctor_a])
    service = TreatmentService(db)  # type: ignore[arg-type]

    # Clinic A attempts to get Clinic B treatment
    with pytest.raises(HTTPException) as exc:
        await service.get_treatment(clinic_id=clinic_a, treatment_id=treatment_b.id)
    assert exc.value.status_code == 404

    # Clinic A attempts to update Clinic B treatment
    with pytest.raises(HTTPException) as exc:
        await service.update_treatment(
            clinic_id=clinic_a,
            treatment_id=treatment_b.id,
            payload=TreatmentUpdate(clinical_findings="Unauthorized edit"),
            actor=doctor_a,
        )
    assert exc.value.status_code == 404

    # Clinic A attempts to complete Clinic B treatment
    with pytest.raises(HTTPException) as exc:
        await service.complete_treatment(
            clinic_id=clinic_a,
            treatment_id=treatment_b.id,
            payload=TreatmentComplete(),
            actor=doctor_a,
        )
    assert exc.value.status_code == 404

    # Clinic A attempts to cancel Clinic B treatment
    with pytest.raises(HTTPException) as exc:
        await service.cancel_treatment(
            clinic_id=clinic_a,
            treatment_id=treatment_b.id,
            payload=TreatmentCancel(reason="Unauthorized cancellation"),
            actor=doctor_a,
        )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_cross_tenant_entity_mismatch_prevention() -> None:
    clinic_a = uuid4()
    clinic_b = uuid4()

    doctor_a = make_user(clinic_a, Role.DENTIST)
    patient_a = Patient(
        id=uuid4(),
        clinic_id=clinic_a,
        patient_number="PAT-A-001",
        first_name="Patient",
        last_name="A",
        gender="MALE",
        date_of_birth=date(1995, 1, 1),
        mobile_number="9111111111",
    )

    apt_b = Appointment(
        id=uuid4(),
        clinic_id=clinic_b,
        patient_id=uuid4(),
        dentist_id=uuid4(),
        chair_id=uuid4(),
        appointment_number="APT-B-099",
        date=date(2026, 9, 9),
        start_time=time(9, 0),
        end_time=time(9, 30),
        duration=30,
        status=AppointmentStatus.CHECKED_IN,
        visit_type=VisitType.CONSULTATION,
    )

    db = MockDbSession([doctor_a, patient_a, apt_b])
    service = TreatmentService(db)  # type: ignore[arg-type]

    payload = TreatmentCreate(
        patient_id=patient_a.id,
        appointment_id=apt_b.id,
        dentist_id=doctor_a.id,
        diagnosis="Cross Tenant Mismatch",
    )
    with pytest.raises(HTTPException) as exc:
        await service.create_treatment(clinic_id=clinic_a, payload=payload, actor=doctor_a)

    assert exc.value.status_code == 404
    assert "Appointment not found in this clinic" in exc.value.detail


# ============================================================================
# 4. RBAC BOUNDARY ENFORCEMENT TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_rbac_receptionist_cannot_override_treatment_lock() -> None:
    clinic_id = uuid4()
    receptionist = make_user(clinic_id, Role.RECEPTIONIST)
    dentist = make_user(clinic_id, Role.DENTIST)

    patient = Patient(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_number="PAT-101",
        first_name="P",
        last_name="One",
        gender="FEMALE",
        date_of_birth=date(1990, 1, 1),
        mobile_number="9876543210",
    )

    apt = Appointment(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_id=patient.id,
        dentist_id=dentist.id,
        chair_id=uuid4(),
        appointment_number="APT-101",
        date=date(2026, 9, 8),
        start_time=time(10, 0),
        end_time=time(10, 30),
        duration=30,
        status=AppointmentStatus.CONFIRMED,
        visit_type=VisitType.CONSULTATION,
    )

    existing_trt = Treatment(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_id=patient.id,
        appointment_id=apt.id,
        dentist_id=dentist.id,
        treatment_number="TRT-20260908-0001",
        diagnosis="Active Caries",
        status=TreatmentStatus.IN_PROGRESS,
    )

    db = MockDbSession([patient, dentist, apt, existing_trt])
    service = TreatmentService(db)  # type: ignore[arg-type]

    payload_override = TreatmentCreate(
        patient_id=patient.id,
        appointment_id=apt.id,
        dentist_id=dentist.id,
        diagnosis="Second treatment override attempt",
        is_override=True,
    )

    with pytest.raises(HTTPException) as exc:
        await service.create_treatment(clinic_id, payload_override, receptionist)

    assert exc.value.status_code == 403
    assert "Only clinic administrators can override" in exc.value.detail


@pytest.mark.asyncio
async def test_rbac_require_roles_enforcement() -> None:
    clinic_id = uuid4()
    receptionist = make_user(clinic_id, Role.RECEPTIONIST)

    admin_only_dependency = require_roles(Role.CLINIC_ADMIN, Role.SUPER_ADMIN)

    with pytest.raises(HTTPException) as exc:
        await admin_only_dependency(user=receptionist)

    assert exc.value.status_code == 403
    assert "Insufficient permissions" in exc.value.detail

    clinic_admin = make_user(clinic_id, Role.CLINIC_ADMIN)
    permitted_user = await admin_only_dependency(user=clinic_admin)
    assert permitted_user.id == clinic_admin.id


# ============================================================================
# 5. CLINICAL RECORD IMMUTABILITY TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_completed_treatment_immutability() -> None:
    clinic_id = uuid4()
    dentist = make_user(clinic_id, Role.DENTIST)
    clinic_admin = make_user(clinic_id, Role.CLINIC_ADMIN)

    treatment = Treatment(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_id=uuid4(),
        appointment_id=uuid4(),
        dentist_id=dentist.id,
        treatment_number="TRT-20260908-LOCKED",
        diagnosis="Locked Medical Record",
        status=TreatmentStatus.COMPLETED,
        completed_at=datetime.now(UTC) - timedelta(hours=2),
    )
    treatment.procedures = []
    treatment.follow_ups = []

    db = MockDbSession([treatment])
    service = TreatmentService(db)  # type: ignore[arg-type]

    # 1. Modification attempt rejected
    with pytest.raises(HTTPException) as exc:
        await service.update_treatment(
            clinic_id,
            treatment.id,
            TreatmentUpdate(clinical_findings="Attempt to alter locked notes"),
            dentist,
        )
    assert exc.value.status_code == 400
    assert "permanently locked and cannot be edited" in exc.value.detail

    # 2. Deletion attempt rejected (even by clinic admin)
    with pytest.raises(HTTPException) as exc:
        await service.delete_treatment(clinic_id, treatment.id, clinic_admin)
    assert exc.value.status_code == 400
    assert "Completed treatments cannot be deleted" in exc.value.detail

    # 3. Cancellation attempt rejected
    with pytest.raises(HTTPException) as exc:
        await service.cancel_treatment(
            clinic_id,
            treatment.id,
            TreatmentCancel(reason="Attempt to cancel completed"),
            dentist,
        )
    assert exc.value.status_code == 400
    assert "permanently locked and cannot be cancelled" in exc.value.detail
