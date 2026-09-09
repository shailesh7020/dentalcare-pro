from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models.communication import (
    Conversation,
    ConversationParticipant,
    ConversationType,
    Message,
)
from app.models.identity import Clinic, Role, User
from app.models.patient import Patient
from app.schemas.communication import (
    ConversationCreate,
    MessageCreate,
    MessageStatusUpdate,
)
from app.services.communication_service import CommunicationService


class FakeCommDb:
    def __init__(self, items: list[object] | None = None):
        self.items: list[object] = items or []
        self.added: list[object] = []

    def add(self, item: object) -> None:
        self.added.append(item)
        if item not in self.items:
            self.items.append(item)

    async def flush(self) -> None:
        for it in self.added:
            if getattr(it, "id", None) is None:
                it.id = uuid4()
            if getattr(it, "created_at", None) is None:
                it.created_at = datetime.now(UTC)
            if getattr(it, "updated_at", None) is None:
                it.updated_at = datetime.now(UTC)

    async def commit(self) -> None:
        await self.flush()

    async def refresh(self, item: object) -> None:
        pass

    async def get(self, model: type, id_: object) -> object | None:
        for it in self.items:
            if isinstance(it, model) and getattr(it, "id", None) == id_:
                return it
        return None

    async def scalar(self, stmt: object) -> object:
        res = await self.execute(stmt)
        if hasattr(res, "scalar_one_or_none"):
            return res.scalar_one_or_none()
        return None

    async def execute(self, stmt: object) -> object:
        text = str(stmt).lower()
        from types import SimpleNamespace

        if "from conversations" in text:
            convs = [i for i in self.items if isinstance(i, Conversation) and i.deleted_at is None]
            return SimpleNamespace(
                scalars=lambda: SimpleNamespace(all=lambda: convs),
                scalar_one_or_none=lambda: convs[0] if convs else None,
            )

        if "from conversation_participants" in text:
            parts = [i for i in self.items if isinstance(i, ConversationParticipant) and i.deleted_at is None]
            return SimpleNamespace(
                scalars=lambda: SimpleNamespace(all=lambda: parts),
                scalar_one_or_none=lambda: parts[0] if parts else None,
            )

        if "from messages" in text:
            msgs = [i for i in self.items if isinstance(i, Message) and i.deleted_at is None]
            if "count(" in text:
                unread = [m for m in msgs if not m.is_read]
                return SimpleNamespace(scalar_one_or_none=lambda: len(unread))
            return SimpleNamespace(
                scalars=lambda: SimpleNamespace(all=lambda: msgs),
                scalar_one_or_none=lambda: msgs[0] if msgs else None,
            )

        if "from clinics" in text:
            clinics = [i for i in self.items if isinstance(i, Clinic)]
            return SimpleNamespace(scalar_one_or_none=lambda: clinics[0] if clinics else None)

        if "from users" in text:
            users = [i for i in self.items if isinstance(i, User)]
            return SimpleNamespace(
                scalar_one_or_none=lambda: users[0] if users else None,
                scalars=lambda: SimpleNamespace(all=lambda: users),
            )

        if "from patients" in text:
            pats = [i for i in self.items if isinstance(i, Patient)]
            return SimpleNamespace(
                scalar_one_or_none=lambda: pats[0] if pats else None,
                scalars=lambda: SimpleNamespace(all=lambda: pats),
            )

        return SimpleNamespace(
            scalars=lambda: SimpleNamespace(all=list),
            scalar_one_or_none=lambda: None,
        )


@pytest.fixture
def comm_setup():
    clinic_id = uuid4()
    clinic = Clinic(id=clinic_id, name="Pearl Dental", slug="pearl-dental", is_active=True)
    doctor = User(
        id=uuid4(),
        clinic_id=clinic_id,
        email="dr.dentist@pearldental.com",
        first_name="Dentist",
        last_name="Smith",
        role=Role.DENTIST,
        is_active=True,
    )
    patient = Patient(
        id=uuid4(),
        clinic_id=clinic_id,
        first_name="Bruce",
        last_name="Wayne",
        patient_number="P-9901",
        mobile_number="+919988776655",
        email="bruce@wayne.com",
    )
    patient_user = User(
        id=uuid4(),
        clinic_id=clinic_id,
        patient_id=patient.id,
        email="bruce@wayne.com",
        first_name="Bruce",
        last_name="Wayne",
        role=Role.PATIENT,
        is_active=True,
    )
    return clinic, doctor, patient, patient_user


@pytest.mark.asyncio
async def test_create_conversation_and_send_message(comm_setup):
    clinic, doctor, patient, patient_user = comm_setup
    db = FakeCommDb([clinic, doctor, patient, patient_user])
    comm_svc = CommunicationService(db)

    payload = ConversationCreate(
        title="Post-op Extraction Followup",
        conversation_type=ConversationType.PATIENT_CLINIC,
        patient_id=patient.id,
        initial_message="Hello Doctor, I have mild swelling after extraction.",
    )

    conv = await comm_svc.create_conversation(clinic.id, patient_user, payload)
    assert conv.id is not None
    assert conv.title == "Post-op Extraction Followup"

    # Doctor replies
    msg_payload = MessageCreate(
        content="Please continue the cold compress and take prescribed analgesic."
    )
    msg = await comm_svc.send_message(clinic.id, doctor, conv.id, msg_payload)
    assert msg.id is not None
    assert msg.sender_user_id == doctor.id
    assert not msg.is_read

    # Mark thread as read by patient
    count = await comm_svc.mark_conversation_read(clinic.id, patient_user, conv.id)
    assert count >= 0


@pytest.mark.asyncio
async def test_conversation_authorization(comm_setup):
    clinic, doctor, patient, patient_user = comm_setup
    other_patient = Patient(
        id=uuid4(),
        clinic_id=clinic.id,
        first_name="Clark",
        last_name="Kent",
        patient_number="P-9902",
        mobile_number="+919988776654",
    )
    other_user = User(
        id=uuid4(),
        clinic_id=clinic.id,
        patient_id=other_patient.id,
        email="clark@dailyplanet.com",
        first_name="Clark",
        last_name="Kent",
        role=Role.PATIENT,
        is_active=True,
    )

    db = FakeCommDb([clinic, doctor, patient, patient_user, other_patient, other_user])
    comm_svc = CommunicationService(db)

    conv = await comm_svc.create_conversation(
        clinic.id,
        patient_user,
        ConversationCreate(
            title="Private Conversation",
            conversation_type=ConversationType.PATIENT_CLINIC,
            patient_id=patient.id,
        ),
    )

    # Attempt unauthorized access by another patient
    with pytest.raises(HTTPException) as exc:
        await comm_svc.get_conversation_detail(clinic.id, other_user, conv.id)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_update_message_read_status(comm_setup):
    clinic, doctor, patient, patient_user = comm_setup
    db = FakeCommDb([clinic, doctor, patient, patient_user])
    comm_svc = CommunicationService(db)

    conv = await comm_svc.create_conversation(
        clinic.id,
        doctor,
        ConversationCreate(
            title="Treatment Consultation",
            conversation_type=ConversationType.PATIENT_CLINIC,
            patient_id=patient.id,
        ),
    )
    msg = await comm_svc.send_message(
        clinic.id, doctor, conv.id, MessageCreate(content="Checkup scheduled")
    )
    assert not msg.is_read

    updated_msg = await comm_svc.update_message_status(
        clinic.id, msg.id, MessageStatusUpdate(is_read=True)
    )
    assert updated_msg.is_read
