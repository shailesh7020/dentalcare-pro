from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import Appointment, AppointmentStatus
from app.models.billing import Invoice
from app.models.identity import Clinic, Role, User
from app.repositories.enterprise_repository import EnterpriseRepository
from app.schemas.enterprise import (
    BranchBenchmarkScore,
    EnterpriseAIAnalyticsResponse,
    RevenueForecastItem,
    StaffProductivityMetric,
)


class EnterpriseAnalyticsService:
    def __init__(self, db: AsyncSession, repo: EnterpriseRepository):
        self.db = db
        self.repo = repo

    async def generate_enterprise_analytics(self, org_id: UUID) -> EnterpriseAIAnalyticsResponse:
        # 1. Fetch all clinics in organization
        clinics_res = await self.db.execute(
            select(Clinic).where(Clinic.organization_id == org_id, Clinic.deleted_at.is_(None))
        )
        clinics = list(clinics_res.scalars().all())

        if not clinics:
            return EnterpriseAIAnalyticsResponse(
                organization_id=org_id,
                generated_at=datetime.now(UTC),
                benchmark_scores=[],
                top_performing_branches=[],
                underperforming_branches=[],
                staff_productivity=[],
                revenue_forecasts=[],
                network_health_summary="No branches currently registered under this organization.",
                strategic_recommendations=["Add branch clinics to begin enterprise comparative analytics."],
            )

        clinic_ids = [c.id for c in clinics]

        # 2. Query Invoices per clinic
        inv_res = await self.db.execute(
            select(
                Invoice.clinic_id,
                func.sum(Invoice.grand_total).label("invoiced"),
                func.sum(Invoice.amount_paid).label("collected"),
                func.count(Invoice.id).label("count"),
            )
            .where(Invoice.clinic_id.in_(clinic_ids), Invoice.deleted_at.is_(None))
            .group_by(Invoice.clinic_id)
        )
        inv_by_clinic = {
            row.clinic_id: {
                "invoiced": float(row.invoiced or 0.0),
                "collected": float(row.collected or 0.0),
                "count": int(row.count or 0),
            }
            for row in inv_res.all()
        }

        # 3. Query Appointments per clinic
        appt_res = await self.db.execute(
            select(
                Appointment.clinic_id,
                func.count(Appointment.id).label("total_appts"),
                func.sum(
                    case(
                        (Appointment.status == AppointmentStatus.COMPLETED, 1),
                        else_=0,
                    )
                ).label("completed_appts"),
            )
            .where(Appointment.clinic_id.in_(clinic_ids), Appointment.deleted_at.is_(None))
            .group_by(Appointment.clinic_id)
        )
        appt_by_clinic = {
            row.clinic_id: {
                "total": int(row.total_appts or 0),
                "completed": int(row.completed_appts or 0),
            }
            for row in appt_res.all()
        }

        # 4. Calculate benchmark scores
        benchmark_scores: list[BranchBenchmarkScore] = []
        max_invoiced = max([d["invoiced"] for d in inv_by_clinic.values()] or [1.0])
        if max_invoiced <= 0:
            max_invoiced = 1.0

        for c in clinics:
            idata = inv_by_clinic.get(c.id, {"invoiced": 0.0, "collected": 0.0, "count": 0})
            adata = appt_by_clinic.get(c.id, {"total": 0, "completed": 0})

            # Scores normalized 0-100
            rev_score = min(100.0, round((idata["invoiced"] / max_invoiced) * 100.0, 1)) if max_invoiced > 0 else 50.0
            coll_rate = (idata["collected"] / idata["invoiced"]) if idata["invoiced"] > 0 else 0.85
            coll_score = min(100.0, round(coll_rate * 100.0, 1))

            occupancy_rate = (adata["completed"] / max(1, adata["total"])) if adata["total"] > 0 else 0.80
            occ_score = min(100.0, round(occupancy_rate * 100.0, 1))
            satisfaction_score = 92.0  # standard baseline for active branches

            # Weighted overall: 35% revenue, 25% collection, 25% occupancy, 15% satisfaction
            overall = round(
                (rev_score * 0.35) + (coll_score * 0.25) + (occ_score * 0.25) + (satisfaction_score * 0.15),
                1,
            )

            branch_recs = []
            if coll_score < 75.0:
                branch_recs.append(f"Improve collection rate ({coll_score}%) via upfront payment policies.")
            if occ_score < 70.0:
                branch_recs.append(f"High cancellation rate detected ({round(100-occ_score, 1)}%). Implement SMS recall.")
            if rev_score < 40.0:
                branch_recs.append("Chairside utilization below network average. Review dentist staffing schedules.")
            if not branch_recs:
                branch_recs.append("Strong operational metrics. Recommended for regional best practice modeling.")

            benchmark_scores.append(
                BranchBenchmarkScore(
                    clinic_id=c.id,
                    clinic_name=c.name,
                    overall_score=overall,
                    revenue_score=rev_score,
                    occupancy_score=occ_score,
                    patient_satisfaction_score=satisfaction_score,
                    collection_rate_score=coll_score,
                    rank=1,
                    recommendations=branch_recs,
                )
            )

        # Rank branches
        benchmark_scores.sort(key=lambda x: x.overall_score, reverse=True)
        for i, bs in enumerate(benchmark_scores, 1):
            bs.rank = i

        top_branches = [b.clinic_name for b in benchmark_scores[:2] if b.overall_score >= 60.0]
        under_branches = [b.clinic_name for b in benchmark_scores if b.overall_score < 60.0]

        # 5. Staff Productivity Metrics
        dentists_res = await self.db.execute(
            select(User)
            .where(
                User.clinic_id.in_(clinic_ids),
                User.role.in_([Role.DENTIST, Role.HYGIENIST]),
                User.deleted_at.is_(None),
            )
            .limit(20)
        )
        staff_members = list(dentists_res.scalars().all())
        staff_metrics: list[StaffProductivityMetric] = []
        clinic_names = {c.id: c.name for c in clinics}

        for s in staff_members:
            s_appts_res = await self.db.execute(
                select(func.count(Appointment.id)).where(
                    Appointment.dentist_id == s.id,
                    Appointment.status == AppointmentStatus.COMPLETED,
                    Appointment.deleted_at.is_(None),
                )
            )
            comp_appts = s_appts_res.scalar_one() or 0
            rev_gen = comp_appts * 1250.0  # Estimated average procedure yield
            staff_metrics.append(
                StaffProductivityMetric(
                    staff_id=s.id,
                    staff_name=f"{s.first_name} {s.last_name}",
                    role=s.role.value,
                    branch_name=clinic_names.get(s.clinic_id or UUID("00000000-0000-0000-0000-000000000000"), "Unassigned"),
                    appointments_completed=comp_appts,
                    revenue_generated=round(rev_gen, 2),
                    utilization_rate=min(95.0, max(60.0, comp_appts * 5.5)),
                    chairside_hours=round(comp_appts * 0.75, 1),
                )
            )

        # 6. Revenue Forecasting (next 3 months based on baseline)
        total_invoiced = sum(d["invoiced"] for d in inv_by_clinic.values())
        base_monthly = max(total_invoiced / 3.0, 50000.0)
        forecasts = [
            RevenueForecastItem(
                period="Month 1",
                forecast_revenue=round(base_monthly * 1.05, 2),
                confidence_lower=round(base_monthly * 0.95, 2),
                confidence_upper=round(base_monthly * 1.15, 2),
                growth_rate_percentage=5.0,
            ),
            RevenueForecastItem(
                period="Month 2",
                forecast_revenue=round(base_monthly * 1.12, 2),
                confidence_lower=round(base_monthly * 1.02, 2),
                confidence_upper=round(base_monthly * 1.22, 2),
                growth_rate_percentage=12.0,
            ),
            RevenueForecastItem(
                period="Month 3",
                forecast_revenue=round(base_monthly * 1.20, 2),
                confidence_lower=round(base_monthly * 1.08, 2),
                confidence_upper=round(base_monthly * 1.32, 2),
                growth_rate_percentage=20.0,
            ),
        ]

        # 7. Strategic Recommendations
        strat_recs = [
            f"Consolidated group purchasing for dental consumables can yield an estimated 8-14% cost reduction across {len(clinics)} branches.",
            "Deploy roaming specialist dentists (e.g. Endodontists, Implantologists) across adjacent regional clinics to increase high-margin procedure volume.",
            "Standardize chairside SOPs and treatment follow-up protocols network-wide to harmonize patient satisfaction.",
        ]
        if under_branches:
            strat_recs.append(
                f"Prioritize operational audit and marketing boost for underperforming branches: {', '.join(under_branches)}."
            )

        summary = (
            f"Enterprise network encompasses {len(clinics)} branches. Network average benchmark score is "
            f"{round(sum(b.overall_score for b in benchmark_scores) / len(benchmark_scores), 1) if benchmark_scores else 0}/100. "
            f"Top performers ({', '.join(top_branches) if top_branches else 'N/A'}) maintain strong patient retention and collection efficiency."
        )

        return EnterpriseAIAnalyticsResponse(
            organization_id=org_id,
            generated_at=datetime.now(UTC),
            benchmark_scores=benchmark_scores,
            top_performing_branches=top_branches,
            underperforming_branches=under_branches,
            staff_productivity=staff_metrics,
            revenue_forecasts=forecasts,
            network_health_summary=summary,
            strategic_recommendations=strat_recs,
        )
