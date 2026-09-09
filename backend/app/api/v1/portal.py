from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.dependencies.auth import current_user
from app.dependencies.rate_limit import rate_limit
from app.models.identity import Role, User
from app.models.patient import Patient
from app.schemas.communication import ConversationRead, MessageCreate, MessageRead
from app.schemas.consent_form import (
    ConsentRecordCreate,
    ConsentRecordRead,
    PatientFormRead,
    PatientFormSubmit,
)
from app.schemas.portal import (
    PortalAppointmentBookRequest,
    PortalAppointmentCancelRequest,
    PortalAppointmentRead,
    PortalDashboardSummary,
    PortalDocumentRead,
    PortalInvoiceRead,
    PortalLoginRequest,
    PortalLoginResponse,
    PortalPatientProfile,
    PortalPrescriptionItemRead,
    PortalPrescriptionRead,
    PortalProfileUpdate,
    PortalRegisterRequest,
    PortalToothRead,
    PortalTreatmentRead,
)
from app.services.communication_service import CommunicationService
from app.services.consent_form_service import ConsentFormService
from app.services.patient_portal_service import PatientPortalService
from app.services.prescription_pdf_service import PrescriptionPDFService

router = APIRouter(prefix="/portal", tags=["Patient Portal"])


def require_patient(user: User = Depends(current_user)) -> User:
    if user.role != Role.PATIENT or not user.patient_id or not user.clinic_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to authenticated dental patient accounts.",
        )
    return user


@router.post("/auth/register", response_model=PortalLoginResponse, status_code=status.HTTP_201_CREATED)
async def portal_register(
    payload: PortalRegisterRequest,
    _: None = Depends(rate_limit("portal_register", "login_rate_limit")),
    db: AsyncSession = Depends(get_db),
) -> PortalLoginResponse:
    portal_svc = PatientPortalService(db)
    tokens = await portal_svc.register_patient_account(payload)
    # Fetch created user and patient details
    from sqlalchemy import select
    user = await db.scalar(select(User).where(User.email == payload.email))
    patient = await db.get(Patient, user.patient_id)
    return PortalLoginResponse(
        token_type="bearer",
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        user_id=user.id,
        patient_id=user.patient_id,
        clinic_id=user.clinic_id,
        patient_name=f"{patient.first_name} {patient.last_name}",
        patient_number=patient.patient_number,
    )


@router.post("/auth/login", response_model=PortalLoginResponse)
async def portal_login(
    payload: PortalLoginRequest,
    _: None = Depends(rate_limit("portal_login", "login_rate_limit")),
    db: AsyncSession = Depends(get_db),
) -> PortalLoginResponse:
    portal_svc = PatientPortalService(db)
    tokens, user = await portal_svc.authenticate_portal_user(payload.email, payload.password)
    patient = await db.get(Patient, user.patient_id)
    return PortalLoginResponse(
        token_type="bearer",
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        user_id=user.id,
        patient_id=user.patient_id,
        clinic_id=user.clinic_id,
        patient_name=f"{patient.first_name} {patient.last_name}",
        patient_number=patient.patient_number,
    )


@router.get("/me", response_model=PortalPatientProfile)
async def get_patient_profile(
    user: User = Depends(require_patient),
    db: AsyncSession = Depends(get_db),
) -> PortalPatientProfile:
    patient = await db.get(Patient, user.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found.")
    return PortalPatientProfile(
        id=patient.id,
        clinic_id=patient.clinic_id,
        patient_number=patient.patient_number,
        first_name=patient.first_name,
        last_name=patient.last_name,
        email=patient.email,
        mobile_number=patient.mobile_number,
        alternate_mobile=patient.alternate_mobile,
        gender=patient.gender.value if hasattr(patient.gender, 'value') else str(patient.gender),
        date_of_birth=patient.date_of_birth,
        blood_group=patient.blood_group.value if hasattr(patient.blood_group, 'value') and patient.blood_group else None,
        address=patient.address,
        city=patient.city,
        state=patient.state,
        pin_code=patient.pin_code,
        emergency_contact_name=patient.emergency_contact_name,
        emergency_contact_number=patient.emergency_contact_number,
        medical_history_notes=patient.medical_history_notes,
        allergies=[a.allergen for a in getattr(patient, 'allergies', [])] if hasattr(patient, 'allergies') else [],
    )


@router.put("/profile", response_model=PortalPatientProfile)
async def update_patient_profile(
    payload: PortalProfileUpdate,
    user: User = Depends(require_patient),
    db: AsyncSession = Depends(get_db),
) -> PortalPatientProfile:
    portal_svc = PatientPortalService(db)
    await portal_svc.update_profile(user.patient_id, user.clinic_id, payload)
    return await get_patient_profile(user=user, db=db)


@router.get("/dashboard", response_model=PortalDashboardSummary)
async def get_portal_dashboard(
    user: User = Depends(require_patient),
    db: AsyncSession = Depends(get_db),
) -> PortalDashboardSummary:
    portal_svc = PatientPortalService(db)
    summary = await portal_svc.get_dashboard_summary(user.patient_id, user.clinic_id)
    
    # Enrich with unread message count and pending forms
    comm_svc = CommunicationService(db)
    convs = await comm_svc.list_conversations(user.clinic_id, user, patient_id=user.patient_id)
    unread_msgs = sum(c.unread_count for c in convs)

    consent_svc = ConsentFormService(db)
    from app.models.consent_form import FormStatus
    pending_forms = await consent_svc.list_patient_forms(user.clinic_id, patient_id=user.patient_id, status=FormStatus.PENDING)

    summary.unread_messages_count = unread_msgs
    summary.pending_forms_count = len(pending_forms)
    return summary


@router.get("/appointments", response_model=list[PortalAppointmentRead])
async def list_portal_appointments(
    user: User = Depends(require_patient),
    db: AsyncSession = Depends(get_db),
) -> list[PortalAppointmentRead]:
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from app.models.appointment import Appointment

    stmt = (
        select(Appointment)
        .options(selectinload(Appointment.dentist))
        .where(
            Appointment.patient_id == user.patient_id,
            Appointment.clinic_id == user.clinic_id,
            Appointment.deleted_at.is_(None),
        )
        .order_by(Appointment.date.desc(), Appointment.start_time.desc())
    )
    res = await db.execute(stmt)
    appts = res.scalars().all()
    return [
        PortalAppointmentRead(
            id=a.id,
            appointment_number=a.appointment_number,
            date=a.date,
            start_time=a.start_time,
            duration_minutes=a.duration_minutes,
            status=a.status.value,
            visit_type=a.visit_type.value,
            reason=a.reason,
            notes=a.notes,
            dentist_name=f"{a.dentist.first_name} {a.dentist.last_name}" if a.dentist else None,
        )
        for a in appts
    ]


@router.post("/appointments/book", response_model=PortalAppointmentRead, status_code=status.HTTP_201_CREATED)
async def book_portal_appointment(
    payload: PortalAppointmentBookRequest,
    user: User = Depends(require_patient),
    db: AsyncSession = Depends(get_db),
) -> PortalAppointmentRead:
    portal_svc = PatientPortalService(db)
    appt = await portal_svc.book_appointment(user.patient_id, user.clinic_id, payload)
    dentist_name = None
    if appt.dentist_id:
        d = await db.get(User, appt.dentist_id)
        if d:
            dentist_name = f"{d.first_name} {d.last_name}"
    return PortalAppointmentRead(
        id=appt.id,
        appointment_number=appt.appointment_number,
        date=appt.date,
        start_time=appt.start_time,
        duration_minutes=appt.duration_minutes,
        status=appt.status.value,
        visit_type=appt.visit_type.value,
        reason=appt.reason,
        notes=appt.notes,
        dentist_name=dentist_name,
    )


@router.post("/appointments/{appointment_id}/cancel", response_model=PortalAppointmentRead)
async def cancel_portal_appointment(
    appointment_id: UUID,
    payload: PortalAppointmentCancelRequest,
    user: User = Depends(require_patient),
    db: AsyncSession = Depends(get_db),
) -> PortalAppointmentRead:
    portal_svc = PatientPortalService(db)
    appt = await portal_svc.cancel_appointment(user.patient_id, user.clinic_id, appointment_id, payload)
    return PortalAppointmentRead(
        id=appt.id,
        appointment_number=appt.appointment_number,
        date=appt.date,
        start_time=appt.start_time,
        duration_minutes=appt.duration_minutes,
        status=appt.status.value,
        visit_type=appt.visit_type.value,
        reason=appt.reason,
        notes=appt.notes,
        dentist_name=None,
    )


@router.get("/prescriptions", response_model=list[PortalPrescriptionRead])
async def list_portal_prescriptions(
    user: User = Depends(require_patient),
    db: AsyncSession = Depends(get_db),
) -> list[PortalPrescriptionRead]:
    portal_svc = PatientPortalService(db)
    rxs = await portal_svc.list_prescriptions(user.patient_id, user.clinic_id)
    return [
        PortalPrescriptionRead(
            id=rx.id,
            prescription_number=rx.prescription_number,
            date=rx.date,
            dentist_name=f"{rx.dentist.first_name} {rx.dentist.last_name}" if rx.dentist else None,
            diagnosis=rx.diagnosis,
            notes=rx.notes,
            items=[
                PortalPrescriptionItemRead(
                    id=it.id,
                    medicine_name=it.medicine_name,
                    dosage=it.dosage,
                    frequency=it.frequency,
                    duration=it.duration,
                    instructions=it.food_instructions or it.notes,
                )
                for it in rx.items
            ],
        )
        for rx in rxs
    ]


@router.get("/prescriptions/{prescription_id}/pdf")
async def download_portal_prescription_pdf(
    prescription_id: UUID,
    user: User = Depends(require_patient),
    db: AsyncSession = Depends(get_db),
) -> Response:
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from app.models.prescription import Prescription

    stmt = (
        select(Prescription)
        .options(
            selectinload(Prescription.patient),
            selectinload(Prescription.dentist),
            selectinload(Prescription.clinic),
            selectinload(Prescription.items),
        )
        .where(
            Prescription.id == prescription_id,
            Prescription.patient_id == user.patient_id,
            Prescription.clinic_id == user.clinic_id,
            Prescription.deleted_at.is_(None),
        )
    )
    rx = await db.scalar(stmt)
    if not rx:
        raise HTTPException(status_code=404, detail="Prescription not found.")
    
    pdf_bytes = PrescriptionPDFService.generate_pdf(rx)
    filename = f"Prescription-{rx.prescription_number}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/invoices", response_model=list[PortalInvoiceRead])
async def list_portal_invoices(
    user: User = Depends(require_patient),
    db: AsyncSession = Depends(get_db),
) -> list[PortalInvoiceRead]:
    portal_svc = PatientPortalService(db)
    invoices = await portal_svc.list_invoices(user.patient_id, user.clinic_id)
    return [
        PortalInvoiceRead(
            id=inv.id,
            invoice_number=inv.invoice_number,
            date=inv.date,
            total_amount=float(inv.subtotal),
            discount_amount=float(inv.discount_amount),
            tax_amount=float(inv.tax_amount),
            final_amount=float(inv.grand_total),
            paid_amount=float(inv.amount_paid),
            balance_due=float(inv.balance_due),
            status=inv.status.value,
        )
        for inv in invoices
    ]


@router.get("/treatments", response_model=list[PortalTreatmentRead])
async def list_portal_treatments(
    user: User = Depends(require_patient),
    db: AsyncSession = Depends(get_db),
) -> list[PortalTreatmentRead]:
    portal_svc = PatientPortalService(db)
    treatments = await portal_svc.list_treatments(user.patient_id, user.clinic_id)
    return [
        PortalTreatmentRead(
            id=t.id,
            treatment_plan_name=t.plan_name,
            status=t.status.value,
            start_date=t.start_date,
            completion_date=t.completed_date,
            dentist_name=f"{t.dentist.first_name} {t.dentist.last_name}" if t.dentist else None,
            notes=t.notes,
        )
        for t in treatments
    ]


@router.get("/odontogram", response_model=list[PortalToothRead])
async def get_portal_odontogram(
    user: User = Depends(require_patient),
    db: AsyncSession = Depends(get_db),
) -> list[PortalToothRead]:
    portal_svc = PatientPortalService(db)
    teeth = await portal_svc.get_odontogram(user.patient_id, user.clinic_id)
    return [
        PortalToothRead(
            tooth_number=t.tooth_number,
            condition=t.condition.value if hasattr(t.condition, 'value') else str(t.condition),
            surface_details=t.surface_details,
            notes=t.notes,
        )
        for t in teeth
    ]


@router.get("/documents", response_model=list[PortalDocumentRead])
async def list_portal_documents(
    user: User = Depends(require_patient),
    db: AsyncSession = Depends(get_db),
) -> list[PortalDocumentRead]:
    portal_svc = PatientPortalService(db)
    docs = await portal_svc.list_documents(user.patient_id, user.clinic_id)
    return [
        PortalDocumentRead(
            id=d.id,
            file_name=d.file_name,
            file_type=d.file_type,
            file_size_bytes=d.file_size_bytes,
            file_url=d.file_url,
            uploaded_at=d.created_at,
        )
        for d in docs
    ]


@router.get("/messages", response_model=list[ConversationRead])
async def list_portal_messages(
    user: User = Depends(require_patient),
    db: AsyncSession = Depends(get_db),
) -> list[ConversationRead]:
    comm_svc = CommunicationService(db)
    return await comm_svc.list_conversations(user.clinic_id, user, patient_id=user.patient_id)


@router.post("/messages", response_model=MessageRead, status_code=status.HTTP_201_CREATED)
async def send_portal_message(
    payload: MessageCreate,
    conversation_id: UUID | None = Query(default=None),
    user: User = Depends(require_patient),
    db: AsyncSession = Depends(get_db),
) -> MessageRead:
    comm_svc = CommunicationService(db)
    if not conversation_id:
        # Create or fetch existing patient thread
        from app.models.communication import ConversationType
        from app.schemas.communication import ConversationCreate
        conv = await comm_svc.create_conversation(
            user.clinic_id,
            user,
            ConversationCreate(
                title=f"Patient Inquiry - {user.first_name} {user.last_name}",
                conversation_type=ConversationType.PATIENT_CLINIC,
                patient_id=user.patient_id,
            ),
        )
        conversation_id = conv.id

    return await comm_svc.send_message(user.clinic_id, user, conversation_id, payload)


@router.get("/forms", response_model=list[PatientFormRead])
async def list_portal_forms(
    user: User = Depends(require_patient),
    db: AsyncSession = Depends(get_db),
) -> list[PatientFormRead]:
    consent_svc = ConsentFormService(db)
    return await consent_svc.list_patient_forms(user.clinic_id, patient_id=user.patient_id)


@router.post("/forms/{form_id}/submit", response_model=PatientFormRead)
async def submit_portal_form(
    form_id: UUID,
    payload: PatientFormSubmit,
    user: User = Depends(require_patient),
    db: AsyncSession = Depends(get_db),
) -> PatientFormRead:
    consent_svc = ConsentFormService(db)
    form = await consent_svc.get_patient_form(user.clinic_id, form_id)
    if form.patient_id != user.patient_id:
        raise HTTPException(status_code=403, detail="Unauthorized form access.")
    return await consent_svc.submit_patient_form(user.clinic_id, form_id, payload)


@router.post("/consents/{form_id}/sign", response_model=ConsentRecordRead, status_code=status.HTTP_201_CREATED)
async def sign_portal_consent(
    form_id: UUID,
    payload: ConsentRecordCreate,
    user: User = Depends(require_patient),
    db: AsyncSession = Depends(get_db),
) -> ConsentRecordRead:
    if payload.patient_id != user.patient_id:
        raise HTTPException(status_code=403, detail="Consent patient mismatch.")
    consent_svc = ConsentFormService(db)
    return await consent_svc.record_consent(user.clinic_id, payload)
