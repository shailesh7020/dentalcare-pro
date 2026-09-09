import asyncio
import json
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.appointment import Appointment, AppointmentStatus
from app.models.billing import Invoice, InvoiceStatus
from app.models.identity import Clinic, RefreshToken, Role, User
from app.models.notification import DeliveryChannel, NotificationPriority, NotificationType
from app.models.odontogram import Tooth
from app.models.patient import Patient, PatientDocument
from app.models.prescription import Prescription
from app.models.treatment import Treatment
from app.schemas.auth import TokenPair
from app.schemas.notification import NotificationCreate
from app.schemas.portal import (
    PortalAppointmentBookRequest,
    PortalAppointmentCancelRequest,
    PortalDashboardSummary,
    PortalProfileUpdate,
    PortalRegisterRequest,
)
from app.security.passwords import hash_password, verify_password
from app.security.tokens import create_access_token, create_refresh_token
from app.services.notifications.notification_service import NotificationService


class PatientPortalService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.notif_service = NotificationService(db)

    async def register_patient_account(self, payload: PortalRegisterRequest) -> TokenPair:
        # Find clinic
        stmt_clinic = select(Clinic).where(Clinic.slug == payload.clinic_slug, Clinic.is_active.is_(True))
        clinic = await self.db.scalar(stmt_clinic)
        if not clinic:
            raise HTTPException(status_code=404, detail="Clinic not found.")

        # Find patient record
        stmt_pat = select(Patient).where(
            Patient.clinic_id == clinic.id,
            Patient.patient_number == payload.patient_number,
            Patient.deleted_at.is_(None),
        )
        patient = await self.db.scalar(stmt_pat)
        if not patient:
            raise HTTPException(
                status_code=404,
                detail="Patient record not found. Please contact the clinic reception to register as a patient.",
            )

        # Verify mobile matches
        if patient.mobile_number != payload.mobile_number:
            raise HTTPException(
                status_code=400,
                detail="Provided mobile number does not match clinic records for this patient number.",
            )

        # Check existing user
        stmt_user = select(User).where(User.email == payload.email)
        existing_user = await self.db.scalar(stmt_user)
        if existing_user:
            raise HTTPException(status_code=400, detail="An account with this email already exists.")

        # Check if patient already has a linked portal user
        stmt_existing_pat_user = select(User).where(User.patient_id == patient.id)
        if await self.db.scalar(stmt_existing_pat_user):
            raise HTTPException(status_code=400, detail="A portal user is already registered for this patient.")

        # Create portal user
        user = User(
            id=uuid4(),
            clinic_id=clinic.id,
            patient_id=patient.id,
            email=payload.email,
            password_hash=hash_password(payload.password),
            first_name=payload.first_name,
            last_name=payload.last_name,
            role=Role.PATIENT,
            is_active=True,
            last_login_at=datetime.now(UTC),
        )
        self.db.add(user)
        await self.db.flush()

        refresh_token, refresh_hash, expires_at = create_refresh_token()
        self.db.add(
            RefreshToken(
                id=uuid4(),
                user_id=user.id,
                token_hash=refresh_hash,
                expires_at=expires_at,
                family_id=uuid4(),
            )
        )
        access_token = create_access_token(str(user.id), str(clinic.id), user.role.value)
        await self.db.commit()

        return TokenPair(access_token=access_token, refresh_token=refresh_token)

    async def authenticate_portal_user(self, email: str, password: str) -> tuple[TokenPair, User]:
        stmt = select(User).where(User.email == email, User.deleted_at.is_(None))
        user = await self.db.scalar(stmt)
        is_valid_pw = False
        if user and user.is_active:
            is_valid_pw = await asyncio.to_thread(verify_password, password, user.password_hash)
        if not user or not user.is_active or not is_valid_pw:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password."
            )

        if user.role != Role.PATIENT or not user.patient_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="This account is not a registered patient portal user."
            )

        user.last_login_at = datetime.now(UTC)
        refresh_token, refresh_hash, expires_at = create_refresh_token()
        self.db.add(
            RefreshToken(
                id=uuid4(),
                user_id=user.id,
                token_hash=refresh_hash,
                expires_at=expires_at,
                family_id=uuid4(),
            )
        )
        access_token = create_access_token(str(user.id), str(user.clinic_id), user.role.value)
        await self.db.commit()

        return TokenPair(access_token=access_token, refresh_token=refresh_token), user

    async def get_dashboard_summary(self, patient_id: UUID, clinic_id: UUID) -> PortalDashboardSummary:
        patient = await self.db.get(Patient, patient_id)
        clinic = await self.db.get(Clinic, clinic_id)
        if not patient or not clinic:
            raise HTTPException(status_code=404, detail="Patient or clinic not found.")

        # Next upcoming appointment
        today = datetime.now(UTC).date()
        stmt_next = (
            select(Appointment)
            .options(selectinload(Appointment.dentist))
            .where(
                Appointment.patient_id == patient_id,
                Appointment.clinic_id == clinic_id,
                Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED]),
                Appointment.date >= today,
                Appointment.deleted_at.is_(None),
            )
            .order_by(Appointment.date.asc(), Appointment.start_time.asc())
            .limit(1)
        )
        next_appt = await self.db.scalar(stmt_next)
        next_dict = None
        if next_appt:
            next_dict = {
                "id": str(next_appt.id),
                "appointment_number": next_appt.appointment_number,
                "date": next_appt.date.strftime("%Y-%m-%d"),
                "time": next_appt.start_time.strftime("%I:%M %p"),
                "dentist_name": f"{next_appt.dentist.first_name} {next_appt.dentist.last_name}" if next_appt.dentist else "Clinic Dentist",
                "visit_type": next_appt.visit_type.value,
                "status": next_appt.status.value,
            }

        # Active prescriptions count
        stmt_rx = select(func.count(Prescription.id)).where(
            Prescription.patient_id == patient_id,
            Prescription.clinic_id == clinic_id,
            Prescription.deleted_at.is_(None),
        )
        active_rx = await self.db.scalar(stmt_rx) or 0

        # Total unpaid balance due
        stmt_inv = select(func.sum(Invoice.balance_due)).where(
            Invoice.patient_id == patient_id,
            Invoice.clinic_id == clinic_id,
            Invoice.status.in_([InvoiceStatus.UNPAID, InvoiceStatus.PARTIALLY_PAID]),
            Invoice.deleted_at.is_(None),
        )
        balance_due = await self.db.scalar(stmt_inv) or 0.0

        return PortalDashboardSummary(
            patient_id=patient.id,
            patient_name=f"{patient.first_name} {patient.last_name}",
            patient_number=patient.patient_number,
            clinic_name=clinic.name,
            next_appointment=next_dict,
            active_prescriptions_count=active_rx,
            total_balance_due=float(balance_due),
            unread_messages_count=0,
            pending_forms_count=0,
        )

    async def update_profile(
        self, patient_id: UUID, clinic_id: UUID, payload: PortalProfileUpdate
    ) -> Patient:
        patient = await self.db.get(Patient, patient_id)
        if not patient or patient.clinic_id != clinic_id:
            raise HTTPException(status_code=404, detail="Patient record not found.")

        for field, value in payload.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(patient, field, value)

        await self.db.commit()
        return patient

    async def book_appointment(
        self, patient_id: UUID, clinic_id: UUID, payload: PortalAppointmentBookRequest
    ) -> Appointment:
        patient = await self.db.get(Patient, patient_id)
        clinic = await self.db.get(Clinic, clinic_id)
        if not patient or not clinic:
            raise HTTPException(status_code=404, detail="Patient or clinic not found.")

        today_str = datetime.now(UTC).strftime("%Y%m%d")
        seq = (await self.db.scalar(select(func.count(Appointment.id)).where(Appointment.clinic_id == clinic_id)) or 0) + 1
        appt_number = f"APT-{today_str}-{seq:04d}"

        # Resolve dentist if not supplied
        dentist_id = payload.dentist_id
        if not dentist_id:
            first_dentist = await self.db.scalar(
                select(User.id).where(User.clinic_id == clinic_id, User.role == Role.DENTIST, User.is_active.is_(True)).limit(1)
            )
            dentist_id = first_dentist or patient.created_by

        chair_id = await self.db.scalar(
            select(Appointment.chair_id).where(Appointment.clinic_id == clinic_id).limit(1)
        ) or uuid4()

        end_dt = datetime.combine(payload.appointment_date, payload.start_time) + timedelta(minutes=30)

        appt = Appointment(
            id=uuid4(),
            clinic_id=clinic_id,
            patient_id=patient_id,
            dentist_id=dentist_id or uuid4(),
            chair_id=chair_id,
            appointment_number=appt_number,
            date=payload.appointment_date,
            start_time=payload.start_time,
            end_time=end_dt.time(),
            duration=30,
            status=AppointmentStatus.SCHEDULED,
            visit_type=payload.visit_type,
            chief_complaint=payload.reason,
            notes="Booked via Patient Portal",
        )
        self.db.add(appt)

        # Send confirmation notification
        notif_payload = NotificationCreate(
            notification_type=NotificationType.APPOINTMENT_BOOKED,
            priority=NotificationPriority.NORMAL,
            delivery_channel=DeliveryChannel.IN_APP,
            patient_id=patient_id,
            title=f"Appointment Booked: {clinic.name}",
            message=f"Your visit on {payload.appointment_date} at {payload.start_time.strftime('%I:%M %p')} has been booked.",
            data_json=json.dumps({"appointment_id": str(appt.id)}),
        )
        await self.notif_service.send_notification(clinic_id, notif_payload)

        await self.db.commit()
        return appt

    async def cancel_appointment(
        self, patient_id: UUID, clinic_id: UUID, appointment_id: UUID, payload: PortalAppointmentCancelRequest
    ) -> Appointment:
        stmt = select(Appointment).where(
            Appointment.id == appointment_id,
            Appointment.patient_id == patient_id,
            Appointment.clinic_id == clinic_id,
            Appointment.deleted_at.is_(None),
        )
        appt = await self.db.scalar(stmt)
        if not appt:
            raise HTTPException(status_code=404, detail="Appointment not found.")

        appt.status = AppointmentStatus.CANCELLED
        appt.cancellation_reason = f"Patient Portal: {payload.cancellation_reason}"

        # Send cancellation notification
        notif_payload = NotificationCreate(
            notification_type=NotificationType.APPOINTMENT_CANCELLED,
            priority=NotificationPriority.NORMAL,
            delivery_channel=DeliveryChannel.IN_APP,
            patient_id=patient_id,
            title="Appointment Cancelled",
            message=f"Your appointment on {appt.date} has been cancelled.",
            data_json=json.dumps({"appointment_id": str(appt.id)}),
        )
        await self.notif_service.send_notification(clinic_id, notif_payload)

        await self.db.commit()
        return appt

    async def list_prescriptions(self, patient_id: UUID, clinic_id: UUID) -> list[Prescription]:
        stmt = (
            select(Prescription)
            .options(selectinload(Prescription.items), selectinload(Prescription.dentist))
            .where(
                Prescription.patient_id == patient_id,
                Prescription.clinic_id == clinic_id,
                Prescription.deleted_at.is_(None),
            )
            .order_by(Prescription.date.desc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def list_invoices(self, patient_id: UUID, clinic_id: UUID) -> list[Invoice]:
        stmt = (
            select(Invoice)
            .options(selectinload(Invoice.items), selectinload(Invoice.payments))
            .where(
                Invoice.patient_id == patient_id,
                Invoice.clinic_id == clinic_id,
                Invoice.deleted_at.is_(None),
            )
            .order_by(Invoice.created_at.desc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def list_treatments(self, patient_id: UUID, clinic_id: UUID) -> list[Treatment]:
        stmt = (
            select(Treatment)
            .options(selectinload(Treatment.procedures), selectinload(Treatment.dentist))
            .where(
                Treatment.patient_id == patient_id,
                Treatment.clinic_id == clinic_id,
                Treatment.deleted_at.is_(None),
            )
            .order_by(Treatment.created_at.desc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_odontogram(self, patient_id: UUID, clinic_id: UUID) -> list[Tooth]:
        stmt = (
            select(Tooth)
            .where(
                Tooth.patient_id == patient_id,
                Tooth.clinic_id == clinic_id,
                Tooth.deleted_at.is_(None),
            )
            .order_by(Tooth.tooth_number.asc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def list_documents(self, patient_id: UUID, clinic_id: UUID) -> list[PatientDocument]:
        stmt = (
            select(PatientDocument)
            .where(
                PatientDocument.patient_id == patient_id,
                PatientDocument.clinic_id == clinic_id,
                PatientDocument.deleted_at.is_(None),
            )
            .order_by(PatientDocument.created_at.desc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())
