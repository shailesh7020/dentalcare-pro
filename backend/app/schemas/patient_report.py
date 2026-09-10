from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PatientReportSectionEnum(StrEnum):
    PERSONAL_DETAILS = "personal_details"
    MEDICAL_HISTORY = "medical_history"
    DENTAL_HISTORY = "dental_history"
    TREATMENT_HISTORY = "treatment_history"
    ODONTOGRAM = "odontogram"
    CLINICAL_NOTES = "clinical_notes"
    PRESCRIPTIONS = "prescriptions"
    RECEIPTS = "receipts"
    INVOICES = "invoices"
    PAYMENT_HISTORY = "payment_history"
    NEXT_APPOINTMENT = "next_appointment"
    XRAYS_AND_IMAGES = "xrays_and_images"
    UPLOADED_DOCUMENTS = "uploaded_documents"


ALL_REPORT_SECTIONS = [
    PatientReportSectionEnum.PERSONAL_DETAILS,
    PatientReportSectionEnum.MEDICAL_HISTORY,
    PatientReportSectionEnum.DENTAL_HISTORY,
    PatientReportSectionEnum.TREATMENT_HISTORY,
    PatientReportSectionEnum.ODONTOGRAM,
    PatientReportSectionEnum.CLINICAL_NOTES,
    PatientReportSectionEnum.PRESCRIPTIONS,
    PatientReportSectionEnum.RECEIPTS,
    PatientReportSectionEnum.INVOICES,
    PatientReportSectionEnum.PAYMENT_HISTORY,
    PatientReportSectionEnum.NEXT_APPOINTMENT,
    PatientReportSectionEnum.XRAYS_AND_IMAGES,
    PatientReportSectionEnum.UPLOADED_DOCUMENTS,
]


class PatientReportGenerateRequest(BaseModel):
    sections: list[PatientReportSectionEnum] = Field(
        default_factory=lambda: list(ALL_REPORT_SECTIONS),
        description="List of sections to include in the patient report",
    )
    save_to_documents: bool = Field(
        default=True,
        description="Whether to automatically archive the generated PDF in the patient's Documents section",
    )
    include_watermark: bool = Field(
        default=False,
        description="Whether to include a subtle confidential watermark across pages",
    )


class PatientReportShareRequest(BaseModel):
    delivery_method: str = Field(
        default="WHATSAPP",
        description="Delivery channel: WHATSAPP, EMAIL, or FOLDER",
    )
    recipient: str = Field(
        ...,
        description="Recipient mobile number or email address",
    )
    report_id: UUID | None = Field(
        default=None,
        description="Optional ID of the stored patient document",
    )
    notes: str | None = Field(
        default=None,
        description="Optional transmission notes",
    )


class PatientReportResponse(BaseModel):
    report_number: str
    file_name: str
    document_id: UUID | None = None
    download_url: str
    generated_at: datetime
    patient_id: UUID
    patient_name: str
    patient_number: str
    patient_phone: str | None = None
    patient_email: str | None = None
    clinic_name: str
    sections_included: list[str]
    whatsapp_url: str | None = None
    whatsapp_message: str | None = None

    model_config = ConfigDict(from_attributes=True)
