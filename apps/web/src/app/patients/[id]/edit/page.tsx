"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { use, useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import {
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  HeartPulse,
  Phone,
  Shield,
  Stethoscope,
  User,
} from "lucide-react";
import { z } from "zod";

import { api } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";

const MOBILE_REGEX = /^[6-9]\d{9}$/;
const AADHAAR_REGEX = /^\d{12}$/;
const PIN_REGEX = /^\d{6}$/;

const editPatientSchema = z
  .object({
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

    mobile_number: z
      .string()
      .regex(MOBILE_REGEX, "Enter a valid 10-digit Indian mobile number"),
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

    emergency_contact_name: z.string().max(160).optional().or(z.literal("")),
    emergency_contact_number: z
      .string()
      .regex(MOBILE_REGEX, "Enter a valid 10-digit mobile number")
      .optional()
      .or(z.literal("")),
    emergency_contact_relation: z.string().max(60).optional().or(z.literal("")),

    insurance_provider: z.string().max(160).optional().or(z.literal("")),
    insurance_policy_number: z.string().max(100).optional().or(z.literal("")),

    notes: z.string().optional().or(z.literal("")),

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

type EditPatientFormValues = z.infer<typeof editPatientSchema>;

export default function EditPatientPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const queryClient = useQueryClient();
  const [duplicateWarnings, setDuplicateWarnings] = useState<{ field: string; patient_number: string }[]>([]);

  const patientQuery = useQuery({
    queryKey: ["patient", id],
    queryFn: async () => {
      const res = await api.get(`/patients/${id}`);
      return res.data;
    },
  });

  const form = useForm<EditPatientFormValues>({
    resolver: zodResolver(editPatientSchema) as any,
  });

  useEffect(() => {
    if (patientQuery.data) {
      const p = patientQuery.data;
      form.reset({
        first_name: p.first_name || "",
        middle_name: p.middle_name || "",
        last_name: p.last_name || "",
        gender: p.gender || "FEMALE",
        date_of_birth: p.date_of_birth || "",
        blood_group: p.blood_group || "",
        marital_status: p.marital_status || "",
        occupation: p.occupation || "",
        aadhaar_number: p.aadhaar_number || "",
        preferred_language: p.preferred_language || "English",
        mobile_number: p.mobile_number || "",
        alternate_mobile: p.alternate_mobile || "",
        email: p.email || "",
        address: p.address || "",
        city: p.city || "",
        state: p.state || "",
        country: p.country || "India",
        pin_code: p.pin_code || "",
        emergency_contact_name: p.emergency_contact_name || "",
        emergency_contact_number: p.emergency_contact_number || "",
        emergency_contact_relation: p.emergency_contact_relation || "",
        insurance_provider: p.insurance_provider || "",
        insurance_policy_number: p.insurance_policy_number || "",
        notes: p.notes || "",
        medical_history: {
          diabetes: p.medical_history?.diabetes || false,
          hypertension: p.medical_history?.hypertension || false,
          cardiac_disease: p.medical_history?.cardiac_disease || false,
          thyroid: p.medical_history?.thyroid || false,
          asthma: p.medical_history?.asthma || false,
          epilepsy: p.medical_history?.epilepsy || false,
          pregnancy: p.medical_history?.pregnancy || false,
          allergies: p.medical_history?.allergies || "",
          current_medications: p.medical_history?.current_medications || "",
          smoking: p.medical_history?.smoking || false,
          tobacco: p.medical_history?.tobacco || false,
          alcohol: p.medical_history?.alcohol || false,
          previous_surgeries: p.medical_history?.previous_surgeries || "",
          infectious_diseases: p.medical_history?.infectious_diseases || "",
          physician_name: p.medical_history?.physician_name || "",
          physician_contact: p.medical_history?.physician_contact || "",
          additional_notes: p.medical_history?.additional_notes || "",
        },
        dental_history: {
          chief_complaint: p.dental_history?.chief_complaint || "",
          previous_dental_treatments: p.dental_history?.previous_dental_treatments || "",
          brushing_frequency: p.dental_history?.brushing_frequency || "Twice daily",
          flossing_habit: p.dental_history?.flossing_habit || false,
          tobacco_habit: p.dental_history?.tobacco_habit || false,
          grinding: p.dental_history?.grinding || false,
          jaw_pain: p.dental_history?.jaw_pain || false,
          tmj_disorder: p.dental_history?.tmj_disorder || false,
          sensitivity: p.dental_history?.sensitivity || false,
          bleeding_gums: p.dental_history?.bleeding_gums || false,
          last_dental_visit: p.dental_history?.last_dental_visit || "",
          dental_notes: p.dental_history?.dental_notes || "",
        },
      });
    }
  }, [patientQuery.data, form]);

  const mutation = useMutation({
    mutationFn: async (values: EditPatientFormValues) => {
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

      const res = await api.patch(`/patients/${id}`, payload);
      return res.data;
    },
    onSuccess: (data) => {
      void queryClient.invalidateQueries({ queryKey: ["patient", id] });
      void queryClient.invalidateQueries({ queryKey: ["patients"] });
      if (data.duplicate_warnings && data.duplicate_warnings.length > 0) {
        setDuplicateWarnings(data.duplicate_warnings);
        setTimeout(() => router.push(`/patients/${id}`), 1800);
      } else {
        router.push(`/patients/${id}`);
      }
    },
  });

  if (patientQuery.isLoading) {
    return (
      <main className="max-w-4xl mx-auto px-4 py-12">
        <Skeleton className="h-8 w-48 mb-4" />
        <Skeleton className="h-64 w-full rounded-lg" />
      </main>
    );
  }

  if (patientQuery.isError || !patientQuery.data) {
    return (
      <main className="max-w-4xl mx-auto px-4 py-12 text-center">
        <p className="text-rose-600 font-semibold">Patient record not found or inaccessible.</p>
        <Link href="/patients" className="mt-3 text-teal-700 underline text-xs">
          Return to Patients Directory
        </Link>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-50/60 pb-24">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 pt-8">
        <div className="mb-6">
          <Link
            href={`/patients/${id}`}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-teal-700 hover:text-teal-800 mb-2"
          >
            <ArrowLeft size={14} /> Back to Profile
          </Link>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-slate-900">
                Edit Patient – {patientQuery.data.patient_number}
              </h1>
              <p className="text-sm text-slate-500 mt-0.5">
                Update personal, contact, medical, or dental history records.
              </p>
            </div>
          </div>
        </div>

        {duplicateWarnings.length > 0 && (
          <div className="mb-6 p-4 rounded-lg bg-amber-50 border border-amber-200 text-amber-900 text-xs">
            <p className="font-semibold text-sm">Potential Duplicate Contacts Detected</p>
            <p className="mt-1">
              Changes saved. Another patient matches these contact details. Redirecting to profile...
            </p>
          </div>
        )}

        <form onSubmit={form.handleSubmit((v) => mutation.mutate(v))} className="space-y-6">
          {/* Section 1: Demographics */}
          <section className="bg-white p-6 rounded-lg border border-slate-200 shadow-xs">
            <h2 className="text-sm font-semibold text-slate-900 flex items-center gap-2 pb-3 border-b border-slate-100 mb-4">
              <User size={16} className="text-teal-700" /> Personal Information
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">First Name</label>
                <input
                  type="text"
                  {...form.register("first_name")}
                  className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Middle Name</label>
                <input
                  type="text"
                  {...form.register("middle_name")}
                  className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Last Name</label>
                <input
                  type="text"
                  {...form.register("last_name")}
                  className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Gender</label>
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
                <label className="block text-xs font-semibold text-slate-700 mb-1">Date of Birth</label>
                <input
                  type="date"
                  max={new Date().toISOString().split("T")[0]}
                  {...form.register("date_of_birth")}
                  className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Blood Group</label>
                <select
                  {...form.register("blood_group")}
                  className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                >
                  <option value="">Select</option>
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
                <label className="block text-xs font-semibold text-slate-700 mb-1">Occupation</label>
                <input
                  type="text"
                  {...form.register("occupation")}
                  className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Aadhaar (12 digits)</label>
                <input
                  type="text"
                  maxLength={12}
                  {...form.register("aadhaar_number")}
                  className="w-full text-xs font-mono px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                />
              </div>
            </div>
          </section>

          {/* Section 2: Contact */}
          <section className="bg-white p-6 rounded-lg border border-slate-200 shadow-xs">
            <h2 className="text-sm font-semibold text-slate-900 flex items-center gap-2 pb-3 border-b border-slate-100 mb-4">
              <Phone size={16} className="text-teal-700" /> Contact & Address
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Primary Mobile</label>
                <input
                  type="tel"
                  maxLength={10}
                  {...form.register("mobile_number")}
                  className="w-full text-xs font-mono px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Alternate Mobile</label>
                <input
                  type="tel"
                  maxLength={10}
                  {...form.register("alternate_mobile")}
                  className="w-full text-xs font-mono px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Email</label>
                <input
                  type="email"
                  {...form.register("email")}
                  className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                />
              </div>
              <div className="sm:col-span-3">
                <label className="block text-xs font-semibold text-slate-700 mb-1">Address</label>
                <textarea
                  rows={2}
                  {...form.register("address")}
                  className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">City</label>
                <input
                  type="text"
                  {...form.register("city")}
                  className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">State</label>
                <input
                  type="text"
                  {...form.register("state")}
                  className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">PIN Code</label>
                <input
                  type="text"
                  maxLength={6}
                  {...form.register("pin_code")}
                  className="w-full text-xs font-mono px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                />
              </div>
            </div>
          </section>

          {/* Section 3: Medical History */}
          <section className="bg-white p-6 rounded-lg border border-slate-200 shadow-xs">
            <h2 className="text-sm font-semibold text-slate-900 flex items-center gap-2 pb-3 border-b border-slate-100 mb-4">
              <HeartPulse size={16} className="text-rose-600" /> Medical History
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4 p-4 bg-slate-50 rounded-lg">
              {[
                { name: "medical_history.diabetes", label: "Diabetes" },
                { name: "medical_history.hypertension", label: "Hypertension" },
                { name: "medical_history.cardiac_disease", label: "Cardiac Disease" },
                { name: "medical_history.thyroid", label: "Thyroid" },
                { name: "medical_history.asthma", label: "Asthma" },
                { name: "medical_history.epilepsy", label: "Epilepsy" },
                { name: "medical_history.pregnancy", label: "Pregnancy" },
                { name: "medical_history.smoking", label: "Smoking" },
                { name: "medical_history.tobacco", label: "Tobacco" },
                { name: "medical_history.alcohol", label: "Alcohol" },
              ].map((item) => (
                <label key={item.name} className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer">
                  <input
                    type="checkbox"
                    // @ts-expect-error nested path
                    {...form.register(item.name)}
                    className="rounded text-teal-600 focus:ring-teal-500 h-4 w-4"
                  />
                  <span>{item.label}</span>
                </label>
              ))}
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Allergies</label>
                <textarea
                  rows={2}
                  {...form.register("medical_history.allergies")}
                  className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Medications</label>
                <textarea
                  rows={2}
                  {...form.register("medical_history.current_medications")}
                  className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
                />
              </div>
            </div>
          </section>

          {/* Section 4: Dental History */}
          <section className="bg-white p-6 rounded-lg border border-slate-200 shadow-xs">
            <h2 className="text-sm font-semibold text-slate-900 flex items-center gap-2 pb-3 border-b border-slate-100 mb-4">
              <Stethoscope size={16} className="text-teal-700" /> Dental History
            </h2>
            <div className="mb-4">
              <label className="block text-xs font-semibold text-slate-700 mb-1">Chief Complaint</label>
              <textarea
                rows={2}
                {...form.register("dental_history.chief_complaint")}
                className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
              />
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-4 bg-slate-50 rounded-lg">
              {[
                { name: "dental_history.flossing_habit", label: "Daily Flossing" },
                { name: "dental_history.bleeding_gums", label: "Bleeding Gums" },
                { name: "dental_history.sensitivity", label: "Sensitivity" },
                { name: "dental_history.grinding", label: "Grinding" },
                { name: "dental_history.jaw_pain", label: "Jaw Pain" },
                { name: "dental_history.tmj_disorder", label: "TMJ Disorder" },
              ].map((item) => (
                <label key={item.name} className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer">
                  <input
                    type="checkbox"
                    // @ts-expect-error nested path
                    {...form.register(item.name)}
                    className="rounded text-teal-600 focus:ring-teal-500 h-4 w-4"
                  />
                  <span>{item.label}</span>
                </label>
              ))}
            </div>
          </section>

          {/* Section 5: Clinical Notes */}
          <section className="bg-white p-6 rounded-lg border border-slate-200 shadow-xs">
            <h2 className="text-sm font-semibold text-slate-900 pb-3 border-b border-slate-100 mb-4">
              Clinical & Practice Notes
            </h2>
            <textarea
              rows={3}
              {...form.register("notes")}
              className="w-full text-xs px-3 py-2 bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
            />
          </section>

          {/* Submit Buttons */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-200">
            <Link href={`/patients/${id}`} className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-900">
              Cancel
            </Link>
            <button
              type="submit"
              disabled={mutation.isPending}
              className="px-5 py-2.5 bg-teal-700 hover:bg-teal-800 text-white font-semibold text-xs rounded-md shadow-sm transition-colors disabled:opacity-50"
            >
              {mutation.isPending ? "Saving Changes..." : "Save Patient Profile"}
            </button>
          </div>
        </form>
      </div>
    </main>
  );
}
