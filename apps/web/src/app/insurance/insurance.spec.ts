import { describe, it, expect } from 'vitest';
import type { ClaimStatus, InsurancePlan, InsuranceCoverageRule } from './types';

// Helper functions mirroring frontend logic
export function calculateProcedureCopay(
  fee: number,
  coveragePercent: number,
  deductibleRemaining: number = 0
): { coveredAmount: number; patientResponsibility: number; deductibleApplied: number } {
  const deductibleApplied = Math.min(fee, deductibleRemaining);
  const subjectToCoinsurance = Math.max(0, fee - deductibleApplied);
  const coveredAmount = Math.round((subjectToCoinsurance * coveragePercent) / 100);
  const patientCoinsurance = subjectToCoinsurance - coveredAmount;
  const patientResponsibility = deductibleApplied + patientCoinsurance;

  return {
    coveredAmount,
    patientResponsibility,
    deductibleApplied,
  };
}

export function isValidClaimStatusTransition(current: ClaimStatus, target: ClaimStatus): boolean {
  const transitions: Record<ClaimStatus, ClaimStatus[]> = {
    DRAFT: ['SUBMITTED', 'CLOSED'],
    SUBMITTED: ['PENDING', 'ADDITIONAL_INFO_REQUESTED', 'APPROVED', 'PARTIALLY_APPROVED', 'REJECTED'],
    PENDING: ['ADDITIONAL_INFO_REQUESTED', 'APPROVED', 'PARTIALLY_APPROVED', 'REJECTED'],
    ADDITIONAL_INFO_REQUESTED: ['SUBMITTED', 'PENDING', 'APPROVED', 'REJECTED'],
    APPROVED: ['PAID', 'CLOSED'],
    PARTIALLY_APPROVED: ['PAID', 'APPEALED', 'CLOSED'],
    REJECTED: ['APPEALED', 'CLOSED'],
    PAID: ['CLOSED'],
    CLOSED: [],
    APPEALED: ['PENDING', 'APPROVED', 'REJECTED'],
  };

  return transitions[current]?.includes(target) ?? false;
}

export function isPreAuthRequired(
  procedureCode: string,
  procedureCost: number,
  plan: InsurancePlan,
  rules: InsuranceCoverageRule[] = []
): boolean {
  const matchedRule = rules.find((r) => r.procedure_code.toUpperCase() === procedureCode.toUpperCase());
  if (matchedRule) {
    if (matchedRule.requires_preauth || matchedRule.coverage_status === 'PREAUTH_REQUIRED') {
      return true;
    }
  }

  if (plan.requires_preauth_above && procedureCost > plan.requires_preauth_above) {
    return true;
  }

  return false;
}

export function evaluateClaimCompleteness(
  procedureCodes: string[],
  attachedDocTypes: string[]
): { score: number; missing: string[]; passed: boolean } {
  let score = 100;
  const missing: string[] = [];

  const requiresXray = procedureCodes.some((code) =>
    ['D3330', 'D7210', 'D2740'].includes(code.toUpperCase())
  );
  if (requiresXray && !attachedDocTypes.includes('X_RAY')) {
    score -= 30;
    missing.push('Mandatory pre-operative radiograph (PA/CBCT)');
  }

  if (!attachedDocTypes.includes('TREATMENT_PLAN')) {
    score -= 15;
    missing.push('Itemized clinician treatment plan');
  }

  return {
    score: Math.max(0, score),
    missing,
    passed: score >= 80,
  };
}

describe('Insurance & Claims Domain Logic', () => {
  describe('calculateProcedureCopay', () => {
    it('calculates 80% coverage and 20% patient copay without deductible', () => {
      const result = calculateProcedureCopay(10000, 80, 0);
      expect(result.coveredAmount).toBe(8000);
      expect(result.patientResponsibility).toBe(2000);
      expect(result.deductibleApplied).toBe(0);
    });

    it('calculates 100% coverage with 0 patient copay for preventive services', () => {
      const result = calculateProcedureCopay(2500, 100, 0);
      expect(result.coveredAmount).toBe(2500);
      expect(result.patientResponsibility).toBe(0);
    });

    it('correctly applies deductible before coinsurance calculation', () => {
      // 10000 fee, 1000 deductible remaining, 80% coinsurance
      // Subject to coinsurance: 9000 -> 80% is 7200 covered, 1800 coinsurance
      // Patient total: 1000 deductible + 1800 coinsurance = 2800
      const result = calculateProcedureCopay(10000, 80, 1000);
      expect(result.deductibleApplied).toBe(1000);
      expect(result.coveredAmount).toBe(7200);
      expect(result.patientResponsibility).toBe(2800);
    });

    it('handles excluded procedures (0% coverage)', () => {
      const result = calculateProcedureCopay(5000, 0, 0);
      expect(result.coveredAmount).toBe(0);
      expect(result.patientResponsibility).toBe(5000);
    });
  });

  describe('Claim Status State Transitions', () => {
    it('allows legal forward transitions', () => {
      expect(isValidClaimStatusTransition('DRAFT', 'SUBMITTED')).toBe(true);
      expect(isValidClaimStatusTransition('SUBMITTED', 'APPROVED')).toBe(true);
      expect(isValidClaimStatusTransition('APPROVED', 'PAID')).toBe(true);
      expect(isValidClaimStatusTransition('PAID', 'CLOSED')).toBe(true);
    });

    it('allows transition to REJECTED and subsequently to APPEALED', () => {
      expect(isValidClaimStatusTransition('SUBMITTED', 'REJECTED')).toBe(true);
      expect(isValidClaimStatusTransition('REJECTED', 'APPEALED')).toBe(true);
      expect(isValidClaimStatusTransition('APPEALED', 'APPROVED')).toBe(true);
    });

    it('blocks illegal transitions directly from DRAFT to PAID or CLOSED', () => {
      expect(isValidClaimStatusTransition('DRAFT', 'PAID')).toBe(false);
      expect(isValidClaimStatusTransition('DRAFT', 'APPROVED')).toBe(false);
    });

    it('blocks transitions out of CLOSED terminal state', () => {
      expect(isValidClaimStatusTransition('CLOSED', 'APPROVED')).toBe(false);
      expect(isValidClaimStatusTransition('CLOSED', 'SUBMITTED')).toBe(false);
    });
  });

  describe('Pre-Authorization Requirements', () => {
    const mockPlan: InsurancePlan = {
      id: 'plan-1',
      provider_id: 'prov-1',
      plan_name: 'PPO Gold',
      plan_code: 'GOLD',
      coverage_percentage: 80,
      annual_limit: 50000,
      deductible: 0,
      copay_fixed: 0,
      waiting_period_days: 0,
      requires_preauth_above: 10000,
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    it('triggers preauth when procedure fee exceeds requires_preauth_above limit', () => {
      expect(isPreAuthRequired('D2740', 15000, mockPlan, [])).toBe(true);
      expect(isPreAuthRequired('D0120', 2000, mockPlan, [])).toBe(false);
    });

    it('triggers preauth when procedure code matches rule with requires_preauth=true', () => {
      const customRule: InsuranceCoverageRule = {
        id: 'rule-1',
        plan_id: 'plan-1',
        procedure_code: 'D3330',
        coverage_status: 'PREAUTH_REQUIRED',
        requires_preauth: true,
        waiting_period_days: 0,
        created_at: new Date().toISOString(),
      };

      // Even if fee is below 10,000 threshold, rule mandates preauth
      expect(isPreAuthRequired('D3330', 8000, mockPlan, [customRule])).toBe(true);
    });
  });

  describe('AI Claim Completeness Evaluation', () => {
    it('penalizes claim when missing mandatory x-ray for surgical/endo procedure', () => {
      const result = evaluateClaimCompleteness(['D3330'], ['TREATMENT_PLAN']);
      expect(result.passed).toBe(false);
      expect(result.score).toBe(70);
      expect(result.missing).toContain('Mandatory pre-operative radiograph (PA/CBCT)');
    });

    it('passes audit when both x-ray and treatment plan are present', () => {
      const result = evaluateClaimCompleteness(['D3330'], ['TREATMENT_PLAN', 'X_RAY']);
      expect(result.passed).toBe(true);
      expect(result.score).toBe(100);
      expect(result.missing.length).toBe(0);
    });
  });
});