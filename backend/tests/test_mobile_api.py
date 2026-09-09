from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.api.v1.mobile import (
    get_digital_signature,
    list_my_mobile_devices,
    list_patient_media,
    mobile_ai_assist,
    pull_offline_sync,
    push_offline_sync,
    record_digital_signature,
    register_mobile_device,
    unregister_mobile_device,
    upload_clinical_media,
)
from app.models.identity import Role, User
from app.models.mobile import (
    DeviceType,
    MobileClinicalMedia,
    MobileDevice,
    MobileDigitalSignature,
    MobileMediaType,
    MobileSyncQueue,
    SignatureType,
    SyncStatus,
)
from app.schemas.mobile import (
    MobileAIAssistRequest,
    MobileClinicalMediaCreate,
    MobileDeviceRegister,
    MobileDigitalSignatureCreate,
    MobileMutation,
    MobileSyncPushRequest,
)


class FakeScalarResult:
    def __init__(self, items):
        self._items = list(items) if items is not None else []

    def all(self):
        return self._items

    def scalars(self):
        return self

    def scalar_one_or_none(self):
        return self._items[0] if self._items else None

    def scalar_one(self):
        return self._items[0] if self._items else 0

    def scalar(self):
        return self._items[0] if self._items else 0


class FakeDb:
    def __init__(self):
        self.items = []

    def add(self, item):
        if not hasattr(item, "id") or item.id is None:
            item.id = uuid4()
        if not hasattr(item, "created_at") or item.created_at is None:
            item.created_at = datetime.now(UTC)
        if not hasattr(item, "updated_at") or item.updated_at is None:
            item.updated_at = datetime.now(UTC)
        if not hasattr(item, "deleted_at"):
            item.deleted_at = None
        self.items.append(item)

    async def flush(self):
        pass

    async def commit(self):
        pass

    async def refresh(self, item):
        pass

    async def execute(self, statement):
        text = str(statement).lower()

        if "mobile_devices" in text:
            matching = [i for i in self.items if isinstance(i, MobileDevice) and getattr(i, "deleted_at", None) is None]
            if "is_active" in text:
                matching = [i for i in matching if getattr(i, "is_active", True) is True]
            return FakeScalarResult(matching)

        if "mobile_sync_queues" in text:
            matching = [i for i in self.items if isinstance(i, MobileSyncQueue)]
            params = statement.compile().params if hasattr(statement, "compile") else {}
            for k, v in params.items():
                if "client_mutation_id" in k:
                    matching = [i for i in matching if i.client_mutation_id == v]
            return FakeScalarResult(matching)

        if "mobile_digital_signatures" in text:
            matching = [i for i in self.items if isinstance(i, MobileDigitalSignature) and getattr(i, "deleted_at", None) is None]
            return FakeScalarResult(matching)

        if "mobile_clinical_media" in text:
            matching = [i for i in self.items if isinstance(i, MobileClinicalMedia) and getattr(i, "deleted_at", None) is None]
            return FakeScalarResult(matching)

        return FakeScalarResult([])


def make_actor(role: Role = Role.DENTIST, clinic_id=None, user_id=None):
    user = User(
        id=user_id or uuid4(),
        email="doctor@dentalcarepro.com",
        password_hash="hash",
        first_name="Dr. Neil",
        last_name="Shah",
        role=role,
        clinic_id=clinic_id or uuid4(),
        is_active=True,
    )
    user.patient_id = uuid4() if role == Role.PATIENT else None
    return user


@pytest.mark.asyncio
async def test_register_and_list_mobile_device():
    db = FakeDb()
    actor = make_actor(Role.DENTIST)

    payload = MobileDeviceRegister(
        device_token="fcm_token_dentist_iphone_15_pro_xyz",
        device_type=DeviceType.IOS,
        device_name="Dr. Shah's iPhone 15 Pro",
        device_os_version="iOS 18.2",
        app_version="1.5.0",
        biometric_enabled=True,
    )

    reg = await register_mobile_device(payload, actor=actor, db=db)
    assert reg.device_token == "fcm_token_dentist_iphone_15_pro_xyz"
    assert reg.device_type == "IOS"
    assert reg.biometric_enabled is True
    assert reg.user_id == actor.id

    devices = await list_my_mobile_devices(actor=actor, db=db)
    assert len(devices) == 1
    assert devices[0].device_name == "Dr. Shah's iPhone 15 Pro"


@pytest.mark.asyncio
async def test_unregister_mobile_device():
    db = FakeDb()
    actor = make_actor(Role.RECEPTIONIST)

    payload = MobileDeviceRegister(
        device_token="fcm_token_ipad_frontdesk",
        device_type=DeviceType.IOS,
        device_name="Frontdesk iPad Pro",
        device_os_version="iPadOS 18.1",
        app_version="1.5.0",
        biometric_enabled=False,
    )

    reg = await register_mobile_device(payload, actor=actor, db=db)
    res = await unregister_mobile_device(reg.id, actor=actor, db=db)
    assert res["status"] == "unregistered"


@pytest.mark.asyncio
async def test_mobile_offline_delta_sync_pull():
    db = FakeDb()
    actor = make_actor(Role.DENTIST)

    since = datetime.now(UTC) - timedelta(days=1)
    response = await pull_offline_sync(since=since, actor=actor, db=db)

    assert response.server_timestamp is not None
    assert isinstance(response.appointments, list)
    assert isinstance(response.patients, list)
    assert isinstance(response.treatments, list)
    assert isinstance(response.prescriptions, list)
    assert response.has_more is False


@pytest.mark.asyncio
async def test_mobile_offline_delta_sync_push_idempotency_and_conflict():
    db = FakeDb()
    actor = make_actor(Role.DENTIST)

    mutation_id = str(uuid4())
    mutation1 = MobileMutation(
        client_mutation_id=mutation_id,
        entity_type="CLINICAL_NOTE",
        action="CREATE",
        client_timestamp=datetime.now(UTC),
        payload={"note": "Scaling and root planing completed on lower arch.", "tooth": 31},
    )

    conflict_mutation_id = str(uuid4())
    old_timestamp = datetime.now(UTC) - timedelta(days=10)
    mutation2 = MobileMutation(
        client_mutation_id=conflict_mutation_id,
        entity_type="ATTENDANCE",
        action="CREATE",
        client_timestamp=old_timestamp,
        payload={"punch_type": "CHECK_IN"},
    )

    req = MobileSyncPushRequest(mutations=[mutation1, mutation2])
    push_res = await push_offline_sync(req, actor=actor, db=db)

    assert push_res.processed_count == 2
    assert push_res.success_count == 1
    assert push_res.conflict_count == 1
    assert len(push_res.results) == 2

    # Verify idempotency by submitting the same mutation again
    dup_req = MobileSyncPushRequest(mutations=[mutation1])
    dup_res = await push_offline_sync(dup_req, actor=actor, db=db)
    assert dup_res.results[0].status == SyncStatus.APPLIED
    assert "already applied" in dup_res.results[0].message


@pytest.mark.asyncio
async def test_mobile_digital_signature_capture_and_retrieve():
    db = FakeDb()
    actor = make_actor(Role.PATIENT)
    consent_id = uuid4()

    payload = MobileDigitalSignatureCreate(
        signature_type=SignatureType.PATIENT_CONSENT,
        target_entity_type="consent_form",
        target_entity_id=consent_id,
        patient_id=actor.patient_id,
        signature_image_url="https://dentalcare.local/signatures/sig_consent_001.png",
        ip_address="192.168.1.55",
        device_fingerprint="iPhone15Pro_iOS18_A17Pro",
    )

    sig = await record_digital_signature(payload, actor=actor, db=db)
    assert sig.signature_type == "PATIENT_CONSENT"
    assert sig.target_entity_id == consent_id
    assert sig.signer_id == actor.id

    fetched = await get_digital_signature(sig.id, actor=actor, db=db)
    assert fetched is not None
    assert fetched.signature_image_url == payload.signature_image_url


@pytest.mark.asyncio
async def test_mobile_clinical_media_upload_and_filter():
    db = FakeDb()
    actor = make_actor(Role.DENTIST)
    patient_id = uuid4()
    treatment_id = uuid4()

    media_payload = MobileClinicalMediaCreate(
        patient_id=patient_id,
        treatment_id=treatment_id,
        media_type=MobileMediaType.INTRAORAL_PHOTO,
        tooth_number=26,
        file_url="https://dentalcare.local/media/intraoral_26_occlusal.jpg",
        file_size_bytes=1048576,
        compression_ratio=0.55,
        notes="Occlusal fracture line visible on disto-palatal cusp.",
    )

    media = await upload_clinical_media(media_payload, actor=actor, db=db)
    assert media.media_type == "INTRAORAL_PHOTO"
    assert media.tooth_number == 26
    assert media.compression_ratio == 0.55
    assert media.captured_by_id == actor.id

    media_list = await list_patient_media(patient_id=patient_id, actor=actor, db=db)
    assert len(media_list) == 1
    assert media_list[0].tooth_number == 26


@pytest.mark.asyncio
async def test_mobile_ai_assist():
    db = FakeDb()
    actor = make_actor(Role.DENTIST)

    req = MobileAIAssistRequest(
        task_type="CLINICAL_SUMMARY",
        context_text="Patient complained of sharp pain with cold stimuli on lower right molar.",
        procedure_name="Tooth #46 Composite Restoration",
    )

    ai_res = await mobile_ai_assist(req, actor=actor, db=db)
    assert ai_res.task_type == "CLINICAL_SUMMARY"
    assert "Subjective" in ai_res.suggestion
    assert "Tooth #46 Composite Restoration" in ai_res.suggestion
    assert ai_res.is_advisory_only is True
