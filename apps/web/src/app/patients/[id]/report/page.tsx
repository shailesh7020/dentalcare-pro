"use client";

import { Suspense, use, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  ArrowLeft,
  Calendar,
  CheckCircle2,
  Clock,
  Download,
  FileCheck,
  FileText,
  HeartPulse,
  Mail,
  MapPin,
  Phone,
  Pill,
  Printer,
  Share2,
  ShieldAlert,
  Sparkles,
  Stethoscope,
  User,
} from "lucide-react";

import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

interface MedicalHistory {
  diabetes: boolean;
  hypertension: boolean;
  cardiac_disease: boolean;
  thyroid: boolean;
  asthma: boolean;
  epilepsy: boolean;
  pregnancy: boolean;
  allergies: string | null;
  current_medications: string | null;
  smoking: boolean;
  tobacco: boolean;
  alcohol: boolean;
  previous_surgeries: string | null;
  infectious_diseases: string | null;
  physician_name: string | null;
  physician_contact: string | null;
  additional_notes: string | null;
}

interface DentalHistory {
  chief_complaint: string | null;
  previous_dental_treatments: string | null;
  brushing_frequency: string | null;
  flossing_habit: boolean;
  tobacco_habit: boolean;
  grinding: boolean;
  jaw_pain: boolean;
  tmj_disorder: boolean;
  sensitivity: boolean;
  bleeding_gums: boolean;
  last_dental_visit: string | null;
  dental_notes: string | null;
}

interface PatientDetail {
  id: string;
  clinic_id: string;
  patient_number: string;
  first_name: string;
  middle_name: string | null;
  last_name: string;
  gender: string;
  blood_group: string | null;
  date_of_birth: string;
  age: number;
  mobile_number: string;
  alternate_mobile: string | null;
  email: string | null;
  address: string | null;
  city: string | null;
  state: string | null;
  country: string;
  pin_code: string | null;
  emergency_contact_name: string | null;
  emergency_contact_number: string | null;
  emergency_contact_relation: string | null;
  medical_history: MedicalHistory | null;
  dental_history: DentalHistory | null;
}

interface TreatmentProcedure {
  id: string;
  procedure_name: string;
  tooth_number?: string | null;
  status?: string;
  cost?: number;
}

interface TreatmentItem {
  id: string;
  treatment_number: string;
  diagnosis: string;
  procedure_performed?: string | null;
  status: string;
  created_at: string;
  dentist?: {
    first_name: string;
    last_name: string;
  } | null;
  procedures?: TreatmentProcedure[];
}

interface PrescriptionItem {
  id: string;
  medicine_name: string;
  strength: string;
  form: string;
  dosage: string;
  frequency: string;
  duration: string;
  timing?: string | null;
  food_instructions?: string | null;
  notes?: string | null;
}

interface PrescriptionItemData {
  id: string;
  prescription_number: string;
  date: string;
  status: string;
  diagnosis: string;
  dentist_name?: string | null;
  items?: PrescriptionItem[];
}

interface AppointmentItem {
  id: string;
  appointment_number: string;
  date: string;
  start_time: string;
  status: string;
  visit_type: string;
  dentist?: {
    first_name: string;
    last_name: string;
  } | null;
  chair?: {
    name: string;
  } | null;
}

function SinglePagePatientReportContent({ id }: { id: string }) {
  const searchParams = useSearchParams();
  const autoPrint = searchParams.get("autoPrint") === "true";
  const [downloading, setDownloading] = useState(false);
  const [sharingWa, setSharingWa] = useState(false);
  const [shareFeedback, setShareFeedback] = useState<string | null>(null);

  // 1. Fetch Patient
  const patientQuery = useQuery<PatientDetail>({
    queryKey: ["patient", id],
    queryFn: async () => {
      const res = await api.get<PatientDetail>(`/patients/${id}`);
      return res.data;
    },
  });

  // 2. Fetch Treatments
  const treatmentsQuery = useQuery<TreatmentItem[]>({
    queryKey: ["patient-treatments", id],
    queryFn: async () => {
      const res = await api.get<TreatmentItem[]>(`/treatments/patient/${id}`);
      return res.data;
    },
  });

  // 3. Fetch Prescriptions
  const prescriptionsQuery = useQuery<PrescriptionItemData[]>({
    queryKey: ["patient-prescriptions", id],
    queryFn: async () => {
      const res = await api.get<PrescriptionItemData[]>(`/prescriptions/patient/${id}`);
      return res.data;
    },
  });

  // 4. Fetch Appointments
  const appointmentsQuery = useQuery<AppointmentItem[]>({
    queryKey: ["patient-appointments", id],
    queryFn: async () => {
      const res = await api.get<AppointmentItem[]>(`/appointments/patient/${id}`);
      return res.data;
    },
  });

  // 5. Fetch Odontogram
  const odontogramQuery = useQuery({
    queryKey: ["patient-odontogram", id],
    queryFn: async () => {
      try {
        const res = await api.get(`/patients/${id}/odontogram`);
        return res.data;
      } catch {
        return null;
      }
    },
  });

  const patient = patientQuery.data;
  const treatments = treatmentsQuery.data || [];
  const prescriptions = prescriptionsQuery.data || [];
  const appointments = appointmentsQuery.data || [];
  const odontogram = odontogramQuery.data;

  // Upcoming appointment
  const nowStr = new Date().toISOString().split("T")[0];
  const upcomingAppointment = appointments.find(
    (a) => a.date >= nowStr && a.status !== "CANCELLED"
  );

  // Auto-print effect when navigated with ?autoPrint=true
  useEffect(() => {
    if (autoPrint && patient && !patientQuery.isLoading && !treatmentsQuery.isLoading) {
      const timer = setTimeout(() => {
        window.print();
      }, 700);
      return () => clearTimeout(timer);
    }
  }, [autoPrint, patient, patientQuery.isLoading, treatmentsQuery.isLoading]);

  // Compile Medical Alert Tags
  const alerts: { text: string; severity: "critical" | "warning" | "info" }[] = [];
  if (patient?.medical_history) {
    const mh = patient.medical_history;
    if (mh.allergies) alerts.push({ text: `ALLERGY: ${mh.allergies}`, severity: "critical" });
    if (mh.cardiac_disease) alerts.push({ text: "Cardiac Condition", severity: "critical" });
    if (mh.pregnancy) alerts.push({ text: "Pregnancy", severity: "critical" });
    if (mh.diabetes) alerts.push({ text: "Diabetic", severity: "warning" });
    if (mh.hypertension) alerts.push({ text: "Hypertensive (High BP)", severity: "warning" });
    if (mh.asthma) alerts.push({ text: "Asthma", severity: "warning" });
    if (mh.epilepsy) alerts.push({ text: "Epilepsy", severity: "warning" });
    if (mh.thyroid) alerts.push({ text: "Thyroid Disorder", severity: "info" });
    if (mh.current_medications)
      alerts.push({ text: `Current Meds: ${mh.current_medications}`, severity: "warning" });
    if (mh.tobacco) alerts.push({ text: "Tobacco Habit", severity: "warning" });
    if (mh.smoking) alerts.push({ text: "Smoker", severity: "warning" });
  }

  // 1-Click Official PDF Download
  const handleDownloadPdf = async () => {
    try {
      setDownloading(true);
      const res = await api.get(`/patients/${id}/reports/download`, {
        responseType: "blob",
      });
      const blob = new Blob([res.data as BlobPart], { type: "application/pdf" });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.setAttribute(
        "download",
        `Clinical_Report_${patient?.patient_number || id}_${new Date().toISOString().slice(0, 10)}.pdf`
      );
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      setShareFeedback("Official PDF downloaded successfully!");
      setTimeout(() => setShareFeedback(null), 4000);
    } catch (err) {
      console.error("PDF download failed:", err);
      alert("Failed to download PDF. Falling back to print view.");
      window.print();
    } finally {
      setDownloading(false);
    }
  };

  // 1-Click WhatsApp Direct Dispatch
  const handleWhatsAppShare = async () => {
    if (!patient?.mobile_number) {
      alert("Patient does not have a registered mobile phone number.");
      return;
    }
    try {
      setSharingWa(true);
      setShareFeedback(null);
      const res = await api.post(`/patients/${id}/reports/share`, {
        delivery_method: "WHATSAPP",
        recipient: patient.mobile_number,
      });
      const data = res.data;
      if (data?.success) {
        setShareFeedback(`Directly sent Clinical Report to ${patient.first_name} via WhatsApp!`);
      } else if (data?.whatsapp_url) {
        window.open(data.whatsapp_url, "_blank");
        setShareFeedback("Opened WhatsApp Web with report preview!");
      } else {
        const cleanPhone = patient.mobile_number.replace(/\D/g, "");
        const msg = encodeURIComponent(
          `Hello ${patient.first_name}, here is your DentalCare Clinical Summary Report (ID: ${patient.patient_number}). Follow-up: ${upcomingAppointment?.date || "As recommended by Dr."}.`
        );
        window.open(`https://wa.me/${cleanPhone}?text=${msg}`, "_blank");
        setShareFeedback("Opened WhatsApp to share report!");
      }
      setTimeout(() => setShareFeedback(null), 5000);
    } catch {
      const cleanPhone = patient.mobile_number.replace(/\D/g, "");
      const msg = encodeURIComponent(
        `Hello ${patient.first_name}, here is your DentalCare Clinical Summary Report (ID: ${patient.patient_number}).`
      );
      window.open(`https://wa.me/${cleanPhone}?text=${msg}`, "_blank");
    } finally {
      setSharingWa(false);
    }
  };

  if (patientQuery.isLoading) {
    return (
      <div className="max-w-4xl mx-auto p-6 space-y-6">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-32 w-full rounded-xl" />
        <Skeleton className="h-48 w-full rounded-xl" />
        <Skeleton className="h-48 w-full rounded-xl" />
      </div>
    );
  }

  if (!patient) {
    return (
      <div className="max-w-md mx-auto p-8 text-center space-y-4">
        <AlertCircle size={40} className="text-rose-500 mx-auto" />
        <h2 className="text-lg font-bold text-slate-800">Patient Not Found</h2>
        <Link
          href="/patients"
          className="inline-flex items-center gap-2 text-xs font-semibold text-teal-700 hover:underline"
        >
          <ArrowLeft size={14} /> Back to Patients Directory
        </Link>
      </div>
    );
  }

  const todayFormatted = new Date().toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });

  return (
    <div className="min-h-screen bg-slate-100/70 text-slate-900 pb-16 print:bg-white print:p-0 print:pb-0">
      {/* ============================================================ */}
      {/* DOCTOR ACTION BAR (Sticky at top, strictly hidden in print)  */}
      {/* ============================================================ */}
      <div className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-xs print:hidden">
        <div className="max-w-4xl mx-auto px-4 py-3 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <Link
              href={`/patients/${id}`}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 bg-slate-50 hover:bg-slate-100 border border-slate-200 px-3 py-1.5 rounded-md transition-colors"
            >
              <ArrowLeft size={14} /> Back to Patient
            </Link>
            <div className="hidden sm:block">
              <span className="text-xs font-bold text-slate-900">
                {patient.first_name} {patient.last_name}
              </span>
              <span className="text-slate-400 text-xs ml-1.5">
                ({patient.patient_number})
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={() => window.print()}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white hover:bg-slate-50 text-slate-700 text-xs font-bold rounded-md border border-slate-300 shadow-2xs transition-colors cursor-pointer"
              title="Print standard A4 Clinical Summary Report"
            >
              <Printer size={13} className="text-slate-700" /> Print Report
            </button>

            <button
              onClick={handleDownloadPdf}
              disabled={downloading}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-teal-700 hover:bg-teal-800 text-white text-xs font-bold rounded-md shadow-2xs disabled:opacity-50 transition-colors cursor-pointer"
              title="Download compiled clinical report PDF"
            >
              <Download size={13} />
              {downloading ? "Preparing PDF..." : "Download PDF"}
            </button>

            <button
              onClick={handleWhatsAppShare}
              disabled={sharingWa}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-md shadow-2xs disabled:opacity-50 transition-colors cursor-pointer"
              title="Dispatch report to patient's WhatsApp"
            >
              <CheckCircle2 size={13} />
              {sharingWa ? "Sending..." : "Send on WhatsApp"}
            </button>
          </div>
        </div>

        {shareFeedback && (
          <div className="max-w-4xl mx-auto px-4 pb-2">
            <div className="p-2 bg-emerald-50 border border-emerald-200 rounded text-xs font-medium text-emerald-800 flex items-center gap-2">
              <CheckCircle2 size={14} className="text-emerald-600 shrink-0" />
              <span>{shareFeedback}</span>
            </div>
          </div>
        )}
      </div>

      {/* ============================================================ */}
      {/* THE SINGLE-PAGE REPORT SHEET (Formatted for Screen & Print)  */}
      {/* ============================================================ */}
      <div className="max-w-4xl mx-auto mt-6 px-4 sm:px-6 print:m-0 print:p-0 print:max-w-none">
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-8 sm:p-10 space-y-6 print:border-none print:shadow-none print:p-4 print:rounded-none">
          {/* 1. CLINIC HEADER / LETTERHEAD */}
          <header className="border-b-2 border-teal-800 pb-5 flex flex-col sm:flex-row sm:items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-teal-700 text-white flex items-center justify-center font-black text-sm">
                  DC
                </div>
                <div>
                  <h1 className="text-xl font-black tracking-tight text-slate-900 uppercase">
                    Family Dental Care & Implant Clinic
                  </h1>
                  <p className="text-xs font-semibold text-teal-800 tracking-wide">
                    Comprehensive Clinical Case Summary & Dental Treatment Report
                  </p>
                </div>
              </div>
              <p className="text-[11px] text-slate-500 mt-1.5">
                Main Road, Near Civil Hospital · Reg. No: DCI-MH-2024-8842 · Tel: +91 98765 43210
              </p>
            </div>

            <div className="text-left sm:text-right text-xs space-y-1">
              <div className="inline-block bg-teal-50 border border-teal-200 text-teal-900 font-mono text-[11px] font-bold px-2 py-0.5 rounded">
                REF: RPT-{patient.patient_number}
              </div>
              <p className="text-slate-500 text-[11px]">
                Date: <span className="font-semibold text-slate-800">{todayFormatted}</span>
              </p>
            </div>
          </header>

          {/* 2. PATIENT DEMOGRAPHIC STRIP */}
          <section className="bg-slate-50 border border-slate-200 rounded-lg p-4 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div>
              <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">
                Patient Name
              </span>
              <span className="font-bold text-slate-900 text-sm">
                {patient.first_name} {patient.last_name}
              </span>
            </div>

            <div>
              <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">
                Patient ID
              </span>
              <span className="font-mono font-bold text-teal-800">
                {patient.patient_number}
              </span>
            </div>

            <div>
              <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">
                Age / Gender / Blood
              </span>
              <span className="font-semibold text-slate-800">
                {patient.age} Yrs · {patient.gender} · {patient.blood_group || "N/A"}
              </span>
            </div>

            <div>
              <span className="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">
                Mobile / Phone
              </span>
              <span className="font-semibold text-slate-800">
                {patient.mobile_number}
              </span>
            </div>
          </section>

          {/* 3. MEDICAL & DRUG ALERTS (HIGH-VISIBILITY SAFETY BANNER) */}
          <section className="break-inside-avoid">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-600 mb-2 flex items-center gap-1.5">
              <HeartPulse size={14} className="text-rose-600" /> Medical & Systemic Health Alerts
            </h2>
            {alerts.length > 0 ? (
              <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg flex flex-wrap gap-2 items-center">
                <ShieldAlert size={16} className="text-rose-700 shrink-0 mr-1" />
                {alerts.map((a, idx) => (
                  <span
                    key={idx}
                    className={`text-xs px-2.5 py-1 rounded-md font-bold ${
                      a.severity === "critical"
                        ? "bg-rose-600 text-white shadow-2xs"
                        : a.severity === "warning"
                        ? "bg-amber-100 text-amber-900 border border-amber-300"
                        : "bg-slate-200 text-slate-800"
                    }`}
                  >
                    {a.text}
                  </span>
                ))}
              </div>
            ) : (
              <div className="p-2.5 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-800 text-xs font-medium flex items-center gap-2">
                <CheckCircle2 size={14} className="text-emerald-600 shrink-0" />
                <span>No known systemic health conditions or drug allergies on record.</span>
              </div>
            )}
          </section>

          {/* 4. CHIEF COMPLAINT & DENTAL HISTORY */}
          <section className="grid grid-cols-1 md:grid-cols-2 gap-4 break-inside-avoid">
            <div className="border border-slate-200 rounded-lg p-3.5 space-y-2">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-600 flex items-center gap-1.5">
                <Stethoscope size={13} className="text-teal-700" /> Chief Complaint & History
              </h3>
              <p className="text-xs text-slate-800 leading-relaxed font-medium">
                {patient.dental_history?.chief_complaint ||
                  "Routine dental examination and follow-up consultation."}
              </p>
              {patient.dental_history?.previous_dental_treatments && (
                <p className="text-[11px] text-slate-500">
                  <span className="font-semibold text-slate-700">Past Dental Work: </span>
                  {patient.dental_history.previous_dental_treatments}
                </p>
              )}
            </div>

            <div className="border border-slate-200 rounded-lg p-3.5 space-y-2">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-600 flex items-center gap-1.5">
                <Activity size={13} className="text-teal-700" /> Dental Examination Findings
              </h3>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-[10px] text-slate-400 block font-bold uppercase">Sensitivity:</span>
                  <span className="font-semibold text-slate-800">
                    {patient.dental_history?.sensitivity ? "⚠️ Present" : "None"}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 block font-bold uppercase">Bleeding Gums:</span>
                  <span className="font-semibold text-slate-800">
                    {patient.dental_history?.bleeding_gums ? "⚠️ Observed" : "Normal"}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 block font-bold uppercase">Brushing:</span>
                  <span className="font-semibold text-slate-800">
                    {patient.dental_history?.brushing_frequency || "Twice daily"}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 block font-bold uppercase">Teeth Grinding:</span>
                  <span className="font-semibold text-slate-800">
                    {patient.dental_history?.grinding ? "⚠️ Bruxisim noted" : "None"}
                  </span>
                </div>
              </div>
            </div>
          </section>

          {/* 5. ODONTOGRAM SUMMARY (TEETH STATUS CHART) */}
          {odontogram?.teeth && (
            <section className="border border-slate-200 rounded-lg p-3.5 break-inside-avoid">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-600 mb-2 flex items-center gap-1.5">
                <Activity size={13} className="text-teal-700" /> Odontogram Tooth Chart Summary
              </h3>
              <div className="flex flex-wrap gap-2">
                {Object.entries(odontogram.teeth as Record<string, any>)
                  .filter(([_, tooth]) => tooth.conditions && tooth.conditions.length > 0)
                  .map(([toothNum, tooth]) => (
                    <span
                      key={toothNum}
                      className="px-2 py-1 bg-slate-100 border border-slate-200 rounded text-xs text-slate-800 font-medium"
                    >
                      <strong className="text-teal-800">#{toothNum}</strong>:{" "}
                      {tooth.conditions.map((c: any) => c.name || c.code || c).join(", ")}
                    </span>
                  ))}
              </div>
            </section>
          )}

          {/* 6. CLINICAL PROCEDURES & TREATMENT HISTORY */}
          <section className="break-inside-avoid">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-600 mb-2 flex items-center gap-1.5">
              <FileCheck size={14} className="text-teal-700" /> Treatment & Clinical Procedures Record
            </h2>
            {treatments.length > 0 ? (
              <div className="border border-slate-200 rounded-lg overflow-hidden">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-100 text-slate-700 font-bold uppercase text-[10px] border-b border-slate-200">
                    <tr>
                      <th className="py-2.5 px-3">Date</th>
                      <th className="py-2.5 px-3">Treatment / Procedure</th>
                      <th className="py-2.5 px-3">Tooth #</th>
                      <th className="py-2.5 px-3">Attending Dentist</th>
                      <th className="py-2.5 px-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-800">
                    {treatments.map((tx) => (
                      <tr key={tx.id} className="hover:bg-slate-50/50">
                        <td className="py-2 px-3 font-mono text-slate-600">
                          {new Date(tx.created_at).toLocaleDateString("en-IN", {
                            day: "2-digit",
                            month: "short",
                            year: "numeric",
                          })}
                        </td>
                        <td className="py-2 px-3">
                          <div className="font-semibold text-slate-900">
                            {tx.diagnosis || tx.procedure_performed || "Dental Procedure"}
                          </div>
                          {tx.procedures && tx.procedures.length > 0 && (
                            <div className="text-[11px] text-teal-800 font-medium mt-0.5">
                              {tx.procedures
                                .map((p) => `${p.procedure_name}${p.tooth_number ? ` (#${p.tooth_number})` : ""}`)
                                .join(", ")}
                            </div>
                          )}
                          {!tx.procedures?.length && tx.procedure_performed && tx.diagnosis && (
                            <div className="text-[11px] text-slate-500 mt-0.5">
                              {tx.procedure_performed}
                            </div>
                          )}
                        </td>
                        <td className="py-2 px-3 font-mono font-medium text-slate-600">
                          {tx.procedures && tx.procedures.length > 0
                            ? tx.procedures
                                .map((p) => p.tooth_number)
                                .filter(Boolean)
                                .join(", ") || "—"
                            : "—"}
                        </td>
                        <td className="py-2 px-3 font-medium text-slate-700">
                          {tx.dentist ? `Dr. ${tx.dentist.first_name} ${tx.dentist.last_name}` : "Attending Dentist"}
                        </td>
                        <td className="py-2 px-3">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              tx.status === "COMPLETED"
                                ? "bg-emerald-100 text-emerald-800"
                                : tx.status === "IN_PROGRESS"
                                ? "bg-blue-100 text-blue-800"
                                : "bg-slate-100 text-slate-700"
                            }`}
                          >
                            {tx.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-500 italic">
                No past treatment procedures recorded.
              </div>
            )}
          </section>

          {/* 7. ACTIVE MEDICATIONS & PRESCRIPTIONS */}
          <section className="break-inside-avoid">
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-600 mb-2 flex items-center gap-1.5">
              <Pill size={14} className="text-teal-700" /> Prescribed Medications (Rx)
            </h2>
            {prescriptions.length > 0 ? (
              <div className="border border-slate-200 rounded-lg overflow-hidden">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-100 text-slate-700 font-bold uppercase text-[10px] border-b border-slate-200">
                    <tr>
                      <th className="py-2.5 px-3">Medication</th>
                      <th className="py-2.5 px-3">Strength & Form</th>
                      <th className="py-2.5 px-3">Dosage & Frequency</th>
                      <th className="py-2.5 px-3">Instructions</th>
                      <th className="py-2.5 px-3">Duration</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-800">
                    {prescriptions.flatMap((rx) =>
                      (rx.items || []).map((item) => (
                        <tr key={item.id} className="hover:bg-slate-50/50">
                          <td className="py-2 px-3 font-bold text-slate-900">
                            {item.medicine_name}
                          </td>
                          <td className="py-2 px-3 text-slate-600">
                            {item.strength} · {item.form}
                          </td>
                          <td className="py-2 px-3 font-semibold text-teal-800">
                            {item.dosage} · {item.frequency}
                          </td>
                          <td className="py-2 px-3 text-slate-700">
                            {item.food_instructions || item.timing || "As directed"}
                          </td>
                          <td className="py-2 px-3 font-medium text-slate-600">
                            {item.duration}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-500 italic">
                No active medications prescribed.
              </div>
            )}
          </section>

          {/* 8. DOCTOR'S ADVICE & UPCOMING APPOINTMENT */}
          <section className="grid grid-cols-1 sm:grid-cols-2 gap-4 break-inside-avoid">
            <div className="border border-slate-200 rounded-lg p-3.5 space-y-1.5">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-600 flex items-center gap-1.5">
                <FileText size={13} className="text-teal-700" /> Post-Operative Advice & Notes
              </h3>
              <ul className="text-xs text-slate-700 space-y-1 list-disc list-inside leading-relaxed">
                <li>Maintain gentle oral hygiene; avoid aggressive brushing over treated teeth.</li>
                <li>Avoid very hot, cold, or hard foods for 24-48 hours.</li>
                <li>Complete the full course of prescribed antibiotics and painkillers.</li>
                <li>Contact the clinic immediately in case of severe pain, swelling, or bleeding.</li>
              </ul>
            </div>

            <div className="border border-slate-200 rounded-lg p-3.5 space-y-2">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-600 flex items-center gap-1.5">
                <Calendar size={13} className="text-teal-700" /> Scheduled Follow-Up / Recall
              </h3>
              {upcomingAppointment ? (
                <div className="p-2.5 bg-teal-50 border border-teal-200 rounded-md text-xs">
                  <p className="font-bold text-teal-950">
                    📅 Next Visit:{" "}
                    {new Date(upcomingAppointment.date).toLocaleDateString("en-IN", {
                      weekday: "short",
                      day: "2-digit",
                      month: "short",
                      year: "numeric",
                    })}{" "}
                    at {upcomingAppointment.start_time}
                  </p>
                  <p className="text-[11px] text-teal-800 mt-0.5">
                    Purpose: {upcomingAppointment.visit_type} · Operatory:{" "}
                    {upcomingAppointment.chair?.name || "General Chair"}
                  </p>
                </div>
              ) : (
                <p className="text-xs text-slate-600 italic">
                  Follow-up advised in 7 days or as scheduled by the doctor.
                </p>
              )}
            </div>
          </section>

          {/* 9. SIGN-OFF BLOCK */}
          <footer className="pt-8 border-t border-slate-200 flex items-end justify-between break-inside-avoid">
            <div className="text-[11px] text-slate-400">
              <p>Generated by DentalCare Pro Clinical Management System</p>
              <p>Document digitally authenticated · Clinic Contact: +91 98765 43210</p>
            </div>

            <div className="text-right space-y-1">
              <div className="w-48 h-12 border-b border-dashed border-slate-400 mb-1 ml-auto" />
              <p className="text-xs font-bold text-slate-900">Dr. Dentist Demo, BDS, MDS</p>
              <p className="text-[11px] text-slate-500">Authorized Dental Surgeon & Reg. Clinician</p>
            </div>
          </footer>
        </div>
      </div>
    </div>
  );
}

export default function SinglePagePatientReport({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);

  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6 text-sm text-slate-500">
          Loading Clinical Report...
        </div>
      }
    >
      <SinglePagePatientReportContent id={id} />
    </Suspense>
  );
}
