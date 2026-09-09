import { describe, expect, it } from "vitest";
import { z } from "zod";
import {
  COLOR_STANDARDS,
  DentitionType,
  NumberingSystem,
  Tooth,
  ToothCondition,
  ToothSurfaceEnum,
  getToothLabel,
} from "./types";

// Helper function to resolve center surface based on anatomical tooth type
export function getCenterSurface(
  toothType: "INCISOR" | "CANINE" | "PREMOLAR" | "MOLAR"
): "INCISAL" | "OCCLUSAL" {
  return toothType === "INCISOR" || toothType === "CANINE"
    ? "INCISAL"
    : "OCCLUSAL";
}

// Aggregation helper to compute KPI stats on frontend
export function computeOdontogramStats(teeth: Tooth[]) {
  let activeCaries = 0;
  let missingTeeth = 0;
  let rootCanals = 0;
  let crowns = 0;
  let implants = 0;
  let restorations = 0;

  for (const tooth of teeth) {
    if (tooth.is_missing || tooth.is_extracted) {
      missingTeeth += 1;
    }
    if (tooth.primary_status === "CARIES") {
      activeCaries += 1;
    } else if (tooth.surfaces.some((s) => s.condition === "CARIES")) {
      activeCaries += 1;
    }
    if (tooth.has_root_canal || tooth.primary_status === "ROOT_CANAL") {
      rootCanals += 1;
    }
    if (tooth.has_crown || tooth.primary_status === "CROWN") {
      crowns += 1;
    }
    if (tooth.has_implant || tooth.primary_status === "IMPLANT") {
      implants += 1;
    }
    if (
      tooth.primary_status === "FILLING" ||
      tooth.surfaces.some((s) => s.condition === "FILLING")
    ) {
      restorations += 1;
    }
  }

  return {
    total_teeth_charted: teeth.length,
    active_caries: activeCaries,
    missing_teeth: missingTeeth,
    root_canals: rootCanals,
    crowns,
    implants,
    restorations,
  };
}

// Frontend clinical invariant rule checkers
export function validateClinicalOperation(
  tooth: Tooth,
  operation: "FILLING" | "CROWN" | "IMPLANT" | "EXTRACTION" | "ROOT_CANAL"
): { allowed: boolean; reason?: string } {
  if (operation === "FILLING") {
    if (tooth.is_extracted || tooth.is_missing) {
      return { allowed: false, reason: "Cannot place filling on missing or extracted tooth" };
    }
  }

  if (operation === "CROWN") {
    if ((tooth.is_missing || tooth.is_extracted) && !tooth.has_implant) {
      return { allowed: false, reason: "Cannot place crown on missing tooth without implant" };
    }
  }

  if (operation === "IMPLANT") {
    if (tooth.has_implant) {
      return { allowed: false, reason: "Tooth site already has an existing implant" };
    }
    if (!tooth.is_missing && !tooth.is_extracted) {
      return { allowed: false, reason: "Natural tooth must be extracted before placing implant" };
    }
  }

  if (operation === "EXTRACTION") {
    if (tooth.is_extracted || tooth.is_missing) {
      return { allowed: false, reason: "Tooth is already extracted or missing" };
    }
  }

  if (operation === "ROOT_CANAL") {
    if (tooth.has_implant) {
      return { allowed: false, reason: "Cannot perform root canal on artificial titanium implant" };
    }
    if (tooth.is_extracted || tooth.is_missing) {
      return { allowed: false, reason: "Cannot perform root canal on missing or extracted tooth" };
    }
  }

  return { allowed: true };
}

// Zod schemas for clinical actions
export const toothConditionSchema = z.object({
  condition: z.enum([
    "HEALTHY",
    "CARIES",
    "FILLING",
    "ROOT_CANAL",
    "CROWN",
    "IMPLANT",
    "EXTRACTION",
    "MISSING",
    "BRIDGE",
    "OBSERVATION",
    "TEMPORARY_CROWN",
    "TEMPORARY_FILLING",
    "VENEER",
    "FRACTURE",
    "SEALANT",
    "ORTHODONTIC_BRACKET",
    "MOBILE_TOOTH",
    "IMPACTED",
  ]),
  surfaces: z
    .array(
      z.enum([
        "MESIAL",
        "DISTAL",
        "BUCCAL",
        "LINGUAL",
        "OCCLUSAL",
        "INCISAL",
        "CERVICAL",
        "ROOT",
      ])
    )
    .optional()
    .default([]),
  notes: z.string().max(1000).optional().nullable(),
  dentist_id: z.string().uuid().optional().nullable(),
});

export const toothProcedureSchema = z.object({
  procedure_code: z.string().min(1).max(50),
  procedure_name: z.string().min(1).max(255),
  surfaces: z
    .array(
      z.enum([
        "MESIAL",
        "DISTAL",
        "BUCCAL",
        "LINGUAL",
        "OCCLUSAL",
        "INCISAL",
        "CERVICAL",
        "ROOT",
      ])
    )
    .optional()
    .default([]),
  notes: z.string().max(1000).optional().nullable(),
  dentist_id: z.string().uuid().optional().nullable(),
});

describe("Odontogram Notation Systems & Helpers", () => {
  const mockTooth18: Tooth = {
    id: "10101010-0000-0000-0000-000000000018",
    clinic_id: "clinic-1",
    patient_id: "patient-1",
    tooth_number: "18",
    universal_number: "1",
    palmer_notation: "8┘",
    name: "Maxillary Right Third Molar",
    dentition_type: "ADULT",
    arch: "UPPER",
    quadrant: 1,
    tooth_type: "MOLAR",
    primary_status: "HEALTHY",
    color: "#10B981",
    is_missing: false,
    is_extracted: false,
    is_impacted: false,
    has_root_canal: false,
    has_crown: false,
    has_implant: false,
    has_bridge: false,
    mobility_grade: 0,
    surfaces: [
      {
        id: "s1",
        surface: "OCCLUSAL",
        condition: "HEALTHY",
        treatment: "NONE",
        color: "#10B981",
        last_modified_at: "2026-09-08T10:00:00Z",
      },
    ],
  };

  const mockTooth11: Tooth = {
    id: "10101010-0000-0000-0000-000000000011",
    clinic_id: "clinic-1",
    patient_id: "patient-1",
    tooth_number: "11",
    universal_number: "8",
    palmer_notation: "1┘",
    name: "Maxillary Right Central Incisor",
    dentition_type: "ADULT",
    arch: "UPPER",
    quadrant: 1,
    tooth_type: "INCISOR",
    primary_status: "HEALTHY",
    color: "#10B981",
    is_missing: false,
    is_extracted: false,
    is_impacted: false,
    has_root_canal: false,
    has_crown: false,
    has_implant: false,
    has_bridge: false,
    mobility_grade: 0,
    surfaces: [
      {
        id: "s2",
        surface: "INCISAL",
        condition: "HEALTHY",
        treatment: "NONE",
        color: "#10B981",
        last_modified_at: "2026-09-08T10:00:00Z",
      },
    ],
  };

  const mockToothPrimary51: Tooth = {
    id: "10101010-0000-0000-0000-000000000051",
    clinic_id: "clinic-1",
    patient_id: "patient-1",
    tooth_number: "51",
    universal_number: "D",
    palmer_notation: "A┘",
    name: "Primary Maxillary Right Central Incisor",
    dentition_type: "PRIMARY",
    arch: "UPPER",
    quadrant: 5,
    tooth_type: "INCISOR",
    primary_status: "HEALTHY",
    color: "#10B981",
    is_missing: false,
    is_extracted: false,
    is_impacted: false,
    has_root_canal: false,
    has_crown: false,
    has_implant: false,
    has_bridge: false,
    mobility_grade: 0,
    surfaces: [],
  };

  it("should return correct notation labels based on numbering system", () => {
    expect(getToothLabel(mockTooth18, "FDI")).toBe("18");
    expect(getToothLabel(mockTooth18, "UNIVERSAL")).toBe("1");
    expect(getToothLabel(mockTooth18, "PALMER")).toBe("8┘");

    expect(getToothLabel(mockTooth11, "FDI")).toBe("11");
    expect(getToothLabel(mockTooth11, "UNIVERSAL")).toBe("8");
    expect(getToothLabel(mockTooth11, "PALMER")).toBe("1┘");

    expect(getToothLabel(mockToothPrimary51, "FDI")).toBe("51");
    expect(getToothLabel(mockToothPrimary51, "UNIVERSAL")).toBe("D");
    expect(getToothLabel(mockToothPrimary51, "PALMER")).toBe("A┘");
  });

  it("should assign OCCLUSAL to molars and INCISAL to anterior teeth", () => {
    expect(getCenterSurface("MOLAR")).toBe("OCCLUSAL");
    expect(getCenterSurface("PREMOLAR")).toBe("OCCLUSAL");
    expect(getCenterSurface("INCISOR")).toBe("INCISAL");
    expect(getCenterSurface("CANINE")).toBe("INCISAL");
  });

  it("should map clinical conditions to standardized hex color codes", () => {
    expect(COLOR_STANDARDS.HEALTHY).toBe("#10B981");
    expect(COLOR_STANDARDS.CARIES).toBe("#EF4444");
    expect(COLOR_STANDARDS.FILLING).toBe("#3B82F6");
    expect(COLOR_STANDARDS.ROOT_CANAL).toBe("#8B5CF6");
    expect(COLOR_STANDARDS.CROWN).toBe("#F59E0B");
    expect(COLOR_STANDARDS.IMPLANT).toBe("#94A3B8");
    expect(COLOR_STANDARDS.EXTRACTION).toBe("#1E293B");
    expect(COLOR_STANDARDS.MISSING).toBe("#64748B");
    expect(COLOR_STANDARDS.BRIDGE).toBe("#854D0E");
  });
});

describe("Odontogram KPI Aggregations", () => {
  it("should correctly compute summary metrics across charted teeth", () => {
    const teeth: Tooth[] = [
      {
        id: "t1",
        clinic_id: "c1",
        patient_id: "p1",
        tooth_number: "16",
        universal_number: "3",
        palmer_notation: "6┘",
        name: "Upper Right 1st Molar",
        dentition_type: "ADULT",
        arch: "UPPER",
        quadrant: 1,
        tooth_type: "MOLAR",
        primary_status: "CARIES",
        color: "#EF4444",
        is_missing: false,
        is_extracted: false,
        is_impacted: false,
        has_root_canal: false,
        has_crown: false,
        has_implant: false,
        has_bridge: false,
        mobility_grade: 0,
        surfaces: [
          {
            id: "s1",
            surface: "OCCLUSAL",
            condition: "CARIES",
            treatment: "NONE",
            color: "#EF4444",
            last_modified_at: "2026-09-08T10:00:00Z",
          },
        ],
      },
      {
        id: "t2",
        clinic_id: "c1",
        patient_id: "p1",
        tooth_number: "26",
        universal_number: "14",
        palmer_notation: "6└",
        name: "Upper Left 1st Molar",
        dentition_type: "ADULT",
        arch: "UPPER",
        quadrant: 2,
        tooth_type: "MOLAR",
        primary_status: "ROOT_CANAL",
        color: "#8B5CF6",
        is_missing: false,
        is_extracted: false,
        is_impacted: false,
        has_root_canal: true,
        has_crown: true,
        has_implant: false,
        has_bridge: false,
        mobility_grade: 0,
        surfaces: [],
      },
      {
        id: "t3",
        clinic_id: "c1",
        patient_id: "p1",
        tooth_number: "46",
        universal_number: "30",
        palmer_notation: "6┌",
        name: "Lower Right 1st Molar",
        dentition_type: "ADULT",
        arch: "LOWER",
        quadrant: 4,
        tooth_type: "MOLAR",
        primary_status: "EXTRACTION",
        color: "#1E293B",
        is_missing: true,
        is_extracted: true,
        is_impacted: false,
        has_root_canal: false,
        has_crown: false,
        has_implant: false,
        has_bridge: false,
        mobility_grade: 0,
        surfaces: [],
      },
      {
        id: "t4",
        clinic_id: "c1",
        patient_id: "p1",
        tooth_number: "36",
        universal_number: "19",
        palmer_notation: "6┐",
        name: "Lower Left 1st Molar",
        dentition_type: "ADULT",
        arch: "LOWER",
        quadrant: 3,
        tooth_type: "MOLAR",
        primary_status: "FILLING",
        color: "#3B82F6",
        is_missing: false,
        is_extracted: false,
        is_impacted: false,
        has_root_canal: false,
        has_crown: false,
        has_implant: false,
        has_bridge: false,
        mobility_grade: 0,
        surfaces: [],
      },
    ];

    const stats = computeOdontogramStats(teeth);
    expect(stats.total_teeth_charted).toBe(4);
    expect(stats.active_caries).toBe(1);
    expect(stats.root_canals).toBe(1);
    expect(stats.crowns).toBe(1);
    expect(stats.missing_teeth).toBe(1);
    expect(stats.restorations).toBe(1);
    expect(stats.implants).toBe(0);
  });
});

describe("Clinical Validation Invariant Rules", () => {
  const healthyTooth: Tooth = {
    id: "t-normal",
    clinic_id: "c1",
    patient_id: "p1",
    tooth_number: "21",
    universal_number: "9",
    palmer_notation: "1└",
    name: "Maxillary Left Central Incisor",
    dentition_type: "ADULT",
    arch: "UPPER",
    quadrant: 2,
    tooth_type: "INCISOR",
    primary_status: "HEALTHY",
    color: "#10B981",
    is_missing: false,
    is_extracted: false,
    is_impacted: false,
    has_root_canal: false,
    has_crown: false,
    has_implant: false,
    has_bridge: false,
    mobility_grade: 0,
    surfaces: [],
  };

  const extractedTooth: Tooth = {
    ...healthyTooth,
    is_extracted: true,
    is_missing: true,
    primary_status: "EXTRACTION",
    color: "#1E293B",
  };

  const implantedTooth: Tooth = {
    ...extractedTooth,
    has_implant: true,
    primary_status: "IMPLANT",
    color: "#94A3B8",
  };

  it("should prevent placing fillings on missing or extracted teeth", () => {
    const validCheck = validateClinicalOperation(healthyTooth, "FILLING");
    expect(validCheck.allowed).toBe(true);

    const invalidCheck = validateClinicalOperation(extractedTooth, "FILLING");
    expect(invalidCheck.allowed).toBe(false);
    expect(invalidCheck.reason).toContain("Cannot place filling on missing or extracted tooth");
  });

  it("should prevent crown on missing tooth unless implant exists", () => {
    const invalidCrown = validateClinicalOperation(extractedTooth, "CROWN");
    expect(invalidCrown.allowed).toBe(false);
    expect(invalidCrown.reason).toContain("Cannot place crown on missing tooth without implant");

    const validCrownWithImplant = validateClinicalOperation(implantedTooth, "CROWN");
    expect(validCrownWithImplant.allowed).toBe(true);
  });

  it("should prevent duplicate extractions or extractions of already missing teeth", () => {
    const validExtract = validateClinicalOperation(healthyTooth, "EXTRACTION");
    expect(validExtract.allowed).toBe(true);

    const invalidExtract = validateClinicalOperation(extractedTooth, "EXTRACTION");
    expect(invalidExtract.allowed).toBe(false);
    expect(invalidExtract.reason).toContain("Tooth is already extracted or missing");
  });

  it("should prevent root canals on extracted teeth or titanium implants", () => {
    const validRCT = validateClinicalOperation(healthyTooth, "ROOT_CANAL");
    expect(validRCT.allowed).toBe(true);

    const rctOnExtracted = validateClinicalOperation(extractedTooth, "ROOT_CANAL");
    expect(rctOnExtracted.allowed).toBe(false);

    const rctOnImplant = validateClinicalOperation(implantedTooth, "ROOT_CANAL");
    expect(rctOnImplant.allowed).toBe(false);
    expect(rctOnImplant.reason).toContain("Cannot perform root canal on artificial titanium implant");
  });

  it("should validate Zod schema for condition and procedure creation", () => {
    const validCondition = toothConditionSchema.safeParse({
      condition: "CARIES",
      surfaces: ["MESIAL", "OCCLUSAL"],
      notes: "Carious lesion detected in enamel and dentin",
    });
    expect(validCondition.success).toBe(true);

    const invalidCondition = toothConditionSchema.safeParse({
      condition: "INVALID_CONDITION_NAME",
    });
    expect(invalidCondition.success).toBe(false);

    const validProcedure = toothProcedureSchema.safeParse({
      procedure_code: "D2391",
      procedure_name: "Resin-based composite - 1 surface, posterior",
      surfaces: ["OCCLUSAL"],
    });
    expect(validProcedure.success).toBe(true);
  });
});
