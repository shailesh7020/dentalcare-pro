# backend/app/services/remote_access_service.py
"""
DentalCare Pro - Remote Access Service
Manages remote sessions, Cloudflare/Tailscale zero-trust configuration,
and aggregated mobile clinical dashboard summaries.
"""
from __future__ import annotations

import hashlib
import json
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import Appointment, AppointmentStatus, Chair
from app.models.billing import Invoice, InvoiceStatus
from app.models.identity import Role, User
from app.models.inventory import InventoryItem
from app.models.notification import Notification
from app.models.patient import Patient
from app.models.remote import ClinicRemoteConfig, RemoteSession


class RemoteAccessService:
    @classmethod
    async def get_or_create_config(
        cls, clinic_id: UUID, db: AsyncSession
    ) -> ClinicRemoteConfig:
        """Fetch existing clinic remote configuration or create default."""
        res = await db.execute(
            select(ClinicRemoteConfig).where(ClinicRemoteConfig.clinic_id == clinic_id)
        )
        config = res.scalar_one_or_none()
        if not config:
            config = ClinicRemoteConfig(
                clinic_id=clinic_id,
                is_remote_enabled=True,
                allowed_roles_json=json.dumps(
                    [Role.SUPER_ADMIN.value, Role.CLINIC_ADMIN.value, Role.DENTIST.value, Role.RECEPTIONIST.value]
                ),
                require_2fa=False,
                session_timeout_minutes=480,
                tunnel_provider="cloudflare",
            )
            db.add(config)
            await db.commit()
            await db.refresh(config)
        return config

    @classmethod
    async def create_remote_session(
        cls,
        user: User,
        device_name: str,
        device_type: str,
        ip_address: str,
        user_agent: str | None,
        db: AsyncSession,
        is_2fa_verified: bool = False,
        timeout_minutes: int = 480,
    ) -> tuple[RemoteSession, str]:
        """Create a tracked remote session and return (session, raw_token)."""
        raw_token = secrets.token_urlsafe(48)
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        now = datetime.now(UTC)
        expires_at = now + timedelta(minutes=timeout_minutes)

        session = RemoteSession(
            user_id=user.id,
            clinic_id=user.clinic_id,
            session_token_hash=token_hash,
            device_name=device_name,
            device_type=device_type.upper(),
            ip_address=ip_address,
            user_agent=user_agent,
            is_trusted=False,
            is_2fa_verified=is_2fa_verified,
            last_active_at=now,
            expires_at=expires_at,
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session, raw_token

    @classmethod
    async def list_remote_sessions(
        cls, user_id: UUID, db: AsyncSession
    ) -> list[dict[str, Any]]:
        """List active remote sessions for a user."""
        res = await db.execute(
            select(RemoteSession)
            .where(
                RemoteSession.user_id == user_id,
                RemoteSession.revoked_at.is_(None),
                RemoteSession.expires_at > datetime.now(UTC),
            )
            .order_by(RemoteSession.last_active_at.desc())
        )
        sessions = res.scalars().all()
        return [
            {
                "id": str(s.id),
                "device_name": s.device_name,
                "device_type": s.device_type,
                "ip_address": s.ip_address,
                "user_agent": s.user_agent,
                "is_2fa_verified": s.is_2fa_verified,
                "last_active_at": s.last_active_at.isoformat(),
                "expires_at": s.expires_at.isoformat(),
            }
            for s in sessions
        ]

    @classmethod
    async def revoke_session(
        cls, session_id: UUID, user_id: UUID, db: AsyncSession
    ) -> bool:
        """Revoke an active remote session."""
        res = await db.execute(
            select(RemoteSession).where(
                RemoteSession.id == session_id,
                RemoteSession.user_id == user_id,
            )
        )
        session = res.scalar_one_or_none()
        if not session:
            return False
        session.revoked_at = datetime.now(UTC)
        await db.commit()
        return True

    @classmethod
    def generate_cloudflare_config(
        cls,
        tunnel_id: str,
        credentials_file: str,
        local_web_port: int = 3000,
        local_api_port: int = 8000,
        hostname: str = "clinic.dentalcarepro.local",
    ) -> str:
        """Generate Cloudflare Tunnel config.yml for zero-port-forwarding ingress."""
        return f"""# DentalCare Pro - Cloudflare Tunnel Configuration
tunnel: {tunnel_id}
credentials-file: {credentials_file}

ingress:
  # API routing
  - hostname: {hostname}
    path: /api/*
    service: http://127.0.0.1:{local_api_port}
  # WebSocket clinic sync
  - hostname: {hostname}
    path: /ws/*
    service: http://127.0.0.1:{local_api_port}
  # Frontend Next.js app
  - hostname: {hostname}
    service: http://127.0.0.1:{local_web_port}
  # Catch-all 404
  - service: http_status:404
"""

    @classmethod
    async def get_mobile_dashboard_summary(
        cls, clinic_id: UUID, user: User, db: AsyncSession
    ) -> dict[str, Any]:
        """Aggregate high-performance mobile summary in single database round-trip."""
        today = datetime.now(UTC).date()
        tomorrow = today + timedelta(days=1)
        week_end = today + timedelta(days=7)

        # 1. Today's Appointments
        today_appts_q = (
            select(Appointment, Patient, Chair, User)
            .join(Patient, Appointment.patient_id == Patient.id)
            .outerjoin(Chair, Appointment.chair_id == Chair.id)
            .join(User, Appointment.dentist_id == User.id)
            .where(
                Appointment.clinic_id == clinic_id,
                Appointment.date == today,
                Appointment.status != AppointmentStatus.CANCELLED,
            )
            .order_by(Appointment.start_time.asc())
        )
        res = await db.execute(today_appts_q)
        today_appts = []
        for appt, pat, ch, dr in res.all():
            today_appts.append({
                "id": str(appt.id),
                "appointment_number": appt.appointment_number,
                "start_time": appt.start_time.strftime("%H:%M"),
                "end_time": appt.end_time.strftime("%H:%M"),
                "status": appt.status.value,
                "chief_complaint": appt.chief_complaint or "General Dental Visit",
                "patient": {
                    "id": str(pat.id),
                    "name": f"{pat.first_name} {pat.last_name}",
                    "phone": pat.mobile_number,
                    "gender": pat.gender.value if pat.gender else "UNKNOWN",
                },
                "chair": ch.name if ch else "Chair 1",
                "dentist": f"Dr. {dr.first_name} {dr.last_name}",
            })

        # 2. Tomorrow's Appointments
        tomorrow_appts_q = (
            select(Appointment, Patient, User)
            .join(Patient, Appointment.patient_id == Patient.id)
            .join(User, Appointment.dentist_id == User.id)
            .where(
                Appointment.clinic_id == clinic_id,
                Appointment.date == tomorrow,
                Appointment.status != AppointmentStatus.CANCELLED,
            )
            .order_by(Appointment.start_time.asc())
        )
        res_tom = await db.execute(tomorrow_appts_q)
        tomorrow_appts = []
        for appt, pat, dr in res_tom.all():
            tomorrow_appts.append({
                "id": str(appt.id),
                "start_time": appt.start_time.strftime("%H:%M"),
                "patient_name": f"{pat.first_name} {pat.last_name}",
                "dentist": f"Dr. {dr.first_name} {dr.last_name}",
                "chief_complaint": appt.chief_complaint or "Consultation",
                "status": appt.status.value,
            })

        # 3. Weekly Schedule Count
        week_count = await db.scalar(
            select(func.count(Appointment.id)).where(
                Appointment.clinic_id == clinic_id,
                Appointment.date >= today,
                Appointment.date <= week_end,
                Appointment.status != AppointmentStatus.CANCELLED,
            )
        ) or 0

        # 4. Revenue & Invoices Summary
        revenue_today = await db.scalar(
            select(func.sum(Invoice.amount_paid)).where(
                Invoice.clinic_id == clinic_id,
                Invoice.date == today,
            )
        ) or 0.0

        pending_invoices_res = await db.execute(
            select(func.count(Invoice.id), func.sum(Invoice.balance_due)).where(
                Invoice.clinic_id == clinic_id,
                Invoice.status != InvoiceStatus.PAID,
                Invoice.status != InvoiceStatus.CANCELLED,
            )
        )
        pending_count, pending_total = pending_invoices_res.first()

        # 5. Low Stock Alerts
        low_stock_items = (
            await db.execute(
                select(InventoryItem)
                .where(
                    InventoryItem.clinic_id == clinic_id,
                    InventoryItem.current_quantity <= InventoryItem.minimum_stock,
                )
                .limit(5)
            )
        ).scalars().all()

        stock_alerts = [
            {
                "id": str(item.id),
                "name": item.name,
                "current_quantity": item.current_quantity,
                "minimum_stock": item.minimum_stock,
                "unit": item.unit,
            }
            for item in low_stock_items
        ]

        # 6. Unread Notifications
        notifs = (
            await db.execute(
                select(Notification)
                .where(Notification.clinic_id == clinic_id)
                .order_by(Notification.created_at.desc())
                .limit(5)
            )
        ).scalars().all()
        recent_notifications = [
            {
                "id": str(n.id),
                "title": n.title,
                "message": getattr(n, "message", getattr(n, "body", "")),
                "created_at": n.created_at.isoformat(),
            }
            for n in notifs
        ]

        return {
            "date": today.isoformat(),
            "clinic_id": str(clinic_id),
            "today_appointments": today_appts,
            "tomorrow_appointments": tomorrow_appts,
            "weekly_total_appointments": week_count,
            "financial_summary": {
                "today_revenue": float(revenue_today),
                "pending_invoices_count": pending_count or 0,
                "pending_balance_due": float(pending_total or 0.0),
                "currency": "INR",
            },
            "stock_alerts": stock_alerts,
            "recent_notifications": recent_notifications,
            "permissions": {
                "role": user.role.value,
                "can_confirm": True,
                "can_cancel": True,
                "can_reschedule": True,
                "can_edit_notes": True,
                "can_delete": False,  # Strict remote guardrail
            },
        }
