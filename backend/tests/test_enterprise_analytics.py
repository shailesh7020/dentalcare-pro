from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.models.appointment import Appointment, AppointmentStatus
from app.models.billing import Invoice
from app.models.identity import Clinic, Role, User
from app.repositories.enterprise_repository import EnterpriseRepository
from app.services.ai.enterprise_analytics_service import EnterpriseAnalyticsService


class RowMock:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class FakeScalarResult:
    def __init__(self, items):
        self._items = list(items) if items is not None else []

    def all(self):
        return self._items

    def scalars(self):
        return self

    def scalar_one(self):
        return self._items[0] if self._items else 0


class FakeDb:
    def __init__(self, clinics=None, invoices=None, appointments=None, users=None):
        self.clinics = list(clinics) if clinics else []
        self.invoices = list(invoices) if invoices else []
        self.appointments = list(appointments) if appointments else []
        self.users = list(users) if users else []

    async def execute(self, query):
        stmt = str(query)
        if "FROM clinics" in stmt:
            return FakeScalarResult(self.clinics)
        if "FROM invoices" in stmt:
            rows = []
            for c in self.clinics:
                cinvs = [inv for inv in self.invoices if inv.clinic_id == c.id]
                tot_inv = sum(i.grand_total for i in cinvs)
                tot_col = sum(i.amount_paid for i in cinvs)
                rows.append(
                    RowMock(
                        clinic_id=c.id,
                        invoiced=tot_inv,
                        collected=tot_col,
                        count=len(cinvs),
                    )
                )
            return FakeScalarResult(rows)
        if "FROM appointments" in stmt:
            if "dentist_id" in stmt:
                return FakeScalarResult([5])
            rows = []
            for c in self.clinics:
                appts = [a for a in self.appointments if a.clinic_id == c.id]
                comp = sum(1 for a in appts if a.status == AppointmentStatus.COMPLETED)
                rows.append(
                    RowMock(
                        clinic_id=c.id,
                        total_appts=len(appts),
                        completed_appts=comp,
                    )
                )
            return FakeScalarResult(rows)
        if "FROM users" in stmt:
            return FakeScalarResult(self.users)
        return FakeScalarResult([])


@pytest.mark.asyncio
async def test_empty_enterprise_analytics():
    db = FakeDb(clinics=[])
    repo = EnterpriseRepository(db)
    service = EnterpriseAnalyticsService(db, repo)

    org_id = uuid4()
    resp = await service.generate_enterprise_analytics(org_id)
    assert resp.organization_id == org_id
    assert len(resp.benchmark_scores) == 0
    assert "No branches" in resp.network_health_summary


@pytest.mark.asyncio
async def test_multi_branch_analytics():
    org_id = uuid4()
    c1 = Clinic(id=uuid4(), organization_id=org_id, name="Central Branch", email="c1@clinic.com")
    c2 = Clinic(id=uuid4(), organization_id=org_id, name="Suburban Branch", email="c2@clinic.com")

    dentist = User(
        id=uuid4(),
        clinic_id=c1.id,
        first_name="Priya",
        last_name="Sharma",
        email="priya@clinic.com",
        role=Role.DENTIST,
        password_hash="fake",
    )

    from datetime import date
    inv1 = Invoice(
        id=uuid4(), clinic_id=c1.id, patient_id=uuid4(), dentist_id=dentist.id,
        created_by=dentist.id, updated_by=dentist.id,
        date=date(2026, 9, 8), invoice_number="INV-01",
        grand_total=150000.0, amount_paid=140000.0,
    )
    inv2 = Invoice(
        id=uuid4(), clinic_id=c2.id, patient_id=uuid4(), dentist_id=dentist.id,
        created_by=dentist.id, updated_by=dentist.id,
        date=date(2026, 9, 8), invoice_number="INV-02",
        grand_total=50000.0, amount_paid=30000.0,
    )

    appts = [
        Appointment(
            id=uuid4(), clinic_id=c1.id, patient_id=uuid4(), dentist_id=dentist.id,
            status=AppointmentStatus.COMPLETED, start_time=datetime.now(UTC), end_time=datetime.now(UTC),
        ),
        Appointment(
            id=uuid4(), clinic_id=c2.id, patient_id=uuid4(), dentist_id=uuid4(),
            status=AppointmentStatus.CONFIRMED, start_time=datetime.now(UTC), end_time=datetime.now(UTC),
        ),
    ]

    db = FakeDb(
        clinics=[c1, c2],
        invoices=[inv1, inv2],
        appointments=appts,
        users=[dentist],
    )
    repo = EnterpriseRepository(db)
    service = EnterpriseAnalyticsService(db, repo)

    analytics = await service.generate_enterprise_analytics(org_id)
    assert analytics.organization_id == org_id
    assert len(analytics.benchmark_scores) == 2

    # Scores should be sorted by overall_score descending
    top_score = analytics.benchmark_scores[0]
    second_score = analytics.benchmark_scores[1]
    assert top_score.overall_score >= second_score.overall_score
    assert top_score.rank == 1
    assert second_score.rank == 2

    # Verify forecasts
    assert len(analytics.revenue_forecasts) == 3
    assert analytics.revenue_forecasts[0].period == "Month 1"
    assert analytics.revenue_forecasts[0].forecast_revenue > 0.0

    # Verify strategic recommendations
    assert len(analytics.strategic_recommendations) >= 3
    assert len(analytics.staff_productivity) == 1
    assert analytics.staff_productivity[0].staff_name == "Priya Sharma"
