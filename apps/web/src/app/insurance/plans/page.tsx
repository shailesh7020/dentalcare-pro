"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ListTree,
  Plus,
  Building2,
  Percent,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  X,
} from "lucide-react";
import { api } from "@/lib/api";
import { InsuranceNav } from "../nav";
import type { InsurancePlan, InsuranceProvider, InsuranceCoverageRule } from "../types";

export default function InsurancePlansPage() {
  const queryClient = useQueryClient();
  const [selectedProviderId, setSelectedProviderId] = useState<string>("");
  const [isPlanModalOpen, setIsPlanModalOpen] = useState(false);
  const [isRuleModalOpen, setIsRuleModalOpen] = useState(false);
  const [selectedPlanForRules, setSelectedPlanForRules] = useState<string | null>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        if (isPlanModalOpen) setIsPlanModalOpen(false);
        if (isRuleModalOpen) setIsRuleModalOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isPlanModalOpen, isRuleModalOpen]);

  // New Plan State
  const [planName, setPlanName] = useState("");
  const [planCode, setPlanCode] = useState("");
  const [coveragePercentage, setCoveragePercentage] = useState(80);
  const [annualLimit, setAnnualLimit] = useState(25000);
  const [deductible, setDeductible] = useState(0);
  const [copayFixed, setCopayFixed] = useState(0);
  const [waitingDays, setWaitingDays] = useState(0);
  const [preauthAbove, setPreauthAbove] = useState(10000);

  // New Rule State
  const [ruleCode, setRuleCode] = useState("");
  const [ruleCategory, setRuleCategory] = useState("Restorative");
  const [ruleStatus, setRuleStatus] = useState<"COVERED" | "PARTIALLY_COVERED" | "EXCLUDED" | "PREAUTH_REQUIRED">("COVERED");
  const [rulePercentage, setRulePercentage] = useState(80);
  const [ruleRequiresPreauth, setRuleRequiresPreauth] = useState(false);

  // Fetch Providers
  const { data: providers = [] } = useQuery<InsuranceProvider[]>({
    queryKey: ["insurance-providers"],
    queryFn: async () => {
      const res = await api.get<InsuranceProvider[]>("/insurance/providers");
      return res.data;
    },
  });

  // Set default provider when loaded
  const currentProviderId = selectedProviderId || (providers[0]?.id ?? "");

  // Fetch Plans for current provider
  const { data: plans = [], isLoading } = useQuery<InsurancePlan[]>({
    queryKey: ["insurance-plans", currentProviderId],
    enabled: !!currentProviderId,
    queryFn: async () => {
      const res = await api.get<InsurancePlan[]>("/insurance/plans", {
        params: { provider_id: currentProviderId },
      });
      return res.data;
    },
  });

  // Plan creation
  const createPlanMutation = useMutation({
    mutationFn: async () => {
      await api.post("/insurance/plans", {
        provider_id: currentProviderId,
        plan_name: planName,
        plan_code: planCode,
        coverage_percentage: Number(coveragePercentage),
        annual_limit: annualLimit ? Number(annualLimit) : null,
        deductible: Number(deductible),
        copay_fixed: Number(copayFixed),
        waiting_period_days: Number(waitingDays),
        requires_preauth_above: preauthAbove ? Number(preauthAbove) : null,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["insurance-plans", currentProviderId] });
      setIsPlanModalOpen(false);
      resetPlanForm();
    },
  });

  // Rule creation
  const createRuleMutation = useMutation({
    mutationFn: async () => {
      if (!selectedPlanForRules) return;
      await api.post(`/insurance/plans/${selectedPlanForRules}/coverage-rules`, {
        plan_id: selectedPlanForRules,
        procedure_code: ruleCode,
        procedure_category: ruleCategory,
        coverage_status: ruleStatus,
        coverage_percentage: Number(rulePercentage),
        requires_preauth: ruleRequiresPreauth,
        waiting_period_days: 0,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["insurance-plans", currentProviderId] });
      setIsRuleModalOpen(false);
      setRuleCode("");
    },
  });

  const resetPlanForm = () => {
    setPlanName("");
    setPlanCode("");
    setCoveragePercentage(80);
    setAnnualLimit(25000);
    setDeductible(0);
    setCopayFixed(0);
    setWaitingDays(0);
    setPreauthAbove(10000);
  };

  return (
    <div className="min-h-screen bg-slate-50/50">
      <InsuranceNav />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Insurance Plans & Coverage Rules</h1>
            <p className="text-sm text-slate-600 mt-1">
              Configure coverage percentages, deductibles, copayments, and procedure-level adjudication rules.
            </p>
          </div>
          <button
            onClick={() => setIsPlanModalOpen(true)}
            disabled={!currentProviderId}
            className="inline-flex items-center gap-2 px-4 py-2 bg-teal-600 text-white rounded-lg text-sm font-semibold hover:bg-teal-700 shadow-sm transition-colors disabled:opacity-50 cursor-pointer"
          >
            <Plus className="w-4 h-4" /> Create Insurance Plan
          </button>
        </div>

        {/* Payer Selector */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-col sm:flex-row items-center gap-3">
          <Building2 className="w-5 h-5 text-teal-600 shrink-0" />
          <span className="text-xs font-semibold text-slate-700 whitespace-nowrap">Select Provider:</span>
          <select
            value={currentProviderId}
            onChange={(e) => setSelectedProviderId(e.target.value)}
            className="w-full sm:w-80 text-xs border border-slate-300 rounded-md p-2 bg-white text-slate-800 focus:ring-2 focus:ring-teal-500 focus:outline-none"
          >
            {providers.map((p) => (
              <option key={p.id} value={p.id}>
                {p.provider_name} ({p.provider_code})
              </option>
            ))}
          </select>
        </div>

        {/* Plans List */}
        {isLoading ? (
          <div className="text-center py-12 text-slate-500 text-sm">Loading plans...</div>
        ) : plans.length === 0 ? (
          <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
            <ListTree className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <h3 className="text-base font-semibold text-slate-800">No insurance plans configured</h3>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              Create a plan for this provider to set procedure coverage rates, annual maximums, and pre-auth limits.
            </p>
            <button
              onClick={() => setIsPlanModalOpen(true)}
              className="mt-4 inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-teal-700 bg-teal-50 border border-teal-200 rounded-lg hover:bg-teal-100"
            >
              <Plus className="w-3.5 h-3.5" /> Create Plan
            </button>
          </div>
        ) : (
          <div className="space-y-6">
            {plans.map((plan) => (
              <div
                key={plan.id}
                className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-lg font-bold text-slate-900">{plan.plan_name}</h3>
                      <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                        {plan.plan_code}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Standard Coverage Rate: <span className="font-semibold text-teal-700">{plan.coverage_percentage}%</span>
                    </p>
                  </div>
                  <button
                    onClick={() => {
                      setSelectedPlanForRules(plan.id);
                      setIsRuleModalOpen(true);
                    }}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-teal-700 bg-teal-50 hover:bg-teal-100 border border-teal-200 rounded-lg transition-colors cursor-pointer"
                  >
                    <Plus className="w-3.5 h-3.5" /> Add Procedure Coverage Rule
                  </button>
                </div>

                {/* Plan Limits Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 bg-slate-50/70 p-3 rounded-lg text-xs">
                  <div>
                    <span className="text-slate-400 block">Annual Limit</span>
                    <span className="font-semibold text-slate-800">
                      {plan.annual_limit ? `₹${plan.annual_limit.toLocaleString()}` : "Unlimited"}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block">Deductible</span>
                    <span className="font-semibold text-slate-800">₹{plan.deductible}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block">Fixed Co-pay</span>
                    <span className="font-semibold text-slate-800">₹{plan.copay_fixed}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block">Waiting Period</span>
                    <span className="font-semibold text-slate-800">{plan.waiting_period_days} days</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block">Pre-Auth Threshold</span>
                    <span className="font-semibold text-amber-700">
                      {plan.requires_preauth_above ? `> ₹${plan.requires_preauth_above.toLocaleString()}` : "None"}
                    </span>
                  </div>
                </div>

                {/* Procedure Rules Subtable */}
                <div>
                  <h4 className="text-xs font-semibold text-slate-700 mb-2">Procedure Specific Rules</h4>
                  {plan.coverage_rules && plan.coverage_rules.length > 0 ? (
                    <div className="overflow-x-auto">
                      <table className="w-full text-xs text-left">
                        <thead className="bg-slate-50 text-slate-600 font-semibold border-y border-slate-200">
                          <tr>
                            <th className="py-2 px-3">Procedure Code</th>
                            <th className="py-2 px-3">Category</th>
                            <th className="py-2 px-3">Status</th>
                            <th className="py-2 px-3">Coverage %</th>
                            <th className="py-2 px-3">Pre-Auth Required</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {plan.coverage_rules.map((rule) => (
                            <tr key={rule.id} className="hover:bg-slate-50/50">
                              <td className="py-2 px-3 font-mono font-medium text-slate-800">{rule.procedure_code}</td>
                              <td className="py-2 px-3 text-slate-600">{rule.procedure_category || "General"}</td>
                              <td className="py-2 px-3">
                                <span
                                  className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold ${
                                    rule.coverage_status === "COVERED"
                                      ? "bg-emerald-50 text-emerald-700"
                                      : rule.coverage_status === "EXCLUDED"
                                      ? "bg-rose-50 text-rose-700"
                                      : "bg-amber-50 text-amber-700"
                                  }`}
                                >
                                  {rule.coverage_status}
                                </span>
                              </td>
                              <td className="py-2 px-3 font-medium text-slate-800">
                                {rule.coverage_percentage !== null ? `${rule.coverage_percentage}%` : "—"}
                              </td>
                              <td className="py-2 px-3">
                                {rule.requires_preauth ? (
                                  <span className="text-amber-700 font-semibold flex items-center gap-1">
                                    <AlertTriangle className="w-3.5 h-3.5" /> Mandatory
                                  </span>
                                ) : (
                                  <span className="text-slate-400">No</span>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="text-xs text-slate-400 italic">
                      No custom rules added. All standard dental procedures fall back to {plan.coverage_percentage}% coverage.
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Modal: Create Plan */}
        {isPlanModalOpen && (
          <div 
            className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/75 p-4 overflow-y-auto"
            onClick={(e) => {
              if (e.target === e.currentTarget) setIsPlanModalOpen(false);
            }}
          >
            <div className="bg-white dark:bg-slate-900 rounded-xl shadow-2xl border border-slate-200 dark:border-slate-800 w-full max-w-lg max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-800">
                <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">Add Plan for Selected Payer</h3>
                <button onClick={() => setIsPlanModalOpen(false)} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300">
                  <X className="w-5 h-5" />
                </button>
              </div>
              <div className="p-6 space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="col-span-2">
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Plan Name *</label>
                    <input
                      type="text"
                      placeholder="e.g. Comprehensive Dental PPO"
                      value={planName}
                      onChange={(e) => setPlanName(e.target.value)}
                      className="w-full text-xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-md p-2 focus:ring-2 focus:ring-teal-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Plan Code *</label>
                    <input
                      type="text"
                      placeholder="e.g. PPO-GOLD"
                      value={planCode}
                      onChange={(e) => setPlanCode(e.target.value)}
                      className="w-full text-xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-md p-2 focus:ring-2 focus:ring-teal-500 focus:outline-none uppercase"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Coverage Rate (%) *</label>
                    <input
                      type="number"
                      value={coveragePercentage}
                      onChange={(e) => setCoveragePercentage(Number(e.target.value))}
                      className="w-full text-xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-md p-2 focus:ring-2 focus:ring-teal-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Annual Limit (₹)</label>
                    <input
                      type="number"
                      value={annualLimit}
                      onChange={(e) => setAnnualLimit(Number(e.target.value))}
                      className="w-full text-xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-md p-2 focus:ring-2 focus:ring-teal-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Deductible (₹)</label>
                    <input
                      type="number"
                      value={deductible}
                      onChange={(e) => setDeductible(Number(e.target.value))}
                      className="w-full text-xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-md p-2 focus:ring-2 focus:ring-teal-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Fixed Co-pay (₹)</label>
                    <input
                      type="number"
                      value={copayFixed}
                      onChange={(e) => setCopayFixed(Number(e.target.value))}
                      className="w-full text-xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-md p-2 focus:ring-2 focus:ring-teal-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Pre-Auth Above (₹)</label>
                    <input
                      type="number"
                      value={preauthAbove}
                      onChange={(e) => setPreauthAbove(Number(e.target.value))}
                      className="w-full text-xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-md p-2 focus:ring-2 focus:ring-teal-500 focus:outline-none"
                    />
                  </div>
                </div>
              </div>
              <div className="px-6 py-3 bg-slate-50 dark:bg-slate-800/60 border-t border-slate-200 dark:border-slate-800 flex justify-end gap-2">
                <button
                  onClick={() => setIsPlanModalOpen(false)}
                  className="px-3 py-1.5 text-xs font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-800 rounded-md transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={() => createPlanMutation.mutate()}
                  disabled={!planName || !planCode || createPlanMutation.isPending}
                  className="px-4 py-1.5 text-xs font-semibold text-white bg-teal-600 hover:bg-teal-700 rounded-md shadow-sm disabled:opacity-50 cursor-pointer transition-colors"
                >
                  {createPlanMutation.isPending ? "Creating..." : "Save Plan"}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Modal: Add Coverage Rule */}
        {isRuleModalOpen && (
          <div 
            className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/75 p-4 overflow-y-auto"
            onClick={(e) => {
              if (e.target === e.currentTarget) setIsRuleModalOpen(false);
            }}
          >
            <div className="bg-white dark:bg-slate-900 rounded-xl shadow-2xl border border-slate-200 dark:border-slate-800 w-full max-w-md max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-800">
                <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">Add Procedure Coverage Rule</h3>
                <button onClick={() => setIsRuleModalOpen(false)} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300">
                  <X className="w-5 h-5" />
                </button>
              </div>
              <div className="p-6 space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">CDT Procedure Code *</label>
                  <input
                    type="text"
                    placeholder="e.g. D3330 (Molar Root Canal)"
                    value={ruleCode}
                    onChange={(e) => setRuleCode(e.target.value)}
                    className="w-full text-xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-md p-2 focus:ring-2 focus:ring-teal-500 focus:outline-none uppercase"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Category</label>
                  <input
                    type="text"
                    placeholder="Endodontics / Restorative / Surgical"
                    value={ruleCategory}
                    onChange={(e) => setRuleCategory(e.target.value)}
                    className="w-full text-xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-md p-2 focus:ring-2 focus:ring-teal-500 focus:outline-none"
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Status</label>
                    <select
                      value={ruleStatus}
                      onChange={(e) => setRuleStatus(e.target.value as any)}
                      className="w-full text-xs border border-slate-300 dark:border-slate-700 rounded-md p-2 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100"
                    >
                      <option value="COVERED">Covered</option>
                      <option value="PARTIALLY_COVERED">Partially Covered</option>
                      <option value="EXCLUDED">Excluded (0%)</option>
                      <option value="PREAUTH_REQUIRED">Pre-Auth Required</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">Coverage (%)</label>
                    <input
                      type="number"
                      value={rulePercentage}
                      onChange={(e) => setRulePercentage(Number(e.target.value))}
                      className="w-full text-xs border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-md p-2"
                    />
                  </div>
                </div>
                <div className="flex items-center gap-2 pt-2">
                  <input
                    type="checkbox"
                    id="reqPreauth"
                    checked={ruleRequiresPreauth}
                    onChange={(e) => setRuleRequiresPreauth(e.target.checked)}
                    className="rounded text-teal-600 focus:ring-teal-500"
                  />
                  <label htmlFor="reqPreauth" className="text-xs font-medium text-slate-700 dark:text-slate-300">
                    Mandatory Pre-Authorization prior to service
                  </label>
                </div>
              </div>
              <div className="px-6 py-3 bg-slate-50 dark:bg-slate-800/60 border-t border-slate-200 dark:border-slate-800 flex justify-end gap-2">
                <button
                  onClick={() => setIsRuleModalOpen(false)}
                  className="px-3 py-1.5 text-xs font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-800 rounded-md transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={() => createRuleMutation.mutate()}
                  disabled={!ruleCode || createRuleMutation.isPending}
                  className="px-4 py-1.5 text-xs font-semibold text-white bg-teal-600 hover:bg-teal-700 rounded-md shadow-sm disabled:opacity-50 cursor-pointer transition-colors"
                >
                  {createRuleMutation.isPending ? "Saving..." : "Save Rule"}
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
