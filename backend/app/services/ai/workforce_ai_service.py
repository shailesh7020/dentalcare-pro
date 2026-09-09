from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import Appointment, AppointmentStatus, Chair
from app.models.hr import (
    AttendanceRecord,
    Employee,
    EmployeeStatus,
    EmployeeTrainingRecord,
    LeaveRequest,
    LeaveStatus,
    ScheduleStatus,
    StaffSchedule,
)
from app.schemas.hr import (
    BurnoutRiskAssessmentResponse,
    BurnoutRiskItem,
    LeaveConflictDetectionResponse,
    LeaveConflictItem,
    ScheduleConflictAuditResponse,
    ScheduleConflictItem,
    StaffingOptimizationResponse,
    StaffingRecommendationItem,
    TrainingComplianceItem,
    TrainingComplianceRecommendationResponse,
)


class WorkforceAIService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_staffing_recommendations(
        self, clinic_id: UUID, target_date: date
    ) -> StaffingOptimizationResponse:
        # Fetch active chairs count
        chair_stmt = select(Chair).where(Chair.clinic_id == clinic_id, Chair.is_active.is_(True))
        chairs = list((await self.db.execute(chair_stmt)).scalars().all())
        total_chairs = len(chairs) or 3

        # Fetch appointments for target date
        app_stmt = select(Appointment).where(
            Appointment.clinic_id == clinic_id,
            Appointment.date == target_date,
            Appointment.status.not_in([AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW]),
            Appointment.deleted_at.is_(None),
        )
        appointments = list((await self.db.execute(app_stmt)).scalars().all())

        # Fetch scheduled clinicians
        sched_stmt = select(StaffSchedule).where(
            StaffSchedule.clinic_id == clinic_id,
            StaffSchedule.schedule_date == target_date,
            StaffSchedule.status != ScheduleStatus.CANCELLED,
            StaffSchedule.deleted_at.is_(None),
        )
        schedules = list((await self.db.execute(sched_stmt)).scalars().all())
        scheduled_clinicians_count = len(schedules)

        # Slot breakdowns: Morning (09:00 - 13:00) & Afternoon/Evening (14:00 - 19:00)
        morning_apps = [a for a in appointments if a.start_time and a.start_time.hour < 13]
        afternoon_apps = [a for a in appointments if a.start_time and a.start_time.hour >= 13]

        recommendations = []

        # Morning slot
        recommended_morn = max(1, min(total_chairs, (len(morning_apps) + 2) // 3))
        morn_status = (
            "UNDERSTAFFED"
            if scheduled_clinicians_count < recommended_morn
            else ("OVERSTAFFED" if scheduled_clinicians_count > recommended_morn + 2 else "OPTIMAL")
        )
        recommendations.append(
            StaffingRecommendationItem(
                clinic_id=clinic_id,
                date=target_date,
                time_slot="Morning (09:00 - 13:00)",
                scheduled_chairs=total_chairs,
                appointments_booked=len(morning_apps),
                scheduled_clinicians=scheduled_clinicians_count,
                recommended_clinicians=recommended_morn,
                status=morn_status,
                recommendation=(
                    f"Roster at least {recommended_morn} dentists/assistants to handle {len(morning_apps)} morning bookings across {total_chairs} chairs."
                    if morn_status == "UNDERSTAFFED"
                    else "Morning staffing capacity is well-balanced."
                ),
            )
        )

        # Afternoon slot
        recommended_aft = max(1, min(total_chairs, (len(afternoon_apps) + 2) // 3))
        aft_status = (
            "UNDERSTAFFED"
            if scheduled_clinicians_count < recommended_aft
            else ("OVERSTAFFED" if scheduled_clinicians_count > recommended_aft + 2 else "OPTIMAL")
        )
        recommendations.append(
            StaffingRecommendationItem(
                clinic_id=clinic_id,
                date=target_date,
                time_slot="Afternoon / Evening (14:00 - 19:00)",
                scheduled_chairs=total_chairs,
                appointments_booked=len(afternoon_apps),
                scheduled_clinicians=scheduled_clinicians_count,
                recommended_clinicians=recommended_aft,
                status=aft_status,
                recommendation=(
                    f"Recommend {recommended_aft} chairside operators for {len(afternoon_apps)} scheduled procedures."
                    if aft_status == "UNDERSTAFFED"
                    else "Evening roster meets clinical patient throughput demands."
                ),
            )
        )

        understaffed_count = sum(1 for r in recommendations if r.status == "UNDERSTAFFED")

        return StaffingOptimizationResponse(
            analysis_period=target_date.isoformat(),
            total_slots_analyzed=len(recommendations),
            understaffed_slots=understaffed_count,
            recommendations=recommendations,
        )

    async def audit_schedule_conflicts(
        self, clinic_id: UUID, start_date: date, end_date: date
    ) -> ScheduleConflictAuditResponse:
        stmt = (
            select(StaffSchedule, Employee)
            .join(Employee, StaffSchedule.employee_id == Employee.id)
            .where(
                StaffSchedule.clinic_id == clinic_id,
                StaffSchedule.schedule_date >= start_date,
                StaffSchedule.schedule_date <= end_date,
                StaffSchedule.status != ScheduleStatus.CANCELLED,
                StaffSchedule.deleted_at.is_(None),
            )
            .order_by(StaffSchedule.employee_id, StaffSchedule.schedule_date)
        )
        results = (await self.db.execute(stmt)).all()

        conflicts: list[ScheduleConflictItem] = []
        by_employee: dict[UUID, list[tuple[StaffSchedule, Employee]]] = {}
        for sched, emp in results:
            by_employee.setdefault(emp.id, []).append((sched, emp))

        for emp_id, records in by_employee.items():
            emp_name = f"{records[0][1].first_name} {records[0][1].last_name}"

            # Check consecutive working days
            unique_dates = sorted({r[0].schedule_date for r in records})
            consecutive = 1
            for i in range(1, len(unique_dates)):
                if (unique_dates[i] - unique_dates[i - 1]).days == 1:
                    consecutive += 1
                    if consecutive >= 6:
                        conflicts.append(
                            ScheduleConflictItem(
                                schedule_id=records[i][0].id,
                                employee_id=emp_id,
                                employee_name=emp_name,
                                conflict_type="CONSECUTIVE_WORK_DAYS",
                                severity="HIGH",
                                description=f"Staff member is rostered for {consecutive} consecutive days without a rest day.",
                            )
                        )
                else:
                    consecutive = 1

            # Check split-shift rest interval
            for sched, _ in records:
                if sched.is_split_shift and sched.split_start_time and sched.split_end_time:
                    gap_hours = (
                        datetime.combine(sched.schedule_date, sched.split_start_time)
                        - datetime.combine(sched.schedule_date, sched.end_time)
                    ).total_seconds() / 3600
                    if gap_hours < 1.5:
                        conflicts.append(
                            ScheduleConflictItem(
                                schedule_id=sched.id,
                                employee_id=emp_id,
                                employee_name=emp_name,
                                conflict_type="SPLIT_REST_TOO_SHORT",
                                severity="MEDIUM",
                                description=f"Split shift break is only {round(gap_hours, 1)} hours; recommended minimum rest interval is 2 hours.",
                            )
                        )

        return ScheduleConflictAuditResponse(
            total_conflicts=len(conflicts),
            conflicts=conflicts,
        )

    async def detect_leave_conflicts(
        self, clinic_id: UUID, start_date: date, end_date: date
    ) -> LeaveConflictDetectionResponse:
        stmt = (
            select(LeaveRequest, Employee)
            .join(Employee, LeaveRequest.employee_id == Employee.id)
            .where(
                LeaveRequest.clinic_id == clinic_id,
                LeaveRequest.start_date <= end_date,
                LeaveRequest.end_date >= start_date,
                LeaveRequest.status.in_([LeaveStatus.SUBMITTED, LeaveStatus.MANAGER_APPROVED, LeaveStatus.HR_APPROVED]),
                LeaveRequest.deleted_at.is_(None),
            )
        )
        leaves = (await self.db.execute(stmt)).all()

        # Group by specialization / designation
        by_spec: dict[str, list[str]] = {}
        for req, emp in leaves:
            spec = emp.specialization or emp.designation or "General Dentistry"
            by_spec.setdefault(spec, []).append(f"{emp.first_name} {emp.last_name}")

        conflict_items: list[LeaveConflictItem] = []
        for spec, emp_names in by_spec.items():
            if len(emp_names) >= 2:
                conflict_items.append(
                    LeaveConflictItem(
                        clinic_id=clinic_id,
                        department_name=spec,
                        overlapping_dates=f"{start_date.isoformat()} to {end_date.isoformat()}",
                        affected_employees=emp_names,
                        warning_level="HIGH" if len(emp_names) >= 3 else "MEDIUM",
                        advice=f"Multiple {spec} practitioners ({', '.join(emp_names)}) have overlapping leaves; arrange locum cover or reschedule non-urgent cases.",
                    )
                )

        return LeaveConflictDetectionResponse(
            conflicts_detected=len(conflict_items),
            details=conflict_items,
        )

    async def assess_burnout_risks(self, clinic_id: UUID) -> BurnoutRiskAssessmentResponse:
        # Fetch active staff in clinic
        emp_stmt = select(Employee).where(
            Employee.clinic_id == clinic_id,
            Employee.status == EmployeeStatus.ACTIVE,
            Employee.deleted_at.is_(None),
        )
        employees = list((await self.db.execute(emp_stmt)).scalars().all())

        assessments: list[BurnoutRiskItem] = []
        month_ago = datetime.now(UTC).date() - timedelta(days=30)

        for emp in employees:
            # Overtime hours in past 30 days
            att_stmt = select(AttendanceRecord).where(
                AttendanceRecord.employee_id == emp.id,
                AttendanceRecord.date >= month_ago,
                AttendanceRecord.deleted_at.is_(None),
            )
            attendances = list((await self.db.execute(att_stmt)).scalars().all())
            total_ot_mins = sum(a.overtime_minutes for a in attendances)
            ot_hours = round(total_ot_mins / 60.0, 1)

            # Check consecutive attendance days without leave
            days_worked = len(attendances)

            factors = []
            risk = "LOW"
            if ot_hours > 25.0:
                factors.append(f"Excessive overtime accumulated: {ot_hours} hours in 30 days")
                risk = "HIGH"
            elif ot_hours > 12.0:
                factors.append(f"Elevated overtime: {ot_hours} hours in 30 days")
                risk = "MODERATE"

            if days_worked >= 25:
                factors.append(f"High working frequency: {days_worked} shifts in 30 days")
                if risk != "HIGH":
                    risk = "MODERATE"

            action = (
                "Immediate schedule relief recommended: reassign upcoming emergency shifts and ensure 2 mandatory rest days."
                if risk == "HIGH"
                else (
                    "Monitor chairside intensity and balance procedure mix."
                    if risk == "MODERATE"
                    else "Workload within healthy parameters."
                )
            )

            assessments.append(
                BurnoutRiskItem(
                    employee_id=emp.id,
                    employee_name=f"{emp.first_name} {emp.last_name}",
                    designation=emp.designation,
                    overtime_hours_month=ot_hours,
                    consecutive_days_worked=days_worked,
                    risk_level=risk,
                    key_factors=factors or ["Standard clinical hours maintained"],
                    suggested_action=action,
                )
            )

        high_count = sum(1 for a in assessments if a.risk_level == "HIGH")
        mod_count = sum(1 for a in assessments if a.risk_level == "MODERATE")

        return BurnoutRiskAssessmentResponse(
            high_risk_count=high_count,
            moderate_risk_count=mod_count,
            assessments=assessments,
        )

    async def audit_training_compliance(
        self, clinic_id: UUID
    ) -> TrainingComplianceRecommendationResponse:
        today = datetime.now(UTC).date()

        # 1. Check doctor license expiration
        emp_stmt = select(Employee).where(
            Employee.clinic_id == clinic_id,
            Employee.license_expiry_date.isnot(None),
            Employee.deleted_at.is_(None),
        )
        employees = list((await self.db.execute(emp_stmt)).scalars().all())

        alerts: list[TrainingComplianceItem] = []

        for emp in employees:
            if emp.license_expiry_date:
                days_left = (emp.license_expiry_date - today).days
                if days_left < 0:
                    alerts.append(
                        TrainingComplianceItem(
                            employee_id=emp.id,
                            employee_name=f"{emp.first_name} {emp.last_name}",
                            item_type="LICENSE_EXPIRY",
                            title=f"Dental Council License #{emp.license_number or 'N/A'} Expired",
                            expiry_date=emp.license_expiry_date,
                            days_remaining=days_left,
                            urgency="CRITICAL",
                        )
                    )
                elif days_left <= 60:
                    alerts.append(
                        TrainingComplianceItem(
                            employee_id=emp.id,
                            employee_name=f"{emp.first_name} {emp.last_name}",
                            item_type="LICENSE_EXPIRY",
                            title=f"Dental Council License #{emp.license_number or 'N/A'} Renewal Due",
                            expiry_date=emp.license_expiry_date,
                            days_remaining=days_left,
                            urgency="WARNING" if days_left <= 30 else "INFO",
                        )
                    )

        # 2. Check training records expiration (e.g. CPR/BLS, Radiation Safety)
        tr_stmt = (
            select(EmployeeTrainingRecord, Employee)
            .join(Employee, EmployeeTrainingRecord.employee_id == Employee.id)
            .where(
                Employee.clinic_id == clinic_id,
                EmployeeTrainingRecord.expiry_date.isnot(None),
                EmployeeTrainingRecord.deleted_at.is_(None),
            )
        )
        records = (await self.db.execute(tr_stmt)).all()

        for rec, emp in records:
            if rec.expiry_date:
                days_left = (rec.expiry_date - today).days
                if days_left < 0:
                    alerts.append(
                        TrainingComplianceItem(
                            employee_id=emp.id,
                            employee_name=f"{emp.first_name} {emp.last_name}",
                            item_type="MANDATORY_COURSE_EXPIRED",
                            title=f"Certification Expired: {rec.course_title}",
                            expiry_date=rec.expiry_date,
                            days_remaining=days_left,
                            urgency="CRITICAL",
                        )
                    )
                elif days_left <= 60:
                    alerts.append(
                        TrainingComplianceItem(
                            employee_id=emp.id,
                            employee_name=f"{emp.first_name} {emp.last_name}",
                            item_type="MANDATORY_COURSE_EXPIRED",
                            title=f"Certification Renewal Due: {rec.course_title}",
                            expiry_date=rec.expiry_date,
                            days_remaining=days_left,
                            urgency="WARNING",
                        )
                    )

        crit_count = sum(1 for a in alerts if a.urgency == "CRITICAL")

        return TrainingComplianceRecommendationResponse(
            total_compliance_alerts=len(alerts),
            critical_alerts=crit_count,
            alerts=alerts,
        )
