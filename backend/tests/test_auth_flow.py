from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.api.v1.auth import issue_tokens, login, refresh
from app.models import RefreshToken, Role, User
from app.schemas.auth import LoginRequest, RefreshRequest
from app.security.passwords import hash_password
from app.security.tokens import create_refresh_token


class FakeSession:
    def __init__(self, scalar_values: list[object] | None = None, user: User | None = None) -> None:
        self.scalar_values = scalar_values or []
        self.user = user
        self.added: list[object] = []
        self.commits = 0

    def add(self, value: object) -> None:
        self.added.append(value)

    async def scalar(self, _query: object) -> object | None:
        return self.scalar_values.pop(0) if self.scalar_values else None

    async def get(self, _model: object, _id: object) -> User | None:
        return self.user

    async def flush(self) -> None:
        return None

    async def commit(self) -> None:
        self.commits += 1

    async def execute(self, _query: object) -> None:
        return None


def user() -> User:
    return User(
        id=uuid4(),
        clinic_id=uuid4(),
        email="dentist@example.com",
        password_hash=hash_password("StrongPassword1!"),
        first_name="Ada",
        last_name="Dentist",
        role=Role.DENTIST,
        is_active=True,
    )


@pytest.mark.asyncio
async def test_issue_tokens_hashes_refresh_token_and_creates_family() -> None:
    db = FakeSession()
    tokens = await issue_tokens(user(), db)
    record = next(item for item in db.added if isinstance(item, RefreshToken))
    assert record.token_hash != tokens.refresh_token
    assert record.family_id == record.id


@pytest.mark.asyncio
async def test_login_creates_audited_session() -> None:
    staff = user()
    db = FakeSession([staff])
    tokens = await login(LoginRequest(email=staff.email, password="StrongPassword1!"), None, db)
    assert tokens.access_token
    assert db.commits == 1
    assert any(isinstance(item, RefreshToken) for item in db.added)


@pytest.mark.asyncio
async def test_refresh_rotates_token_in_same_family() -> None:
    staff = user()
    raw, digest, _ = create_refresh_token()
    original = RefreshToken(
        id=uuid4(),
        user_id=staff.id,
        token_hash=digest,
        expires_at=datetime.now(UTC) + timedelta(days=1),
        family_id=uuid4(),
    )
    db = FakeSession([original, None], staff)
    result = await refresh(RefreshRequest(refresh_token=raw), None, db)
    assert original.revoked_at is not None
    assert result.refresh_token != raw
    replacement = next(item for item in db.added if isinstance(item, RefreshToken))
    assert replacement.family_id == original.family_id


@pytest.mark.asyncio
async def test_refresh_replay_revokes_the_family() -> None:
    staff = user()
    raw, digest, _ = create_refresh_token()
    replay = RefreshToken(
        id=uuid4(),
        user_id=staff.id,
        token_hash=digest,
        expires_at=datetime.now(UTC) + timedelta(days=1),
        family_id=uuid4(),
        revoked_at=datetime.now(UTC),
    )
    db = FakeSession([replay], staff)
    with pytest.raises(Exception, match="replay"):
        await refresh(RefreshRequest(refresh_token=raw), None, db)
    assert db.commits == 1
