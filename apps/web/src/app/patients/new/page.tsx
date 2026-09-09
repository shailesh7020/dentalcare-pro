"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import {
  AlertCircle,
  ArrowLeft,
  Calendar,
  CheckCircle2,
  FileHeart,
  FileSpreadsheet,
  HeartPulse,
  Phone,
  Shield,
  Stethoscope,
  User,
} from "lucide-react";
import { z } from "zod";

import { api } from "@/lib/api";

const MOBILE_REGEX = /^[6-9]\d{9}$/;
const AADHAAR_REGEX = /^\d{12}$/;
const PIN_REGEX = /^\d{6}$/;

const newPatientSchema = z
  .object({
    // Section 1: Personal Information
    first_name: z.string().min(1, "First name is required").max(80),
    middle_name: z.string().max(80).optional().or(z.literal("")),
    last_name: z.string().min(1, "Last name is required").max(80),
    gender: z.enum(["FEMALE", "MALE", "NON_BINARY", "PREFER_NOT_TO_SAY"]),
    date_of_birth: z
      .string()
      .min(1, "Date of birth is required")
      .refine((dob) => new Date(dob) <= new Date(), "Date of birth cannot be in the future"),
    blood_group: z
      .enum(["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "UNKNOWN"])
      .optional()
      .or(z.literal("")),
    marital_status: z.string().max(40).optional().or(z.literal("")),
    occupation: z.string().max(100).optional().or(z.literal("")),
    aadhaar_number: z
      .string()
      .regex(AADHAAR_REGEX, "Aadhaar must be exactly 12 numeric digits")
      .optional()
      .or(z.literal("")),
    preferred_language: z.string(),

    // Section 2: Contact Information
    mobile_number: z
      .string()
      .regex(MOBILE_REGEX, "Enter a valid 10-digit Indian mobile number starting with 6-9"),
    alternate_mobile: z
      .string()
      .regex(MOBILE_REGEX, "Enter a valid 10-digit mobile number")
      .optional()
      .or(z.literal("")),
    email: z
      .string()
      .email("Enter a valid email address")
      .optional()
      .or(z.literal("")),
    address: z.string().optional().or(z.literal("")),
    city: z.string().max(80).optional().or(z.literal("")),
    state: z.string().max(80).optional().or(z.literal("")),
    country: z.string(),
    pin_code: z
      .string()
      .regex(PIN_REGEX, "PIN code must be exactly 6 digits")
      .optional()
      .or(z.literal("")),

    // Section 3: Emergency Contact
    emergency_contact_name: z.string().max(160).optional().or(z.literal("")),
    emergency_contact_number: z
      .string()
      .regex(MOBILE_REGEX, "Enter a valid 10-digit mobile number")
      .optional()
      .or(z.literal("")),
    emergency_contact_relation: z.string().max(60).optional().or(z.literal("")),

    // Section 4: Insurance
    insurance_provider: z.string().max(160).optional().or(z.literal("")),
    insurance_policy_number: z.string().max(100).optional().or(z.literal("")),

    // Section 5: Clinical Notes
    notes: z.string().optional().or(z.literal("")),

    // Section 6: Medical History
    medical_history: z.object({
      diabetes: z.boolean(),
      hypertension: z.boolean(),
      cardiac_disease: z.boolean(),
      thyroid: z.boolean(),
      asthma: z.boolean(),
      epilepsy: z.boolean(),
      pregnancy: z.boolean(),
      allergies: z.string().optional().or(z.literal("")),
      current_medications: z.string().optional().or(z.literal("")),
      smoking: z.boolean(),
      tobacco: z.boolean(),
      alcohol: z.boolean(),
      previous_surgeries: z.string().optional().or(z.literal("")),
      infectious_diseases: z.string().optional().or(z.literal("")),
      physician_name: z.string().optional().or(z.literal("")),
      physician_contact: z
        .string()
        .regex(MOBILE_REGEX, "Enter a valid 10-digit mobile number")
        .optional()
        .or(z.literal("")),
      additional_notes: z.string().optional().or(z.literal("")),
    }),

    // Section 7: Dental History
    dental_history: z.object({
      chief_complaint: z.string().optional().or(z.literal("")),
      previous_dental_treatments: z.string().optional().or(z.literal("")),
      brushing_frequency: z.string().optional().or(z.literal("")),
      flossing_habit: z.boolean(),
      tobacco_habit: z.boolean(),
      grinding: z.boolean(),
      jaw_pain: z.boolean(),
      tmj_disorder: z.boolean(),
      sensitivity: z.boolean(),
      bleeding_gums: z.boolean(),
      last_dental_visit: z.string().optional().or(z.literal("")),
      dental_notes: z.string().optional().or(z.literal("")),
    }),
  })
  .refine(
    (data) => !data.alternate_mobile || data.alternate_mobile !== data.mobile_number,
    {
      message: "Alternate mobile must be different from primary mobile number",
      path: ["alternate_mobile"],
    }
  );

type NewPatientFormValues = z.infer<typeof newPatientSchema>;

type DuplicateWarning = {
  field: string;
  patient_id: string;
  patient_number: string;
};

export default function NewPatientPage() {
  const router = useRouter();
  const [duplicateWarnings, setDuplicateWarnings] = useState<DuplicateWarning[]>([]);

  const form = useForm<NewPatientFormValues>({
    resolver: zodResolver(newPatientSchema) as any,
    defaultValues: {
      gender: "FEMALE",
      country: "India",
      preferred_language: "English",
      date_of_birth: "",
      blood_group: "",
      marital_status: "",
      occupation: "",
      aadhaar_number: "",
      mobile_number: "",
      alternate_mobile: "",
      email: "",
      address: "",
      city: "",
      state: "",
      pin_code: "",
      emergency_contact_name: "",
      emergency_contact_number: "",
      emergency_contact_relation: "",
      insurance_provider: "",
      insurance_policy_number: "",
      notes: "",
      medical_history: {
        diabetes: false,
        hypertension: false,
        cardiac_disease: false,
        thyroid: false,
        asthma: false,
        epilepsy: false,
        pregnancy: false,
        allergies: "",
        current_medications: "",
        smoking: false,
        tobacco: false,
        alcohol: false,
        previous_surgeries: "",
        infectious_diseases: "",
        physician_name: "",
        physician_contact: "",
        additional_notes: "",
      },
      dental_history: {
        chief_complaint: "",
        previous_dental_treatments: "",
        brushing_frequency: "Twice daily",
        flossing_habit: false,
        tobacco_habit: false,
        grinding: false,
        jaw_pain: false,
        tmj_disorder: false,
        sensitivity: false,
        bleeding_gums: false,
        last_dental_visit: "",
        dental_notes: "",
      },
    },
  });

  const dobValue = form.watch("date_of_birth");
  const calculatedAge = dobValue
    ? Math.max(
        0,
        Math.floor(
          (new Date().getTime() - new Date(dobValue).getTime()) /
            (365.25 * 24 * 60 * 60 * 1000)
        )
      )
    : null;

  const mutation = useMutation({
    mutationFn: async (values: NewPatientFormValues) => {
      // Clean empty strings to null for backend
      const payload = {
        ...values,
        middle_name: values.middle_name || null,
        blood_group: values.blood_group || null,
        marital_status: values.marital_status || null,
        occupation: values.occupation || null,
        aadhaar_number: values.aadhaar_number || null,
        alternate_mobile: values.alternate_mobile || null,
        email: values.email || null,
        address: values.address || null,
        city: values.city || null,
        state: values.state || null,
        pin_code: values.pin_code || null,
        emergency_contact_name: values.emergency_contact_name || null,
        emergency_contact_number: values.emergency_contact_number || null,
        emergency_contact_relation: values.emergency_contact_relation || null,
        insurance_provider: values.insurance_provider || null,
        insurance_policy_number: values.insurance_policy_number || null,
        notes: values.notes || null,
        medical_history: {
          ...values.medical_history,
          allergies: values.medical_history.allergies || null,
          current_medications: values.medical_history.current_medications || null,
          previous_surgeries: values.medical_history.previous_surgeries || null,
          infectious_diseases: values.medical_history.infectious_diseases || null,
          physician_name: values.medical_history.physician_name || null,
          physician_contact: values.medical_history.physician_contact || null,
          additional_notes: values.medical_history.additional_notes || null,
        },
        dental_history: {
          ...values.dental_history,
          chief_complaint: values.dental_history.chief_complaint || null,
          previous_dental_treatments: values.dental_history.previous_dental_treatments || null,
          brushing_frequency: values.dental_history.brushing_frequency || null,
          last_dental_visit: values.dental_history.last_dental_visit || null,
          dental_notes: values.dental_history.dental_notes || null,
        },
      };

      const res = await api.post("/patients", payload);
      return res.data;
    },
    onSuccess: (data) => {
      if (data.duplicate_warnings && data.duplicate_warnings.length > 0) {
        setDuplicateWarnings(data.duplicate_warnings);
        // If there are warnings, display them for 2 seconds then navigate, or let user acknowledge
        setTimeout(() => {
          router.push(`/patients/${data.patient.id}`);
        }, 1800);
      } else {
        router.push(`/patients/${data.patient.id}`);
      }
    },
  });

  function onSubmit(values: NewPatientFormValues) {
    mutation.mutate(values);
  }

  return (
    <main className="min-h-screen bg-slate-50/60 pb-24">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pt-8">
        {/* Navigation & Header */}
        <div className="mb-6">
          <Link
            href="/patients"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-teal-700 hover:text-teal-800 mb-2"
          >
            <ArrowLeft size={14} /> Back to Patients
          </Link>
          <h1 className="text-2xl font-bold text-slate-900">Patient Registration</h1>
          <p className="text-sm text-slate-500 mt-1">
            Complete the patient intake record. Medical and dental histories can be updated anytime from the profile.
          </p>
        </div>

        {/* Duplicate Warning Callout */}
        {duplicateWarnings.length > 0 && (
          <div className="mb-6 p-4 rounded-lg bg-amber-50 border border-amber-200 text-amber-900 text-xs">
            <div className="flex items-start gap-2.5">
              <AlertCircle size={18} className="text-amber-600 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-sm">Potential Duplicate Patient Detected</p>
                <p className="mt-1">
                  The following matching active patient records already exist in your clinic:
                </p>
                <ul className="list-disc list-inside mt-1 font-mono">
                  {duplicateWarnings.map((w, idx) => (
                    <li key={idx}>
                      Matching {w.field.replace("_", " ")}: Patient{" "}
                      <Link href={`/patients/${w.patient_id}`} className="underline font-bold">
                        {w.patient_number}
                      </Link>
                    </li>
                  ))}
                </ul>
                <p className="mt-1.5 text-amber-700">
                  The record was created. Redirecting to patient profile...
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Error Alert */}
        {mutation.isError && (
          <div className="mb-6 p-4 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2.5">
            <AlertCircle size={18} className="text-rose-600 shrink-0" />
            <div>
              <p className="font-semibold">Unable to register patient</p>
              <p>Please check the fields marked in red and verify contact uniqueness.</p>
            </div>
          </div>
        )}

        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          {/* 1. Demographics & Identity */}
          <section className="bg-white p-6 rounded-lg border border-slate-200 shadow-xs">
            <h2 className="text-sm font-semibold text-slate-900 flex items-center gap-2 pb-3 border-b border-slate-100 mb-4">
              <User size={16} className="text-teal-700" /> 1. Personal Information & Identity
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  First Name <span className="text-rose-600">*</span>
                </label>
                <input
                  type="text"
                  {...form.register("first_name")}
                  className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                  placeholder="e.g. Ramesh"
                />
                {form.formState.errors.first_name && (
                  <p className="text-[11px] text-rose-600 mt-1">
                    {form.formState.errors.first_name.message}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Middle Name
                </label>
                <input
                  type="text"
                  {...form.register("middle_name")}
                  className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                  placeholder="Optional"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Last Name <span className="text-rose-600">*</span>
                </label>
                <input
                  type="text"
                  {...form.register("last_name")}
                  className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                  placeholder="e.g. Sharma"
                />
                {form.formState.errors.last_name && (
                  <p className="text-[11px] text-rose-600 mt-1">
                    {form.formState.errors.last_name.message}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Gender <span className="text-rose-600">*</span>
                </label>
                <select
                  {...form.register("gender")}
                  className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                >
                  <option value="FEMALE">Female</option>
                  <option value="MALE">Male</option>
                  <option value="NON_BINARY">Non-Binary</option>
                  <option value="PREFER_NOT_TO_SAY">Prefer not to say</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Date of Birth <span className="text-rose-600">*</span>{" "}
                  {calculatedAge !== null && (
                    <span className="text-teal-700 font-normal">({calculatedAge} yrs)</span>
                  )}
                </label>
                <input
                  type="date"
                  max={new Date().toISOString().split("T")[0]}
                  {...form.register("date_of_birth")}
                  className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                />
                {form.formState.errors.date_of_birth && (
                  <p className="text-[11px] text-rose-600 mt-1">
                    {form.formState.errors.date_of_birth.message}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Blood Group
                </label>
                <select
                  {...form.register("blood_group")}
                  className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                >
                  <option value="">Select blood group</option>
                  <option value="A+">A+</option>
                  <option value="A-">A-</option>
                  <option value="B+">B+</option>
                  <option value="B-">B-</option>
                  <option value="AB+">AB+</option>
                  <option value="AB-">AB-</option>
                  <option value="O+">O+</option>
                  <option value="O-">O-</option>
                  <option value="UNKNOWN">Unknown</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Marital Status
                </label>
                <select
                  {...form.register("marital_status")}
                  className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                >
                  <option value="">Select status</option>
                  <option value="Single">Single</option>
                  <option value="Married">Married</option>
                  <option value="Divorced">Divorced</option>
                  <option value="Widowed">Widowed</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Occupation
                </label>
                <input
                  type="text"
                  {...form.register("occupation")}
                  className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                  placeholder="e.g. Teacher, Engineer"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Aadhaar Number (12 digits)
                </label>
                <input
                  type="text"
                  maxLength={12}
                  inputMode="numeric"
                  {...form.register("aadhaar_number")}
                  className="w-full text-xs font-mono px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                  placeholder="123456789012"
                />
                {form.formState.errors.aadhaar_number && (
                  <p className="text-[11px] text-rose-600 mt-1">
                    {form.formState.errors.aadhaar_number.message}
                  </p>
                )}
              </div>
            </div>
          </section>

          {/* 2. Contact & Address */}
          <section className="bg-white p-6 rounded-lg border border-slate-200 shadow-xs">
            <h2 className="text-sm font-semibold text-slate-900 flex items-center gap-2 pb-3 border-b border-slate-100 mb-4">
              <Phone size={16} className="text-teal-700" /> 2. Contact & Residential Address
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Primary Mobile Number <span className="text-rose-600">*</span>
                </label>
                <input
                  type="tel"
                  maxLength={10}
                  inputMode="numeric"
                  {...form.register("mobile_number")}
                  className="w-full text-xs font-mono px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                  placeholder="9876543210"
                />
                {form.formState.errors.mobile_number && (
                  <p className="text-[11px] text-rose-600 mt-1">
                    {form.formState.errors.mobile_number.message}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Alternate Mobile
                </label>
                <input
                  type="tel"
                  maxLength={10}
                  inputMode="numeric"
                  {...form.register("alternate_mobile")}
                  className="w-full text-xs font-mono px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                  placeholder="Optional"
                />
                {form.formState.errors.alternate_mobile && (
                  <p className="text-[11px] text-rose-600 mt-1">
                    {form.formState.errors.alternate_mobile.message}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Email</label>
                <input
                  type="email"
                  {...form.register("email")}
                  className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                  placeholder="patient@example.com"
                />
                {form.formState.errors.email && (
                  <p className="text-[11px] text-rose-600 mt-1">
                    {form.formState.errors.email.message}
                  </p>
                )}
              </div>

              <div className="sm:col-span-3">
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Street Address
                </label>
                <textarea
                  rows={2}
                  {...form.register("address")}
                  className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                  placeholder="House number, apartment, street..."
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">City</label>
                <input
                  type="text"
                  {...form.register("city")}
                  className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                  placeholder="e.g. Mumbai"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">State</label>
                <input
                  type="text"
                  {...form.register("state")}
                  className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                  placeholder="e.g. Maharashtra"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">PIN Code</label>
                <input
                  type="text"
                  maxLength={6}
                  inputMode="numeric"
                  {...form.register("pin_code")}
                  className="w-full text-xs font-mono px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                  placeholder="400001"
                />
                {form.formState.errors.pin_code && (
                  <p className="text-[11px] text-rose-600 mt-1">
                    {form.formState.errors.pin_code.message}
                  </p>
                )}
              </div>
            </div>
          </section>

          {/* 3. Emergency Contact & Insurance */}
          <section className="bg-white p-6 rounded-lg border border-slate-200 shadow-xs">
            <h2 className="text-sm font-semibold text-slate-900 flex items-center gap-2 pb-3 border-b border-slate-100 mb-4">
              <Shield size={16} className="text-teal-700" /> 3. Emergency Contact & Insurance
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Emergency Contact Name
                </label>
                <input
                  type="text"
                  {...form.register("emergency_contact_name")}
                  className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                  placeholder="e.g. Sunita Sharma"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Emergency Phone Number
                </label>
                <input
                  type="tel"
                  maxLength={10}
                  inputMode="numeric"
                  {...form.register("emergency_contact_number")}
                  className="w-full text-xs font-mono px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                  placeholder="9876543210"
                />
                {form.formState.errors.emergency_contact_number && (
                  <p className="text-[11px] text-rose-600 mt-1">
                    {form.formState.errors.emergency_contact_number.message}
                  </p>
                )}
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Relationship
                </label>
                <select
                  {...form.register("emergency_contact_relation")}
                  className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                >
                  <option value="">Select relation</option>
                  <option value="Spouse">Spouse</option>
                  <option value="Parent">Parent</option>
                  <option value="Child">Child</option>
                  <option value="Sibling">Sibling</option>
                  <option value="Friend">Friend</option>
                  <option value="Other">Other</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-3 border-t border-slate-100">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Insurance Provider
                </label>
                <input
                  type="text"
                  {...form.register("insurance_provider")}
                  className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                  placeholder="e.g. Star Health / ICICI Lombard"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Policy Number
                </label>
                <input
                  type="text"
                  {...form.register("insurance_policy_number")}
                  className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                  placeholder="e.g. POL-893274"
                />
              </div>
            </div>
          </section>

          {/* 4. Medical History */}
          <section className="bg-white p-6 rounded-lg border border-slate-200 shadow-xs">
            <h2 className="text-sm font-semibold text-slate-900 flex items-center gap-2 pb-3 border-b border-slate-100 mb-4">
              <HeartPulse size={16} className="text-rose-600" /> 4. Medical History & Systemic Conditions
            </h2>
            <p className="text-xs text-slate-500 mb-4">
              Identify potential medical risks before administering local anesthesia or dental procedures.
            </p>

            {/* Condition Checkbox Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5 p-4 bg-slate-50 rounded-lg border border-slate-100">
              {[
                { name: "medical_history.diabetes", label: "Diabetes" },
                { name: "medical_history.hypertension", label: "Hypertension / BP" },
                { name: "medical_history.cardiac_disease", label: "Cardiac Disease" },
                { name: "medical_history.thyroid", label: "Thyroid Disorder" },
                { name: "medical_history.asthma", label: "Asthma" },
                { name: "medical_history.epilepsy", label: "Epilepsy / Seizures" },
                { name: "medical_history.pregnancy", label: "Pregnancy" },
                { name: "medical_history.smoking", label: "Smoking" },
                { name: "medical_history.tobacco", label: "Chewing Tobacco" },
                { name: "medical_history.alcohol", label: "Alcohol Consumption" },
              ].map((item) => (
                <label
                  key={item.name}
                  className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer select-none"
                >
                  <input
                    type="checkbox"
                    // @ts-expect-error react-hook-form nested path
                    {...form.register(item.name)}
                    className="rounded text-teal-600 focus:ring-teal-500 h-4 w-4"
                  />
                  <span>{item.label}</span>
                </label>
              ))}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Known Drug & Material Allergies
                </label>
                <textarea
                  rows={2}
                  {...form.register("medical_history.allergies")}
                  className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                  placeholder="e.g. Penicillin, Latex, NSAIDs..."
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Current Medications
                </label>
                <textarea
                  rows={2}
                  {...form.register("medical_history.current_medications")}
                  className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                  placeholder="Blood thinners, Metformin, Amlodipine..."
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Previous Surgeries & Hospitalizations
                </label>
                <textarea
                  rows={2}
                  {...form.register("medical_history.previous_surgeries")}
                  className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                  placeholder="Stent placement, Appendectomy..."
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Infectious Diseases
                </label>
                <textarea
                  rows={2}
                  {...form.register("medical_history.infectious_diseases")}
                  className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                  placeholder="Hepatitis B/C, HIV, Tuberculosis..."
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Primary Physician Name
                </label>
                <input
                  type="text"
                  {...form.register("medical_history.physician_name")}
                  className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                  placeholder="Dr. R. K. Gupta"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Physician Contact Number
                </label>
                <input
                  type="tel"
                  maxLength={10}
                  inputMode="numeric"
                  {...form.register("medical_history.physician_contact")}
                  className="w-full text-xs font-mono px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                  placeholder="9876543210"
                />
              </div>
            </div>
          </section>

          {/* 5. Dental History */}
          <section className="bg-white p-6 rounded-lg border border-slate-200 shadow-xs">
            <h2 className="text-sm font-semibold text-slate-900 flex items-center gap-2 pb-3 border-b border-slate-100 mb-4">
              <Stethoscope size={16} className="text-teal-700" /> 5. Dental History & Oral Hygiene
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
              <div className="sm:col-span-2">
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Chief Complaint
                </label>
                <textarea
                  rows={2}
                  {...form.register("dental_history.chief_complaint")}
                  className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                  placeholder="e.g. Severe toothache on lower right molar when drinking cold water..."
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Previous Dental Treatments
                </label>
                <input
                  type="text"
                  {...form.register("dental_history.previous_dental_treatments")}
                  className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                  placeholder="Root canal 2024, extraction, braces..."
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Brushing Frequency
                </label>
                <select
                  {...form.register("dental_history.brushing_frequency")}
                  className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                >
                  <option value="Once daily">Once daily</option>
                  <option value="Twice daily">Twice daily</option>
                  <option value="More than twice">More than twice</option>
                  <option value="Irregular">Irregular</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Last Dental Visit
                </label>
                <input
                  type="date"
                  {...form.register("dental_history.last_dental_visit")}
                  className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                />
              </div>
            </div>

            {/* Dental Symptoms Checkbox Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-4 bg-slate-50 rounded-lg border border-slate-100">
              {[
                { name: "dental_history.flossing_habit", label: "Daily Flossing" },
                { name: "dental_history.bleeding_gums", label: "Bleeding Gums" },
                { name: "dental_history.sensitivity", label: "Teeth Sensitivity" },
                { name: "dental_history.grinding", label: "Bruxism / Grinding" },
                { name: "dental_history.jaw_pain", label: "Jaw / Facial Pain" },
                { name: "dental_history.tmj_disorder", label: "TMJ Clicking / Disorder" },
                { name: "dental_history.tobacco_habit", label: "Tobacco Stain/Habit" },
              ].map((item) => (
                <label
                  key={item.name}
                  className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer select-none"
                >
                  <input
                    type="checkbox"
                    // @ts-expect-error react-hook-form nested path
                    {...form.register(item.name)}
                    className="rounded text-teal-600 focus:ring-teal-500 h-4 w-4"
                  />
                  <span>{item.label}</span>
                </label>
              ))}
            </div>
          </section>

          {/* 6. Clinical Notes */}
          <section className="bg-white p-6 rounded-lg border border-slate-200 shadow-xs">
            <h2 className="text-sm font-semibold text-slate-900 flex items-center gap-2 pb-3 border-b border-slate-100 mb-4">
              <FileSpreadsheet size={16} className="text-teal-700" /> 6. Clinical & Practice Notes
            </h2>
            <textarea
              rows={3}
              {...form.register("notes")}
              className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
              placeholder="Additional clinical notes, patient behavior, special requests..."
            />
          </section>

          {/* Form Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-200">
            <Link
              href="/patients"
              className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-900"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={mutation.isPending}
              className="inline-flex items-center gap-2 bg-teal-700 hover:bg-teal-800 text-white font-semibold text-xs px-5 py-2.5 rounded-md shadow-sm transition-colors disabled:opacity-50"
            >
              {mutation.isPending ? "Registering..." : "Register Patient"}
            </button>
          </div>
        </form>
      </div>
    </main>
  );
}
