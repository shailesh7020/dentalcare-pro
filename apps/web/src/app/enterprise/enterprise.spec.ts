import { describe, it, expect } from "vitest";
import type {
  BranchFinancialSummary,
  InventoryTransferStatus,
  PatientSharingMode,
  TransferStatus,
} from "./types";

// ===========================================================================
// Domain Business Logic Functions
// ===========================================================================

export function calculateConsolidatedRevenue(branchSummaries: BranchFinancialSummary[]): {
  totalInvoiced: number;
  totalCollected: number;
  totalOutstanding: number;
  collectionRate: number;
} {
  const totalInvoiced = branchSummaries.reduce((sum, b) => sum + b.total_invoiced, 0);
  const totalCollected = branchSummaries.reduce((sum, b) => sum + b.total_collected, 0);
  const totalOutstanding = branchSummaries.reduce((sum, b) => sum + b.outstanding_balance, 0);
  const collectionRate = totalInvoiced > 0 ? Math.round((totalCollected / totalInvoiced) * 1000) / 10 : 0;

  return {
    totalInvoiced,
    totalCollected,
    totalOutstanding,
    collectionRate,
  };
}

export function isValidInventoryTransferTransition(
  current: InventoryTransferStatus,
  target: InventoryTransferStatus
): boolean {
  const transitions: Record<InventoryTransferStatus, InventoryTransferStatus[]> = {
    DRAFT: ["DISPATCHED", "CANCELLED"],
    DISPATCHED: ["IN_TRANSIT", "RECEIVED", "REJECTED", "CANCELLED"],
    IN_TRANSIT: ["RECEIVED", "REJECTED"],
    RECEIVED: [],
    REJECTED: [],
    CANCELLED: [],
  };

  return transitions[current]?.includes(target) ?? false;
}

export function isValidPatientTransferTransition(
  current: TransferStatus,
  target: TransferStatus
): boolean {
  const transitions: Record<TransferStatus, TransferStatus[]> = {
    PENDING: ["APPROVED", "REJECTED", "CANCELLED"],
    APPROVED: ["COMPLETED", "CANCELLED"],
    REJECTED: [],
    COMPLETED: [],
    CANCELLED: [],
  };

  return transitions[current]?.includes(target) ?? false;
}

export function calculatePatientDuplicateSimilarity(
  p1: { name: string; phone: string; email?: string },
  p2: { name: string; phone: string; email?: string }
): { score: number; matchedFields: string[] } {
  const matchedFields: string[] = [];
  let score = 0.0;

  const phone1 = p1.phone.replace(/\D/g, "").slice(-10);
  const phone2 = p2.phone.replace(/\D/g, "").slice(-10);
  if (phone1 && phone2 && phone1 === phone2) {
    matchedFields.push("phone");
    score += 0.5;
  }

  if (
    p1.email &&
    p2.email &&
    p1.email.trim().toLowerCase() === p2.email.trim().toLowerCase()
  ) {
    matchedFields.push("email");
    score += 0.35;
  }

  const name1 = p1.name.trim().toLowerCase();
  const name2 = p2.name.trim().toLowerCase();
  if (name1 === name2) {
    matchedFields.push("name");
    score += 0.3;
  } else if (name1.includes(name2) || name2.includes(name1)) {
    matchedFields.push("name_partial");
    score += 0.15;
  }

  return {
    score: Math.min(1.0, Math.round(score * 100) / 100),
    matchedFields,
  };
}

export function calculateBranchBenchmarkEfficiency(
  revenueScore: number,
  occupancyScore: number,
  collectionRateScore: number,
  patientSatisfactionScore: number
): number {
  // 35% revenue, 25% collection, 25% occupancy, 15% satisfaction
  const weighted =
    revenueScore * 0.35 +
    collectionRateScore * 0.25 +
    occupancyScore * 0.25 +
    patientSatisfactionScore * 0.15;
  return Math.round(weighted * 10) / 10;
}

export function resolveUserPermissions(
  role: string,
  overrides: Record<string, boolean>,
  baseRolePermissions: Record<string, string[]>
): string[] {
  if (role === "SUPER_ADMIN" || role === "ORGANIZATION_ADMIN") {
    return ["*"];
  }

  const granted = new Set<string>(baseRolePermissions[role] || []);

  for (const [permKey, isGranted] of Object.entries(overrides)) {
    if (isGranted) {
      granted.add(permKey);
    } else {
      granted.delete(permKey);
    }
  }

  return Array.from(granted).sort();
}

export function calculateForecastGrowth(
  baseMonthlyRevenue: number,
  growthRatePercent: number
): number {
  return Math.round(baseMonthlyRevenue * (1 + growthRatePercent / 100));
}

// ===========================================================================
// Test Suites
// ===========================================================================

describe("Enterprise Multi-Branch Administration", () => {
  describe("Consolidated Financial Rollups", () => {
    it("aggregates branch revenue, collections, and calculates collection rate correctly", () => {
      const summaries: BranchFinancialSummary[] = [
        {
          clinic_id: "c1",
          clinic_name: "Central Clinic",
          total_invoiced: 200000,
          total_collected: 180000,
          insurance_collected: 50000,
          outstanding_balance: 20000,
          tax_amount: 36000,
          invoice_count: 50,
        },
        {
          clinic_id: "c2",
          clinic_name: "Suburban Clinic",
          total_invoiced: 100000,
          total_collected: 80000,
          insurance_collected: 20000,
          outstanding_balance: 20000,
          tax_amount: 18000,
          invoice_count: 25,
        },
      ];

      const res = calculateConsolidatedRevenue(summaries);
      expect(res.totalInvoiced).toBe(300000);
      expect(res.totalCollected).toBe(260000);
      expect(res.totalOutstanding).toBe(40000);
      expect(res.collectionRate).toBe(86.7);
    });

    it("handles zero invoiced amount gracefully", () => {
      const res = calculateConsolidatedRevenue([]);
      expect(res.totalInvoiced).toBe(0);
      expect(res.collectionRate).toBe(0);
    });
  });

  describe("Inventory Transfer State Transitions", () => {
    it("allows valid transitions from DRAFT to DISPATCHED", () => {
      expect(isValidInventoryTransferTransition("DRAFT", "DISPATCHED")).toBe(true);
      expect(isValidInventoryTransferTransition("DRAFT", "CANCELLED")).toBe(true);
    });

    it("prevents skipping directly from DRAFT to RECEIVED", () => {
      expect(isValidInventoryTransferTransition("DRAFT", "RECEIVED")).toBe(false);
    });

    it("allows valid dispatch to receive transition", () => {
      expect(isValidInventoryTransferTransition("DISPATCHED", "RECEIVED")).toBe(true);
      expect(isValidInventoryTransferTransition("DISPATCHED", "IN_TRANSIT")).toBe(true);
    });

    it("does not allow transitions from terminal RECEIVED status", () => {
      expect(isValidInventoryTransferTransition("RECEIVED", "DISPATCHED")).toBe(false);
      expect(isValidInventoryTransferTransition("RECEIVED", "CANCELLED")).toBe(false);
    });
  });

  describe("Patient Transfer State Transitions", () => {
    it("allows valid approval workflow", () => {
      expect(isValidPatientTransferTransition("PENDING", "APPROVED")).toBe(true);
      expect(isValidPatientTransferTransition("PENDING", "REJECTED")).toBe(true);
      expect(isValidPatientTransferTransition("APPROVED", "COMPLETED")).toBe(true);
    });

    it("rejects invalid transitions from terminal REJECTED state", () => {
      expect(isValidPatientTransferTransition("REJECTED", "APPROVED")).toBe(false);
    });
  });

  describe("Cross-Clinic Duplicate Patient Similarity", () => {
    it("detects exact phone and email match with high confidence", () => {
      const p1 = { name: "Rajesh Sharma", phone: "+91 98765 43210", email: "rajesh@example.com" };
      const p2 = { name: "Rajesh Sharma", phone: "9876543210", email: "rajesh@example.com" };

      const match = calculatePatientDuplicateSimilarity(p1, p2);
      expect(match.score).toBe(1.0);
      expect(match.matchedFields).toContain("phone");
      expect(match.matchedFields).toContain("email");
      expect(match.matchedFields).toContain("name");
    });

    it("detects phone match with partial name match", () => {
      const p1 = { name: "Rajesh Kumar Sharma", phone: "+91 98765 43210" };
      const p2 = { name: "Rajesh", phone: "09876543210" };

      const match = calculatePatientDuplicateSimilarity(p1, p2);
      expect(match.score).toBe(0.65);
      expect(match.matchedFields).toContain("phone");
      expect(match.matchedFields).toContain("name_partial");
    });
  });

  describe("AI Branch Benchmark Scoring", () => {
    it("calculates weighted overall score correctly", () => {
      const score = calculateBranchBenchmarkEfficiency(90, 85, 80, 90);
      expect(score).toBe(86.3);
    });
  });

  describe("Enterprise Permission Resolution & Overrides", () => {
    const baseRoles: Record<string, string[]> = {
      DENTIST: ["patient:cross_view", "treatment:perform"],
      RECEPTIONIST: ["patient:transfer", "appointment:book"],
    };

    it("grants wildcard access to SUPER_ADMIN", () => {
      const perms = resolveUserPermissions("SUPER_ADMIN", {}, baseRoles);
      expect(perms).toEqual(["*"]);
    });

    it("applies user-level permission override correctly", () => {
      const perms = resolveUserPermissions(
        "DENTIST",
        { "inventory:transfer": true, "treatment:perform": false },
        baseRoles
      );
      expect(perms).toContain("inventory:transfer");
      expect(perms).toContain("patient:cross_view");
      expect(perms).not.toContain("treatment:perform");
    });
  });

  describe("Revenue Forecasting", () => {
    it("projects forward monthly revenue based on percentage growth", () => {
      const projected = calculateForecastGrowth(4000000, 12);
      expect(projected).toBe(4480000);
    });
  });
});
