from fastapi import APIRouter

from app.api import health
from app.api.v1 import (
    ai,
    appointments,
    auth,
    billing,
    calendar,
    chairs,
    clinics,
    communications,
    consents_forms,
    dentists,
    enterprise,
    hr,
    insurance,
    inventory,
    mobile,
    notifications,
    odontogram,
    patients,
    portal,
    prescriptions,
    treatments,
    users,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(clinics.router)
api_router.include_router(patients.router)
api_router.include_router(users.router)
api_router.include_router(chairs.router)
api_router.include_router(dentists.router)
api_router.include_router(calendar.router)
api_router.include_router(appointments.router)
api_router.include_router(treatments.router)
api_router.include_router(odontogram.router)
api_router.include_router(prescriptions.router)
api_router.include_router(billing.router)
api_router.include_router(inventory.router)
api_router.include_router(notifications.router)
api_router.include_router(communications.router)
api_router.include_router(consents_forms.router)
api_router.include_router(portal.router)
api_router.include_router(ai.router)
api_router.include_router(insurance.router)
api_router.include_router(enterprise.router)
api_router.include_router(hr.router)
api_router.include_router(mobile.router)
