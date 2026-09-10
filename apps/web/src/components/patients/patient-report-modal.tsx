"use client";

import React, { useEffect, useState } from "react";
import {
  Activity,
  AlertCircle,
  Calendar,
  CheckCircle2,
  Clock,
  Download,
  FileCheck,
  FileDown,
  FileText,
  HeartPulse,
  IndianRupee,
  Mail,
  MessageSquare,
  Pill,
  Printer,
  Receipt,
  Share2,
  ShieldAlert,
  Sparkles,
  Stethoscope,
  User,
  X,
} from "lucide-react";
import { api } from "@/lib/api";

export type ReportSectionKey =
  | "personal_details"
  | "medical_history"
  | "dental_history"
  | "treatment_history"
  | "odontogram"
  | "clinical_notes"
  | "prescriptions"
  | "receipts"
  | "invoices"
  | "payment_history"
  | "next_appointment"
  | "xrays_and_images"
  | "uploaded_documents";

interface SectionConfig {
  key: ReportSectionKey;
  label: string;
  description: string;
  icon: React.ElementType;
}

const REPORT_SECTIONS: SectionConfig[] = [
  {
    key: "personal_details",
    label: "Personal Details",
    description: "Name, ID, Age, Gender, DOB, Blood Group, Contacts",
    icon: User,
  },
  {
    key: "medical_history",
    label: "Medical History",
    description: "Systemic conditions, allergies, current medications",
    icon: HeartPulse,
  },
  {
    key: "dental_history",
    label: "Dental History",
    description: "Chief complaint, previous dental visits, habits",
    icon: Stethoscope,
  },
  {
    key: "treatment_history",
    label: "Treatment History",
    description: "Chronological procedures, diagnoses, treating dentists",
    icon: FileCheck,
  },
  {
    key: "odontogram",
    label: "Odontogram",
    description: "Exact graphical 32-tooth chart with color-coded conditions",
    icon: Activity,
  },
  {
    key: "clinical_notes",
    label: "Clinical Notes",
    description: "Doctor visit findings, notes, and observations",
    icon: FileText,
  },
  {
    key: "prescriptions",
    label: "Prescriptions",
    description: "Active medications, dosage, frequency, and instructions",
    icon: Pill,
  },
  {
    key: "receipts",
    label: "Receipts",
    description: "Payment transaction receipts and references",
    icon: Receipt,
  },
  {
    key: "invoices",
    label: "Invoices",
    description: "Itemized tax invoices, GST breakdowns, balance dues",
    icon: IndianRupee,
  },
  {
    key: "payment_history",
    label: "Payment History",
    description: "Complete ledger of patient payments and refunds",
    icon: Clock,
  },
  {
    key: "next_appointment",
    label: "Next Appointment",
    description: "Upcoming visit date, time, dentist, and instructions",
    icon: Calendar,
  },
  {
    key: "xrays_and_images",
    label: "X-rays & Images",
    description: "Index of periapical radiographs, OPGs, and clinical photos",
    icon: FileDown,
  },
  {
    key: "uploaded_documents",
    label: "Uploaded Documents",
    description: "Signed consent forms and external diagnostic records",
    icon: FileText,
  },
];

interface GeneratedReportMeta {
  report_number: string;
  file_name: string;
  document_id?: string;
  download_url: string;
  patient_name: string;
  patient_phone?: string;
  patient_email?: string;
  clinic_name: string;
  sections_included: string[];
  whatsapp_url?: string;
  whatsapp_message?: string;
}

interface PatientReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  patient: {
    id: string;
    first_name: string;
    last_name: string;
    patient_number: string;
    mobile_number?: string | null;
    email?: string | null;
  };
  onReportSaved?: () => void;
}

export function PatientReportModal({
  isOpen,
  onClose,
  patient,
  onReportSaved,
}: PatientReportModalProps) {
  const [selectedSections, setSelectedSections] = useState<ReportSectionKey[]>(
    REPORT_SECTIONS.map((s) => s.key)
  );
  const [includeWatermark, setIncludeWatermark] = useState<boolean>(false);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [generatedMeta, setGeneratedMeta] = useState<GeneratedReportMeta | null>(
    null
  );
  const [shareFeedback, setShareFeedback] = useState<string | null>(null);
  const [shareError, setShareError] = useState<string | null>(null);
  const [isSendingEmail, setIsSendingEmail] = useState<boolean>(false);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const toggleSection = (key: ReportSectionKey) => {
    setSelectedSections((prev) =>
      prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key]
    );
  };

  const handleSelectAll = () => {
    setSelectedSections(REPORT_SECTIONS.map((s) => s.key));
  };

  const handleDeselectAll = () => {
    setSelectedSections([]);
  };

  // Generate Report
  const handleGenerate = async () => {
    if (selectedSections.length === 0) {
      alert("Please select at least one section to include in the report.");
      return;
    }

    try {
      setIsGenerating(true);
      setShareFeedback(null);
      setShareError(null);

      const res = await api.post<GeneratedReportMeta>(
        `/patients/${patient.id}/reports/generate`,
        {
          sections: selectedSections,
          save_to_documents: true,
          include_watermark: includeWatermark,
        }
      );

      setGeneratedMeta(res.data);
      if (onReportSaved) {
        onReportSaved();
      }
    } catch (err: any) {
      console.error("Failed to generate report:", err);
      alert(
        err.response?.data?.detail ||
          "Failed to generate patient report. Please try again."
      );
    } finally {
      setIsGenerating(false);
    }
  };

  // Download PDF Blob
  const handleDownload = async () => {
    if (!generatedMeta) return;
    try {
      const res = await api.get(`/patients/${patient.id}/reports/download`, {
        params: {
          report_number: generatedMeta.report_number,
          watermark: includeWatermark,
        },
        responseType: "blob",
      });
      const blob = new Blob([res.data as BlobPart], {
        type: "application/pdf",
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.setAttribute("download", generatedMeta.file_name);
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      setShareFeedback(`Downloaded ${generatedMeta.file_name} successfully!`);
    } catch (err) {
      console.error("Download failed:", err);
      alert("Failed to download PDF. Please try again.");
    }
  };

  // Print PDF
  const handlePrint = async () => {
    if (!generatedMeta) return;
    try {
      const res = await api.get(`/patients/${patient.id}/reports/download`, {
        params: {
          report_number: generatedMeta.report_number,
          watermark: includeWatermark,
        },
        responseType: "blob",
      });
      const blob = new Blob([res.data as BlobPart], {
        type: "application/pdf",
      });
      const url = window.URL.createObjectURL(blob);
      const iframe = document.createElement("iframe");
      iframe.style.display = "none";
      iframe.src = url;
      document.body.appendChild(iframe);
      iframe.onload = () => {
        iframe.contentWindow?.print();
      };
    } catch (err) {
      console.error("Print failed:", err);
      alert("Failed to prepare PDF for printing.");
    }
  };

  // Share via WhatsApp
  const handleShareWhatsApp = async () => {
    setShareFeedback(null);
    setShareError(null);

    const phone = patient.mobile_number?.trim();
    if (!phone) {
      setShareError(
        "Patient does not have a registered mobile phone number. Please update their profile."
      );
      return;
    }

    try {
      // Record share audit
      await api.post(`/patients/${patient.id}/reports/share`, {
        delivery_method: "WHATSAPP",
        recipient: phone,
        report_id: generatedMeta?.document_id,
      });

      // Open WhatsApp Web/Mobile
      if (generatedMeta?.whatsapp_url) {
        window.open(generatedMeta.whatsapp_url, "_blank");
      }

      setShareFeedback(
        `WhatsApp opened for ${patient.first_name}! Notice: Remember to attach the saved report PDF (${generatedMeta?.file_name}) directly from the patient's Documents section.`
      );
    } catch (err) {
      console.error("WhatsApp share audit error:", err);
      if (generatedMeta?.whatsapp_url) {
        window.open(generatedMeta.whatsapp_url, "_blank");
      }
    }
  };

  // Share via Email
  const handleShareEmail = async () => {
    setShareFeedback(null);
    setShareError(null);

    const email = patient.email?.trim();
    if (!email) {
      setShareError(
        "Patient does not have a registered email address. Please update their profile."
      );
      return;
    }

    try {
      setIsSendingEmail(true);
      await api.post(`/patients/${patient.id}/reports/share`, {
        delivery_method: "EMAIL",
        recipient: email,
        report_id: generatedMeta?.document_id,
      });
      setShareFeedback(
        `Email successfully dispatched to ${email} with subject "Your Dental Treatment Report".`
      );
    } catch (err: any) {
      console.error("Email share error:", err);
      setShareError(
        err.response?.data?.detail || "Failed to dispatch report via email."
      );
    } finally {
      setIsSendingEmail(false);
    }
  };

  // Reset to Generate Another
  const handleReset = () => {
    setGeneratedMeta(null);
    setShareFeedback(null);
    setShareError(null);
  };

  return (
    <div
      className="fixed inset-0 z-50 bg-slate-950/75 flex items-center justify-center p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto flex flex-col">
        {/* Header */}
        <div className="p-5 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between sticky top-0 bg-white dark:bg-slate-900 z-10">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-teal-50 dark:bg-teal-950/50 text-teal-700 dark:text-teal-400 flex items-center justify-center border border-teal-200 dark:border-teal-800">
              <FileDown className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
                Generate Patient Report
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {patient.first_name} {patient.last_name} ({patient.patient_number})
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6 flex-1">
          {!generatedMeta ? (
            /* STAGE 1: Section Selection */
            <div className="space-y-5">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                    Select Report Sections to Include:
                  </h4>
                  <p className="text-xs text-slate-500">
                    {selectedSections.length} of {REPORT_SECTIONS.length} sections
                    selected
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={handleSelectAll}
                    className="text-xs text-teal-700 dark:text-teal-400 hover:underline font-medium"
                  >
                    Select All
                  </button>
                  <span className="text-slate-300">|</span>
                  <button
                    type="button"
                    onClick={handleDeselectAll}
                    className="text-xs text-slate-500 hover:underline font-medium"
                  >
                    Deselect All
                  </button>
                </div>
              </div>

              {/* Section Checkboxes Matrix */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                {REPORT_SECTIONS.map((sec) => {
                  const isChecked = selectedSections.includes(sec.key);
                  const Icon = sec.icon;
                  return (
                    <label
                      key={sec.key}
                      onClick={() => toggleSection(sec.key)}
                      className={`flex items-start gap-3 p-3 rounded-lg border transition-all cursor-pointer select-none ${
                        isChecked
                          ? "bg-teal-50/50 dark:bg-teal-950/20 border-teal-300 dark:border-teal-700 shadow-2xs"
                          : "bg-slate-50/50 dark:bg-slate-800/40 border-slate-200 dark:border-slate-700 opacity-65 hover:opacity-100"
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => {}} // handled by container onClick
                        className="mt-0.5 rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                      />
                      <div className="space-y-0.5">
                        <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800 dark:text-slate-200">
                          <Icon className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400" />
                          <span>{sec.label}</span>
                        </div>
                        <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-tight">
                          {sec.description}
                        </p>
                      </div>
                    </label>
                  );
                })}
              </div>

              {/* Optional Settings */}
              <div className="pt-2 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between">
                <label className="flex items-center gap-2.5 text-xs text-slate-700 dark:text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={includeWatermark}
                    onChange={(e) => setIncludeWatermark(e.target.checked)}
                    className="rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                  />
                  <span>
                    Apply subtle confidential watermark across PDF pages
                  </span>
                </label>
                <span className="text-[11px] text-slate-400">
                  Archives to Documents
                </span>
              </div>
            </div>
          ) : (
            /* STAGE 2: Report Generated Success & Sharing Actions */
            <div className="space-y-6">
              {/* Success Banner */}
              <div className="p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <h4 className="text-sm font-bold text-emerald-900 dark:text-emerald-200">
                    Patient Report Generated Successfully!
                  </h4>
                  <p className="text-xs text-emerald-800 dark:text-emerald-300 font-mono">
                    {generatedMeta.file_name} &bull; {generatedMeta.report_number}
                  </p>
                  <p className="text-xs text-emerald-700 dark:text-emerald-400">
                    Automatically archived to the patient's Documents section.
                  </p>
                </div>
              </div>

              {/* Alerts / Feedback */}
              {shareError && (
                <div className="p-3.5 rounded-lg bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 flex items-center gap-2 text-xs text-rose-700 dark:text-rose-300">
                  <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
                  <span>{shareError}</span>
                </div>
              )}

              {shareFeedback && (
                <div className="p-3.5 rounded-lg bg-teal-50 dark:bg-teal-950/40 border border-teal-200 dark:border-teal-800 flex items-center gap-2 text-xs text-teal-800 dark:text-teal-200">
                  <Sparkles className="w-4 h-4 shrink-0 text-teal-600" />
                  <span>{shareFeedback}</span>
                </div>
              )}

              {/* Primary Output Actions */}
              <div className="space-y-2">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Actions & Delivery Options:
                </span>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
                  {/* Download PDF */}
                  <button
                    type="button"
                    onClick={handleDownload}
                    className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 hover:border-blue-500 bg-white dark:bg-slate-800/80 hover:bg-blue-50/50 dark:hover:bg-blue-950/30 transition-all flex flex-col items-center justify-center gap-2 text-slate-800 dark:text-slate-200 group"
                  >
                    <div className="p-2 bg-blue-50 dark:bg-blue-950/50 text-blue-600 rounded-lg group-hover:scale-110 transition-transform">
                      <Download className="w-5 h-5" />
                    </div>
                    <span className="text-xs font-bold">Download PDF</span>
                    <span className="text-[10px] text-slate-400">
                      Save to computer
                    </span>
                  </button>

                  {/* Print */}
                  <button
                    type="button"
                    onClick={handlePrint}
                    className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 hover:border-slate-400 bg-white dark:bg-slate-800/80 hover:bg-slate-100/50 dark:hover:bg-slate-700/30 transition-all flex flex-col items-center justify-center gap-2 text-slate-800 dark:text-slate-200 group"
                  >
                    <div className="p-2 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 rounded-lg group-hover:scale-110 transition-transform">
                      <Printer className="w-5 h-5" />
                    </div>
                    <span className="text-xs font-bold">Print</span>
                    <span className="text-[10px] text-slate-400">
                      Clinical printer
                    </span>
                  </button>

                  {/* Save to Folder */}
                  <button
                    type="button"
                    onClick={handleDownload}
                    className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 hover:border-amber-500 bg-white dark:bg-slate-800/80 hover:bg-amber-50/50 dark:hover:bg-amber-950/30 transition-all flex flex-col items-center justify-center gap-2 text-slate-800 dark:text-slate-200 group"
                  >
                    <div className="p-2 bg-amber-50 dark:bg-amber-950/50 text-amber-600 rounded-lg group-hover:scale-110 transition-transform">
                      <FileDown className="w-5 h-5" />
                    </div>
                    <span className="text-xs font-bold">Save to Folder</span>
                    <span className="text-[10px] text-slate-400">
                      Export A4 copy
                    </span>
                  </button>
                </div>
              </div>

              {/* Sharing Channels: WhatsApp & Email */}
              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 space-y-3">
                <span className="text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                  <Share2 className="w-4 h-4 text-teal-600" />
                  Instant Direct Sharing with Patient:
                </span>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  {/* WhatsApp Button */}
                  <button
                    type="button"
                    onClick={handleShareWhatsApp}
                    className="inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-lg shadow-sm transition-colors"
                  >
                    <MessageSquare className="w-4 h-4" />
                    Share on WhatsApp
                  </button>

                  {/* Email Button */}
                  <button
                    type="button"
                    onClick={handleShareEmail}
                    disabled={isSendingEmail}
                    className="inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-lg shadow-sm transition-colors disabled:opacity-50"
                  >
                    <Mail className="w-4 h-4" />
                    {isSendingEmail ? "Sending Email..." : "Send via Email"}
                  </button>
                </div>

                <div className="text-[11px] text-slate-500 dark:text-slate-400 space-y-1">
                  <p>
                    <b>WhatsApp Target:</b>{" "}
                    {patient.mobile_number || (
                      <span className="text-rose-500 font-semibold">
                        No phone registered
                      </span>
                    )}
                  </p>
                  <p>
                    <b>Email Target:</b>{" "}
                    {patient.email || (
                      <span className="text-amber-500 font-semibold">
                        No email registered
                      </span>
                    )}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between bg-slate-50 dark:bg-slate-900 sticky bottom-0">
          {!generatedMeta ? (
            <>
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-xs font-semibold text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleGenerate}
                disabled={isGenerating || selectedSections.length === 0}
                className="inline-flex items-center gap-2 px-5 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-lg shadow-sm transition-colors disabled:opacity-50"
              >
                <FileDown className="w-4 h-4" />
                {isGenerating
                  ? "Compiling Medical Report..."
                  : "Generate Patient Report"}
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                onClick={handleReset}
                className="px-3 py-1.5 text-xs font-medium text-slate-600 dark:text-slate-400 hover:underline"
              >
                ← Generate Another Report
              </button>
              <button
                type="button"
                onClick={onClose}
                className="px-5 py-2 bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 text-xs font-bold rounded-lg hover:opacity-90 transition-opacity"
              >
                Done
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
