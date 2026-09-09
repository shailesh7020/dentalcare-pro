import pytest
from pydantic import ValidationError

from app.models import Role
from app.schemas.auth import UserCreate


def user_payload(password: str) -> dict[str, str]:
    return {
        "email": "dentist@example.com",
        "password": password,
        "first_name": "Ada",
        "last_name": "Dentist",
        "role": Role.DENTIST,
    }


@pytest.mark.parametrize(
    "password",
    ["alllowercasepassword1!", "ALLUPPERCASEPASSWORD1!", "NoNumberPassword!", "NoSpecialPassword1"],
)
def test_password_policy_rejects_weak_passwords(password: str) -> None:
    with pytest.raises(ValidationError):
        UserCreate(**user_payload(password))


def test_password_policy_accepts_strong_password() -> None:
    assert UserCreate(**user_payload("StrongPassword1!"))
