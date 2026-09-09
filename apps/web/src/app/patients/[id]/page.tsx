"use client";

import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { use, useRef, useState } from "react";
import {
  AlertTriangle,
  Archive,
  ArrowLeft,
  Calendar,
  CheckCircle2,
  Clock,
  Download,
  Edit2,
  FileCheck,
  FileText,
  HeartPulse,
  Mail,
  MapPin,
  Phone,
  Plus,
  RotateCcw,
  Shield,
  Stethoscope,
  Upload,
  User,
  X,
  Activity,
  Pill,
  IndianRupee,
  Receipt,
  CreditCard,
} from "lucide-react";

import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Dialog } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { BookingModal } from "@/components/appointments/booking-modal";
import { AppointmentDetailDialog } from "@/components/appointments/appointment-detail-dialog";
import { OdontogramCanvas } from "@/components/odontogram/odontogram-canvas";
import { DentitionType, NumberingSystem, PatientOdontogram, Tooth } from "./odontogram/types";

type MedicalHistory = {
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
};

type DentalHistory = {
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
};

type PatientDetail = {
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
  insurance_provider: string | null;
  insurance_policy_number: string | null;
  preferred_language: string;
  photo_url: string | null;
  notes: string | null;
  aadhaar_number: string | null;
  marital_status: string | null;
  occupation: string | null;
  status: "ACTIVE" | "ARCHIVED";
  created_at: string;
  deleted_at: string | null;
  medical_history: MedicalHistory | null;
  dental_history: DentalHistory | null;
};

type TimelineEvent = {
  id: string;
  event_type: string;
  title: string;
  description: string | null;
  created_at: string;
};

type PatientDocument = {
  id: string;
  file_name: string;
  content_type: string;
  document_type: string;
  url: string;
  created_at: string;
};

export default function PatientProfilePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState("overview");
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [isArchiveOpen, setIsArchiveOpen] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadDocType, setUploadDocType] = useState<string>("DOCUMENT");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const patientQuery = useQuery({
    queryKey: ["patient", id],
    queryFn: async () => {
      const res = await api.get<PatientDetail>(`/patients/${id}`);
      return res.data;
    },
  });

  const timelineQuery = useQuery({
    queryKey: ["patient-timeline", id],
    queryFn: async () => {
      const res = await api.get<TimelineEvent[]>(`/patients/${id}/timeline`);
      return res.data;
    },
  });

  const documentsQuery = useQuery({
    queryKey: ["patient-documents", id],
    queryFn: async () => {
      const res = await api.get<PatientDocument[]>(`/patients/${id}/documents`);
      return res.data;
    },
  });

  const [isBookModalOpen, setIsBookModalOpen] = useState(false);
  const [selectedAppointment, setSelectedAppointment] = useState<any | null>(null);

  const appointmentsQuery = useQuery({
    queryKey: ["patient-appointments", id],
    queryFn: async () => {
      const res = await api.get<any[]>(`/appointments/patient/${id}`);
      return res.data;
    },
  });

  const patientTreatmentsQuery = useQuery({
    queryKey: ["patient-treatments", id],
    queryFn: async () => {
      const res = await api.get<any[]>(`/treatments/patient/${id}`);
      return res.data;
    },
  });

  const patientPrescriptionsQuery = useQuery({
    queryKey: ["patient-prescriptions", id],
    queryFn: async () => {
      const res = await api.get<any[]>(`/prescriptions/patient/${id}`);
      return res.data;
    },
  });

  const patientBillingQuery = useQuery({
    queryKey: ["patient-billing-summary", id],
    queryFn: async () => {
      const res = await api.get<any>(`/billing/patient/${id}`);
      return res.data;
    },
  });

  const [dentitionType, setDentitionType] = useState<DentitionType>("ADULT");
  const [numberingSystem, setNumberingSystem] = useState<NumberingSystem>("FDI");
  const [selectedTooth, setSelectedTooth] = useState<Tooth | null>(null);

  const odontogramQuery = useQuery<PatientOdontogram>({
    queryKey: ["odontogram", id, dentitionType],
    queryFn: async () => {
      const res = await api.get(`/patients/${id}/odontogram`, {
        params: { dentition: dentitionType },
      });
      return res.data;
    },
    enabled: Boolean(id),
  });

  const archiveMutation = useMutation({
    mutationFn: async () => {
      await api.delete(`/patients/${id}`);
    },
    onSuccess: () => {
      setIsArchiveOpen(false);
      showToast("Patient record archived.");
      void queryClient.invalidateQueries({ queryKey: ["patient", id] });
    },
  });

  const restoreMutation = useMutation({
    mutationFn: async () => {
      await api.post(`/patients/${id}/restore`);
    },
    onSuccess: () => {
      showToast("Patient record restored to active status.");
      void queryClient.invalidateQueries({ queryKey: ["patient", id] });
    },
  });

  const uploadMutation = useMutation({
    mutationFn: async () => {
      if (!selectedFile) return;
      const formData = new FormData();
      formData.append("file", selectedFile);
      await api.post(`/patients/${id}/documents`, formData, {
        params: { document_type: uploadDocType },
        headers: { "Content-Type": "multipart/form-data" },
      });
    },
    onSuccess: () => {
      setIsUploadOpen(false);
      setSelectedFile(null);
      showToast("Document uploaded successfully.");
      void queryClient.invalidateQueries({ queryKey: ["patient-documents", id] });
      void queryClient.invalidateQueries({ queryKey: ["patient-timeline", id] });
      void queryClient.invalidateQueries({ queryKey: ["patient", id] });
    },
  });

  function showToast(msg: string) {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 4000);
  }

  if (patientQuery.isLoading) {
    return (
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8">
        <Skeleton className="h-6 w-32 mb-4" />
        <Skeleton className="h-44 w-full rounded-lg mb-6" />
        <Skeleton className="h-96 w-full rounded-lg" />
      </main>
    );
  }

  if (patientQuery.isError || !patientQuery.data) {
    return (
      <main className="max-w-4xl mx-auto px-4 py-16 text-center">
        <p className="text-base font-semibold text-rose-600">Patient record is unavailable</p>
        <p className="text-xs text-slate-500 mt-1">The record may not exist or belongs to another clinic.</p>
        <Link href="/patients" className="mt-4 inline-block text-xs font-semibold text-teal-700 underline">
          Back to Patients Directory
        </Link>
      </main>
    );
  }

  const patient = patientQuery.data;
  const isArchived = Boolean(patient.deleted_at);
  const fullName = [patient.first_name, patient.middle_name, patient.last_name].filter(Boolean).join(" ");
  const initials = [patient.first_name[0], patient.last_name[0]].filter(Boolean).join("").toUpperCase();

  // Highlight high-risk medical alerts
  const med = patient.medical_history;
  const criticalConditions = [
    med?.cardiac_disease && "Cardiac Disease",
    med?.hypertension && "Hypertension / High BP",
    med?.diabetes && "Diabetes",
    med?.asthma && "Asthma",
    med?.epilepsy && "Epilepsy",
    med?.pregnancy && "Pregnancy",
    med?.allergies && `Allergies: ${med.allergies}`,
  ].filter(Boolean) as string[];

  return (
    <main className="min-h-screen bg-slate-50/60 pb-24">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed top-6 right-6 z-50 flex items-center gap-2.5 px-4 py-3 bg-emerald-900 text-emerald-50 rounded-lg shadow-lg border border-emerald-700 animate-in slide-in-from-top duration-300">
          <CheckCircle2 size={18} className="text-emerald-400" />
          <span className="text-sm font-medium">{toastMessage}</span>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8">
        {/* Top Breadcrumb */}
        <div className="mb-4">
          <Link
            href="/patients"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-teal-700 hover:text-teal-800"
          >
            <ArrowLeft size={14} /> Back to Patients Directory
          </Link>
        </div>

        {/* Profile Header Card */}
        <section className="bg-white rounded-lg border border-slate-200 shadow-xs p-6 mb-6">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
            {/* Avatar & Identifiers */}
            <div className="flex items-center gap-4">
              {patient.photo_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={patient.photo_url}
                  alt={fullName}
                  className="w-16 h-16 rounded-full object-cover border-2 border-teal-600"
                />
              ) : (
                <div className="w-16 h-16 rounded-full bg-teal-100 text-teal-800 flex items-center justify-center font-bold text-xl border-2 border-teal-300">
                  {initials}
                </div>
              )}
              <div>
                <div className="flex items-center gap-2.5 flex-wrap">
                  <h1 className="text-2xl font-bold text-slate-900">{fullName}</h1>
                  <Badge variant="secondary" className="font-mono text-xs">
                    {patient.patient_number}
                  </Badge>
                  {isArchived ? (
                    <Badge variant="archived">Archived Record</Badge>
                  ) : (
                    <Badge variant="active">Active Patient</Badge>
                  )}
                  {patient.blood_group && (
                    <Badge variant="outline" className="font-semibold text-slate-700">
                      {patient.blood_group}
                    </Badge>
                  )}
                </div>

                <div className="flex items-center gap-4 text-xs text-slate-500 mt-2 flex-wrap">
                  <span>{patient.age} years old</span>
                  <span>·</span>
                  <span className="capitalize">{patient.gender.toLowerCase().replaceAll("_", " ")}</span>
                  <span>·</span>
                  <span className="flex items-center gap-1 font-mono text-slate-700">
                    <Phone size={12} className="text-slate-400" /> {patient.mobile_number}
                  </span>
                  {patient.email && (
                    <>
                      <span>·</span>
                      <span className="flex items-center gap-1">
                        <Mail size={12} className="text-slate-400" /> {patient.email}
                      </span>
                    </>
                  )}
                  {patient.city && (
                    <>
                      <span>·</span>
                      <span className="flex items-center gap-1">
                        <MapPin size={12} className="text-slate-400" /> {patient.city}
                      </span>
                    </>
                  )}
                </div>
              </div>
            </div>

            {/* Header Action Buttons */}
            <div className="flex items-center gap-2.5 w-full md:w-auto justify-end">
              {!isArchived && (
                <Link
                  href={`/patients/${id}/edit`}
                  className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 font-semibold text-xs rounded-md shadow-2xs"
                >
                  <Edit2 size={13} /> Edit Profile
                </Link>
              )}
              <button
                onClick={() => setIsUploadOpen(true)}
                className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 font-semibold text-xs rounded-md shadow-2xs"
              >
                <Upload size={13} /> Upload File
              </button>
              {isArchived ? (
                <button
                  onClick={() => restoreMutation.mutate()}
                  disabled={restoreMutation.isPending}
                  className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-emerald-700 hover:bg-emerald-800 text-white font-semibold text-xs rounded-md shadow-2xs disabled:opacity-50"
                >
                  <RotateCcw size={13} /> Restore Patient
                </button>
              ) : (
                <button
                  onClick={() => setIsArchiveOpen(true)}
                  className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 font-semibold text-xs rounded-md"
                >
                  <Archive size={13} /> Archive
                </button>
              )}
            </div>
          </div>

          {/* Critical Medical Warning Bar if applicable */}
          {criticalConditions.length > 0 && (
            <div className="mt-5 p-3.5 rounded-md bg-rose-50 border border-rose-200 flex items-start gap-2.5 text-xs text-rose-900">
              <AlertTriangle size={17} className="text-rose-600 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold text-rose-800 uppercase tracking-wide mr-2">
                  Clinical Medical Alerts:
                </span>
                <span className="font-medium">{criticalConditions.join("  |  ")}</span>
              </div>
            </div>
          )}
        </section>

        {/* Navigation Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="bg-white p-1 rounded-t-lg border border-slate-200">
            <TabsTrigger value="overview">
              <User size={14} /> Demographics & Contacts
            </TabsTrigger>
            <TabsTrigger value="medical">
              <HeartPulse size={14} /> Medical History
              {criticalConditions.length > 0 && (
                <span className="w-2 h-2 rounded-full bg-rose-500" />
              )}
            </TabsTrigger>
            <TabsTrigger value="dental">
              <Stethoscope size={14} /> Dental History
            </TabsTrigger>
            <TabsTrigger value="timeline">
              <Clock size={14} /> Clinical Timeline
            </TabsTrigger>
            <TabsTrigger value="appointments">
              <Calendar size={14} /> Appointments ({appointmentsQuery.data?.length ?? 0})
            </TabsTrigger>
            <TabsTrigger value="treatments">
              <FileCheck size={14} /> Treatments ({patientTreatmentsQuery.data?.length ?? 0})
            </TabsTrigger>
            <TabsTrigger value="odontogram">
              <Activity size={14} /> Odontogram ({odontogramQuery.data?.stats?.total_teeth_charted ?? 32})
            </TabsTrigger>
            <TabsTrigger value="documents">
              <FileText size={14} /> Documents ({documentsQuery.data?.length ?? 0})
            </TabsTrigger>
            <TabsTrigger value="prescriptions">
              <Pill size={14} /> Prescriptions ({patientPrescriptionsQuery.data?.length ?? 0})
            </TabsTrigger>
            <TabsTrigger value="billing">
              <IndianRupee size={14} /> Billing ({patientBillingQuery.data?.invoices_count ?? 0})
            </TabsTrigger>
          </TabsList>

          {/* Tab 1: Overview & Demographics */}
          <TabsContent value="overview">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {/* Personal Details */}
              <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-xs">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-4 pb-2 border-b border-slate-100">
                  Personal Details
                </h3>
                <dl className="grid grid-cols-2 gap-y-3 text-xs">
                  <dt className="text-slate-500">Date of Birth</dt>
                  <dd className="font-medium text-slate-800">{patient.date_of_birth}</dd>
                  <dt className="text-slate-500">Age</dt>
                  <dd className="font-medium text-slate-800">{patient.age} years</dd>
                  <dt className="text-slate-500">Gender</dt>
                  <dd className="font-medium text-slate-800 capitalize">
                    {patient.gender.toLowerCase().replaceAll("_", " ")}
                  </dd>
                  <dt className="text-slate-500">Blood Group</dt>
                  <dd className="font-medium text-slate-800">{patient.blood_group || "Not recorded"}</dd>
                  <dt className="text-slate-500">Marital Status</dt>
                  <dd className="font-medium text-slate-800">{patient.marital_status || "Not recorded"}</dd>
                  <dt className="text-slate-500">Occupation</dt>
                  <dd className="font-medium text-slate-800">{patient.occupation || "Not recorded"}</dd>
                  <dt className="text-slate-500">Aadhaar Number</dt>
                  <dd className="font-mono text-slate-800">{patient.aadhaar_number || "Not recorded"}</dd>
                  <dt className="text-slate-500">Preferred Language</dt>
                  <dd className="font-medium text-slate-800">{patient.preferred_language}</dd>
                </dl>
              </div>

              {/* Contact Information */}
              <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-xs">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-4 pb-2 border-b border-slate-100">
                  Contact & Residence
                </h3>
                <dl className="grid grid-cols-2 gap-y-3 text-xs">
                  <dt className="text-slate-500">Primary Mobile</dt>
                  <dd className="font-mono font-medium text-slate-800">{patient.mobile_number}</dd>
                  <dt className="text-slate-500">Alternate Mobile</dt>
                  <dd className="font-mono text-slate-800">{patient.alternate_mobile || "Not recorded"}</dd>
                  <dt className="text-slate-500">Email Address</dt>
                  <dd className="text-slate-800">{patient.email || "Not recorded"}</dd>
                  <dt className="text-slate-500">Street Address</dt>
                  <dd className="text-slate-800">{patient.address || "Not recorded"}</dd>
                  <dt className="text-slate-500">City / State</dt>
                  <dd className="text-slate-800">
                    {[patient.city, patient.state].filter(Boolean).join(", ") || "Not recorded"}
                  </dd>
                  <dt className="text-slate-500">Country / PIN Code</dt>
                  <dd className="text-slate-800">
                    {patient.country} {patient.pin_code ? `- ${patient.pin_code}` : ""}
                  </dd>
                </dl>
              </div>

              {/* Emergency Contact */}
              <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-xs">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-4 pb-2 border-b border-slate-100">
                  Emergency Contact
                </h3>
                <dl className="grid grid-cols-2 gap-y-3 text-xs">
                  <dt className="text-slate-500">Contact Name</dt>
                  <dd className="font-medium text-slate-800">
                    {patient.emergency_contact_name || "Not recorded"}
                  </dd>
                  <dt className="text-slate-500">Contact Phone</dt>
                  <dd className="font-mono font-medium text-slate-800">
                    {patient.emergency_contact_number || "Not recorded"}
                  </dd>
                  <dt className="text-slate-500">Relationship</dt>
                  <dd className="font-medium text-slate-800">
                    {patient.emergency_contact_relation || "Not recorded"}
                  </dd>
                </dl>
              </div>

              {/* Insurance & Notes */}
              <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-xs">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-4 pb-2 border-b border-slate-100">
                  Insurance & General Notes
                </h3>
                <dl className="grid grid-cols-2 gap-y-3 text-xs mb-4">
                  <dt className="text-slate-500">Insurance Provider</dt>
                  <dd className="font-medium text-slate-800">
                    {patient.insurance_provider || "Not recorded"}
                  </dd>
                  <dt className="text-slate-500">Policy Number</dt>
                  <dd className="font-mono font-medium text-slate-800">
                    {patient.insurance_policy_number || "Not recorded"}
                  </dd>
                </dl>
                <div className="pt-3 border-t border-slate-100">
                  <span className="text-xs text-slate-500 block mb-1">Clinical / Reception Notes:</span>
                  <p className="text-xs text-slate-700 bg-slate-50 p-2.5 rounded border border-slate-100">
                    {patient.notes || "No additional notes recorded for this patient."}
                  </p>
                </div>
              </div>
            </div>
          </TabsContent>

          {/* Tab 2: Medical History */}
          <TabsContent value="medical">
            <div className="space-y-5">
              {/* Systemic Conditions Grid */}
              <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-xs">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-4 pb-2 border-b border-slate-100">
                  Systemic Health Conditions
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
                  {[
                    { label: "Diabetes", active: med?.diabetes },
                    { label: "Hypertension (BP)", active: med?.hypertension },
                    { label: "Cardiac Disease", active: med?.cardiac_disease },
                    { label: "Thyroid Disorder", active: med?.thyroid },
                    { label: "Asthma", active: med?.asthma },
                    { label: "Epilepsy", active: med?.epilepsy },
                    { label: "Pregnancy", active: med?.pregnancy },
                    { label: "Smoking", active: med?.smoking },
                    { label: "Chewing Tobacco", active: med?.tobacco },
                    { label: "Alcohol Consumption", active: med?.alcohol },
                  ].map((item) => (
                    <div
                      key={item.label}
                      className={`p-3 rounded-md border text-xs flex flex-col justify-between h-18 ${
                        item.active
                          ? "bg-rose-50/80 border-rose-200 text-rose-900 font-semibold"
                          : "bg-slate-50 border-slate-100 text-slate-600"
                      }`}
                    >
                      <span>{item.label}</span>
                      <span className="text-[11px]">
                        {item.active ? "Positive" : "None reported"}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Detailed Medical Information */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-xs">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
                    Known Drug & Substance Allergies
                  </h4>
                  <p className="text-xs p-3 rounded bg-slate-50 border border-slate-100 text-slate-800">
                    {med?.allergies || "No drug or material allergies recorded."}
                  </p>
                </div>

                <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-xs">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
                    Current Prescriptions & Medications
                  </h4>
                  <p className="text-xs p-3 rounded bg-slate-50 border border-slate-100 text-slate-800">
                    {med?.current_medications || "No active medications recorded."}
                  </p>
                </div>

                <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-xs">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
                    Past Surgeries & Hospitalizations
                  </h4>
                  <p className="text-xs p-3 rounded bg-slate-50 border border-slate-100 text-slate-800">
                    {med?.previous_surgeries || "No prior surgeries recorded."}
                  </p>
                </div>

                <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-xs">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
                    Infectious Diseases
                  </h4>
                  <p className="text-xs p-3 rounded bg-slate-50 border border-slate-100 text-slate-800">
                    {med?.infectious_diseases || "No infectious diseases reported."}
                  </p>
                </div>
              </div>

              {/* Primary Physician */}
              <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-xs">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3 pb-2 border-b border-slate-100">
                  Attending / Primary Care Physician
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                  <div>
                    <span className="text-slate-500 block">Physician Name:</span>
                    <span className="font-medium text-slate-800">{med?.physician_name || "Not recorded"}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Physician Contact:</span>
                    <span className="font-mono text-slate-800">{med?.physician_contact || "Not recorded"}</span>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>

          {/* Tab 3: Dental History */}
          <TabsContent value="dental">
            <div className="space-y-5">
              {/* Chief Complaint Callout */}
              <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-xs">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">
                  Chief Complaint
                </h3>
                <p className="text-sm font-medium text-slate-900 bg-teal-50/60 p-4 rounded-md border border-teal-100">
                  {patient.dental_history?.chief_complaint || "No chief complaint recorded."}
                </p>
              </div>

              {/* Habits & Oral Hygiene */}
              <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-xs">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-4 pb-2 border-b border-slate-100">
                  Oral Health Habits & Clinical Symptoms
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
                  {[
                    { label: "Daily Flossing", active: patient.dental_history?.flossing_habit },
                    { label: "Bleeding Gums", active: patient.dental_history?.bleeding_gums },
                    { label: "Teeth Sensitivity", active: patient.dental_history?.sensitivity },
                    { label: "Grinding / Bruxism", active: patient.dental_history?.grinding },
                    { label: "Jaw / Facial Pain", active: patient.dental_history?.jaw_pain },
                    { label: "TMJ Disorder", active: patient.dental_history?.tmj_disorder },
                    { label: "Tobacco Habit", active: patient.dental_history?.tobacco_habit },
                  ].map((item) => (
                    <div
                      key={item.label}
                      className={`p-3 rounded-md border text-xs flex flex-col justify-between h-18 ${
                        item.active
                          ? "bg-amber-50 border-amber-200 text-amber-900 font-semibold"
                          : "bg-slate-50 border-slate-100 text-slate-600"
                      }`}
                    >
                      <span>{item.label}</span>
                      <span className="text-[11px]">{item.active ? "Yes" : "No"}</span>
                    </div>
                  ))}
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs pt-3 border-t border-slate-100">
                  <div>
                    <span className="text-slate-500 block">Brushing Frequency:</span>
                    <span className="font-medium text-slate-800">
                      {patient.dental_history?.brushing_frequency || "Not recorded"}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Last Dental Visit:</span>
                    <span className="font-medium text-slate-800">
                      {patient.dental_history?.last_dental_visit || "Not recorded"}
                    </span>
                  </div>
                  <div className="sm:col-span-2">
                    <span className="text-slate-500 block mb-1">Previous Dental Treatments:</span>
                    <p className="p-2.5 rounded bg-slate-50 border border-slate-100 text-slate-800">
                      {patient.dental_history?.previous_dental_treatments || "None recorded."}
                    </p>
                  </div>
                  <div className="sm:col-span-2">
                    <span className="text-slate-500 block mb-1">Dental Clinical Notes:</span>
                    <p className="p-2.5 rounded bg-slate-50 border border-slate-100 text-slate-800">
                      {patient.dental_history?.dental_notes || "None recorded."}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>

          {/* Tab 4: Clinical Timeline */}
          <TabsContent value="timeline">
            <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-xs">
              <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-6">
                <div>
                  <h3 className="text-sm font-semibold text-slate-900">Patient Activity Timeline</h3>
                  <p className="text-xs text-slate-500">
                    Chronological audit log of registrations, visits, and clinical events.
                  </p>
                </div>
              </div>

              {timelineQuery.isLoading ? (
                <div className="space-y-4">
                  <Skeleton className="h-12 w-full" />
                  <Skeleton className="h-12 w-full" />
                </div>
              ) : timelineQuery.data && timelineQuery.data.length > 0 ? (
                <ol className="relative border-l-2 border-teal-200 ml-4 space-y-6">
                  {timelineQuery.data.map((event) => (
                    <li key={event.id} className="ml-6">
                      <span className="absolute -left-2.5 flex items-center justify-center w-5 h-5 bg-teal-600 rounded-full ring-4 ring-white">
                        <span className="w-1.5 h-1.5 bg-white rounded-full" />
                      </span>
                      <div className="bg-slate-50 p-4 rounded-lg border border-slate-200/80">
                        <div className="flex items-center justify-between gap-2 flex-wrap mb-1">
                          <strong className="text-xs font-semibold text-slate-900">
                            {event.title}
                          </strong>
                          <time className="text-[11px] text-slate-400 font-mono">
                            {new Date(event.created_at).toLocaleString()}
                          </time>
                        </div>
                        {event.description && (
                          <p className="text-xs text-slate-600 mt-1">{event.description}</p>
                        )}
                        <span className="inline-block text-[10px] uppercase font-semibold text-teal-700 mt-2 bg-teal-50 px-2 py-0.5 rounded">
                          {event.event_type.replaceAll("_", " ")}
                        </span>
                      </div>
                    </li>
                  ))}
                </ol>
              ) : (
                <p className="text-xs text-slate-500 py-6 text-center">No timeline events recorded yet.</p>
              )}
            </div>
          </TabsContent>

          {/* Tab 5: Patient Appointments (Phase 3) */}
          <TabsContent value="appointments">
            <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-xs space-y-6">
              {/* Header with quick booking CTA */}
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-4 border-b border-slate-100">
                <div>
                  <h3 className="text-sm font-semibold text-slate-900">
                    Patient Scheduled Appointments
                  </h3>
                  <p className="text-xs text-slate-500">
                    Upcoming visits, operatory bookings, and past clinical consultations for {fullName}.
                  </p>
                </div>
                {!isArchived && (
                  <button
                    onClick={() => setIsBookModalOpen(true)}
                    className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-teal-700 hover:bg-teal-800 text-white font-semibold text-xs rounded-md shadow-2xs transition-colors self-start sm:self-auto"
                  >
                    <Plus size={13} /> Book Appointment
                  </button>
                )}
              </div>

              {appointmentsQuery.isLoading ? (
                <div className="space-y-3">
                  <Skeleton className="h-16 w-full" />
                  <Skeleton className="h-16 w-full" />
                </div>
              ) : (appointmentsQuery.data?.length ?? 0) === 0 ? (
                <div className="py-12 text-center text-slate-500 max-w-sm mx-auto">
                  <Calendar size={32} className="mx-auto mb-2 text-slate-300" />
                  <h4 className="text-sm font-semibold text-slate-800">No appointments scheduled</h4>
                  <p className="text-xs text-slate-500 mt-1 mb-4">
                    There are no recorded appointments for this patient yet.
                  </p>
                  {!isArchived && (
                    <button
                      onClick={() => setIsBookModalOpen(true)}
                      className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-teal-700 hover:bg-teal-800 text-white font-semibold text-xs rounded-md shadow-2xs"
                    >
                      <Plus size={13} /> Book First Visit
                    </button>
                  )}
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Active / Upcoming Section */}
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3 flex items-center gap-2">
                      <Clock size={13} className="text-teal-600" /> Upcoming & Active Visits
                    </h4>
                    {appointmentsQuery.data?.filter(
                      (a: any) =>
                        a.status !== "COMPLETED" &&
                        a.status !== "CANCELLED" &&
                        a.status !== "NO_SHOW"
                    ).length === 0 ? (
                      <p className="text-xs text-slate-400 italic py-2">
                        No upcoming visits currently scheduled.
                      </p>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {appointmentsQuery.data
                          ?.filter(
                            (a: any) =>
                              a.status !== "COMPLETED" &&
                              a.status !== "CANCELLED" &&
                              a.status !== "NO_SHOW"
                          )
                          .map((apt: any) => (
                            <div
                              key={apt.id}
                              onClick={() => setSelectedAppointment(apt)}
                              className="p-4 rounded-lg border border-slate-200 hover:border-teal-300 bg-slate-50/50 hover:bg-slate-50 transition-all cursor-pointer shadow-2xs"
                            >
                              <div className="flex items-center justify-between gap-2 mb-2">
                                <span className="text-xs font-mono font-bold text-slate-900">
                                  {apt.appointment_number}
                                </span>
                                <span
                                  className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded border ${
                                    apt.status === "CONFIRMED"
                                      ? "bg-indigo-50 text-indigo-800 border-indigo-200"
                                      : apt.status === "CHECKED_IN"
                                      ? "bg-amber-50 text-amber-800 border-amber-200"
                                      : apt.status === "IN_CHAIR"
                                      ? "bg-purple-50 text-purple-800 border-purple-200"
                                      : "bg-sky-50 text-sky-800 border-sky-200"
                                  }`}
                                >
                                  {apt.status}
                                </span>
                              </div>

                              <div className="text-xs text-slate-700 font-semibold mb-1">
                                {apt.date} · {apt.start_time.slice(0, 5)} - {apt.end_time.slice(0, 5)} ({apt.duration}m)
                              </div>

                              <div className="text-[11px] text-slate-600 space-y-0.5 mb-2">
                                <div>Clinician: Dr. {apt.dentist_name || "Assigned Dentist"}</div>
                                <div>Operatory: {apt.chair_name || "Chair"}</div>
                              </div>

                              {apt.chief_complaint && (
                                <p className="text-[11px] text-slate-500 italic truncate mb-2">
                                  &ldquo;{apt.chief_complaint}&rdquo;
                                </p>
                              )}

                              <div className="flex items-center justify-between pt-2 border-t border-slate-200/80 text-[11px]">
                                <span className="uppercase font-semibold text-teal-700 bg-teal-50 px-1.5 py-0.5 rounded">
                                  {apt.visit_type}
                                </span>
                                <span className="font-semibold text-teal-700 hover:text-teal-900">
                                  Manage Visit →
                                </span>
                              </div>
                            </div>
                          ))}
                      </div>
                    )}
                  </div>

                  {/* Past Visits Section */}
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3 flex items-center gap-2">
                      <CheckCircle2 size={13} className="text-emerald-600" /> Past & Completed Visits
                    </h4>
                    {appointmentsQuery.data?.filter(
                      (a: any) =>
                        a.status === "COMPLETED" ||
                        a.status === "CANCELLED" ||
                        a.status === "NO_SHOW"
                    ).length === 0 ? (
                      <p className="text-xs text-slate-400 italic py-2">
                        No past appointments recorded.
                      </p>
                    ) : (
                      <div className="space-y-2">
                        {appointmentsQuery.data
                          ?.filter(
                            (a: any) =>
                              a.status === "COMPLETED" ||
                              a.status === "CANCELLED" ||
                              a.status === "NO_SHOW"
                          )
                          .map((apt: any) => (
                            <div
                              key={apt.id}
                              onClick={() => setSelectedAppointment(apt)}
                              className="p-3 rounded-lg border border-slate-200 hover:bg-slate-50 transition-all cursor-pointer flex items-center justify-between text-xs"
                            >
                              <div className="space-y-0.5">
                                <div className="flex items-center gap-2">
                                  <span className="font-bold text-slate-900">{apt.date}</span>
                                  <span className="text-slate-400 font-mono">
                                    {apt.start_time.slice(0, 5)}
                                  </span>
                                  <span
                                    className={`text-[9px] uppercase font-bold px-1.5 py-0.2 rounded border ${
                                      apt.status === "COMPLETED"
                                        ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                                        : "bg-rose-50 text-rose-700 border-rose-200"
                                    }`}
                                  >
                                    {apt.status}
                                  </span>
                                </div>
                                <div className="text-[11px] text-slate-500">
                                  Dr. {apt.dentist_name} · {apt.visit_type} · {apt.duration} min
                                </div>
                              </div>
                              <span className="font-semibold text-teal-700 hover:text-teal-900 text-xs">
                                Details →
                              </span>
                            </div>
                          ))}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </TabsContent>

          {/* Tab 6: Real Treatments Module */}
          <TabsContent value="treatments">
            <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-xs">
              <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-6">
                <div>
                  <h3 className="text-sm font-semibold text-slate-900">
                    Clinical Treatments & Procedures
                  </h3>
                  <p className="text-xs text-slate-500">
                    Longitudinal dental charting, diagnoses, procedure records, and SOAP notes.
                  </p>
                </div>
                <Link
                  href={`/treatments/new?patient_id=${id}`}
                  className="inline-flex items-center gap-1.5 bg-teal-700 hover:bg-teal-800 text-white font-semibold text-xs px-3.5 py-2 rounded-md shadow-2xs transition-colors"
                >
                  <Plus size={14} /> Start New Treatment
                </Link>
              </div>

              {patientTreatmentsQuery.isLoading ? (
                <div className="space-y-3">
                  <Skeleton className="h-16 w-full" />
                  <Skeleton className="h-16 w-full" />
                </div>
              ) : patientTreatmentsQuery.data && patientTreatmentsQuery.data.length > 0 ? (
                <div className="divide-y divide-slate-100">
                  {patientTreatmentsQuery.data.map((t: any) => (
                    <div
                      key={t.id}
                      className="py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:bg-slate-50/70 px-3 rounded-lg transition-colors"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <Link
                            href={`/treatments/${t.id}`}
                            className="font-mono text-xs font-bold text-teal-700 hover:underline"
                          >
                            {t.treatment_number}
                          </Link>
                          <span
                            className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
                              t.status === "COMPLETED"
                                ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                                : t.status === "IN_PROGRESS"
                                ? "bg-amber-50 text-amber-700 border-amber-200"
                                : t.status === "PLANNED"
                                ? "bg-sky-50 text-sky-700 border-sky-200"
                                : "bg-rose-50 text-rose-700 border-rose-200"
                            }`}
                          >
                            {t.status.replace("_", " ")}
                          </span>
                          {t.is_override && (
                            <span className="text-[9px] font-bold px-1.5 py-0.2 bg-purple-50 text-purple-700 border border-purple-200 rounded uppercase">
                              Override
                            </span>
                          )}
                        </div>

                        <div className="text-xs font-medium text-slate-800">
                          {t.diagnosis}
                        </div>

                        <div className="flex items-center gap-3 text-[11px] text-slate-400 flex-wrap">
                          <span>Dr. {t.dentist_name || "Unassigned"}</span>
                          <span>·</span>
                          <span>{new Date(t.created_at).toLocaleDateString()}</span>
                          <span>·</span>
                          <span>{t.procedures_count || 0} procedure(s)</span>
                          <span>·</span>
                          <span className="font-mono font-semibold text-slate-700">
                            ₹{Number(t.total_cost || 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 self-end sm:self-center">
                        <Link
                          href={`/treatments/${t.id}`}
                          className="inline-flex items-center gap-1 text-xs font-semibold text-teal-700 hover:text-teal-800 bg-teal-50 hover:bg-teal-100 px-3 py-1.5 rounded-md transition-colors"
                        >
                          View Details →
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-12 text-center text-slate-500">
                  <FileCheck size={36} className="text-slate-300 mx-auto mb-2" />
                  <p className="text-sm font-semibold text-slate-700">No treatments charted yet</p>
                  <p className="text-xs text-slate-400 mt-0.5 max-w-sm mx-auto">
                    No clinical treatments or procedures have been recorded for this patient.
                  </p>
                  <Link
                    href={`/treatments/new?patient_id=${id}`}
                    className="mt-4 inline-flex items-center gap-1.5 bg-teal-700 hover:bg-teal-800 text-white font-semibold text-xs px-3.5 py-2 rounded-md shadow-2xs"
                  >
                    <Plus size={13} /> Start First Treatment
                  </Link>
                </div>
              )}
            </div>
          </TabsContent>

          {/* Tab 7: Documents */}
          <TabsContent value="documents">
            <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-xs">
              <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-6">
                <div>
                  <h3 className="text-sm font-semibold text-slate-900">Patient Document Storage</h3>
                  <p className="text-xs text-slate-500">
                    Consent forms, medical records, ID proofs, and uploaded radiographs.
                  </p>
                </div>
                <button
                  onClick={() => setIsUploadOpen(true)}
                  className="inline-flex items-center gap-1.5 bg-teal-700 hover:bg-teal-800 text-white font-semibold text-xs px-3.5 py-2 rounded-md shadow-2xs"
                >
                  <Plus size={14} /> Upload New Document
                </button>
              </div>

              {documentsQuery.isLoading ? (
                <div className="space-y-3">
                  <Skeleton className="h-12 w-full" />
                  <Skeleton className="h-12 w-full" />
                </div>
              ) : documentsQuery.data && documentsQuery.data.length > 0 ? (
                <div className="divide-y divide-slate-100">
                  {documentsQuery.data.map((doc) => (
                    <div
                      key={doc.id}
                      className="py-3.5 flex items-center justify-between gap-4 hover:bg-slate-50 px-2 rounded-md transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded bg-teal-50 text-teal-700">
                          <FileText size={18} />
                        </div>
                        <div>
                          <p className="text-xs font-semibold text-slate-900">{doc.file_name}</p>
                          <div className="flex items-center gap-2 text-[11px] text-slate-400 mt-0.5">
                            <span className="uppercase font-medium text-slate-600">
                              {doc.document_type}
                            </span>
                            <span>·</span>
                            <span>{new Date(doc.created_at).toLocaleDateString()}</span>
                            <span>·</span>
                            <span>{doc.content_type}</span>
                          </div>
                        </div>
                      </div>

                      <a
                        href={doc.url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 text-xs font-semibold text-teal-700 hover:text-teal-800 bg-teal-50 hover:bg-teal-100 px-3 py-1.5 rounded-md transition-colors"
                      >
                        <Download size={13} /> Download
                      </a>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-12 text-center text-slate-500">
                  <FileText size={32} className="text-slate-300 mx-auto mb-2" />
                  <p className="text-sm font-semibold text-slate-700">No documents uploaded yet</p>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Upload signed consent forms, photo IDs, or clinical attachments.
                  </p>
                  <button
                    onClick={() => setIsUploadOpen(true)}
                    className="mt-3 inline-flex items-center gap-1.5 text-xs font-semibold text-teal-700 hover:underline"
                  >
                    <Upload size={13} /> Upload now
                  </button>
                </div>
              )}
            </div>
          </TabsContent>

          {/* Tab 8: Odontogram (Dental Charting) */}
          <TabsContent value="odontogram">
            <div className="space-y-4">
              {/* Header card with Actions */}
              <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <Activity size={18} className="text-teal-700" />
                    <h2 className="text-base font-bold text-slate-900">
                      Interactive Odontogram Chart
                    </h2>
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Anatomical tooth surface visualization, active pathologies, and restorative history.
                  </p>
                </div>
                <Link
                  href={`/patients/${id}/odontogram`}
                  className="inline-flex items-center gap-2 px-3.5 py-2 bg-teal-700 hover:bg-teal-800 text-white font-semibold text-xs rounded-md shadow-xs transition-colors"
                >
                  <Activity size={14} /> Open Full Operatory Workstation &rarr;
                </Link>
              </div>

              {/* KPI Stat Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-2xs">
                  <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">Teeth Charted</span>
                  <span className="text-lg font-bold text-slate-900 mt-1 block">
                    {odontogramQuery.data?.stats?.total_teeth_charted ?? 32}
                  </span>
                </div>
                <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-2xs">
                  <span className="text-[11px] font-bold text-rose-600 uppercase tracking-wider block">Active Caries</span>
                  <span className="text-lg font-bold text-rose-700 mt-1 block">
                    {odontogramQuery.data?.stats?.active_caries ?? 0}
                  </span>
                </div>
                <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-2xs">
                  <span className="text-[11px] font-bold text-blue-600 uppercase tracking-wider block">Restorations</span>
                  <span className="text-lg font-bold text-blue-700 mt-1 block">
                    {odontogramQuery.data?.stats?.restorations ?? 0}
                  </span>
                </div>
                <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-2xs">
                  <span className="text-[11px] font-bold text-purple-600 uppercase tracking-wider block">Root Canals</span>
                  <span className="text-lg font-bold text-purple-700 mt-1 block">
                    {odontogramQuery.data?.stats?.root_canals ?? 0}
                  </span>
                </div>
                <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-2xs">
                  <span className="text-[11px] font-bold text-amber-600 uppercase tracking-wider block">Crowns</span>
                  <span className="text-lg font-bold text-amber-700 mt-1 block">
                    {odontogramQuery.data?.stats?.crowns ?? 0}
                  </span>
                </div>
                <div className="bg-white p-3 rounded-lg border border-slate-200 shadow-2xs">
                  <span className="text-[11px] font-bold text-slate-600 uppercase tracking-wider block">Missing/Extracted</span>
                  <span className="text-lg font-bold text-slate-700 mt-1 block">
                    {odontogramQuery.data?.stats?.missing_teeth ?? 0}
                  </span>
                </div>
              </div>

              {/* Odontogram Canvas Component */}
              <OdontogramCanvas
                teeth={odontogramQuery.data?.teeth || []}
                dentitionType={dentitionType}
                numberingSystem={numberingSystem}
                selectedTooth={selectedTooth}
                onSelectTooth={(tooth) => setSelectedTooth(tooth)}
                onChangeDentition={setDentitionType}
                onChangeNumberingSystem={setNumberingSystem}
              />

              {/* Selected Tooth Quick Info Card */}
              {selectedTooth && (
                <div className="bg-white p-4 rounded-lg border border-teal-200 bg-teal-50/20 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                  <div className="space-y-1 text-xs">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-slate-900 text-sm">
                        Tooth #{selectedTooth.tooth_number} ({selectedTooth.name})
                      </span>
                      <Badge variant="outline" className="text-slate-700 font-mono">
                        Universal: #{selectedTooth.universal_number}
                      </Badge>
                      <Badge variant="outline" className="text-slate-700 font-mono">
                        Palmer: {selectedTooth.palmer_notation}
                      </Badge>
                      <span
                        className="px-2 py-0.5 rounded text-[11px] font-bold uppercase text-white"
                        style={{ backgroundColor: selectedTooth.color }}
                      >
                        {selectedTooth.primary_status}
                      </span>
                    </div>
                    <div className="text-slate-600 flex items-center gap-3">
                      <span>Arch: {selectedTooth.arch}</span>
                      <span>Quadrant: {selectedTooth.quadrant}</span>
                      <span>Type: {selectedTooth.tooth_type}</span>
                      {selectedTooth.has_crown && <span className="text-amber-700 font-semibold">Crown</span>}
                      {selectedTooth.has_root_canal && <span className="text-purple-700 font-semibold">Root Canal</span>}
                      {selectedTooth.has_implant && <span className="text-slate-700 font-semibold">Implant</span>}
                    </div>
                  </div>

                  <Link
                    href={`/patients/${id}/odontogram?tooth=${selectedTooth.tooth_number}`}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs rounded-md shadow-xs transition-colors shrink-0"
                  >
                    Edit Tooth in Operatory &rarr;
                  </Link>
                </div>
              )}
            </div>
          </TabsContent>

          {/* Tab 9: Prescriptions */}
          <TabsContent value="prescriptions">
            <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-xs space-y-4">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
                <div>
                  <h3 className="text-sm font-semibold text-slate-900">
                    Patient Prescription Records
                  </h3>
                  <p className="text-xs text-slate-500">
                    Clinical medication history, instructions, and official A4 printable records.
                  </p>
                </div>
                <Link
                  href={`/prescriptions/new?patient_id=${id}`}
                  className="inline-flex items-center gap-1.5 bg-teal-700 hover:bg-teal-800 text-white font-semibold text-xs px-3.5 py-2 rounded-md shadow-2xs transition-colors"
                >
                  <Plus size={14} /> Write Prescription
                </Link>
              </div>

              {patientPrescriptionsQuery.isLoading ? (
                <div className="space-y-3">
                  <Skeleton className="h-10 w-full" />
                  <Skeleton className="h-14 w-full" />
                  <Skeleton className="h-14 w-full" />
                </div>
              ) : patientPrescriptionsQuery.data && patientPrescriptionsQuery.data.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="bg-slate-50 text-[11px] font-bold text-slate-600 uppercase border-b border-slate-200">
                        <th className="py-2.5 px-3">Rx Number</th>
                        <th className="py-2.5 px-3">Date</th>
                        <th className="py-2.5 px-3">Diagnosis & Medications</th>
                        <th className="py-2.5 px-3">Clinician</th>
                        <th className="py-2.5 px-3">Status</th>
                        <th className="py-2.5 px-3 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {patientPrescriptionsQuery.data.map((rx: any) => (
                        <tr key={rx.id} className="hover:bg-slate-50/60">
                          <td className="py-3 px-3 font-mono font-bold text-teal-800">
                            <Link
                              href={`/prescriptions/${rx.id}`}
                              className="hover:underline flex items-center gap-1"
                            >
                              <Pill size={13} className="text-teal-600" />
                              {rx.prescription_number}
                            </Link>
                          </td>
                          <td className="py-3 px-3 text-slate-600 whitespace-nowrap">
                            {new Date(rx.date).toLocaleDateString()}
                          </td>
                          <td className="py-3 px-3">
                            <p className="font-semibold text-slate-900">{rx.diagnosis}</p>
                            <p className="text-[11px] text-slate-500 mt-0.5">
                              {rx.items_count} medication(s):{" "}
                              {rx.items
                                ?.map((it: any) => it.medicine_name)
                                .slice(0, 3)
                                .join(", ")}
                            </p>
                          </td>
                          <td className="py-3 px-3 text-slate-700">
                            {rx.dentist_name || "Clinician"}
                          </td>
                          <td className="py-3 px-3 whitespace-nowrap">
                            <span
                              className={`px-2 py-0.5 rounded text-[11px] font-semibold ${
                                rx.status === "ISSUED"
                                  ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                                  : rx.status === "CANCELLED"
                                  ? "bg-rose-50 text-rose-700 border border-rose-200"
                                  : "bg-amber-50 text-amber-700 border border-amber-200"
                              }`}
                            >
                              {rx.status}
                            </span>
                          </td>
                          <td className="py-3 px-3 text-right whitespace-nowrap">
                            <Link
                              href={`/prescriptions/${rx.id}`}
                              className="inline-flex items-center gap-1 text-xs font-semibold text-teal-700 hover:text-teal-800 bg-teal-50 hover:bg-teal-100 px-2.5 py-1 rounded transition-colors"
                            >
                              View Rx &rarr;
                            </Link>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="py-12 text-center text-slate-500">
                  <Pill size={36} className="text-slate-300 mx-auto mb-2" />
                  <p className="text-sm font-semibold text-slate-700">
                    No prescriptions recorded
                  </p>
                  <p className="text-xs text-slate-400 mt-0.5 max-w-sm mx-auto">
                    Prescribe medications or apply dental procedure templates for this patient.
                  </p>
                  <Link
                    href={`/prescriptions/new?patient_id=${id}`}
                    className="mt-4 inline-flex items-center gap-1.5 bg-teal-700 hover:bg-teal-800 text-white font-semibold text-xs px-3.5 py-2 rounded-md shadow-2xs"
                  >
                    <Plus size={13} /> Write First Prescription
                  </Link>
                </div>
              )}
            </div>
          </TabsContent>

          {/* Tab 10: Billing, Invoices & Payments */}
          <TabsContent value="billing">
            <div className="space-y-6">
              {/* Ledger Summary Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
                    Total Invoiced
                  </span>
                  <div className="text-xl font-bold text-slate-900 mt-1">
                    {patientBillingQuery.isLoading ? (
                      <Skeleton className="h-6 w-20" />
                    ) : (
                      `₹${(patientBillingQuery.data?.total_invoiced ?? 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`
                    )}
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    {patientBillingQuery.data?.invoices_count ?? 0} invoice(s)
                  </p>
                </div>

                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
                  <span className="text-xs font-semibold text-emerald-600 uppercase tracking-wider block">
                    Total Paid
                  </span>
                  <div className="text-xl font-bold text-emerald-600 mt-1">
                    {patientBillingQuery.isLoading ? (
                      <Skeleton className="h-6 w-20" />
                    ) : (
                      `₹${(patientBillingQuery.data?.total_paid ?? 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`
                    )}
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    {patientBillingQuery.data?.payments_count ?? 0} payment(s)
                  </p>
                </div>

                <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
                  <span className="text-xs font-semibold text-rose-600 uppercase tracking-wider block">
                    Balance Due
                  </span>
                  <div className="text-xl font-bold text-rose-600 mt-1">
                    {patientBillingQuery.isLoading ? (
                      <Skeleton className="h-6 w-20" />
                    ) : (
                      `₹${(patientBillingQuery.data?.balance_due ?? 0).toLocaleString("en-IN", { minimumFractionDigits: 2 })}`
                    )}
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5">
                    Outstanding patient balance
                  </p>
                </div>
              </div>

              {/* Invoices List */}
              <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <div>
                    <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                      <Receipt size={16} className="text-blue-600" />
                      Invoices Ledger
                    </h3>
                    <p className="text-xs text-slate-500">
                      Tax invoices generated for consultations, procedures, and dental services
                    </p>
                  </div>
                  <Link
                    href={`/billing/new?patient_id=${id}`}
                    className="inline-flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs px-3.5 py-2 rounded-lg shadow-2xs transition-colors"
                  >
                    <Plus size={13} /> Create Invoice
                  </Link>
                </div>

                {patientBillingQuery.isLoading ? (
                  <div className="space-y-2">
                    <Skeleton className="h-8 w-full" />
                    <Skeleton className="h-12 w-full" />
                    <Skeleton className="h-12 w-full" />
                  </div>
                ) : !patientBillingQuery.data?.invoices || patientBillingQuery.data.invoices.length === 0 ? (
                  <div className="py-8 text-center text-slate-400 text-xs">
                    <FileText size={32} className="mx-auto mb-2 text-slate-300" />
                    No invoices generated for this patient yet.
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold uppercase">
                        <tr>
                          <th className="py-2.5 px-3">Invoice #</th>
                          <th className="py-2.5 px-3">Date</th>
                          <th className="py-2.5 px-3">Clinician</th>
                          <th className="py-2.5 px-3 text-right">Grand Total</th>
                          <th className="py-2.5 px-3 text-right">Paid</th>
                          <th className="py-2.5 px-3 text-right">Balance</th>
                          <th className="py-2.5 px-3 text-center">Status</th>
                          <th className="py-2.5 px-3 text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {patientBillingQuery.data.invoices.map((inv: any) => (
                          <tr key={inv.id} className="hover:bg-slate-50/50">
                            <td className="py-3 px-3 font-semibold text-blue-600">
                              <Link href={`/billing/${inv.id}`} className="hover:underline">
                                {inv.invoice_number}
                              </Link>
                            </td>
                            <td className="py-3 px-3 text-slate-600">
                              {inv.date || inv.created_at?.slice(0, 10)}
                            </td>
                            <td className="py-3 px-3 text-slate-700">
                              {inv.dentist_name || "Doctor"}
                            </td>
                            <td className="py-3 px-3 text-right font-bold text-slate-900">
                              ₹{inv.grand_total.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                            </td>
                            <td className="py-3 px-3 text-right font-semibold text-emerald-600">
                              ₹{inv.amount_paid.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                            </td>
                            <td className="py-3 px-3 text-right font-bold">
                              {inv.balance_due > 0 ? (
                                <span className="text-rose-600">
                                  ₹{inv.balance_due.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                                </span>
                              ) : (
                                <span className="text-slate-400">₹0.00</span>
                              )}
                            </td>
                            <td className="py-3 px-3 text-center">
                              <span
                                className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                  inv.status === "PAID"
                                    ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                                    : inv.status === "PARTIALLY_PAID"
                                    ? "bg-amber-50 text-amber-700 border border-amber-200"
                                    : "bg-rose-50 text-rose-700 border border-rose-200"
                                }`}
                              >
                                {inv.status}
                              </span>
                            </td>
                            <td className="py-3 px-3 text-right">
                              <Link
                                href={`/billing/${inv.id}`}
                                className="inline-flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-800 bg-blue-50 px-2.5 py-1 rounded"
                              >
                                View Invoice &rarr;
                              </Link>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </div>

      {/* Upload Document Modal */}
      <Dialog
        open={isUploadOpen}
        onOpenChange={setIsUploadOpen}
        title="Upload Patient Document"
        description="Attach photos, signed consent forms, or reports (JPEG, PNG, PDF up to 10 MB)."
      >
        <div className="space-y-4 text-xs">
          <div>
            <label className="block text-slate-700 font-semibold mb-1">Document Category</label>
            <select
              value={uploadDocType}
              onChange={(e) => setUploadDocType(e.target.value)}
              className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
            >
              <option value="DOCUMENT">General Clinical Document</option>
              <option value="CONSENT">Signed Consent Form</option>
              <option value="PHOTO">Patient Photo Avatar</option>
              <option value="LAB_REPORT">Lab / Diagnostic Report</option>
              <option value="ID_PROOF">Government Photo ID</option>
            </select>
          </div>

          <div>
            <label className="block text-slate-700 font-semibold mb-1">Select File</label>
            <input
              type="file"
              ref={fileInputRef}
              accept=".pdf,.png,.jpg,.jpeg"
              onChange={(e) => {
                const file = e.target.files?.[0] || null;
                setSelectedFile(file);
              }}
              className="w-full text-xs text-slate-500 file:mr-4 file:py-2 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-teal-50 file:text-teal-700 hover:file:bg-teal-100"
            />
            {selectedFile && (
              <p className="mt-1 text-[11px] text-teal-700 font-medium">
                Ready to upload: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
              </p>
            )}
          </div>

          <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-slate-100">
            <button
              onClick={() => {
                setIsUploadOpen(false);
                setSelectedFile(null);
              }}
              className="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium rounded-md"
            >
              Cancel
            </button>
            <button
              onClick={() => uploadMutation.mutate()}
              disabled={!selectedFile || uploadMutation.isPending}
              className="px-4 py-2 bg-teal-700 hover:bg-teal-800 text-white font-semibold rounded-md shadow-xs disabled:opacity-50"
            >
              {uploadMutation.isPending ? "Uploading..." : "Start Upload"}
            </button>
          </div>
        </div>
      </Dialog>

      {/* Archive Confirmation Dialog */}
      <Dialog
        open={isArchiveOpen}
        onOpenChange={setIsArchiveOpen}
        title="Archive Patient Record"
        description="Soft-deletes the patient record from active view."
      >
        <div className="space-y-4 text-xs text-slate-600">
          <p>
            Are you sure you want to archive <strong>{fullName}</strong> ({patient.patient_number})?
            This will hide the patient from active directory listings while maintaining full clinical history and timeline integrity.
          </p>
          <div className="flex items-center justify-end gap-2.5 pt-2">
            <button
              onClick={() => setIsArchiveOpen(false)}
              className="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium rounded-md"
            >
              Cancel
            </button>
            <button
              onClick={() => archiveMutation.mutate()}
              disabled={archiveMutation.isPending}
              className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white font-medium rounded-md shadow-xs disabled:opacity-50"
            >
              {archiveMutation.isPending ? "Archiving..." : "Confirm Archive"}
            </button>
          </div>
        </div>
      </Dialog>

      {/* Booking Modal preselected for this patient */}
      <BookingModal
        isOpen={isBookModalOpen}
        onClose={() => setIsBookModalOpen(false)}
        preselectedPatient={{
          id: patient.id,
          name: fullName,
          patientNumber: patient.patient_number,
          alerts: criticalConditions,
        }}
        onSuccess={() => {
          setIsBookModalOpen(false);
          void queryClient.invalidateQueries({ queryKey: ["patient-appointments", id] });
          void queryClient.invalidateQueries({ queryKey: ["patient-timeline", id] });
        }}
      />

      {/* Appointment Detail & Actions Dialog */}
      <AppointmentDetailDialog
        appointment={selectedAppointment}
        isOpen={!!selectedAppointment}
        onClose={() => setSelectedAppointment(null)}
        onUpdated={() => {
          setSelectedAppointment(null);
          void queryClient.invalidateQueries({ queryKey: ["patient-appointments", id] });
          void queryClient.invalidateQueries({ queryKey: ["patient-timeline", id] });
        }}
      />
    </main>
  );
}
