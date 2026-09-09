import { describe, expect, it } from "vitest";
import { z } from "zod";
import type {
  DosageFrequency,
  MedicineForm,
  PrescriptionItemCreate,
  PrescriptionStatus,
  TemplateCategory,
} from "./types";

// Prescription Item Validation Schema
export const prescriptionItemSchema = z.object({
  medicine_name: z.string().min(1, "Medicine name is required").max(255),
  generic_name: z.string().max(255).optional().or(z.literal("")),
  brand_name: z.string().max(255).optional().or(z.literal("")),
  strength: z.string().max(100).optional().or(z.literal("")),
  form: z.enum([
    "TABLET",
    "CAPSULE",
    "SYRUP",
    "MOUTHWASH",
    "GEL",
    "INJECTION",
    "DROPS",
  ]).default("TABLET"),
  dosage: z.string().min(1, "Dosage is required").max(100),
  route: z.string().default("Oral"),
  frequency: z.enum(["OD", "BD", "TDS", "QID", "SOS", "STAT"]),
  duration: z.string().min(1, "Duration is required").max(100),
  quantity: z.number().int().min(1, "Quantity must be at least 1").max(500),
  timing: z.string().max(255).optional().or(z.literal("")),
  food_instructions: z.string().max(255).optional().or(z.literal("")),
  notes: z.string().max(1000).optional().or(z.literal("")),
});

// Prescription Create Validation Schema
export const prescriptionCreateSchema = z
  .object({
    patient_id: z.string().uuid("Invalid patient UUID"),
    treatment_id: z.string().uuid().nullable().optional(),
    appointment_id: z.string().uuid().nullable().optional(),
    dentist_id: z.string().uuid().nullable().optional(),
    diagnosis: z.string().min(1, "Clinical diagnosis is required").max(500),
    notes: z.string().max(2000).nullable().optional(),
    instructions: z.string().max(2000).nullable().optional(),
    follow_up_date: z
      .string()
      .regex(/^\d{4}-\d{2}-\d{2}$/, "Invalid date format (YYYY-MM-DD)")
      .nullable()
      .optional(),
    items: z.array(prescriptionItemSchema).default([]),
    issue_immediately: z.boolean().default(false),
  })
  .refine(
    (data) => {
      // Clinical Invariant: Cannot issue an empty prescription immediately
      if (data.issue_immediately && data.items.length === 0) {
        return false;
      }
      return true;
    },
    {
      message: "Cannot issue an empty prescription without medications.",
      path: ["items"],
    }
  )
  .refine(
    (data) => {
      // Clinical Invariant: Duplicate medicines prohibited
      const names = data.items.map((it) => it.medicine_name.trim().toLowerCase());
      const unique = new Set(names);
      return names.length === unique.size;
    },
    {
      message: "Duplicate medication entries detected.",
      path: ["items"],
    }
  );

// Duplicate Detection Helper
export function findDuplicateMedicines(items: PrescriptionItemCreate[]): string[] {
  const seen = new Set<string>();
  const duplicates = new Set<string>();
  for (const item of items) {
    const clean = item.medicine_name.trim().toLowerCase();
    if (!clean) continue;
    if (seen.has(clean)) {
      duplicates.add(item.medicine_name.trim());
    } else {
      seen.add(clean);
    }
  }
  return Array.from(duplicates);
}

// Prescription State Machine
export const PRESCRIPTION_TRANSITIONS: Record<
  PrescriptionStatus,
  PrescriptionStatus[]
> = {
  DRAFT: ["ISSUED", "CANCELLED"],
  ISSUED: ["CANCELLED"], // Issued records are immutable; modifications require revision/cancellation
  CANCELLED: [], // Terminal audited state
};

export function canTransitionPrescription(
  current: PrescriptionStatus,
  target: PrescriptionStatus
): boolean {
  return PRESCRIPTION_TRANSITIONS[current]?.includes(target) ?? false;
}

// Allergy Cross-Check Helper
export function checkMedicationAllergyWarnings(
  patientAllergies: string | null | undefined,
  medications: PrescriptionItemCreate[]
): string[] {
  if (!patientAllergies) return [];
  const allergyStr = patientAllergies.toLowerCase();
  const warnings: string[] = [];

  for (const med of medications) {
    const medName = (med.medicine_name + " " + (med.generic_name || "")).toLowerCase();
    if (
      allergyStr.includes("penicillin") &&
      (medName.includes("amox") || medName.includes("augmentin") || medName.includes("penicillin"))
    ) {
      warnings.push(`PENICILLIN CONTRAINDICATION: Patient is allergic to Penicillin. '${med.medicine_name}' is a beta-lactam.`);
    }
    if (
      (allergyStr.includes("nsaid") || allergyStr.includes("aspirin") || allergyStr.includes("ibuprofen")) &&
      (medName.includes("ibuprofen") || medName.includes("ketorol") || medName.includes("diclofenac"))
    ) {
      warnings.push(`NSAID CONTRAINDICATION: Patient is allergic to NSAIDs/Aspirin. '${med.medicine_name}' is an NSAID.`);
    }
  }
  return warnings;
}

describe("Prescription Validation Schemas", () => {
  const validItem: PrescriptionItemCreate = {
    medicine_name: "Amoxicillin",
    generic_name: "Amoxicillin",
    brand_name: "Amoxil 500",
    strength: "500 mg",
    form: "CAPSULE",
    dosage: "1 capsule",
    route: "Oral",
    frequency: "TDS",
    duration: "5 days",
    quantity: 15,
    timing: "Morning - Afternoon - Night",
    food_instructions: "After food",
    notes: "First-line coverage",
  };

  const validPayload = {
    patient_id: "7662c9c5-8422-4cf4-942a-4db54cbcf1a2",
    diagnosis: "Acute apical periodontitis #46",
    instructions: "Take painkillers after meals",
    items: [validItem],
    issue_immediately: false,
  };

  it("should validate a compliant draft prescription payload", () => {
    const res = prescriptionCreateSchema.safeParse(validPayload);
    expect(res.success).toBe(true);
  });

  it("should fail validation if diagnosis is missing", () => {
    const invalid = { ...validPayload, diagnosis: "" };
    const res = prescriptionCreateSchema.safeParse(invalid);
    expect(res.success).toBe(false);
    if (!res.success) {
      expect(res.error.issues[0].message).toContain("diagnosis is required");
    }
  });

  it("should prevent issuing an empty prescription", () => {
    const emptyIssued = {
      ...validPayload,
      items: [],
      issue_immediately: true,
    };
    const res = prescriptionCreateSchema.safeParse(emptyIssued);
    expect(res.success).toBe(false);
    if (!res.success) {
      expect(res.error.issues[0].message).toContain(
        "Cannot issue an empty prescription"
      );
    }
  });

  it("should permit saving a draft prescription with 0 items for later completion", () => {
    const emptyDraft = {
      ...validPayload,
      items: [],
      issue_immediately: false,
    };
    const res = prescriptionCreateSchema.safeParse(emptyDraft);
    expect(res.success).toBe(true);
  });

  it("should reject duplicate medications in the same prescription", () => {
    const duplicatePayload = {
      ...validPayload,
      items: [
        validItem,
        {
          ...validItem,
          dosage: "2 capsules",
        },
      ],
    };
    const res = prescriptionCreateSchema.safeParse(duplicatePayload);
    expect(res.success).toBe(false);
    if (!res.success) {
      expect(res.error.issues[0].message).toContain("Duplicate medication");
    }
  });
});

describe("Prescription Duplicate Detection Helper", () => {
  it("should identify duplicate medicines case-insensitively", () => {
    const items: PrescriptionItemCreate[] = [
      {
        medicine_name: "Amoxicillin",
        dosage: "1 tab",
        frequency: "TDS",
        duration: "5 days",
        quantity: 15,
      },
      {
        medicine_name: "Dolo 650",
        dosage: "1 tab",
        frequency: "TDS",
        duration: "3 days",
        quantity: 9,
      },
      {
        medicine_name: "amoxicillin",
        dosage: "500 mg",
        frequency: "BD",
        duration: "3 days",
        quantity: 6,
      },
    ];

    const dupes = findDuplicateMedicines(items);
    expect(dupes).toHaveLength(1);
    expect(dupes[0].toLowerCase()).toBe("amoxicillin");
  });

  it("should return empty array when all medications are distinct", () => {
    const items: PrescriptionItemCreate[] = [
      {
        medicine_name: "Augmentin 625",
        dosage: "1 tab",
        frequency: "BD",
        duration: "5 days",
        quantity: 10,
      },
      {
        medicine_name: "Metrogyl 400",
        dosage: "1 tab",
        frequency: "TDS",
        duration: "5 days",
        quantity: 15,
      },
      {
        medicine_name: "Ketorol DT",
        dosage: "1 tab",
        frequency: "SOS",
        duration: "2 days",
        quantity: 4,
      },
    ];

    expect(findDuplicateMedicines(items)).toHaveLength(0);
  });
});

describe("Prescription State Machine Transitions", () => {
  it("should allow transition from DRAFT to ISSUED", () => {
    expect(canTransitionPrescription("DRAFT", "ISSUED")).toBe(true);
  });

  it("should allow cancellation of DRAFT or ISSUED prescriptions", () => {
    expect(canTransitionPrescription("DRAFT", "CANCELLED")).toBe(true);
    expect(canTransitionPrescription("ISSUED", "CANCELLED")).toBe(true);
  });

  it("should disallow modifying an ISSUED prescription back to DRAFT (immutability)", () => {
    expect(canTransitionPrescription("ISSUED", "DRAFT")).toBe(false);
  });

  it("should disallow any transition out of CANCELLED (terminal state)", () => {
    expect(canTransitionPrescription("CANCELLED", "DRAFT")).toBe(false);
    expect(canTransitionPrescription("CANCELLED", "ISSUED")).toBe(false);
  });
});

describe("Clinical Allergy Warning Detection", () => {
  it("should trigger contraindication warning when prescribing Amoxicillin to Penicillin-allergic patient", () => {
    const patientAllergies = "Penicillin, Sulfa drugs";
    const medications: PrescriptionItemCreate[] = [
      {
        medicine_name: "Amoxil 500",
        generic_name: "Amoxicillin",
        dosage: "1 cap",
        frequency: "TDS",
        duration: "5 days",
        quantity: 15,
      },
    ];

    const warnings = checkMedicationAllergyWarnings(patientAllergies, medications);
    expect(warnings.length).toBeGreaterThanOrEqual(1);
    expect(warnings[0]).toContain("PENICILLIN CONTRAINDICATION");
  });

  it("should trigger contraindication warning when prescribing Ketorolac to NSAID-allergic patient", () => {
    const patientAllergies = "Aspirin, NSAIDs";
    const medications: PrescriptionItemCreate[] = [
      {
        medicine_name: "Ketorol DT",
        generic_name: "Ketorolac Tromethamine",
        dosage: "1 tab",
        frequency: "SOS",
        duration: "2 days",
        quantity: 4,
      },
    ];

    const warnings = checkMedicationAllergyWarnings(patientAllergies, medications);
    expect(warnings.length).toBeGreaterThanOrEqual(1);
    expect(warnings[0]).toContain("NSAID CONTRAINDICATION");
  });

  it("should return no warnings for safe medications", () => {
    const patientAllergies = "Penicillin";
    const medications: PrescriptionItemCreate[] = [
      {
        medicine_name: "Paracetamol",
        generic_name: "Acetaminophen",
        dosage: "1 tab",
        frequency: "TDS",
        duration: "3 days",
        quantity: 9,
      },
      {
        medicine_name: "Chlorhexidine 0.2%",
        generic_name: "Chlorhexidine Gluconate",
        dosage: "10 ml",
        frequency: "BD",
        duration: "14 days",
        quantity: 1,
      },
    ];

    const warnings = checkMedicationAllergyWarnings(patientAllergies, medications);
    expect(warnings).toHaveLength(0);
  });
});
