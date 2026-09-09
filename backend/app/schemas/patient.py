from datetime import UTC, date, datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.models.patient import BloodGroup, Gender

MOBILE_PATTERN = r"^[6-9]\d{9}$"


class MedicalHistoryInput(BaseModel):
    model_config = {"from_attributes": True}
    diabetes: bool = False
    hypertension: bool = False
    cardiac_disease: bool = False
    thyroid: bool = False
    asthma: bool = False
    epilepsy: bool = False
    pregnancy: bool = False
    allergies: str | None = None
    current_medications: str | None = None
    smoking: bool = False
    tobacco: bool = False
    alcohol: bool = False
    previous_surgeries: str | None = None
    infectious_diseases: str | None = None
    physician_name: str | None = None
    physician_contact: str | None = Field(default=None, pattern=MOBILE_PATTERN)
    additional_notes: str | None = None


class DentalHistoryInput(BaseModel):
    model_config = {"from_attributes": True}
    chief_complaint: str | None = None
    previous_dental_treatments: str | None = None
    brushing_frequency: str | None = None
    flossing_habit: bool = False
    tobacco_habit: bool = False
    grinding: bool = False
    jaw_pain: bool = False
    tmj_disorder: bool = False
    sensitivity: bool = False
    bleeding_gums: bool = False
    last_dental_visit: date | None = None
    dental_notes: str | None = None


class PatientInput(BaseModel):
    first_name: str = Field(min_length=1, max_length=80)
    middle_name: str | None = Field(default=None, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    gender: Gender
    date_of_birth: date
    blood_group: BloodGroup | None = None
    marital_status: str | None = Field(default=None, max_length=40)
    occupation: str | None = Field(default=None, max_length=100)
    aadhaar_number: str | None = Field(default=None, pattern=r"^\d{12}$")
    email: EmailStr | None = None
    mobile_number: str = Field(pattern=MOBILE_PATTERN)
    alternate_mobile: str | None = Field(default=None, pattern=MOBILE_PATTERN)
    address: str | None = None
    city: str | None = Field(default=None, max_length=80)
    state: str | None = Field(default=None, max_length=80)
    country: str = Field(default="India", min_length=2, max_length=80)
    pin_code: str | None = Field(default=None, pattern=r"^\d{6}$")
    emergency_contact_name: str | None = Field(default=None, max_length=160)
    emergency_contact_number: str | None = Field(default=None, pattern=MOBILE_PATTERN)
    emergency_contact_relation: str | None = Field(default=None, max_length=60)
    insurance_provider: str | None = Field(default=None, max_length=160)
    insurance_policy_number: str | None = Field(default=None, max_length=100)
    preferred_language: str = Field(default="English", max_length=40)
    notes: str | None = None
    medical_history: MedicalHistoryInput | None = None
    dental_history: DentalHistoryInput | None = None

    @field_validator("date_of_birth")
    @classmethod
    def date_must_not_be_future(cls, value: date) -> date:
        if value > datetime.now(UTC).date():
            raise ValueError("Date of birth cannot be in the future")
        return value

    @model_validator(mode="after")
    def contacts_must_differ(self) -> "PatientInput":
        if self.alternate_mobile and self.alternate_mobile == self.mobile_number:
            raise ValueError("Alternate mobile must be different from mobile number")
        return self


class PatientUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=80)
    middle_name: str | None = Field(default=None, max_length=80)
    last_name: str | None = Field(default=None, min_length=1, max_length=80)
    gender: Gender | None = None
    date_of_birth: date | None = None
    blood_group: BloodGroup | None = None
    marital_status: str | None = Field(default=None, max_length=40)
    occupation: str | None = Field(default=None, max_length=100)
    aadhaar_number: str | None = Field(default=None, pattern=r"^\d{12}$")
    email: EmailStr | None = None
    mobile_number: str | None = Field(default=None, pattern=MOBILE_PATTERN)
    alternate_mobile: str | None = Field(default=None, pattern=MOBILE_PATTERN)
    address: str | None = None
    city: str | None = Field(default=None, max_length=80)
    state: str | None = Field(default=None, max_length=80)
    country: str | None = Field(default=None, min_length=2, max_length=80)
    pin_code: str | None = Field(default=None, pattern=r"^\d{6}$")
    emergency_contact_name: str | None = Field(default=None, max_length=160)
    emergency_contact_number: str | None = Field(default=None, pattern=MOBILE_PATTERN)
    emergency_contact_relation: str | None = Field(default=None, max_length=60)
    insurance_provider: str | None = Field(default=None, max_length=160)
    insurance_policy_number: str | None = Field(default=None, max_length=100)
    preferred_language: str | None = Field(default=None, max_length=40)
    notes: str | None = None
    medical_history: MedicalHistoryInput | None = None
    dental_history: DentalHistoryInput | None = None

    @field_validator("date_of_birth")
    @classmethod
    def date_must_not_be_future(cls, value: date | None) -> date | None:
        if value and value > datetime.now(UTC).date():
            raise ValueError("Date of birth cannot be in the future")
        return value


class DuplicateWarning(BaseModel):
    field: str
    patient_id: UUID
    patient_number: str


class PatientRead(BaseModel):
    id: UUID
    clinic_id: UUID
    patient_number: str
    first_name: str
    middle_name: str | None
    last_name: str
    gender: Gender
    date_of_birth: date
    age: int
    mobile_number: str
    email: EmailStr | None
    city: str | None
    blood_group: BloodGroup | None
    photo_url: str | None
    status: str = "ACTIVE"
    created_at: datetime | None = None
    deleted_at: datetime | None = None
    model_config = {"from_attributes": True}


class PatientDetail(PatientRead):
    alternate_mobile: str | None
    address: str | None
    state: str | None
    country: str
    pin_code: str | None
    emergency_contact_name: str | None
    emergency_contact_number: str | None
    emergency_contact_relation: str | None
    insurance_provider: str | None
    insurance_policy_number: str | None
    preferred_language: str
    notes: str | None
    aadhaar_number: str | None
    marital_status: str | None
    occupation: str | None
    medical_history: MedicalHistoryInput | None = None
    dental_history: DentalHistoryInput | None = None


class PatientList(BaseModel):
    items: list[PatientRead]
    total: int
    skip: int
    limit: int


class TimelineRead(BaseModel):
    id: UUID
    patient_id: UUID | None = None
    clinic_id: UUID | None = None
    event_type: str
    title: str
    description: str | None
    created_at: datetime
    model_config = {"from_attributes": True}


class DocumentRead(BaseModel):
    id: UUID
    patient_id: UUID
    clinic_id: UUID
    file_name: str
    content_type: str
    document_type: str
    storage_key: str
    url: str
    created_at: datetime
    model_config = {"from_attributes": True}


class DocumentUploadResponse(BaseModel):
    id: str
    file_name: str
    content_type: str
    document_type: str
    url: str


class PatientMutationResponse(BaseModel):
    patient: PatientRead
    duplicate_warnings: list[DuplicateWarning]

