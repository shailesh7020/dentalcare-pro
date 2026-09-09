import { describe, it, expect } from "vitest";
import type {
  LeaveStatus,
} from "./types";

// ===========================================================================
// Domain Business Logic Functions
// ===========================================================================

export interface PayrollBreakdown {
  basic_salary: number;
  hra: number;
  allowances: number;
  overtime_pay: number;
  incentives: number;
  bonus: number;
  pf_deduction: number;
  professional_tax: number;
  tds_deduction: number;
  insurance_deduction: number;
  unpaid_leave_deduction: number;
}

export function calculatePayrollTotals(input: PayrollBreakdown): {
  gross_pay: number;
  total_deductions: number;
  net_pay: number;
} {
  const gross_pay =
    input.basic_salary +
    input.hra +
    input.allowances +
    input.overtime_pay +
    input.incentives +
    input.bonus;

  const total_deductions =
    input.pf_deduction +
    input.professional_tax +
    input.tds_deduction +
    input.insurance_deduction +
    input.unpaid_leave_deduction;

  const net_pay = Math.max(0, gross_pay - total_deductions);

  return {
    gross_pay: Math.round(gross_pay * 100) / 100,
    total_deductions: Math.round(total_deductions * 100) / 100,
    net_pay: Math.round(net_pay * 100) / 100,
  };
}

export function isValidLeaveStatusTransition(
  current: LeaveStatus,
  target: LeaveStatus
): boolean {
  const allowedTransitions: Record<LeaveStatus, LeaveStatus[]> = {
    DRAFT: ["SUBMITTED", "CANCELLED"],
    SUBMITTED: ["MANAGER_APPROVED", "HR_APPROVED", "REJECTED", "CANCELLED"],
    MANAGER_APPROVED: ["HR_APPROVED", "REJECTED", "CANCELLED"],
    HR_APPROVED: ["CANCELLED"],
    REJECTED: [],
    CANCELLED: [],
  };

  return allowedTransitions[current]?.includes(target) ?? false;
}

export function evaluateLeaveQuota(
  allocated: number,
  used: number,
  requestedDays: number
): { canApprove: boolean; remaining: number } {
  const remaining = Math.max(0, allocated - used);
  return {
    canApprove: remaining >= requestedDays,
    remaining,
  };
}

export function calculateAttendancePunctuality(
  scheduledStart: string, // "HH:MM"
  scheduledEnd: string, // "HH:MM"
  actualCheckIn: string, // "HH:MM"
  actualCheckOut: string | null, // "HH:MM"
  gracePeriodMinutes = 15
): {
  isLate: boolean;
  lateMinutes: number;
  isEarlyDeparture: boolean;
  earlyDepartureMinutes: number;
  overtimeMinutes: number;
} {
  const parseMins = (timeStr: string) => {
    const [h, m] = timeStr.split(":").map(Number);
    return h * 60 + m;
  };

  const startMins = parseMins(scheduledStart);
  const endMins = parseMins(scheduledEnd);
  const inMins = parseMins(actualCheckIn);

  const lateDiff = inMins - startMins;
  const isLate = lateDiff > gracePeriodMinutes;
  const lateMinutes = lateDiff > 0 ? lateDiff : 0;

  let isEarlyDeparture = false;
  let earlyDepartureMinutes = 0;
  let overtimeMinutes = 0;

  if (actualCheckOut) {
    const outMins = parseMins(actualCheckOut);
    if (outMins < endMins) {
      isEarlyDeparture = true;
      earlyDepartureMinutes = endMins - outMins;
    } else if (outMins > endMins) {
      overtimeMinutes = outMins - endMins;
    }
  }

  return {
    isLate,
    lateMinutes,
    isEarlyDeparture,
    earlyDepartureMinutes,
    overtimeMinutes,
  };
}

export function detectScheduleConflict(
  slotA: { date: string; start: string; end: string; employeeId: string; operatoryId?: string },
  slotB: { date: string; start: string; end: string; employeeId: string; operatoryId?: string }
): { hasConflict: boolean; reason?: "STAFF_DOUBLE_BOOKED" | "OPERATORY_CONFLICT" } {
  if (slotA.date !== slotB.date) return { hasConflict: false };

  const parseMins = (t: string) => {
    const [h, m] = t.split(":").map(Number);
    return h * 60 + m;
  };

  const startA = parseMins(slotA.start);
  const endA = parseMins(slotA.end);
  const startB = parseMins(slotB.start);
  const endB = parseMins(slotB.end);

  const isOverlapping = Math.max(startA, startB) < Math.min(endA, endB);
  if (!isOverlapping) return { hasConflict: false };

  if (slotA.employeeId === slotB.employeeId) {
    return { hasConflict: true, reason: "STAFF_DOUBLE_BOOKED" };
  }

  if (slotA.operatoryId && slotB.operatoryId && slotA.operatoryId === slotB.operatoryId) {
    return { hasConflict: true, reason: "OPERATORY_CONFLICT" };
  }

  return { hasConflict: false };
}

export function evaluateLicenseCompliance(
  expiryDateStr: string,
  referenceDateStr: string
): {
  status: "VALID" | "EXPIRING_SOON" | "EXPIRED";
  daysRemaining: number;
} {
  const expiry = new Date(expiryDateStr).getTime();
  const ref = new Date(referenceDateStr).getTime();
  const diffDays = Math.round((expiry - ref) / (1000 * 60 * 60 * 24));

  if (diffDays < 0) {
    return { status: "EXPIRED", daysRemaining: diffDays };
  }
  if (diffDays <= 30) {
    return { status: "EXPIRING_SOON", daysRemaining: diffDays };
  }
  return { status: "VALID", daysRemaining: diffDays };
}

export function calculateOverallPerformanceRating(scores: {
  clinical_skills: number;
  patient_satisfaction: number;
  punctuality: number;
  teamwork: number;
  protocol_adherence: number;
}): number {
  const sum =
    scores.clinical_skills +
    scores.patient_satisfaction +
    scores.punctuality +
    scores.teamwork +
    scores.protocol_adherence;
  return Math.round((sum / 5) * 10) / 10;
}

// ===========================================================================
// Test Suites
// ===========================================================================

describe("Human Resources (HR), Payroll & Workforce Management", () => {
  describe("Payroll Gross-to-Net Calculation Engine", () => {
    it("calculates gross, itemized deductions, and net salary accurately", () => {
      const breakdown: PayrollBreakdown = {
        basic_salary: 50000,
        hra: 20000,
        allowances: 10000,
        overtime_pay: 3000,
        incentives: 5000,
        bonus: 2000,
        pf_deduction: 6000,
        professional_tax: 200,
        tds_deduction: 4500,
        insurance_deduction: 1500,
        unpaid_leave_deduction: 0,
      };

      const result = calculatePayrollTotals(breakdown);
      expect(result.gross_pay).toBe(90000);
      expect(result.total_deductions).toBe(12200);
      expect(result.net_pay).toBe(77800);
    });

    it("prevents negative net salary when deductions exceed gross", () => {
      const breakdown: PayrollBreakdown = {
        basic_salary: 10000,
        hra: 0,
        allowances: 0,
        overtime_pay: 0,
        incentives: 0,
        bonus: 0,
        pf_deduction: 8000,
        professional_tax: 200,
        tds_deduction: 3000,
        insurance_deduction: 1000,
        unpaid_leave_deduction: 0,
      };

      const result = calculatePayrollTotals(breakdown);
      expect(result.gross_pay).toBe(10000);
      expect(result.total_deductions).toBe(12200);
      expect(result.net_pay).toBe(0);
    });
  });

  describe("Two-Tier Leave Management Workflow", () => {
    it("allows valid forward progression through manager and HR review", () => {
      expect(isValidLeaveStatusTransition("DRAFT", "SUBMITTED")).toBe(true);
      expect(isValidLeaveStatusTransition("SUBMITTED", "MANAGER_APPROVED")).toBe(true);
      expect(isValidLeaveStatusTransition("MANAGER_APPROVED", "HR_APPROVED")).toBe(true);
    });

    it("allows direct HR approval or rejection from intermediate review stages", () => {
      expect(isValidLeaveStatusTransition("SUBMITTED", "HR_APPROVED")).toBe(true);
      expect(isValidLeaveStatusTransition("SUBMITTED", "REJECTED")).toBe(true);
      expect(isValidLeaveStatusTransition("MANAGER_APPROVED", "REJECTED")).toBe(true);
    });

    it("disallows unauthorized skipping or reverse transitions", () => {
      expect(isValidLeaveStatusTransition("DRAFT", "HR_APPROVED")).toBe(false);
      expect(isValidLeaveStatusTransition("HR_APPROVED", "DRAFT")).toBe(false);
      expect(isValidLeaveStatusTransition("REJECTED", "HR_APPROVED")).toBe(false);
      expect(isValidLeaveStatusTransition("CANCELLED", "SUBMITTED")).toBe(false);
    });

    it("verifies quota deduction feasibility", () => {
      const quota1 = evaluateLeaveQuota(18, 5, 3);
      expect(quota1.canApprove).toBe(true);
      expect(quota1.remaining).toBe(13);

      const quota2 = evaluateLeaveQuota(18, 16, 4);
      expect(quota2.canApprove).toBe(false);
      expect(quota2.remaining).toBe(2);
    });
  });

  describe("Real-Time Attendance & Punctuality Tracking", () => {
    it("recognizes punctual check-in within grace period", () => {
      const result = calculateAttendancePunctuality("09:00", "17:00", "09:10", "17:00", 15);
      expect(result.isLate).toBe(false);
      expect(result.lateMinutes).toBe(10);
      expect(result.isEarlyDeparture).toBe(false);
      expect(result.overtimeMinutes).toBe(0);
    });

    it("flags late arrival exceeding grace period", () => {
      const result = calculateAttendancePunctuality("09:00", "17:00", "09:30", "17:00", 15);
      expect(result.isLate).toBe(true);
      expect(result.lateMinutes).toBe(30);
    });

    it("flags early departure and overtime hours correctly", () => {
      const early = calculateAttendancePunctuality("09:00", "17:00", "08:55", "16:15", 15);
      expect(early.isEarlyDeparture).toBe(true);
      expect(early.earlyDepartureMinutes).toBe(45);
      expect(early.overtimeMinutes).toBe(0);

      const ot = calculateAttendancePunctuality("09:00", "17:00", "08:50", "19:00", 15);
      expect(ot.isEarlyDeparture).toBe(false);
      expect(ot.overtimeMinutes).toBe(120);
    });
  });

  describe("Staff Scheduling & Conflict Prevention", () => {
    it("detects staff double-booking on overlapping shifts", () => {
      const shift1 = { date: "2026-09-15", start: "09:00", end: "14:00", employeeId: "emp-1" };
      const shift2 = { date: "2026-09-15", start: "12:00", end: "17:00", employeeId: "emp-1" };

      const conflict = detectScheduleConflict(shift1, shift2);
      expect(conflict.hasConflict).toBe(true);
      expect(conflict.reason).toBe("STAFF_DOUBLE_BOOKED");
    });

    it("detects operatory / chair double-booking on overlapping times", () => {
      const shift1 = { date: "2026-09-15", start: "09:00", end: "13:00", employeeId: "emp-1", operatoryId: "chair-1" };
      const shift2 = { date: "2026-09-15", start: "11:00", end: "15:00", employeeId: "emp-2", operatoryId: "chair-1" };

      const conflict = detectScheduleConflict(shift1, shift2);
      expect(conflict.hasConflict).toBe(true);
      expect(conflict.reason).toBe("OPERATORY_CONFLICT");
    });

    it("allows non-overlapping shifts on same date or different dates", () => {
      const morning = { date: "2026-09-15", start: "08:00", end: "12:00", employeeId: "emp-1", operatoryId: "chair-1" };
      const afternoon = { date: "2026-09-15", start: "13:00", end: "17:00", employeeId: "emp-2", operatoryId: "chair-1" };

      const conflict = detectScheduleConflict(morning, afternoon);
      expect(conflict.hasConflict).toBe(false);
    });
  });

  describe("Doctor Credentialing & License Compliance Radar", () => {
    it("classifies upcoming expiration within 30 days as EXPIRING_SOON", () => {
      const radar = evaluateLicenseCompliance("2026-09-25", "2026-09-09");
      expect(radar.status).toBe("EXPIRING_SOON");
      expect(radar.daysRemaining).toBe(16);
    });

    it("classifies past expiration as EXPIRED", () => {
      const radar = evaluateLicenseCompliance("2026-08-30", "2026-09-09");
      expect(radar.status).toBe("EXPIRED");
      expect(radar.daysRemaining).toBe(-10);
    });

    it("classifies licenses with > 30 days as VALID", () => {
      const radar = evaluateLicenseCompliance("2027-03-31", "2026-09-09");
      expect(radar.status).toBe("VALID");
      expect(radar.daysRemaining).toBeGreaterThan(30);
    });
  });

  describe("Staff Performance Review Aggregator", () => {
    it("computes 5-point composite KPI appraisal rating accurately", () => {
      const rating = calculateOverallPerformanceRating({
        clinical_skills: 4.5,
        patient_satisfaction: 4.8,
        punctuality: 4.0,
        teamwork: 4.7,
        protocol_adherence: 4.5,
      });

      expect(rating).toBe(4.5);
    });
  });
});
