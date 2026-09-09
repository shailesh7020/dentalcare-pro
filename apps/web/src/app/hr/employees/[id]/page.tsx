"use client";

import Link from "next/link";
import { use } from "react";
import { useState } from "react";
import {
  Users,
  ArrowLeft,
  Mail,
  Phone,
  Calendar,
  DollarSign,
  Award,
  ShieldCheck,
  GraduationCap,
  Clock,
  FileText,
  Briefcase,
  AlertTriangle,
} from "lucide-react";
import { HRNav } from "../../nav";

export default function EmployeeDossierPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const [activeTab, setActiveTab] = useState<"PROFILE" | "CREDENTIALS" | "PAYROLL" | "ATTENDANCE" | "DOCS">("PROFILE");

  return (
    <div className="min-h-screen bg-slate-50">
      <HRNav />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Link
          href="/hr/employees"
          className="inline-flex items-center gap-1 text-xs font-semibold text-teal-600 hover:text-teal-700 mb-6"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Employee Directory
        </Link>

        {/* Hero Card */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-2xs mb-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 rounded-2xl bg-teal-600 text-white font-bold text-xl flex items-center justify-center shadow-sm">
                AS
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-xl font-bold text-slate-900">Dr. Ananya Shah</h1>
                  <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                    ACTIVE
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-0.5">
                  Chief Prosthodontist & Clinic Admin · <span className="font-mono text-slate-400">EMP-1001</span>
                </p>
                <div className="flex flex-wrap gap-4 mt-2 text-xs text-slate-600">
                  <span className="inline-flex items-center gap-1"><Mail className="w-3.5 h-3.5 text-slate-400" /> ananya.shah@dentalcare.com</span>
                  <span className="inline-flex items-center gap-1"><Phone className="w-3.5 h-3.5 text-slate-400" /> +91 98201 12345</span>
                  <span className="inline-flex items-center gap-1"><GraduationCap className="w-3.5 h-3.5 text-slate-400" /> MDS (Prosthodontics)</span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="text-right">
                <span className="text-xs text-slate-400 block">Monthly Compensation</span>
                <span className="text-lg font-bold text-slate-900">₹1,40,000</span>
              </div>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex space-x-2 border-t border-slate-100 mt-6 pt-4 text-xs font-semibold">
            <button
              onClick={() => setActiveTab("PROFILE")}
              className={`px-3 py-1.5 rounded-lg transition-colors ${
                activeTab === "PROFILE" ? "bg-teal-50 text-teal-700 border border-teal-200" : "text-slate-500 hover:bg-slate-50"
              }`}
            >
              Staff Profile
            </button>
            <button
              onClick={() => setActiveTab("CREDENTIALS")}
              className={`px-3 py-1.5 rounded-lg transition-colors ${
                activeTab === "CREDENTIALS" ? "bg-teal-50 text-teal-700 border border-teal-200" : "text-slate-500 hover:bg-slate-50"
              }`}
            >
              Doctor Credentials & Licenses
            </button>
            <button
              onClick={() => setActiveTab("PAYROLL")}
              className={`px-3 py-1.5 rounded-lg transition-colors ${
                activeTab === "PAYROLL" ? "bg-teal-50 text-teal-700 border border-teal-200" : "text-slate-500 hover:bg-slate-50"
              }`}
            >
              Payslips & Remuneration
            </button>
            <button
              onClick={() => setActiveTab("ATTENDANCE")}
              className={`px-3 py-1.5 rounded-lg transition-colors ${
                activeTab === "ATTENDANCE" ? "bg-teal-50 text-teal-700 border border-teal-200" : "text-slate-500 hover:bg-slate-50"
              }`}
            >
              Attendance & Leave Ledger
            </button>
            <button
              onClick={() => setActiveTab("DOCS")}
              className={`px-3 py-1.5 rounded-lg transition-colors ${
                activeTab === "DOCS" ? "bg-teal-50 text-teal-700 border border-teal-200" : "text-slate-500 hover:bg-slate-50"
              }`}
            >
              Document Vault
            </button>
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === "PROFILE" && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs">
            <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-2xs space-y-3">
              <h3 className="font-bold text-slate-900 text-sm border-b border-slate-100 pb-2">Employment Information</h3>
              <div className="grid grid-cols-2 gap-2">
                <span className="text-slate-400">Department:</span>
                <span className="font-semibold text-slate-800">Prosthodontics & Implants</span>
                <span className="text-slate-400">Employment Type:</span>
                <span className="font-semibold text-slate-800">Full Time Regular</span>
                <span className="text-slate-400">Date of Joining:</span>
                <span className="font-semibold text-slate-800">10 January 2023</span>
                <span className="text-slate-400">Primary Branch:</span>
                <span className="font-semibold text-slate-800">BrightSmile Flagship Clinic</span>
              </div>
            </div>

            <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-2xs space-y-3">
              <h3 className="font-bold text-slate-900 text-sm border-b border-slate-100 pb-2">Banking & Statutory</h3>
              <div className="grid grid-cols-2 gap-2">
                <span className="text-slate-400">Bank Name:</span>
                <span className="font-semibold text-slate-800">HDFC Bank Ltd.</span>
                <span className="text-slate-400">Account Number:</span>
                <span className="font-mono text-slate-800">•••• •••• 4492</span>
                <span className="text-slate-400">IFSC Code:</span>
                <span className="font-mono text-slate-800">HDFC0001234</span>
                <span className="text-slate-400">Income Tax PAN:</span>
                <span className="font-mono text-slate-800">ABFPS1234K</span>
              </div>
            </div>
          </div>
        )}

        {activeTab === "CREDENTIALS" && (
          <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-2xs text-xs space-y-4">
            <h3 className="font-bold text-slate-900 text-sm">Regulatory Dental Council Registration & CE Points</h3>
            <div className="p-4 bg-teal-50 border border-teal-200 rounded-lg flex items-center justify-between">
              <div>
                <span className="font-bold text-teal-900 block text-sm">Dental Council of India (Maharashtra State)</span>
                <span className="text-teal-700 font-mono">Registration Number: DCI-MH-44821</span>
                <span className="text-teal-600 block text-[11px] mt-0.5">Valid through: 15 April 2027 (Active & Verified)</span>
              </div>
              <span className="px-2.5 py-1 bg-teal-600 text-white font-semibold rounded-lg text-xs">
                Verified
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              <div className="p-3 border border-slate-200 rounded-lg">
                <span className="font-semibold text-slate-800 block">CPR & Basic Life Support (BLS)</span>
                <span className="text-slate-500 text-[11px]">Provider: American Heart Association</span>
                <span className="text-emerald-600 font-semibold block mt-1 text-[11px]">Expires: March 2027</span>
              </div>
              <div className="p-3 border border-slate-200 rounded-lg">
                <span className="font-semibold text-slate-800 block">Radiation Protection & CBCT Safety</span>
                <span className="text-slate-500 text-[11px]">Provider: Atomic Energy Regulatory Board</span>
                <span className="text-emerald-600 font-semibold block mt-1 text-[11px]">Expires: December 2026</span>
              </div>
            </div>
          </div>
        )}

        {activeTab === "PAYROLL" && (
          <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-2xs text-xs space-y-4">
            <h3 className="font-bold text-slate-900 text-sm">Recent Remuneration Records</h3>
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-100 text-slate-400">
                  <th className="py-2">Period</th>
                  <th className="py-2">Basic</th>
                  <th className="py-2">HRA</th>
                  <th className="py-2">Incentive</th>
                  <th className="py-2">Deductions</th>
                  <th className="py-2 font-bold text-slate-700">Net Paid</th>
                  <th className="py-2 text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                <tr>
                  <td className="py-2.5 font-semibold text-slate-800">August 2026</td>
                  <td className="py-2.5">₹1,40,000</td>
                  <td className="py-2.5">₹56,000</td>
                  <td className="py-2.5 text-emerald-600 font-semibold">+₹12,500</td>
                  <td className="py-2.5 text-rose-600">-₹18,200</td>
                  <td className="py-2.5 font-bold text-slate-900">₹1,90,300</td>
                  <td className="py-2.5 text-right"><span className="px-2 py-0.5 rounded-full text-[10px] bg-emerald-50 text-emerald-700 font-bold">PAID</span></td>
                </tr>
                <tr>
                  <td className="py-2.5 font-semibold text-slate-800">July 2026</td>
                  <td className="py-2.5">₹1,40,000</td>
                  <td className="py-2.5">₹56,000</td>
                  <td className="py-2.5 text-emerald-600 font-semibold">+₹10,000</td>
                  <td className="py-2.5 text-rose-600">-₹18,200</td>
                  <td className="py-2.5 font-bold text-slate-900">₹1,87,800</td>
                  <td className="py-2.5 text-right"><span className="px-2 py-0.5 rounded-full text-[10px] bg-emerald-50 text-emerald-700 font-bold">PAID</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        )}

        {activeTab === "ATTENDANCE" && (
          <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-2xs text-xs space-y-4">
            <h3 className="font-bold text-slate-900 text-sm">Leave Balances (2026)</h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-center">
                <span className="text-slate-400 block">Casual Leave</span>
                <span className="text-lg font-bold text-slate-900">8 / 12</span>
                <span className="text-[10px] text-slate-400 block">days left</span>
              </div>
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-center">
                <span className="text-slate-400 block">Sick Leave</span>
                <span className="text-lg font-bold text-slate-900">9 / 10</span>
                <span className="text-[10px] text-slate-400 block">days left</span>
              </div>
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-center">
                <span className="text-slate-400 block">Annual Leave</span>
                <span className="text-lg font-bold text-slate-900">12 / 15</span>
                <span className="text-[10px] text-slate-400 block">days left</span>
              </div>
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-center">
                <span className="text-slate-400 block">Emergency</span>
                <span className="text-lg font-bold text-slate-900">5 / 5</span>
                <span className="text-[10px] text-slate-400 block">days left</span>
              </div>
            </div>
          </div>
        )}

        {activeTab === "DOCS" && (
          <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-2xs text-xs space-y-3">
            <h3 className="font-bold text-slate-900 text-sm">Stored Verified Documents</h3>
            <div className="divide-y divide-slate-100">
              <div className="py-2.5 flex items-center justify-between">
                <div>
                  <span className="font-semibold text-slate-800 block">Employment Contract (Executed)</span>
                  <span className="text-slate-400 text-[11px]">PDF · 1.4 MB · Uploaded Jan 2023</span>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-50 text-emerald-700 font-semibold">VERIFIED</span>
              </div>
              <div className="py-2.5 flex items-center justify-between">
                <div>
                  <span className="font-semibold text-slate-800 block">State Dental Council Certificate</span>
                  <span className="text-slate-400 text-[11px]">PDF · 2.1 MB · Uploaded Jan 2023</span>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-50 text-emerald-700 font-semibold">VERIFIED</span>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
