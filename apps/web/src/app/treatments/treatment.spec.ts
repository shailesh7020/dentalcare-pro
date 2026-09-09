import { describe, expect, it } from "vitest";
import { z } from "zod";
import type { ProcedureItem, TreatmentStatus } from "./types";

const DATE_REGEX = /^\d{4}-\d{2}-\d{2}$/;

// Frontend validation schema for treatment creation
export const procedureRowSchema = z.object({
  procedure_name: z.string().min(1, "Procedure name is required").max(160),
  tooth_number: z.string().max(20).optional().or(z.literal("")),
  quantity: z.number().int().min(1).max(32),
  cost: z.number().min(0),
  duration: z.number().int().min(5).max(480),
  notes: z.string().max(500).optional().or(z.literal("")),
  status: z.string().default("COMPLETED"),
});

export const followUpSchema = z.object({
  follow_up_date: z.string().regex(DATE_REGEX, "Invalid date format (YYYY-MM-DD)"),
  reason: z.string().min(1, "Follow-up reason is required").max(255),
  instructions: z.string().max(1000).optional().or(z.literal("")),
});

export const treatmentCreateSchema = z
  .object({
    patient_id: z.string().uuid("Invalid patient UUID"),
    appointment_id: z.string().uuid("Invalid appointment UUID"),
    dentist_id: z.string().uuid("Invalid clinician UUID"),
    diagnosis: z.string().min(1, "Clinical diagnosis is required").max(500),
    chief_complaint: z.string().max(1000).optional().or(z.literal("")),
    clinical_findings: z.string().max(2000).optional().or(z.literal("")),
    treatment_plan: z.string().max(2000).optional().or(z.literal("")),
    procedure_performed: z.string().max(2000).optional().or(z.literal("")),
    local_anaesthesia_used: z.string().max(255).optional().or(z.literal("")),
    medicines_used: z.string().max(500).optional().or(z.literal("")),
    clinical_notes: z.string().max(5000).optional().or(z.literal("")),
    soap_subjective: z.string().max(2000).optional().or(z.literal("")),
    soap_objective: z.string().max(2000).optional().or(z.literal("")),
    soap_assessment: z.string().max(2000).optional().or(z.literal("")),
    soap_plan: z.string().max(2000).optional().or(z.literal("")),
    follow_up_instructions: z.string().max(1000).optional().or(z.literal("")),
    status: z.enum(["PLANNED", "IN_PROGRESS", "COMPLETED", "CANCELLED"]),
    is_override: z.boolean().default(false),
    procedures: z.array(procedureRowSchema).default([]),
    follow_up: followUpSchema.nullable().optional(),
    appointment_date: z.string().regex(DATE_REGEX).optional(),
  })
  .refine(
    (data) => {
      // Follow-up date cannot be earlier than appointment date
      if (data.follow_up && data.appointment_date) {
        return data.follow_up.follow_up_date >= data.appointment_date;
      }
      return true;
    },
    {
      message: "Follow-up date cannot be before the treatment date",
      path: ["follow_up", "follow_up_date"],
    }
  );

// Financial & Time aggregations
export function calculateTreatmentTotals(
  procedures: Array<{ cost: number; quantity: number; duration: number }>
) {
  const totalCost = procedures.reduce(
    (sum, p) => sum + (Number(p.cost) || 0) * (Number(p.quantity) || 1),
    0
  );
  const totalDuration = procedures.reduce(
    (sum, p) => sum + (Number(p.duration) || 0),
    0
  );
  return {
    totalCost: Math.round(totalCost * 100) / 100,
    totalDuration,
  };
}

// State Machine transitions
export const TREATMENT_TRANSITIONS: Record<TreatmentStatus, TreatmentStatus[]> = {
  PLANNED: ["IN_PROGRESS", "CANCELLED"],
  IN_PROGRESS: ["COMPLETED", "CANCELLED"],
  COMPLETED: [], // Permanently locked & immutable!
  CANCELLED: [], // Terminal
};

export function canTransitionTreatment(
  current: TreatmentStatus,
  target: TreatmentStatus
): boolean {
  return TREATMENT_TRANSITIONS[current]?.includes(target) ?? false;
}

describe("Treatment Validation Schemas", () => {
  const validPayload = {
    patient_id: "5e5b2cb0-d49e-4fb9-9018-e42b68d17ebb",
    appointment_id: "a1f90f9f-e1e0-4314-92bf-1bb710fd7923",
    dentist_id: "1fb84471-0fcb-481d-a9aa-42e91965bd37",
    diagnosis: "Deep dentinal caries on tooth #46",
    chief_complaint: "Severe spontaneous throbbing pain",
    status: "IN_PROGRESS" as const,
    procedures: [
      {
        procedure_name: "Root Canal Therapy Stage 1",
        tooth_number: "46",
        quantity: 1,
        cost: 4500,
        duration: 45,
        notes: "MB, ML, D canals located",
        status: "COMPLETED",
      },
    ],
    follow_up: {
      follow_up_date: "2026-09-15",
      reason: "Canal obturation Stage 2",
    },
    appointment_date: "2026-09-08",
  };

  it("accepts valid treatment creation payload", () => {
    const res = treatmentCreateSchema.safeParse(validPayload);
    expect(res.success).toBe(true);
  });

  it("fails when diagnosis is empty", () => {
    const res = treatmentCreateSchema.safeParse({
      ...validPayload,
      diagnosis: "",
    });
    expect(res.success).toBe(false);
    if (!res.success) {
      expect(res.error.issues[0].message).toContain("diagnosis is required");
    }
  });

  it("fails when patient UUID is malformed", () => {
    const res = treatmentCreateSchema.safeParse({
      ...validPayload,
      patient_id: "invalid-uuid-123",
    });
    expect(res.success).toBe(false);
    if (!res.success) {
      expect(res.error.issues[0].path).toContain("patient_id");
    }
  });

  it("fails when follow-up date is earlier than appointment date", () => {
    const res = treatmentCreateSchema.safeParse({
      ...validPayload,
      appointment_date: "2026-09-08",
      follow_up: {
        follow_up_date: "2026-09-05", // 3 days in the past!
        reason: "Review",
      },
    });
    expect(res.success).toBe(false);
    if (!res.success) {
      expect(res.error.issues[0].message).toContain(
        "cannot be before the treatment date"
      );
    }
  });
});

describe("Treatment Procedure & Financial Calculations", () => {
  it("correctly computes total cost and chair duration", () => {
    const procedures = [
      { cost: 3500, quantity: 1, duration: 45 },
      { cost: 1200, quantity: 2, duration: 30 },
      { cost: 500, quantity: 1, duration: 15 },
    ];
    const { totalCost, totalDuration } = calculateTreatmentTotals(procedures);
    // 3500*1 + 1200*2 + 500*1 = 3500 + 2400 + 500 = 6400
    expect(totalCost).toBe(6400);
    // 45 + 30 + 15 = 90 mins
    expect(totalDuration).toBe(90);
  });

  it("handles empty procedure list gracefully", () => {
    const { totalCost, totalDuration } = calculateTreatmentTotals([]);
    expect(totalCost).toBe(0);
    expect(totalDuration).toBe(0);
  });
});

describe("Treatment State Machine & Immutability Rules", () => {
  it("allows transition from PLANNED to IN_PROGRESS", () => {
    expect(canTransitionTreatment("PLANNED", "IN_PROGRESS")).toBe(true);
  });

  it("allows transition from IN_PROGRESS to COMPLETED", () => {
    expect(canTransitionTreatment("IN_PROGRESS", "COMPLETED")).toBe(true);
  });

  it("allows transition from IN_PROGRESS to CANCELLED", () => {
    expect(canTransitionTreatment("IN_PROGRESS", "CANCELLED")).toBe(true);
  });

  it("strictly prohibits transitioning from COMPLETED (immutability)", () => {
    expect(canTransitionTreatment("COMPLETED", "IN_PROGRESS")).toBe(false);
    expect(canTransitionTreatment("COMPLETED", "CANCELLED")).toBe(false);
    expect(canTransitionTreatment("COMPLETED", "PLANNED")).toBe(false);
  });

  it("strictly prohibits transitioning from CANCELLED (terminal)", () => {
    expect(canTransitionTreatment("CANCELLED", "IN_PROGRESS")).toBe(false);
    expect(canTransitionTreatment("CANCELLED", "COMPLETED")).toBe(false);
  });
});
