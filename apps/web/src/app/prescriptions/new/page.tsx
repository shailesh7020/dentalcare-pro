"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  AlertCircle,
  AlertTriangle,
  ArrowLeft,
  Calendar,
  CheckCircle2,
  FileCheck,
  FileText,
  HeartPulse,
  Pill,
  Plus,
  Search,
  Sparkles,
  Stethoscope,
  Trash2,
  User,
  Zap,
} from "lucide-react";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import type {
  DosageFrequency,
  MedicineCatalogItem,
  MedicineForm,
  PrescriptionCreate,
  PrescriptionDetail,
  PrescriptionItemCreate,
  PrescriptionTemplateItem,
} from "../types";

function MedicineStockBadge({ medicineName }: { medicineName: string }) {
  const stockQuery = useQuery({
    queryKey: ["medicine-stock", medicineName],
    queryFn: async () => {
      if (!medicineName || medicineName.trim().length < 2) return null;
      try {
        const res = await api.get("/inventory/medicines/check-availability", {
          params: { name: medicineName.trim() },
        });
        return res.data;
      } catch {
        return null;
      }
    },
    enabled: Boolean(medicineName && medicineName.trim().length >= 2),
    staleTime: 30_000,
  });

  const data = stockQuery.data;
  if (!data) return null;

  if (data.status === "IN_STOCK") {
    return (
      <span className="inline-block text-[10px] px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 font-medium">
        ✓ In Stock ({data.available_quantity} {data.unit || ""})
      </span>
    );
  }
  if (data.status === "LOW_STOCK") {
    return (
      <span className="inline-block text-[10px] px-1.5 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200 font-medium">
        ⚠ Low Stock ({data.available_quantity} {data.unit || ""})
      </span>
    );
  }
  if (data.status === "OUT_OF_STOCK") {
    return (
      <span className="inline-block text-[10px] px-1.5 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200 font-medium">
        ✕ Out of Stock
      </span>
    );
  }
  if (data.status === "EXPIRED") {
    return (
      <span className="inline-block text-[10px] px-1.5 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200 font-medium">
        ⚠ Expired Batch
      </span>
    );
  }
  return null;
}

const QUICK_DIAGNOSIS_CHIPS = [
  "Dental Caries & Odontalgia",
  "Acute Apical Periodontitis (RCT)",
  "Post-Extraction Surgical Prophylaxis",
  "Pericoronitis / Wisdom Tooth Pain",
  "Acute Gingivitis / Periodontitis",
  "Post-Implant Surgical Coverage",
  "Dentin Hypersensitivity",
  "Oral Ulcer / Aphthous Stomatitis",
];

const QUICK_ADD_MEDICINES: PrescriptionItemCreate[] = [
  {
    medicine_name: "Augmentin 625 Duo",
    generic_name: "Amoxicillin + Clavulanic Acid",
    brand_name: "Augmentin 625 Duo",
    strength: "625 mg",
    form: "TABLET",
    dosage: "1 tablet",
    route: "Oral",
    frequency: "BD",
    duration: "5 days",
    quantity: 10,
    timing: "Morning - Night",
    food_instructions: "After food",
    notes: "Broad-spectrum antibiotic coverage.",
  },
  {
    medicine_name: "Amoxicillin",
    generic_name: "Amoxicillin",
    brand_name: "Amoxil 500",
    strength: "500 mg",
    form: "CAPSULE",
    dosage: "1 capsule",
    route: "Oral",
    frequency: "TDS",
    duration: "5 days",
    quantity: 15,
    timing: "Morning - Afternoon - Night",
    food_instructions: "After food",
    notes: "First-line antibacterial coverage.",
  },
  {
    medicine_name: "Zerodol-SP",
    generic_name: "Aceclofenac + Paracetamol + Serratiopeptidase",
    brand_name: "Zerodol-SP",
    strength: "100/325/15 mg",
    form: "TABLET",
    dosage: "1 tablet",
    route: "Oral",
    frequency: "BD",
    duration: "5 days",
    quantity: 10,
    timing: "Morning - Night",
    food_instructions: "After food",
    notes: "Anti-inflammatory, analgesic & anti-edema.",
  },
  {
    medicine_name: "Ketorol DT",
    generic_name: "Ketorolac Tromethamine",
    brand_name: "Ketorol DT",
    strength: "10 mg",
    form: "TABLET",
    dosage: "1 tablet",
    route: "Oral",
    frequency: "SOS",
    duration: "3 days",
    quantity: 6,
    timing: "As needed for severe pain",
    food_instructions: "Dissolve in half glass water after food",
    notes: "For acute dental pain relief.",
  },
  {
    medicine_name: "Dolo 650",
    generic_name: "Paracetamol",
    brand_name: "Dolo 650",
    strength: "650 mg",
    form: "TABLET",
    dosage: "1 tablet",
    route: "Oral",
    frequency: "TDS",
    duration: "3 days",
    quantity: 9,
    timing: "Morning - Afternoon - Night",
    food_instructions: "After food",
    notes: "Antipyretic and mild analgesic.",
  },
  {
    medicine_name: "Flagyl 400",
    generic_name: "Metronidazole",
    brand_name: "Flagyl 400",
    strength: "400 mg",
    form: "TABLET",
    dosage: "1 tablet",
    route: "Oral",
    frequency: "TDS",
    duration: "5 days",
    quantity: 15,
    timing: "Morning - Afternoon - Night",
    food_instructions: "After food (Avoid alcohol)",
    notes: "Anaerobic infection coverage.",
  },
  {
    medicine_name: "Pan-D 40",
    generic_name: "Pantoprazole + Domperidone",
    brand_name: "Pan-D",
    strength: "40 mg",
    form: "CAPSULE",
    dosage: "1 capsule",
    route: "Oral",
    frequency: "OD",
    duration: "5 days",
    quantity: 5,
    timing: "Morning empty stomach",
    food_instructions: "30 mins before breakfast",
    notes: "Gastroprotection with antibiotics/NSAIDs.",
  },
  {
    medicine_name: "Chymoral Forte",
    generic_name: "Trypsin + Chymotrypsin",
    brand_name: "Chymoral Forte",
    strength: "100000 AU",
    form: "TABLET",
    dosage: "1 tablet",
    route: "Oral",
    frequency: "TDS",
    duration: "5 days",
    quantity: 15,
    timing: "Morning - Afternoon - Night",
    food_instructions: "30 mins before food",
    notes: "Reduces post-operative swelling.",
  },
  {
    medicine_name: "Hexidine Mouthwash",
    generic_name: "Chlorhexidine Gluconate",
    brand_name: "Hexidine 0.2%",
    strength: "0.2% w/v",
    form: "MOUTHWASH",
    dosage: "10 ml undiluted",
    route: "Topical",
    frequency: "BD",
    duration: "7 days",
    quantity: 1,
    timing: "Morning - Night",
    food_instructions: "Rinse 30s after meals; do not eat/drink for 30m",
    notes: "Antiseptic plaque & gingival control.",
  },
  {
    medicine_name: "Sensodent-K Paste",
    generic_name: "Potassium Nitrate",
    brand_name: "Sensodent-K",
    strength: "5% w/w",
    form: "DENTAL_PASTE",
    dosage: "Pea-sized amount",
    route: "Topical",
    frequency: "BD",
    duration: "14 days",
    quantity: 1,
    timing: "Morning - Night",
    food_instructions: "Apply with soft brush, leave 2 mins then spit",
    notes: "Desensitizing dental paste.",
  },
];

function computeAutoQuantity(
  frequency: string,
  duration: string,
  form: string
): number | null {
  if (["MOUTHWASH", "DENTAL_PASTE", "GEL", "CREAM", "SYRUP", "DROPS"].includes(form)) {
    return 1;
  }
  const daysMatch = duration.match(/(\d+)/);
  const days = daysMatch ? parseInt(daysMatch[1], 10) : 0;
  if (!days || days <= 0) return null;

  const freqMap: Record<string, number> = {
    OD: 1,
    BD: 2,
    TDS: 3,
    QID: 4,
    SOS: 2,
    STAT: 1,
  };
  const perDay = freqMap[frequency] ?? 2;
  return Math.max(1, perDay * days);
}

function PrescriptionWizardContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const queryPatientId = searchParams.get("patient_id") || "";
  const queryTreatmentId = searchParams.get("treatment_id") || "";
  const queryAppointmentId = searchParams.get("appointment_id") || "";

  const [patientId, setPatientId] = useState<string>(queryPatientId);
  const [patientSearch, setPatientSearch] = useState<string>("");
  const [diagnosis, setDiagnosis] = useState<string>("Dental Caries & Odontalgia");
  const [instructions, setInstructions] = useState<string>(
    "1. Complete the full antibiotic course as prescribed.\n2. Take painkillers after meals.\n3. Warm saline gargles 3-4 times daily.\n4. Return immediately if you experience severe pain, swelling, or allergic rash."
  );
  const [notes, setNotes] = useState<string>("");
  const [followUpDate, setFollowUpDate] = useState<string>("");
  const [sendWhatsAppAfterIssue, setSendWhatsAppAfterIssue] = useState<boolean>(false);

  const [items, setItems] = useState<PrescriptionItemCreate[]>([
    {
      medicine_name: "Amoxicillin",
      generic_name: "Amoxicillin",
      brand_name: "Amoxil 500",
      strength: "500 mg",
      form: "CAPSULE",
      dosage: "1 capsule",
      route: "Oral",
      frequency: "TDS",
      duration: "5 days",
      quantity: 15,
      timing: "Morning - Afternoon - Night",
      food_instructions: "After food",
      notes: "First-line antibacterial coverage.",
    },
    {
      medicine_name: "Dolo 650",
      generic_name: "Paracetamol",
      brand_name: "Dolo 650",
      strength: "650 mg",
      form: "TABLET",
      dosage: "1 tablet",
      route: "Oral",
      frequency: "TDS",
      duration: "3 days",
      quantity: 9,
      timing: "Morning - Afternoon - Night",
      food_instructions: "After food",
      notes: "Antipyretic and mild analgesic.",
    },
  ]);

  const [medicineQuery, setMedicineQuery] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Fetch Patient Details if patientId set
  const patientQuery = useQuery({
    queryKey: ["patient-detail", patientId],
    queryFn: async () => {
      if (!patientId) return null;
      const res = await api.get(`/patients/${patientId}`);
      return res.data;
    },
    enabled: Boolean(patientId),
  });

  // Search Patients if selecting
  const patientListQuery = useQuery({
    queryKey: ["patients-search", patientSearch],
    queryFn: async () => {
      const res = await api.get("/patients", {
        params: { search: patientSearch.trim() || undefined, limit: 15 },
      });
      const data = res.data;
      if (Array.isArray(data)) return data;
      if (Array.isArray(data?.items)) return data.items;
      return [];
    },
    enabled: !patientId,
  });

  // Fetch Procedure Templates
  const templatesQuery = useQuery({
    queryKey: ["prescription-templates"],
    queryFn: async () => {
      const res = await api.get<PrescriptionTemplateItem[]>(
        "/prescriptions/templates"
      );
      return res.data;
    },
  });

  // Autocomplete Medication Search
  const medicinesCatalogQuery = useQuery({
    queryKey: ["medicines-search", medicineQuery],
    queryFn: async () => {
      if (!medicineQuery || medicineQuery.length < 2) return [];
      const res = await api.get<MedicineCatalogItem[]>(
        "/prescriptions/medicines/search",
        {
          params: { q: medicineQuery, limit: 8 },
        }
      );
      return res.data;
    },
    enabled: medicineQuery.length >= 2,
  });

  const patient = patientQuery.data;

  // Compute patient allergy & medical risk flags
  const med = patient?.medical_history;
  const criticalConditions = [
    med?.cardiac_disease && "Cardiac Condition",
    med?.hypertension && "Hypertension",
    med?.diabetes && "Diabetic",
    med?.asthma && "Asthma",
    med?.pregnancy && "Pregnancy",
    med?.allergies && `ALLERGIES: ${med.allergies}`,
  ].filter(Boolean) as string[];

  // Duplicate medicines check
  const duplicateNames = items
    .map((it) => it.medicine_name.trim().toLowerCase())
    .filter((name, idx, arr) => name && arr.indexOf(name) !== idx);

  // Apply Template
  const applyTemplate = (tmpl: PrescriptionTemplateItem) => {
    if (tmpl.diagnosis_template) {
      setDiagnosis(tmpl.diagnosis_template);
    } else if (tmpl.name) {
      setDiagnosis(tmpl.name);
    }
    if (tmpl.instructions_template) {
      setInstructions(tmpl.instructions_template);
    }
    if (tmpl.default_items && tmpl.default_items.length > 0) {
      setItems(
        tmpl.default_items.map((item) => ({
          medicine_name: item.medicine_name,
          generic_name: item.generic_name || item.medicine_name,
          brand_name: item.brand_name || item.medicine_name,
          strength: item.strength || "",
          form: (item.form as MedicineForm) || "TABLET",
          dosage: item.dosage || "1 tablet",
          route: item.route || "Oral",
          frequency: (item.frequency as DosageFrequency) || "BD",
          duration: item.duration || "5 days",
          quantity: item.quantity || 10,
          timing: item.timing || "",
          food_instructions: item.food_instructions || "After food",
          notes: item.notes || "",
        }))
      );
    }
  };

  // Toggle Quick-Add Medicine
  const toggleQuickMedicine = (preset: PrescriptionItemCreate) => {
    const existsIdx = items.findIndex(
      (it) =>
        it.medicine_name.trim().toLowerCase() ===
        preset.medicine_name.trim().toLowerCase()
    );
    if (existsIdx >= 0) {
      setItems((prev) => prev.filter((_, i) => i !== existsIdx));
    } else {
      setItems((prev) => [...prev, { ...preset }]);
    }
  };

  // Add Item from Catalog
  const addMedicineFromCatalog = (medItem: MedicineCatalogItem) => {
    const freq = medItem.default_frequency || "BD";
    const dur = medItem.default_duration || "5 days";
    const form = medItem.form || "TABLET";
    const newItem: PrescriptionItemCreate = {
      medicine_name: medItem.brand_name || medItem.generic_name,
      generic_name: medItem.generic_name,
      brand_name: medItem.brand_name,
      strength: medItem.strength || "",
      form,
      dosage: medItem.standard_dosage || "1 tablet",
      route: medItem.default_route || "Oral",
      frequency: freq,
      duration: dur,
      quantity: computeAutoQuantity(freq, dur, form) ?? 10,
      timing: "Morning - Night",
      food_instructions: medItem.default_instructions || "After food",
      notes: medItem.notes || "",
    };
    setItems((prev) => [...prev, newItem]);
    setMedicineQuery("");
  };

  // Add Blank Row
  const addBlankItem = () => {
    setItems((prev) => [
      ...prev,
      {
        medicine_name: "",
        generic_name: "",
        brand_name: "",
        strength: "500 mg",
        form: "TABLET",
        dosage: "1 tablet",
        route: "Oral",
        frequency: "BD",
        duration: "5 days",
        quantity: 10,
        timing: "Morning - Night",
        food_instructions: "After food",
        notes: "",
      },
    ]);
  };

  const removeItem = (index: number) => {
    setItems((prev) => prev.filter((_, idx) => idx !== index));
  };

  const updateItem = (index: number, field: keyof PrescriptionItemCreate, val: any) => {
    setItems((prev) => {
      const updated = [...prev];
      const nextRow = { ...updated[index], [field]: val };
      if (field === "frequency" || field === "duration" || field === "form") {
        const autoQty = computeAutoQuantity(
          String(nextRow.frequency || "BD"),
          String(nextRow.duration || "5 days"),
          String(nextRow.form || "TABLET")
        );
        if (autoQty !== null) {
          nextRow.quantity = autoQty;
        }
      }
      updated[index] = nextRow;
      return updated;
    });
  };

  // Mutation to Create Prescription
  const createMutation = useMutation({
    mutationFn: async ({
      issueImmediately,
      alsoSendWhatsApp,
    }: {
      issueImmediately: boolean;
      alsoSendWhatsApp?: boolean;
    }) => {
      setErrorMessage(null);
      setSendWhatsAppAfterIssue(Boolean(alsoSendWhatsApp));
      if (!patientId) {
        throw new Error("Please select a patient first.");
      }
      const validItems = items.filter((it) => it.medicine_name.trim().length > 0);
      if (issueImmediately && validItems.length === 0) {
        throw new Error("Please add at least one medicine before issuing.");
      }
      if (duplicateNames.length > 0) {
        throw new Error(
          `Duplicate medicine detected: ${duplicateNames[0]}. Please remove duplicates.`
        );
      }

      const finalDiagnosis =
        diagnosis.trim() || "General Dental Consultation & Pain Management";

      const payload: any = {
        patient_id: patientId,
        treatment_id: queryTreatmentId || null,
        appointment_id: queryAppointmentId || null,
        diagnosis: finalDiagnosis,
        notes: notes.trim() || null,
        instructions: instructions.trim() || null,
        follow_up_date: followUpDate || null,
        items: validItems.map((it) => ({
          ...it,
          strength: (it.strength || "Standard").trim(),
          dosage: (it.dosage || "1 unit").trim(),
          duration: (it.duration || "5 days").trim(),
          quantity: Math.max(1, Number(it.quantity) || 1),
        })),
        issue_immediately: issueImmediately,
      };

      const res = await api.post<PrescriptionDetail>("/prescriptions", payload);
      const createdRx = res.data;

      if (alsoSendWhatsApp && createdRx?.id) {
        try {
          await api.post(`/prescriptions/${createdRx.id}/send-whatsapp`, {});
        } catch (waErr) {
          console.warn("WhatsApp auto-send warning:", waErr);
        }
      }

      return { createdRx, sentWhatsApp: Boolean(alsoSendWhatsApp) };
    },
    onSuccess: ({ createdRx, sentWhatsApp }) => {
      router.push(
        `/prescriptions/${createdRx.id}${sentWhatsApp ? "?whatsapp=sent" : ""}`
      );
    },
    onError: (err: any) => {
      const rawDetail = err.response?.data?.detail;
      let formatted = err.message || "Failed to create prescription.";
      if (typeof rawDetail === "string") {
        formatted = rawDetail;
      } else if (Array.isArray(rawDetail)) {
        formatted = rawDetail
          .map((d: any) => `${(d.loc || []).slice(-1)[0] || "Field"}: ${d.msg}`)
          .join(" | ");
      }
      setErrorMessage(formatted);
    },
  });

  return (
    <main className="min-h-screen bg-slate-50/60 pb-28">
      {/* Top Header */}
      <div className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-2xs">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Link
              href="/prescriptions"
              className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-md transition-colors"
              title="Back to Prescriptions"
            >
              <ArrowLeft size={18} />
            </Link>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold text-slate-900">
                  Write Clinical Prescription
                </h1>
                <span className="text-xs bg-teal-50 text-teal-700 border border-teal-200 px-2 py-0.5 rounded-full font-semibold">
                  1-Click Fast Rx Pad
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Tap a procedure template or quick medicine pill below to issue & WhatsApp Rx in seconds
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() =>
                createMutation.mutate({
                  issueImmediately: false,
                  alsoSendWhatsApp: false,
                })
              }
              disabled={createMutation.isPending}
              className="px-3.5 py-2 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-semibold rounded-md shadow-2xs disabled:opacity-50 transition-colors"
            >
              Save as Draft
            </button>
            <button
              onClick={() =>
                createMutation.mutate({
                  issueImmediately: true,
                  alsoSendWhatsApp: false,
                })
              }
              disabled={createMutation.isPending}
              className="px-4 py-2 bg-teal-700 hover:bg-teal-800 text-white text-xs font-semibold rounded-md shadow-2xs disabled:opacity-50 transition-colors flex items-center gap-1.5"
            >
              <CheckCircle2 size={14} />
              {createMutation.isPending && !sendWhatsAppAfterIssue
                ? "Issuing..."
                : "Issue & Sign Prescription"}
            </button>
            <button
              onClick={() =>
                createMutation.mutate({
                  issueImmediately: true,
                  alsoSendWhatsApp: true,
                })
              }
              disabled={createMutation.isPending}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-md shadow-xs disabled:opacity-50 transition-colors flex items-center gap-1.5"
              title="Issue prescription and immediately send the PDF directly to the patient's WhatsApp"
            >
              <CheckCircle2 size={14} />
              {createMutation.isPending && sendWhatsAppAfterIssue
                ? "Sending PDF to WhatsApp..."
                : "Issue & Send PDF on WhatsApp"}
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pt-6 space-y-6">
        {/* Error Notification */}
        {errorMessage && (
          <div className="p-4 bg-rose-50 border border-rose-200 rounded-lg flex items-start gap-3 text-rose-800 text-xs">
            <AlertCircle size={17} className="text-rose-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-bold">Validation Error</p>
              <p className="mt-0.5">{errorMessage}</p>
            </div>
          </div>
        )}

        {/* Section 1: Patient Selection & Medical Alerts */}
        <section className="bg-white p-5 rounded-lg border border-slate-200 shadow-2xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <User size={16} className="text-teal-600" />
              <h2 className="text-sm font-bold text-slate-900">
                Patient Encounter
              </h2>
            </div>
            {patient && (
              <span className="text-xs font-mono bg-slate-100 text-slate-700 px-2 py-0.5 rounded">
                ID: {patient.patient_number}
              </span>
            )}
          </div>

          {!patientId ? (
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-700">
                Search & Select Patient:
              </label>
              <div className="relative">
                <Search
                  size={15}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400"
                />
                <input
                  type="text"
                  placeholder="Type patient name or mobile number..."
                  value={patientSearch}
                  onChange={(e) => setPatientSearch(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 text-xs bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:ring-1 focus:ring-teal-600"
                />
              </div>

              {patientListQuery.data && patientListQuery.data.length > 0 && (
                <div className="bg-white border border-slate-200 rounded-md shadow-md divide-y divide-slate-100 max-h-48 overflow-y-auto">
                  {patientListQuery.data.map((p: any) => (
                    <button
                      key={p.id}
                      onClick={() => {
                        setPatientId(p.id);
                        setPatientSearch("");
                      }}
                      className="w-full px-3 py-2 text-left hover:bg-teal-50 flex items-center justify-between text-xs"
                    >
                      <span className="font-semibold text-slate-800">
                        {p.first_name} {p.last_name}
                      </span>
                      <span className="text-slate-500 font-mono">
                        {p.patient_number} · {p.mobile_number}
                      </span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-slate-50 p-3.5 rounded-md border border-slate-100">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <p className="font-bold text-slate-900 text-sm">
                    {patient?.first_name} {patient?.last_name}
                  </p>
                  <span className="text-xs text-slate-500">
                    ({patient?.gender}, {patient?.age} yrs)
                  </span>
                </div>
                <p className="text-xs text-slate-500">
                  Mobile: {patient?.mobile_number} · City: {patient?.city || "N/A"}
                </p>
              </div>

              {!queryPatientId && (
                <button
                  onClick={() => setPatientId("")}
                  className="text-xs text-teal-700 hover:underline font-medium"
                >
                  Change Patient
                </button>
              )}
            </div>
          )}

          {/* Prominent Medical Alert Banner */}
          {criticalConditions.length > 0 && (
            <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-md flex items-start gap-2.5 text-xs text-rose-900 animate-in fade-in duration-200">
              <AlertTriangle size={17} className="text-rose-600 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold text-rose-800 uppercase tracking-wide mr-2">
                  Clinical Allergies & Warnings:
                </span>
                <span className="font-semibold">
                  {criticalConditions.join("  |  ")}
                </span>
              </div>
            </div>
          )}

          {/* Quick Diagnosis Bar right at the top */}
          <div className="pt-2 border-t border-slate-100 space-y-2">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <label className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                <Stethoscope size={14} className="text-teal-600" />
                Clinical Diagnosis / Indication:
              </label>
              <span className="text-[11px] text-slate-400">
                Tap a common diagnosis chip or type custom diagnosis
              </span>
            </div>
            <input
              type="text"
              value={diagnosis}
              onChange={(e) => setDiagnosis(e.target.value)}
              placeholder="e.g. Dental Caries & Odontalgia / Post-extraction surgical coverage"
              className="w-full px-3 py-2 text-xs font-medium bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:ring-1 focus:ring-teal-600 text-slate-900"
            />
            <div className="flex flex-wrap gap-1.5">
              {QUICK_DIAGNOSIS_CHIPS.map((chip) => {
                const isSelected = diagnosis.trim().toLowerCase() === chip.toLowerCase();
                return (
                  <button
                    key={chip}
                    type="button"
                    onClick={() => setDiagnosis(chip)}
                    className={`px-2.5 py-1 rounded-full text-[11px] font-medium border transition-all ${
                      isSelected
                        ? "bg-teal-600 text-white border-teal-600 shadow-2xs"
                        : "bg-slate-50 text-slate-600 border-slate-200 hover:border-teal-400 hover:text-teal-700"
                    }`}
                  >
                    {chip}
                  </button>
                );
              })}
            </div>
          </div>
        </section>

        {/* Section 2: 1-Click Procedure Templates */}
        <section className="bg-white p-5 rounded-lg border border-slate-200 shadow-2xs space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Zap size={16} className="text-amber-500" />
              <h2 className="text-sm font-bold text-slate-900">
                1-Click Dental Procedure Templates
              </h2>
            </div>
            <span className="text-[11px] text-slate-500">
              Select a procedure to pre-populate standard medications & instructions
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2.5 pt-1">
            {templatesQuery.data?.map((tmpl) => (
              <button
                key={tmpl.id}
                type="button"
                onClick={() => applyTemplate(tmpl)}
                className="p-3 text-left border border-slate-200 hover:border-teal-500 hover:bg-teal-50/40 rounded-md transition-all group"
              >
                <p className="font-bold text-xs text-slate-800 group-hover:text-teal-800 truncate">
                  {tmpl.name}
                </p>
                <p className="text-[10px] text-slate-500 mt-1 line-clamp-2">
                  {tmpl.description}
                </p>
                <span className="inline-block mt-2 text-[10px] font-semibold text-teal-700">
                  {tmpl.default_items?.length ?? 0} meds · Apply →
                </span>
              </button>
            ))}
          </div>
        </section>

        {/* Section 3: Medication Items */}
        <section className="bg-white p-5 rounded-lg border border-slate-200 shadow-2xs space-y-4">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <Pill size={16} className="text-teal-600" />
              <h2 className="text-sm font-bold text-slate-900">
                Prescribed Medications ({items.length})
              </h2>
            </div>

            {/* Quick Catalog Search */}
            <div className="relative w-full sm:w-80">
              <Search
                size={14}
                className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400"
              />
              <input
                type="text"
                placeholder="Search medication catalog (e.g. Amoxil, Ketorol)..."
                value={medicineQuery}
                onChange={(e) => setMedicineQuery(e.target.value)}
                className="w-full pl-8 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-md focus:bg-white focus:ring-1 focus:ring-teal-600"
              />

              {medicinesCatalogQuery.data &&
                medicinesCatalogQuery.data.length > 0 && (
                  <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-slate-200 rounded-md shadow-lg z-20 divide-y divide-slate-100 max-h-56 overflow-y-auto">
                    {medicinesCatalogQuery.data.map((medItem) => (
                      <button
                        key={medItem.id}
                        type="button"
                        onClick={() => addMedicineFromCatalog(medItem)}
                        className="w-full px-3 py-2 text-left hover:bg-teal-50 flex items-center justify-between text-xs"
                      >
                        <div>
                          <p className="font-bold text-slate-800">
                            {medItem.brand_name} ({medItem.strength})
                          </p>
                          <p className="text-[10px] text-slate-500">
                            {medItem.generic_name} · {medItem.form}
                          </p>
                        </div>
                        <span className="text-[10px] font-semibold text-teal-700">
                          + Add
                        </span>
                      </button>
                    ))}
                  </div>
                )}
            </div>
          </div>

          {/* 1-Click Quick-Add Common Dental Medicines Bar */}
          <div className="bg-slate-50/80 p-3 rounded-lg border border-slate-200/80 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-600">
                ⚡ 1-Click Quick-Add Common Dental Medicines (Tap to Add / Remove):
              </span>
              <button
                type="button"
                onClick={() => setItems([])}
                className="text-[11px] text-rose-600 hover:underline font-medium"
              >
                Clear All
              </button>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {QUICK_ADD_MEDICINES.map((preset) => {
                const isAdded = items.some(
                  (it) =>
                    it.medicine_name.trim().toLowerCase() ===
                    preset.medicine_name.trim().toLowerCase()
                );
                return (
                  <button
                    key={preset.medicine_name}
                    type="button"
                    onClick={() => toggleQuickMedicine(preset)}
                    className={`px-2.5 py-1.5 rounded-md text-xs font-semibold border transition-all flex items-center gap-1.5 ${
                      isAdded
                        ? "bg-emerald-600 text-white border-emerald-600 shadow-2xs"
                        : "bg-white text-slate-700 border-slate-200 hover:border-teal-500 hover:bg-teal-50/40"
                    }`}
                  >
                    <span>{isAdded ? "✓" : "+"}</span>
                    <span>{preset.medicine_name}</span>
                    <span
                      className={`text-[10px] font-normal ${
                        isAdded ? "text-emerald-100" : "text-slate-400"
                      }`}
                    >
                      ({preset.frequency} × {preset.duration})
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Duplicate Warning */}
          {duplicateNames.length > 0 && (
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-md flex items-center gap-2 text-xs text-amber-800">
              <AlertCircle size={15} className="text-amber-600 shrink-0" />
              <span>
                <strong>Warning:</strong> Duplicate medication entry detected: "
                {duplicateNames[0]}". Please remove duplicates before issuing.
              </span>
            </div>
          )}

          {/* Dynamic Items Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-50 text-[11px] font-bold text-slate-600 uppercase border-b border-slate-200">
                  <th className="py-2.5 px-3 min-w-[160px]">Medicine Name</th>
                  <th className="py-2.5 px-3 min-w-[110px]">Form</th>
                  <th className="py-2.5 px-3 min-w-[100px]">Strength</th>
                  <th className="py-2.5 px-3 min-w-[100px]">Dosage</th>
                  <th className="py-2.5 px-3 min-w-[90px]">Frequency</th>
                  <th className="py-2.5 px-3 min-w-[110px]">Duration</th>
                  <th className="py-2.5 px-3 min-w-[70px]">Qty</th>
                  <th className="py-2.5 px-3 min-w-[120px]">Food & Timing</th>
                  <th className="py-2.5 px-3 text-right">Del</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {items.map((item, idx) => (
                  <tr key={idx} className="hover:bg-slate-50/50">
                    {/* Name */}
                    <td className="py-2 px-2">
                      <input
                        type="text"
                        value={item.medicine_name}
                        onChange={(e) =>
                          updateItem(idx, "medicine_name", e.target.value)
                        }
                        placeholder="Medicine name"
                        className="w-full px-2 py-1 text-xs border border-slate-200 rounded focus:ring-1 focus:ring-teal-600"
                      />
                      <div className="mt-1">
                        <MedicineStockBadge medicineName={item.medicine_name} />
                      </div>
                    </td>

                    {/* Form */}
                    <td className="py-2 px-2">
                      <select
                        value={item.form}
                        onChange={(e) =>
                          updateItem(idx, "form", e.target.value as MedicineForm)
                        }
                        className="w-full px-2 py-1 text-xs border border-slate-200 rounded focus:ring-1 focus:ring-teal-600 bg-white"
                      >
                        <option value="TABLET">TABLET</option>
                        <option value="CAPSULE">CAPSULE</option>
                        <option value="SYRUP">SYRUP</option>
                        <option value="MOUTHWASH">MOUTHWASH</option>
                        <option value="DENTAL_PASTE">DENTAL PASTE</option>
                        <option value="GEL">GEL</option>
                        <option value="INJECTION">INJECTION</option>
                        <option value="DROPS">DROPS</option>
                      </select>
                    </td>

                    {/* Strength */}
                    <td className="py-2 px-2">
                      <input
                        type="text"
                        value={item.strength || ""}
                        onChange={(e) =>
                          updateItem(idx, "strength", e.target.value)
                        }
                        placeholder="e.g. 500 mg"
                        className="w-full px-2 py-1 text-xs border border-slate-200 rounded focus:ring-1 focus:ring-teal-600"
                      />
                    </td>

                    {/* Dosage */}
                    <td className="py-2 px-2">
                      <input
                        type="text"
                        value={item.dosage}
                        onChange={(e) =>
                          updateItem(idx, "dosage", e.target.value)
                        }
                        placeholder="1 tablet"
                        className="w-full px-2 py-1 text-xs border border-slate-200 rounded focus:ring-1 focus:ring-teal-600"
                      />
                    </td>

                    {/* Frequency */}
                    <td className="py-2 px-2">
                      <select
                        value={item.frequency}
                        onChange={(e) =>
                          updateItem(
                            idx,
                            "frequency",
                            e.target.value as DosageFrequency
                          )
                        }
                        className="w-full px-2 py-1 text-xs border border-slate-200 rounded focus:ring-1 focus:ring-teal-600 bg-white"
                      >
                        <option value="OD">OD (Once daily)</option>
                        <option value="BD">BD (Twice daily)</option>
                        <option value="TDS">TDS (Thrice daily)</option>
                        <option value="QID">QID (4 times daily)</option>
                        <option value="SOS">SOS (As needed)</option>
                        <option value="STAT">STAT (Immediately)</option>
                      </select>
                    </td>

                    {/* Duration */}
                    <td className="py-2 px-2">
                      <input
                        type="text"
                        value={item.duration}
                        onChange={(e) =>
                          updateItem(idx, "duration", e.target.value)
                        }
                        placeholder="5 days"
                        className="w-full px-2 py-1 text-xs border border-slate-200 rounded focus:ring-1 focus:ring-teal-600"
                      />
                      <div className="flex items-center gap-1 mt-1">
                        {["3 days", "5 days", "7 days"].map((durPreset) => (
                          <button
                            key={durPreset}
                            type="button"
                            onClick={() => updateItem(idx, "duration", durPreset)}
                            className={`px-1.5 py-0.5 text-[9px] rounded border ${
                              item.duration === durPreset
                                ? "bg-teal-600 text-white border-teal-600 font-bold"
                                : "bg-slate-100 text-slate-600 border-slate-200 hover:bg-slate-200"
                            }`}
                          >
                            {durPreset.replace(" days", "d")}
                          </button>
                        ))}
                      </div>
                    </td>

                    {/* Quantity */}
                    <td className="py-2 px-2">
                      <input
                        type="number"
                        min="1"
                        value={item.quantity}
                        onChange={(e) =>
                          updateItem(idx, "quantity", parseInt(e.target.value) || 1)
                        }
                        className="w-full px-2 py-1 text-xs border border-slate-200 rounded focus:ring-1 focus:ring-teal-600"
                      />
                    </td>

                    {/* Instructions */}
                    <td className="py-2 px-2">
                      <input
                        type="text"
                        value={item.food_instructions || ""}
                        onChange={(e) =>
                          updateItem(idx, "food_instructions", e.target.value)
                        }
                        placeholder="After food"
                        className="w-full px-2 py-1 text-xs border border-slate-200 rounded focus:ring-1 focus:ring-teal-600"
                      />
                    </td>

                    {/* Delete */}
                    <td className="py-2 px-2 text-right">
                      <button
                        type="button"
                        onClick={() => removeItem(idx)}
                        className="p-1.5 text-slate-400 hover:text-rose-600 rounded transition-colors"
                        title="Remove medication"
                      >
                        <Trash2 size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="pt-2">
            <button
              type="button"
              onClick={addBlankItem}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded transition-colors"
            >
              <Plus size={14} /> Add Another Medication Row
            </button>
          </div>
        </section>

        {/* Section 4: Clinical Diagnosis & Directions */}
        <section className="bg-white p-5 rounded-lg border border-slate-200 shadow-2xs space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
            <Stethoscope size={16} className="text-teal-600" />
            <h2 className="text-sm font-bold text-slate-900">
              Clinical Diagnosis & Instructions
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Diagnosis */}
            <div className="space-y-1 md:col-span-2">
              <label className="text-xs font-semibold text-slate-700">
                Primary Diagnosis: <span className="text-rose-500">*</span>
              </label>
              <input
                type="text"
                value={diagnosis}
                onChange={(e) => setDiagnosis(e.target.value)}
                placeholder="e.g. Acute apical periodontitis #46 / Post-extraction surgical coverage"
                className="w-full px-3 py-2 text-xs border border-slate-200 rounded-md focus:ring-1 focus:ring-teal-600"
              />
            </div>

            {/* Patient Instructions */}
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-700">
                Patient Instructions & Precautions:
              </label>
              <textarea
                rows={4}
                value={instructions}
                onChange={(e) => setInstructions(e.target.value)}
                placeholder="Post-operative care, dietary precautions, warm saline gargles..."
                className="w-full px-3 py-2 text-xs border border-slate-200 rounded-md focus:ring-1 focus:ring-teal-600"
              />
            </div>

            {/* Internal Notes */}
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-700">
                Internal Clinical Notes (Clinician Reference):
              </label>
              <textarea
                rows={4}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Internal notes, stage of treatment, tolerance observations..."
                className="w-full px-3 py-2 text-xs border border-slate-200 rounded-md focus:ring-1 focus:ring-teal-600"
              />
            </div>

            {/* Follow-up Date */}
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-700">
                Follow-up Review Date:
              </label>
              <input
                type="date"
                value={followUpDate}
                onChange={(e) => setFollowUpDate(e.target.value)}
                className="w-full px-3 py-2 text-xs border border-slate-200 rounded-md focus:ring-1 focus:ring-teal-600"
              />
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

export default function NewPrescriptionPage() {
  return (
    <Suspense
      fallback={
        <div className="p-8 max-w-6xl mx-auto space-y-4">
          <Skeleton className="h-10 w-48" />
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-64 w-full" />
        </div>
      }
    >
      <PrescriptionWizardContent />
    </Suspense>
  );
}
