from __future__ import annotations

import hashlib
import signal
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.models.appointment import AppointmentStatus
from app.models.commercial import (
    SignatureType,
)
from app.models.identity import Role, User
from app.models.notification import (
    NotificationPriority,
)
from app.models.remote import ClinicRemoteConfig
from app.security.crypto import decrypt_value, encrypt_value
from app.services.clinic_network_service import ClinicNetworkService
from app.services.remote_access_service import RemoteAccessService
from app.services.remote_notification_service import RemoteNotificationService
from app.services.signature_service import ClinicianSignatureService
from app.services.update_service import UpdateService
from app.workers.task_worker import DentalCareTaskWorker


class MockDb:
    def __init__(self, entities: list[Any] | None = None) -> None:
        self.entities = entities or []
        self.added: list[Any] = []

    def add(self, item: Any) -> None:
        self.added.append(item)

    async def commit(self) -> None:
        pass

    async def refresh(self, item: Any) -> None:
        if not hasattr(item, "id") or not item.id:
            item.id = uuid4()

    async def get(self, model: Any, ident: Any) -> Any:
        for e in self.entities:
            if getattr(e, "id", None) == ident:
                return e
        return None

    async def execute(self, stmt: Any) -> Any:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = self.entities[0] if self.entities else None
        mock_result.scalars.return_value.all.return_value = self.entities
        mock_result.first.return_value = (self.entities[0], MagicMock()) if self.entities else None
        return mock_result


# ==============================================================================
# 1. DentalCareTaskWorker Tests (app.workers.task_worker)
# ==============================================================================


@pytest.mark.asyncio
async def test_task_worker_initialization_and_process():
    worker = DentalCareTaskWorker()
    assert worker.is_running is True

    # Process task execution
    await worker.process_task("process_insurance_claim", {"id": "CLM-12345"})


def test_task_worker_signal_shutdown():
    worker = DentalCareTaskWorker()
    assert worker.is_running is True

    # Handle signal
    worker._handle_shutdown_signal(signal.SIGTERM, None)
    assert worker.is_running is False


def test_task_worker_setup_signal_handlers():
    worker = DentalCareTaskWorker()
    with patch("signal.signal") as mock_signal:
        worker.setup_signal_handlers()
        assert mock_signal.call_count >= 2


@pytest.mark.asyncio
async def test_task_worker_run_loop_execution():
    worker = DentalCareTaskWorker()

    iterations_run = 0

    async def fake_sleep(duration):
        nonlocal iterations_run
        iterations_run += 1
        # Stop after hitting 30 iterations to test the heartbeat branch
        if iterations_run >= 30:
            worker.is_running = False

    with (
        patch("asyncio.sleep", side_effect=fake_sleep),
        patch.object(worker, "setup_signal_handlers"),
    ):
        await worker.run()

    assert worker.is_running is False
    assert iterations_run >= 30


# ==============================================================================
# 2. UpdateService Tests (app.services.update_service)
# ==============================================================================


@pytest.mark.asyncio
async def test_update_service_status():
    status = UpdateService.get_status()
    assert status.status is not None
    assert status.progress_percent >= 0


@pytest.mark.asyncio
async def test_update_service_apply_update_success():
    with tempfile.TemporaryDirectory() as tmpdir:
        package_file = Path(tmpdir) / "update_v2.0.0.zip"
        content = b"fake-package-contents-v2.0.0"
        package_file.write_bytes(content)
        pkg_sha = hashlib.sha256(content).hexdigest()

        db = MockDb()
        with patch("app.services.backup_service.BackupService.create_backup") as mock_backup:
            mock_backup.return_value = MagicMock(file_name="pre_update_backup.dcb")

            res = await UpdateService.apply_update(
                db=db,  # type: ignore
                clinic_id=uuid4(),
                target_version="2.0.0",
                package_path=str(package_file),
                expected_sha256=pkg_sha,
            )

            assert res.status == "READY"
            assert res.progress_percent == 100
            assert res.target_version == "2.0.0"


@pytest.mark.asyncio
async def test_update_service_apply_update_sha_mismatch():
    with tempfile.TemporaryDirectory() as tmpdir:
        package_file = Path(tmpdir) / "update_v2.0.0.zip"
        package_file.write_bytes(b"actual-content")

        db = MockDb()
        with patch("app.services.backup_service.BackupService.create_backup") as mock_backup:
            mock_backup.return_value = MagicMock(file_name="pre_update_backup.dcb")

            with pytest.raises(ValueError, match="Package SHA-256 verification failed"):
                await UpdateService.apply_update(
                    db=db,  # type: ignore
                    clinic_id=uuid4(),
                    target_version="2.0.0",
                    package_path=str(package_file),
                    expected_sha256="wrong-expected-sha",
                )


@pytest.mark.asyncio
async def test_update_service_apply_update_missing_package():
    db = MockDb()
    with patch("app.services.backup_service.BackupService.create_backup") as mock_backup:
        mock_backup.return_value = MagicMock(file_name="pre_update_backup.dcb")

        with pytest.raises(FileNotFoundError):
            await UpdateService.apply_update(
                db=db,  # type: ignore
                clinic_id=uuid4(),
                target_version="2.0.0",
                package_path="C:/non_existent_package_file.zip",
            )


@pytest.mark.asyncio
async def test_update_service_apply_update_backup_failure():
    db = MockDb()
    with (
        patch("app.services.backup_service.BackupService.create_backup", side_effect=OSError("Disk full")),
        pytest.raises(RuntimeError, match="Pre-update safety backup failed"),
    ):
        await UpdateService.apply_update(
            db=db,  # type: ignore
            clinic_id=uuid4(),
            target_version="2.0.0",
        )


# ==============================================================================
# 3. ClinicianSignatureService Tests (app.services.signature_service)
# ==============================================================================


@pytest.mark.asyncio
async def test_clinician_signature_service_flow():
    user_id = uuid4()
    sig_data = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

    # 1. Save new signature
    db = MockDb()
    sig = await ClinicianSignatureService.save_signature(
        db=db,  # type: ignore
        user_id=user_id,
        signature_data=sig_data,
        signature_type=SignatureType.DRAWN,
    )
    assert sig is not None
    assert sig.user_id == user_id
    assert sig.is_active is True

    # 2. Update existing signature
    db_existing = MockDb([sig])
    updated_sig = await ClinicianSignatureService.save_signature(
        db=db_existing,  # type: ignore
        user_id=user_id,
        signature_data="data:image/png;base64,UPDATED_DATA",
        signature_type=SignatureType.UPLOADED,
    )
    assert updated_sig.signature_type == str(SignatureType.UPLOADED)

    # 3. Query signature
    found = await ClinicianSignatureService.get_by_user_id(db_existing, user_id)  # type: ignore
    assert found is not None

    # 4. Deactivate signature
    success = await ClinicianSignatureService.deactivate_signature(db_existing, user_id)  # type: ignore
    assert success is True
    assert sig.is_active is False

    # 5. Deactivate non-existent
    empty_db = MockDb()
    assert await ClinicianSignatureService.deactivate_signature(empty_db, uuid4()) is False  # type: ignore

    # 6. Flowable creation
    flowable = ClinicianSignatureService.create_signature_flowable(sig_data)
    assert flowable is not None

    invalid_flowable = ClinicianSignatureService.create_signature_flowable("invalid-corrupt-data!")
    assert invalid_flowable is None


# ==============================================================================
# 4. RemoteNotificationService Tests (app.services.remote_notification_service)
# ==============================================================================


@pytest.mark.asyncio
async def test_remote_notification_service_helpers():
    clinic_id = uuid4()
    db = MockDb()

    # 1. General create and dispatch
    notif = await RemoteNotificationService.create_and_dispatch(
        db=db,  # type: ignore
        clinic_id=clinic_id,
        title="Test Alert",
        body="Notification body",
        priority=NotificationPriority.HIGH,
    )
    assert notif.title == "Test Alert"
    assert notif.priority == NotificationPriority.HIGH

    # 2. Appointment reminder
    appt_notif = await RemoteNotificationService.notify_appointment_reminder(
        db=db,  # type: ignore
        clinic_id=clinic_id,
        patient_name="John Doe",
        appointment_time="10:30 AM",
        dentist_name="Dr. Smith",
    )
    assert "John Doe" in appt_notif.title

    # 3. Low stock alert
    stock_notif = await RemoteNotificationService.notify_low_stock(
        db=db,  # type: ignore
        clinic_id=clinic_id,
        item_name="Dental Composite",
        current_stock=2,
        minimum_stock=10,
    )
    assert "Dental Composite" in stock_notif.title

    # 4. Backup status alerts
    succ_notif = await RemoteNotificationService.notify_backup_status(
        db=db,  # type: ignore
        clinic_id=clinic_id,
        file_name="backup.dcb",
        is_success=True,
    )
    assert succ_notif.priority == NotificationPriority.LOW

    fail_notif = await RemoteNotificationService.notify_backup_status(
        db=db,  # type: ignore
        clinic_id=clinic_id,
        file_name="backup.dcb",
        is_success=False,
        error_message="Storage disk write timeout",
    )
    assert fail_notif.priority == NotificationPriority.URGENT

    # 5. Web push formatting
    push_payload = RemoteNotificationService.format_web_push_payload(succ_notif)
    assert "notification" in push_payload
    assert push_payload["notification"]["title"] == succ_notif.title


# ==============================================================================
# 5. ClinicNetworkService Tests (app.services.clinic_network_service)
# ==============================================================================


@pytest.mark.asyncio
async def test_clinic_network_service_lifecycle():
    clinic_id = uuid4()
    ws_id_1 = "workstation-operatory-1"
    ws_id_2 = "workstation-reception"

    mock_ws1 = AsyncMock()
    mock_ws2 = AsyncMock()

    # 1. Connect first workstation
    await ClinicNetworkService.connect_workstation(
        websocket=mock_ws1,
        clinic_id=clinic_id,
        workstation_id=ws_id_1,
        role="DENTIST",
        client_ip="192.168.1.10",
    )
    mock_ws1.accept.assert_awaited_once()

    # 2. Connect second workstation
    await ClinicNetworkService.connect_workstation(
        websocket=mock_ws2,
        clinic_id=clinic_id,
        workstation_id=ws_id_2,
        role="RECEPTIONIST",
        client_ip="192.168.1.20",
    )

    # 3. Verify active workstations
    active = ClinicNetworkService.get_active_workstations(clinic_id)
    assert len(active) == 2
    ids = [item["workstation_id"] for item in active]
    assert ws_id_1 in ids
    assert ws_id_2 in ids

    # 4. Broadcast event
    sent = await ClinicNetworkService.broadcast_event(
        clinic_id=clinic_id,
        event_type="PATIENT_ARRIVED",
        payload={"patient_name": "Alice"},
        target_role="DENTIST",
    )
    assert sent == 1

    # 5. Disconnect workstation
    await ClinicNetworkService.disconnect_workstation(clinic_id, ws_id_1)
    active_after = ClinicNetworkService.get_active_workstations(clinic_id)
    assert len(active_after) == 1

    await ClinicNetworkService.disconnect_workstation(clinic_id, ws_id_2)
    assert len(ClinicNetworkService.get_active_workstations(clinic_id)) == 0


# ==============================================================================
# 6. RemoteAccessService Tests (app.services.remote_access_service)
# ==============================================================================


@pytest.mark.asyncio
async def test_remote_access_get_or_create_config():
    clinic_id = uuid4()

    # 1. Existing config branch
    mock_db = MagicMock()
    mock_res = MagicMock()
    existing_config = ClinicRemoteConfig(
        clinic_id=clinic_id,
        is_remote_enabled=True,
        allowed_roles_json="[]",
        require_2fa=False,
        session_timeout_minutes=480,
        tunnel_provider="cloudflare",
    )
    mock_res.scalar_one_or_none.return_value = existing_config
    mock_db.execute = AsyncMock(return_value=mock_res)

    res = await RemoteAccessService.get_or_create_config(clinic_id, mock_db)
    assert res == existing_config

    # 2. Non-existing config branch (creates default)
    mock_db_new = MagicMock()
    mock_res_new = MagicMock()
    mock_res_new.scalar_one_or_none.return_value = None
    mock_db_new.execute = AsyncMock(return_value=mock_res_new)
    mock_db_new.add = MagicMock()
    mock_db_new.commit = AsyncMock()
    mock_db_new.refresh = AsyncMock()

    created_config = await RemoteAccessService.get_or_create_config(clinic_id, mock_db_new)
    assert created_config.clinic_id == clinic_id
    assert created_config.is_remote_enabled is True
    assert created_config.tunnel_provider == "cloudflare"
    mock_db_new.add.assert_called_once()
    mock_db_new.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_remote_access_session_lifecycle():
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.clinic_id = uuid4()

    # 1. Create session
    mock_db = MagicMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    session, raw_token = await RemoteAccessService.create_remote_session(
        user=user,
        device_name="Clinician iPad",
        device_type="TABLET",
        ip_address="192.168.1.150",
        user_agent="DentalCare-Mobile/1.0",
        db=mock_db,
        is_2fa_verified=True,
        timeout_minutes=120,
    )
    assert session.user_id == user.id
    assert session.device_name == "Clinician iPad"
    assert session.device_type == "TABLET"
    assert session.is_2fa_verified is True
    assert len(raw_token) > 20
    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited_once()

    # 2. List sessions
    mock_res = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [session]
    mock_res.scalars.return_value = mock_scalars
    mock_db.execute = AsyncMock(return_value=mock_res)

    sessions_list = await RemoteAccessService.list_remote_sessions(user.id, mock_db)
    assert len(sessions_list) == 1
    assert sessions_list[0]["device_name"] == "Clinician iPad"
    assert sessions_list[0]["ip_address"] == "192.168.1.150"

    # 3. Revoke session (found)
    rev_session = MagicMock()
    rev_session.revoked_at = None
    mock_rev_res = MagicMock()
    mock_rev_res.scalar_one_or_none.return_value = rev_session
    mock_db.execute = AsyncMock(return_value=mock_rev_res)

    revoked = await RemoteAccessService.revoke_session(uuid4(), user.id, mock_db)
    assert revoked is True
    assert rev_session.revoked_at is not None

    # 4. Revoke session (not found)
    mock_rev_res.scalar_one_or_none.return_value = None
    revoked_none = await RemoteAccessService.revoke_session(uuid4(), user.id, mock_db)
    assert revoked_none is False


@pytest.mark.asyncio
async def test_remote_access_mobile_dashboard_summary():
    clinic_id = uuid4()
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.role = Role.DENTIST

    appt_today = MagicMock()
    appt_today.id = uuid4()
    appt_today.appointment_number = "APP-101"
    appt_today.start_time = datetime(2026, 9, 9, 9, 30, tzinfo=UTC)
    appt_today.end_time = datetime(2026, 9, 9, 10, 15, tzinfo=UTC)
    appt_today.status = AppointmentStatus.CONFIRMED
    appt_today.chief_complaint = "Routine Checkup"

    pat = MagicMock()
    pat.id = uuid4()
    pat.first_name = "Sarah"
    pat.last_name = "Connor"
    pat.mobile_number = "+919876543210"
    pat.gender = MagicMock(value="FEMALE")

    chair = MagicMock()
    chair.name = "Operatory 2"

    dentist = MagicMock()
    dentist.first_name = "Miles"
    dentist.last_name = "Dyson"

    appt_tomorrow = MagicMock()
    appt_tomorrow.id = uuid4()
    appt_tomorrow.start_time = datetime(2026, 9, 10, 11, 0, tzinfo=UTC)
    appt_tomorrow.chief_complaint = "Crown Placement"
    appt_tomorrow.status = AppointmentStatus.SCHEDULED

    item = MagicMock()
    item.id = uuid4()
    item.name = "Dental Floss"
    item.current_quantity = 3
    item.minimum_stock = 10
    item.unit = "rolls"

    notif = MagicMock()
    notif.id = uuid4()
    notif.title = "Lab Arrived"
    notif.message = "Crown arrived from lab"
    notif.created_at = datetime.now(UTC)

    # 1. today_appts_q -> res.all()
    res_today = MagicMock()
    res_today.all.return_value = [(appt_today, pat, chair, dentist)]

    # 2. tomorrow_appts_q -> res_tom.all()
    res_tom = MagicMock()
    res_tom.all.return_value = [(appt_tomorrow, pat, dentist)]

    # 3. pending_invoices_res -> res.first()
    res_pending = MagicMock()
    res_pending.first.return_value = (5, 15000.0)

    # 4. low_stock_items -> res.scalars().all()
    res_stock = MagicMock()
    res_stock.scalars.return_value.all.return_value = [item]

    # 5. notifs -> res.scalars().all()
    res_notifs = MagicMock()
    res_notifs.scalars.return_value.all.return_value = [notif]

    mock_db = MagicMock()
    mock_db.execute = AsyncMock(side_effect=[res_today, res_tom, res_pending, res_stock, res_notifs])
    mock_db.scalar = AsyncMock(side_effect=[18, 4500.0])

    summary = await RemoteAccessService.get_mobile_dashboard_summary(clinic_id, user, mock_db)
    assert summary["clinic_id"] == str(clinic_id)
    assert len(summary["today_appointments"]) == 1
    assert summary["today_appointments"][0]["chair"] == "Operatory 2"
    assert summary["today_appointments"][0]["patient"]["name"] == "Sarah Connor"
    assert len(summary["tomorrow_appointments"]) == 1
    assert summary["weekly_total_appointments"] == 18
    assert summary["financial_summary"]["today_revenue"] == 4500.0
    assert summary["financial_summary"]["pending_invoices_count"] == 5
    assert summary["financial_summary"]["pending_balance_due"] == 15000.0
    assert len(summary["stock_alerts"]) == 1
    assert summary["stock_alerts"][0]["name"] == "Dental Floss"
    assert len(summary["recent_notifications"]) == 1
    assert summary["recent_notifications"][0]["message"] == "Crown arrived from lab"
    assert summary["permissions"]["role"] == "DENTIST"
    assert summary["permissions"]["can_delete"] is False


# ==============================================================================
# 7. Security Crypto Tests (app.security.crypto)
# ==============================================================================


def test_crypto_encryption_and_decryption():
    # Empty / None inputs
    assert encrypt_value(None) is None
    assert encrypt_value("") is None
    assert decrypt_value(None) is None
    assert decrypt_value("") is None

    # Normal round-trip
    original = "Confidential-Medical-Record-7788"
    encrypted = encrypt_value(original)
    assert encrypted is not None
    assert encrypted != original
    assert len(encrypted) > 20

    decrypted = decrypt_value(encrypted)
    assert decrypted == original

    # Legacy / invalid token fallback
    legacy_plain = "PLAIN_TEXT_PASSWORD_OR_DATA"
    fallback_result = decrypt_value(legacy_plain)
    assert fallback_result == legacy_plain
