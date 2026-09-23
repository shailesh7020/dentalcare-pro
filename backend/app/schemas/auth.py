from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.identity import Role


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    role: Role

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        requirements = {
            "an uppercase letter": any(character.isupper() for character in value),
            "a lowercase letter": any(character.islower() for character in value),
            "a number": any(character.isdigit() for character in value),
            "a special character": any(not character.isalnum() for character in value),
        }
        missing = [label for label, present in requirements.items() if not present]
        if missing:
            raise ValueError(f"Password must include {', '.join(missing)}")
        return value


class UserRead(BaseModel):
    id: UUID
    clinic_id: UUID | None
    email: str
    first_name: str
    last_name: str
    role: Role
    is_active: bool
    model_config = {"from_attributes": True}
