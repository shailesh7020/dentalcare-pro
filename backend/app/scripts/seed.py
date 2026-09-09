"""Idempotently seed development roles. Requires an explicitly configured database."""

import asyncio
import os

from sqlalchemy import select

from app.database.session import AsyncSessionLocal
from app.models import Clinic, Role, User
from app.security.passwords import hash_password

DEMO_CLINIC_SLUG = "demo-dentalcare"
DEMO_PASSWORD_ENV = "DEMO_SEED_PASSWORD"


async def seed() -> None:
    password = os.environ.get(DEMO_PASSWORD_ENV)
    if not password:
        raise RuntimeError(f"{DEMO_PASSWORD_ENV} must be set before seeding users")
    async with AsyncSessionLocal() as db:
        clinic = await db.scalar(select(Clinic).where(Clinic.slug == DEMO_CLINIC_SLUG))
        if clinic is None:
            clinic = Clinic(
                name="DentalCare Demo Clinic", slug=DEMO_CLINIC_SLUG, email="demo@dentalcare.local"
            )
            db.add(clinic)
            await db.flush()
        roles = [
            Role.SUPER_ADMIN,
            Role.CLINIC_ADMIN,
            Role.DENTIST,
            Role.RECEPTIONIST,
            Role.ASSISTANT,
        ]
        for role in roles:
            for domain in ["dentalcare.local", "dentalcare.com"]:
                email = f"{role.value.lower()}@{domain}"
                existing = await db.scalar(select(User).where(User.email == email))
                if existing is None:
                    db.add(
                        User(
                            clinic_id=None if role == Role.SUPER_ADMIN else clinic.id,
                            email=email,
                            password_hash=hash_password(password),
                            first_name=role.value.replace("_", " ").title(),
                            last_name="Demo",
                            role=role,
                        )
                    )
        # Convenience alias for admin@dentalcare.com and admin@dentalcarepro.com
        for alias in ["admin@dentalcare.com", "admin@dentalcare.local", "admin@dentalcarepro.com"]:
            existing = await db.scalar(select(User).where(User.email == alias))
            if existing is None:
                db.add(
                    User(
                        clinic_id=clinic.id,
                        email=alias,
                        password_hash=hash_password(password),
                        first_name="Admin",
                        last_name="Demo",
                        role=Role.CLINIC_ADMIN,
                    )
                )

        from app.models.appointment import Chair, ChairStatus
        demo_chairs = [
            ("Chair 1 - General Operatory", "Room 101"),
            ("Chair 2 - Ortho & Hygiene", "Room 102"),
            ("Chair 3 - Surgical Suite", "Suite A"),
        ]
        for name, room in demo_chairs:
            existing_chair = await db.scalar(
                select(Chair).where(Chair.clinic_id == clinic.id, Chair.name == name)
            )
            if existing_chair is None:
                db.add(
                    Chair(
                        clinic_id=clinic.id,
                        name=name,
                        room_number=room,
                        status=ChairStatus.ACTIVE,
                        is_active=True,
                    )
                )
        await db.commit()


if __name__ == "__main__":
    asyncio.run(seed())
