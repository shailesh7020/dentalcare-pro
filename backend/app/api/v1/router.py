from fastapi import APIRouter

from app.api import health
from app.api.v1 import (
    admin_settings,
    ai,
    appointments,
    auth,
    backups,
    billing,
    calendar,
    chairs,
    clinics,
    communications,
    consents_forms,
    dentists,
    documents,
    enterprise,
    hr,
    insurance,
    inventory,
    mobile,
    network,
    notifications,
    odontogram,
    patients,
    portal,
    prescriptions,
    remote,
    setup_wizard,
    signatures,
    treatments,
    updates,
    users,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(setup_wizard.router)
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
api_router.include_router(signatures.router)
api_router.include_router(backups.router)
api_router.include_router(updates.router)
api_router.include_router(documents.router)
api_router.include_router(network.router)
api_router.include_router(admin_settings.router)
api_router.include_router(remote.router)

