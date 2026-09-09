import { describe, expect, it } from "vitest";
import { z } from "zod";

const TIME_REGEX = /^([01]\d|2[0-3]):[0-5]\d$/;
const DATE_REGEX = /^\d{4}-\d{2}-\d{2}$/;

const appointmentBookingSchema = z
  .object({
    patient_id: z.string().uuid("Invalid patient ID"),
    dentist_id: z.string().uuid("Invalid clinician ID"),
    chair_id: z.string().uuid("Invalid operatory chair ID"),
    date: z.string().regex(DATE_REGEX, "Invalid date format (YYYY-MM-DD)"),
    start_time: z.string().regex(TIME_REGEX, "Invalid time format (HH:MM)"),
    duration: z.number().int().min(5).max(480),
    visit_type: z.enum([
      "CONSULTATION",
      "CHECKUP",
      "CLEANING",
      "PROCEDURE",
      "SURGERY",
      "FOLLOW_UP",
      "EMERGENCY",
    ]),
    priority: z.enum(["LOW", "NORMAL", "HIGH", "URGENT"]),
    chief_complaint: z.string().max(1000).optional().or(z.literal("")),
    notes: z.string().max(2000).optional().or(z.literal("")),
    is_emergency_override: z.boolean().default(false),
  })
  .refine(
    (data) => {
      // If visit_type is EMERGENCY and emergency override is checked, priority should ideally be HIGH or URGENT
      if (data.is_emergency_override && data.visit_type !== "EMERGENCY") {
        return false;
      }
      return true;
    },
    {
      message: "Emergency override can only be used with EMERGENCY visit type",
      path: ["is_emergency_override"],
    }
  );

// Valid state machine transitions
const ALLOWED_TRANSITIONS: Record<string, string[]> = {
  SCHEDULED: ["CONFIRMED", "CHECKED_IN", "CANCELLED", "NO_SHOW"],
  CONFIRMED: ["CHECKED_IN", "CANCELLED", "NO_SHOW"],
  CHECKED_IN: ["IN_CHAIR", "CANCELLED", "NO_SHOW"],
  IN_CHAIR: ["COMPLETED"],
  COMPLETED: [], // Immutable!
  CANCELLED: [], // Terminal
  NO_SHOW: [], // Terminal
};

function canTransition(fromStatus: string, toStatus: string): boolean {
  return ALLOWED_TRANSITIONS[fromStatus]?.includes(toStatus) ?? false;
}

function calculateWaitMinutes(checkedInAt: string, now: Date): number {
  const checkInTime = new Date(checkedInAt).getTime();
  const diffMs = now.getTime() - checkInTime;
  return Math.max(0, Math.floor(diffMs / (1000 * 60)));
}

describe("Appointment Booking Validation Schema", () => {
  const validPayload = {
    patient_id: "a0000000-0000-4000-8000-000000000001",
    dentist_id: "b0000000-0000-4000-8000-000000000002",
    chair_id: "c0000000-0000-4000-8000-000000000003",
    date: "2026-09-15",
    start_time: "10:30",
    duration: 45,
    visit_type: "CONSULTATION" as const,
    priority: "NORMAL" as const,
    chief_complaint: "Routine scaling and polishing",
    notes: "Patient prefers morning appointments",
    is_emergency_override: false,
  };

  it("validates a compliant appointment booking payload", () => {
    const res = appointmentBookingSchema.safeParse(validPayload);
    expect(res.success).toBe(true);
  });

  it("enforces duration bounds (5 to 480 minutes)", () => {
    expect(
      appointmentBookingSchema.safeParse({ ...validPayload, duration: 4 }).success
    ).toBe(false);

    expect(
      appointmentBookingSchema.safeParse({ ...validPayload, duration: 5 }).success
    ).toBe(true);

    expect(
      appointmentBookingSchema.safeParse({ ...validPayload, duration: 480 }).success
    ).toBe(true);

    expect(
      appointmentBookingSchema.safeParse({ ...validPayload, duration: 481 }).success
    ).toBe(false);
  });

  it("rejects invalid time formats", () => {
    const invalidTimes = ["25:00", "12:60", "9:30", "14-00", "noon"];
    for (const time of invalidTimes) {
      expect(
        appointmentBookingSchema.safeParse({ ...validPayload, start_time: time }).success
      ).toBe(false);
    }
  });

  it("allows emergency override ONLY when visit type is EMERGENCY", () => {
    // Non-emergency visit with emergency override => rejected
    const invalidOverride = {
      ...validPayload,
      visit_type: "CLEANING" as const,
      is_emergency_override: true,
    };
    expect(appointmentBookingSchema.safeParse(invalidOverride).success).toBe(false);

    // Emergency visit with emergency override => accepted
    const validEmergency = {
      ...validPayload,
      visit_type: "EMERGENCY" as const,
      priority: "URGENT" as const,
      is_emergency_override: true,
    };
    expect(appointmentBookingSchema.safeParse(validEmergency).success).toBe(true);
  });
});

describe("Appointment Lifecycle State Machine & Immutability", () => {
  it("allows valid forward workflow progressions", () => {
    expect(canTransition("SCHEDULED", "CONFIRMED")).toBe(true);
    expect(canTransition("CONFIRMED", "CHECKED_IN")).toBe(true);
    expect(canTransition("CHECKED_IN", "IN_CHAIR")).toBe(true);
    expect(canTransition("IN_CHAIR", "COMPLETED")).toBe(true);
  });

  it("enforces strict immutability on COMPLETED appointments", () => {
    expect(canTransition("COMPLETED", "SCHEDULED")).toBe(false);
    expect(canTransition("COMPLETED", "CONFIRMED")).toBe(false);
    expect(canTransition("COMPLETED", "CHECKED_IN")).toBe(false);
    expect(canTransition("COMPLETED", "IN_CHAIR")).toBe(false);
    expect(canTransition("COMPLETED", "CANCELLED")).toBe(false);
    expect(canTransition("COMPLETED", "NO_SHOW")).toBe(false);
  });

  it("enforces terminal state on CANCELLED appointments", () => {
    expect(canTransition("CANCELLED", "CONFIRMED")).toBe(false);
    expect(canTransition("CANCELLED", "COMPLETED")).toBe(false);
  });
});

describe("Reception Queue Wait Time Calculations", () => {
  it("accurately calculates elapsed minutes in waiting lobby", () => {
    const fixedNow = new Date("2026-09-08T10:30:00Z");
    const checkIn20MinAgo = new Date("2026-09-08T10:10:00Z").toISOString();
    const checkInJustNow = new Date("2026-09-08T10:29:30Z").toISOString();

    expect(calculateWaitMinutes(checkIn20MinAgo, fixedNow)).toBe(20);
    expect(calculateWaitMinutes(checkInJustNow, fixedNow)).toBe(0);
  });
});
