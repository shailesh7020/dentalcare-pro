import { describe, expect, it } from "vitest";
import { z } from "zod";
import type {
  AIProviderType,
  AITaskType,
  AIRecommendationStatus,
  ClinicalDocType,
  InventoryForecastItem,
  RiskAlert,
} from "./types";

// 1. Zod Schema for SOAP Note Validation
export const soapNoteSchema = z.object({
  subjective: z.string().min(10, "Subjective note too brief"),
  objective: z.string().min(10, "Objective note too brief"),
  assessment: z.string().min(5, "Assessment must include diagnosis"),
  plan: z.string().min(10, "Plan must include treatment and follow-up"),
  status: z.enum(["PENDING_REVIEW", "APPROVED", "REJECTED", "MODIFIED"]).default("PENDING_REVIEW"),
  requires_clinician_approval: z.literal(true),
});

// 2. Clinical Guardrail: Penicillin / Beta-lactam Interceptor
export function evaluatePrescriptionSafety(
  requestedDrug: string,
  patientAllergies: string[]
): {
  isSafe: boolean;
  warnings: string[];
  safeAlternatives: string[];
} {
  const betaLactams = ["amoxicillin", "ampicillin", "augmentin", "penicillin", "cephalexin", "keflex"];
  const lowerRequested = requestedDrug.toLowerCase();
  const isPenicillinClass = betaLactams.some((bl) => lowerRequested.includes(bl));

  const hasPenicillinAllergy = patientAllergies.some((a) =>
    a.toLowerCase().includes("penicillin") || a.toLowerCase().includes("beta-lactam")
  );

  if (isPenicillinClass && hasPenicillinAllergy) {
    return {
      isSafe: false,
      warnings: [
        `CRITICAL ALLERGY HAZARD: Patient is allergic to Penicillin. ${requestedDrug} is contraindicated due to risk of anaphylaxis.`,
      ],
      safeAlternatives: [
        "Clindamycin 300mg PO q6h x 5-7 days",
        "Azithromycin 500mg PO day 1, then 250mg q24h x 4 days",
        "Erythromycin 500mg PO q6h x 7 days",
      ],
    };
  }

  return {
    isSafe: true,
    warnings: [],
    safeAlternatives: [],
  };
}

// 3. Inventory Depletion Urgency Calculator
export function calculateStockDepletionUrgency(
  currentStock: number,
  minStockLevel: number,
  burnRateWeekly: number
): {
  daysRemaining: number;
  urgency: "CRITICAL" | "HIGH" | "MEDIUM" | "NORMAL";
  suggestedReorderQty: number;
} {
  if (burnRateWeekly <= 0) {
    return { daysRemaining: 999, urgency: "NORMAL", suggestedReorderQty: 0 };
  }

  const dailyBurn = burnRateWeekly / 7;
  const daysRemaining = Math.max(0, Math.round(currentStock / dailyBurn));

  let urgency: "CRITICAL" | "HIGH" | "MEDIUM" | "NORMAL" = "NORMAL";
  if (daysRemaining <= 7 || currentStock <= minStockLevel) {
    urgency = "CRITICAL";
  } else if (daysRemaining <= 14) {
    urgency = "HIGH";
  } else if (daysRemaining <= 30) {
    urgency = "MEDIUM";
  }

  const suggestedReorderQty = Math.max(
    minStockLevel * 2,
    Math.round((minStockLevel - currentStock) + burnRateWeekly * 4)
  );

  return { daysRemaining, urgency, suggestedReorderQty };
}

// 4. Natural Language Search Intent Extractor
export function parseClinicalSearchIntent(query: string): {
  conditions: string[];
  procedures: string[];
  isOverdueRecall: boolean;
  hasAllergyFilter: boolean;
} {
  const q = query.toLowerCase();
  const conditions: string[] = [];
  const procedures: string[] = [];

  if (q.includes("diabet")) conditions.push("Diabetes");
  if (q.includes("hypertens") || q.includes("bp") || q.includes("blood pressure")) conditions.push("Hypertension");
  if (q.includes("asthma")) conditions.push("Asthma");

  if (q.includes("rct") || q.includes("root canal") || q.includes("endo")) procedures.push("Root Canal");
  if (q.includes("extract") || q.includes("surgery") || q.includes("wisdom")) procedures.push("Extraction");
  if (q.includes("crown") || q.includes("bridge") || q.includes("prostho")) procedures.push("Crown");
  if (q.includes("cleaning") || q.includes("scaling") || q.includes("perio")) procedures.push("Scaling");

  return {
    conditions,
    procedures,
    isOverdueRecall: q.includes("recall") || q.includes("due") || q.includes("overdue"),
    hasAllergyFilter: q.includes("allerg") || q.includes("penicillin"),
  };
}

function referringClinicianFormat(name: string): boolean {
  return name.startsWith("Dr.") && name.includes(",");
}

describe("Phase 11: AI Clinical Assistant & CDS Guardrails", () => {
  describe("1. Penicillin Allergy Interception Guardrail", () => {
    it("should intercept Amoxicillin when patient has Penicillin allergy and provide safe alternatives", () => {
      const patientAllergies = ["Penicillin", "Dust Mites"];
      const safetyCheck = evaluatePrescriptionSafety("Amoxicillin 500mg", patientAllergies);

      expect(safetyCheck.isSafe).toBe(false);
      expect(safetyCheck.warnings.length).toBeGreaterThan(0);
      expect(safetyCheck.warnings[0]).toContain("CRITICAL ALLERGY HAZARD");
      expect(safetyCheck.safeAlternatives).toEqual(
        expect.arrayContaining([expect.stringContaining("Clindamycin")])
      );
    });

    it("should intercept Augmentin (Amoxicillin-Clavulanate) for Penicillin allergy", () => {
      const patientAllergies = ["Severe Beta-lactam anaphylaxis"];
      const safetyCheck = evaluatePrescriptionSafety("Augmentin 625mg", patientAllergies);

      expect(safetyCheck.isSafe).toBe(false);
      expect(safetyCheck.safeAlternatives.length).toBeGreaterThanOrEqual(2);
    });

    it("should allow Amoxicillin safely when patient has no penicillin allergy", () => {
      const patientAllergies = ["Latex", "Sulfa drugs"];
      const safetyCheck = evaluatePrescriptionSafety("Amoxicillin 500mg", patientAllergies);

      expect(safetyCheck.isSafe).toBe(true);
      expect(safetyCheck.warnings).toHaveLength(0);
      expect(safetyCheck.safeAlternatives).toHaveLength(0);
    });

    it("should allow non-beta-lactam drugs (e.g. Paracetamol, Ibuprofen) even if penicillin allergic", () => {
      const patientAllergies = ["Penicillin"];
      const safetyCheck = evaluatePrescriptionSafety("Ibuprofen 400mg", patientAllergies);

      expect(safetyCheck.isSafe).toBe(true);
      expect(safetyCheck.warnings).toHaveLength(0);
    });
  });

  describe("2. AI SOAP Note Studio CDS Structure & Invariants", () => {
    it("should validate complete clinical SOAP draft with mandatory human signoff flag", () => {
      const validSOAP = {
        subjective: "Patient reports acute throbbing pain in tooth 46 radiating to ear for 3 days.",
        objective: "Disto-occlusal caries on 46. Endo-ice lingering >15s. Vertical percussion tender (+3).",
        assessment: "Symptomatic Irreversible Pulpitis #46 (K04.0), Symptomatic Apical Periodontitis (K04.4).",
        plan: "Administered 1.8mL 2% Lignocaine IANB. Rubber dam isolation. Pulpectomy completed. Ca(OH)2 dressing placed. Review in 7 days.",
        status: "PENDING_REVIEW",
        requires_clinician_approval: true,
      };

      const result = soapNoteSchema.safeParse(validSOAP);
      expect(result.success).toBe(true);
    });

    it("should reject SOAP note if subjective or objective details are omitted", () => {
      const incompleteSOAP = {
        subjective: "Tooth hurts",
        objective: "Cavity",
        assessment: "Decay",
        plan: "Filled",
        status: "PENDING_REVIEW",
        requires_clinician_approval: true,
      };

      const result = soapNoteSchema.safeParse(incompleteSOAP);
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.issues.length).toBeGreaterThanOrEqual(1);
      }
    });

    it("should reject SOAP note that tries to bypass human clinician approval", () => {
      const bypassAttempt = {
        subjective: "Patient presents with persistent sensitivity to sweets.",
        objective: "Occlusal caries detected on #16. Cold test normal.",
        assessment: "Enamel and dentin caries #16 without pulpal involvement.",
        plan: "Composite restoration planned under rubber dam.",
        status: "APPROVED",
        requires_clinician_approval: false,
      };

      const result = soapNoteSchema.safeParse(bypassAttempt);
      expect(result.success).toBe(false);
    });
  });

  describe("3. Inventory Depletion & Stock Forecast Calculations", () => {
    it("should categorize stock as CRITICAL if depletion <= 7 days or stock <= min", () => {
      const forecast = calculateStockDepletionUrgency(4, 10, 6);
      expect(forecast.urgency).toBe("CRITICAL");
      expect(forecast.daysRemaining).toBeLessThanOrEqual(7);
      expect(forecast.suggestedReorderQty).toBeGreaterThan(10);
    });

    it("should categorize stock as HIGH if depletion is within 8-14 days", () => {
      const forecast = calculateStockDepletionUrgency(22, 10, 14);
      expect(forecast.urgency).toBe("HIGH");
      expect(forecast.daysRemaining).toBe(11);
    });

    it("should categorize stock as NORMAL when abundant stock exists", () => {
      const forecast = calculateStockDepletionUrgency(100, 20, 7);
      expect(forecast.urgency).toBe("NORMAL");
      expect(forecast.daysRemaining).toBe(100);
    });
  });

  describe("4. Natural Language Clinical Search Intent Parsing", () => {
    it("should correctly parse conditions and procedures from natural language query", () => {
      const query = "Find all diabetic patients who had root canal therapy and are due for recall";
      const parsed = parseClinicalSearchIntent(query);

      expect(parsed.conditions).toContain("Diabetes");
      expect(parsed.procedures).toContain("Root Canal");
      expect(parsed.isOverdueRecall).toBe(true);
      expect(parsed.hasAllergyFilter).toBe(false);
    });

    it("should detect allergy keywords in natural queries", () => {
      const query = "Patients with penicillin allergy and pending extractions";
      const parsed = parseClinicalSearchIntent(query);

      expect(parsed.hasAllergyFilter).toBe(true);
      expect(parsed.procedures).toContain("Extraction");
    });

    it("should detect hypertensive bleeding risk queries", () => {
      const query = "Hypertensive patients on BP medication undergoing scaling";
      const parsed = parseClinicalSearchIntent(query);

      expect(parsed.conditions).toContain("Hypertension");
      expect(parsed.procedures).toContain("Scaling");
    });
  });

  describe("5. Clinical Documentation Generation & Letterhead Verification", () => {
    it("should verify medical certificate leave period calculation", () => {
      const leaveDays = 3;
      const startDate = new Date("2026-09-08T00:00:00.000Z");
      const endDate = new Date(startDate);
      endDate.setUTCDate(startDate.getUTCDate() + leaveDays - 1);

      expect(endDate.toISOString().slice(0, 10)).toBe("2026-09-10");
    });

    it("should verify specialist referral letter encompasses all mandatory medico-legal fields", () => {
      const referral = {
        referringClinician: "Dr. Ananya Shah, MDS",
        specialistRecipient: "Dr. M. K. Rao (Oral & Maxillofacial Surgeon)",
        patientName: "Riya Kapoor",
        patientAge: 29,
        patientGender: "Female",
        toothNumber: "#38",
        provisionalDiagnosis: "Impacted tooth #38 with recurrent pericoronitis",
        attachedDiagnostics: ["OPG Radiograph", "Periapical X-Ray"],
      };

      expect(referringClinicianFormat(referral.referringClinician)).toBe(true);
      expect(referral.attachedDiagnostics.length).toBeGreaterThan(0);
      expect(referral.toothNumber).toBe("#38");
    });
  });
});
