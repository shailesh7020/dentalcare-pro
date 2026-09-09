from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class ClinicCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    slug: str = Field(pattern=r"^[a-z0-9-]{3,80}$")
    email: EmailStr
    phone: str | None = Field(default=None, max_length=32)
    timezone: str = Field(default="Asia/Kolkata", max_length=64)


class ClinicRead(BaseModel):
    id: UUID
    name: str
    slug: str
    email: EmailStr
    phone: str | None
    timezone: str
    is_active: bool
    model_config = {"from_attributes": True}
