"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { setAccessToken } from "@/lib/auth/token-store";

interface DayHours {
  day: string;
  is_closed: boolean;
  open_time: string;
  close_time: string;
  morning_session: string;
  evening_session: string;
  lunch_break: string;
}

interface ChairItem {
  name: string;
  room_number: string;
  color: string;
  is_active: boolean;
}

interface StaffItem {
  name: string;
  username: string;
  password: string;
  role: string;
}

const STEP_TITLES = [
  "1. Welcome",
  "2. Clinic Info *",
  "3. Admin Account *",
  "4. Working Hours",
  "5. Chairs / Rooms",
  "6. Staff",
  "7. Appointments",
  "8. Patient IDs",
  "9. Invoicing",
  "10. Backups",
  "11. Notifications",
  "12. Preferences",
  "13. Security",
  "14. Review & Finish",
];

const DEFAULT_WORKING_HOURS: DayHours[] = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
].map((day) => ({
  day,
  is_closed: day === "Sunday",
  open_time: "09:00",
  close_time: day === "Saturday" ? "17:00" : "20:00",
  morning_session: "09:00 - 13:30",
  evening_session: day === "Saturday" ? "14:00 - 17:00" : "16:00 - 20:00",
  lunch_break: "13:30 - 16:00",
}));

export default function FirstLaunchSetupWizardPage() {
  const router = useRouter();
  const [step, setStep] = useState<number>(1);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string>("");

  // Step 2: Clinic Information
  const [clinicName, setClinicName] = useState("SmileCare Dental Clinic");
  const [logoDataUrl, setLogoDataUrl] = useState<string>("");
  const [doctorName, setDoctorName] = useState("Dr. Chief Dental Surgeon");
  const [registrationNumber, setRegistrationNumber] = useState("");
  const [gstNumber, setGstNumber] = useState("");
  const [clinicEmail, setClinicEmail] = useState("clinic@dentalcare.com");
  const [clinicPhone, setClinicPhone] = useState("");
  const [alternatePhone, setAlternatePhone] = useState("");
  const [website, setWebsite] = useState("");
  const [address, setAddress] = useState("");
  const [googleMapsUrl, setGoogleMapsUrl] = useState("");
  const [clinicNotes, setClinicNotes] = useState("");

  // Step 3: Administrator Account
  const [adminUsername, setAdminUsername] = useState("admin@dentalcare.com");
  const [adminPassword, setAdminPassword] = useState("Password123!");
  const [adminConfirmPassword, setAdminConfirmPassword] = useState("Password123!");
  const [adminFullName, setAdminFullName] = useState("Dr. Clinic Administrator");
  const [adminEmail, setAdminEmail] = useState("admin@dentalcare.com");
  const [adminMobile, setAdminMobile] = useState("");
  const [securityQuestion, setSecurityQuestion] = useState("What is the name of your first dental clinic?");
  const [securityAnswer, setSecurityAnswer] = useState("");

  // Step 4: Working Hours
  const [workingHours, setWorkingHours] = useState<DayHours[]>(DEFAULT_WORKING_HOURS);
  const [emergencyHours, setEmergencyHours] = useState("24/7 Emergency On-Call Available");

  // Step 5: Treatment Rooms / Chairs
  const [chairs, setChairs] = useState<ChairItem[]>([
    { name: "Chair 1 - Main Operatory", room_number: "Room 101", color: "#0d9488", is_active: TrueBool(true) },
    { name: "Chair 2 - Endodontics & Crown", room_number: "Room 102", color: "#2563eb", is_active: TrueBool(true) },
    { name: "Chair 3 - Hygiene & Pediatric", room_number: "Room 103", color: "#7c3aed", is_active: TrueBool(true) },
  ]);

  // Step 6: Staff (Optional)
  const [staff, setStaff] = useState<StaffItem[]>([]);

  // Step 7: Appointment Settings
  const [apptDuration, setApptDuration] = useState<number>(30);
  const [bufferMinutes, setBufferMinutes] = useState<number>(5);
  const [maxBookingDays, setMaxBookingDays] = useState<number>(90);
  const [allowWalkIns, setAllowWalkIns] = useState<boolean>(true);
  const [allowDoubleBooking, setAllowDoubleBooking] = useState<boolean>(false);
  const [requireConfirmation, setRequireConfirmation] = useState<boolean>(false);

  // Step 8: Patient Number Format
  const [patPrefix, setPatPrefix] = useState<string>("PAT");
  const [patSeparator, setPatSeparator] = useState<string>("-");
  const [patIncludeYear, setPatIncludeYear] = useState<boolean>(false);
  const [patPadding, setPatPadding] = useState<number>(5);
  const [patStartNumber, setPatStartNumber] = useState<number>(1);
  const [patAutoIncrement, setPatAutoIncrement] = useState<boolean>(true);

  // Step 9: Invoice Settings
  const [invPrefix, setInvPrefix] = useState<string>("INV");
  const [invFormat, setInvFormat] = useState<string>("INV-{YYYY}-{SEQ}");
  const [taxEnabled, setTaxEnabled] = useState<boolean>(false);
  const [defaultTaxPercent, setDefaultTaxPercent] = useState<number>(0);
  const [currency, setCurrency] = useState<string>("INR");
  const [decimalPlaces, setDecimalPlaces] = useState<number>(2);
  const [defaultPaymentMethod, setDefaultPaymentMethod] = useState<string>("CASH");

  // Step 10: Backup Settings
  const [autoBackup, setAutoBackup] = useState<boolean>(true);
  const [backupFrequency, setBackupFrequency] = useState<string>("DAILY");
  const [backupFolder, setBackupFolder] = useState<string>("C:\\DentalCarePro_Backups");
  const [cloudBackup, setCloudBackup] = useState<boolean>(false);
  const [encryptBackup, setEncryptBackup] = useState<boolean>(true);
  const [passwordProtectBackup, setPasswordProtectBackup] = useState<boolean>(false);
  const [backupPassword, setBackupPassword] = useState<string>("");

  // Step 11: Notifications
  const [notifAppointment, setNotifAppointment] = useState<boolean>(true);
  const [notifBirthday, setNotifBirthday] = useState<boolean>(true);
  const [notifFollowup, setNotifFollowup] = useState<boolean>(true);
  const [notifPayment, setNotifPayment] = useState<boolean>(true);
  const [channelWhatsapp, setChannelWhatsapp] = useState<boolean>(true);
  const [channelEmail, setChannelEmail] = useState<boolean>(true);
  const [channelSms, setChannelSms] = useState<boolean>(false);

  // Step 12: Preferences
  const [theme, setTheme] = useState<string>("light");
  const [language, setLanguage] = useState<string>("en-IN");
  const [dateFormat, setDateFormat] = useState<string>("DD-MM-YYYY");
  const [timeFormat, setTimeFormat] = useState<string>("12h");
  const [timezone, setTimezone] = useState<string>("Asia/Kolkata");

  // Step 13: Security
  const [sessionTimeout, setSessionTimeout] = useState<number>(60);
  const [requirePasswordForDelete, setRequirePasswordForDelete] = useState<boolean>(true);
  const [enableAuditLog, setEnableAuditLog] = useState<boolean>(true);
  const [enableTwoFactor, setEnableTwoFactor] = useState<boolean>(false);
  const [passwordExpiryDays, setPasswordExpiryDays] = useState<number>(0);

  useEffect(() => {
    fetch("/api/setup/status")
      .then((r) => r.json())
      .then((data) => {
        if (data?.clinic_name) setClinicName(data.clinic_name);
        if (data?.clinic_email) setClinicEmail(data.clinic_email);
        if (data?.clinic_phone) setClinicPhone(data.clinic_phone || "");
        if (data?.clinic_address) setAddress(data.clinic_address || "");
        const cfg = data?.config || {};
        if (cfg.doctor_name) setDoctorName(cfg.doctor_name);
        if (cfg.registration_number) setRegistrationNumber(cfg.registration_number);
        if (cfg.gst_number) setGstNumber(cfg.gst_number);
        if (cfg.logo_url) setLogoDataUrl(cfg.logo_url);
      })
      .catch(() => null);
  }, []);

  function handleLogoUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === "string") {
        setLogoDataUrl(reader.result);
      }
    };
    reader.readAsDataURL(file);
  }

  function getPasswordStrength(pw: string): { label: string; color: string } {
    if (!pw || pw.length < 6) return { label: "Too short (min 6 chars)", color: "#dc2626" };
    let score = 0;
    if (pw.length >= 8) score++;
    if (/[A-Z]/.test(pw)) score++;
    if (/[0-9]/.test(pw)) score++;
    if (/[^A-Za-z0-9]/.test(pw)) score++;
    if (score >= 3) return { label: "Strong password ✓", color: "#16a34a" };
    if (score === 2) return { label: "Good password", color: "#d97706" };
    return { label: "Fair password", color: "#ca8a04" };
  }

  function validateStep(targetStep: number): boolean {
    setError("");
    if (targetStep > 2 && !clinicName.trim()) {
      setError("Please enter your Clinic Name in Step 2 (Required).");
      setStep(2);
      return false;
    }
    if (targetStep > 3) {
      if (!adminUsername.trim()) {
        setError("Please enter an Administrator Username or Email in Step 3.");
        setStep(3);
        return false;
      }
      if (adminPassword.length < 6) {
        setError("Password must be at least 6 characters long.");
        setStep(3);
        return false;
      }
      if (adminPassword !== adminConfirmPassword) {
        setError("Passwords do not match in Step 3.");
        setStep(3);
        return false;
      }
    }
    return true;
  }

  function nextStep() {
    if (!validateStep(step + 1)) return;
    setStep((s) => Math.min(14, s + 1));
  }

  function prevStep() {
    setError("");
    setStep((s) => Math.max(1, s - 1));
  }

  async function handleFinishSetup() {
    if (!validateStep(14)) return;
    setSubmitting(true);
    setError("");
    try {
      const payload = {
        clinic: {
          name: clinicName.trim(),
          logo_data_url: logoDataUrl || null,
          doctor_name: doctorName || null,
          registration_number: registrationNumber || null,
          gst_number: gstNumber || null,
          email: clinicEmail || null,
          phone: clinicPhone || null,
          alternate_phone: alternatePhone || null,
          website: website || null,
          address: address || null,
          google_maps_url: googleMapsUrl || null,
          notes: clinicNotes || null,
        },
        admin: {
          username: adminUsername.trim(),
          password: adminPassword,
          full_name: adminFullName || doctorName || "Clinic Admin",
          email: adminEmail || adminUsername.trim(),
          mobile_number: adminMobile || clinicPhone || null,
          security_question: securityQuestion || null,
          security_answer: securityAnswer || null,
        },
        working_hours: workingHours,
        emergency_hours: emergencyHours,
        chairs,
        staff: staff.filter((s) => s.name.trim() && s.username.trim() && s.password.trim()),
        appointment_settings: {
          default_duration_minutes: apptDuration,
          buffer_time_minutes: bufferMinutes,
          max_future_booking_days: maxBookingDays,
          allow_walk_ins: allowWalkIns,
          allow_double_booking: allowDoubleBooking,
          require_confirmation: requireConfirmation,
        },
        patient_number_format: {
          prefix: patPrefix,
          separator: patSeparator,
          include_year: patIncludeYear,
          padding_digits: patPadding,
          start_number: patStartNumber,
          auto_increment: patAutoIncrement,
        },
        invoice_settings: {
          receipt_prefix: invPrefix,
          receipt_number_format: invFormat,
          tax_enabled: taxEnabled,
          default_tax_percent: defaultTaxPercent,
          currency,
          decimal_places: decimalPlaces,
          default_payment_method: defaultPaymentMethod,
        },
        backup_settings: {
          auto_backup_enabled: autoBackup,
          frequency: backupFrequency,
          backup_folder: backupFolder,
          cloud_backup_enabled: cloudBackup,
          encryption_enabled: encryptBackup,
          password_protect: passwordProtectBackup,
          backup_password: backupPassword || null,
        },
        notification_settings: {
          appointment_reminder: notifAppointment,
          birthday_reminder: notifBirthday,
          treatment_followup: notifFollowup,
          payment_reminder: notifPayment,
          channel_email: channelEmail,
          channel_whatsapp: channelWhatsapp,
          channel_sms: channelSms,
        },
        preferences: {
          theme,
          language,
          date_format: dateFormat,
          time_format: timeFormat,
          currency,
          timezone,
        },
        security: {
          session_timeout_minutes: sessionTimeout,
          require_password_for_delete: requirePasswordForDelete,
          enable_audit_log: enableAuditLog,
          enable_two_factor: enableTwoFactor,
          password_expiry_days: passwordExpiryDays,
        },
      };

      const res = await fetch("/api/setup/complete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => null);
        throw new Error(errData?.detail || "Failed to complete clinic setup");
      }
      const result = await res.json();
      if (result.access_token) {
        setAccessToken(result.access_token);
      }
      router.replace("/");
      router.refresh();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to save setup");
      setSubmitting(false);
    }
  }

  const samplePatientNumber = `${patPrefix ? patPrefix + patSeparator : ""}${
    patIncludeYear ? new Date().getFullYear() + patSeparator : ""
  }${String(patStartNumber).padStart(patPadding, "0")}`;

  const pwStrength = getPasswordStrength(adminPassword);

  return (
    <div className="min-h-screen bg-slate-50 py-8 px-4 md:px-8">
      <div className="max-w-5xl mx-auto bg-white rounded-2xl shadow-xl border border-slate-200 overflow-hidden">
        {/* Top Banner */}
        <div className="bg-gradient-to-r from-teal-800 via-teal-700 to-emerald-700 px-6 py-5 text-white flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-teal-200 text-xs font-semibold uppercase tracking-wider">
              <span>DentalCare Pro Enterprise</span>
              <span>•</span>
              <span>First Launch Setup Wizard</span>
            </div>
            <h1 className="text-2xl font-bold mt-1">
              {STEP_TITLES[step - 1]} <span className="text-teal-200 font-normal text-base">(Step {step} of 14)</span>
            </h1>
          </div>
          <div className="flex items-center gap-2">
            {step >= 3 && step < 14 && (
              <button
                type="button"
                onClick={handleFinishSetup}
                disabled={submitting}
                className="px-4 py-2 rounded-lg bg-amber-400 hover:bg-amber-300 text-slate-900 font-bold text-xs shadow transition cursor-pointer"
                title="Save your Clinic Name & Admin Account and use smart defaults for all remaining optional steps"
              >
                ⚡ Save & Quick Finish Now
              </button>
            )}
            <button
              type="button"
              onClick={() => router.push("/")}
              className="px-3 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-white text-xs font-medium transition cursor-pointer"
            >
              Skip to Dashboard →
            </button>
          </div>
        </div>

        {/* Stepper Pills */}
        <div className="bg-slate-100 px-4 py-3 border-b border-slate-200 flex items-center gap-1.5 overflow-x-auto">
          {STEP_TITLES.map((title, idx) => {
            const sNum = idx + 1;
            const active = step === sNum;
            const completed = step > sNum;
            return (
              <button
                key={title}
                type="button"
                onClick={() => {
                  if (validateStep(sNum)) setStep(sNum);
                }}
                className={`px-2.5 py-1.5 rounded-md text-xs font-semibold whitespace-nowrap transition cursor-pointer ${
                  active
                    ? "bg-teal-700 text-white shadow-sm"
                    : completed
                    ? "bg-teal-100 text-teal-800 hover:bg-teal-200"
                    : "bg-white text-slate-600 hover:bg-slate-200 border border-slate-200"
                }`}
              >
                {completed ? `✓ ${title}` : title}
              </button>
            );
          })}
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mx-6 mt-5 p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm font-medium flex items-center justify-between">
            <span>⚠ {error}</span>
            <button type="button" onClick={() => setError("")} className="text-xs underline">
              Dismiss
            </button>
          </div>
        )}

        {/* Step Body */}
        <div className="p-6 md:p-8 min-h-[430px]">
          {/* STEP 1: WELCOME */}
          {step === 1 && (
            <div className="max-w-2xl mx-auto text-center py-6">
              <div className="w-16 h-16 rounded-2xl bg-teal-100 text-teal-700 flex items-center justify-center text-3xl font-bold mx-auto mb-4">
                🦷
              </div>
              <h2 className="text-2xl font-bold text-slate-900">Welcome to DentalCare Pro</h2>
              <p className="text-slate-600 mt-2 text-base">
                This wizard will help you configure your dental clinic before daily use.
              </p>
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-teal-50 text-teal-800 text-xs font-semibold mt-3 border border-teal-200">
                ⏱ Estimated time: 5 minutes • Only Clinic Name & Admin Account are required
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-8 text-left">
                <button
                  type="button"
                  onClick={() => setStep(2)}
                  className="p-5 rounded-xl bg-teal-700 hover:bg-teal-800 text-white shadow-md transition flex flex-col justify-between cursor-pointer"
                >
                  <div>
                    <span className="text-xs uppercase tracking-wider text-teal-200 font-bold">Recommended</span>
                    <h3 className="text-lg font-bold mt-1">Start Clinic Setup →</h3>
                    <p className="text-xs text-teal-100 mt-1">
                      Configure your clinic branding, doctor profile, chairs, and working hours.
                    </p>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={handleFinishSetup}
                  disabled={submitting}
                  className="p-5 rounded-xl bg-emerald-50 hover:bg-emerald-100 text-emerald-950 border border-emerald-200 transition flex flex-col justify-between cursor-pointer"
                >
                  <div>
                    <span className="text-xs uppercase tracking-wider text-emerald-700 font-bold">Instant 1-Click</span>
                    <h3 className="text-lg font-bold mt-1">⚡ Start with Smart Defaults</h3>
                    <p className="text-xs text-emerald-800 mt-1">
                      Skip the wizard and open the clinic dashboard right now with ready-made settings.
                    </p>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => router.push("/settings")}
                  className="p-4 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-800 border border-slate-200 transition text-left cursor-pointer"
                >
                  <h4 className="font-bold text-sm">📦 Restore Backup / Import Database</h4>
                  <p className="text-xs text-slate-500 mt-1">
                    Restore a previous clinic SQL backup from C:\DentalCarePro_Backups.
                  </p>
                </button>

                <button
                  type="button"
                  onClick={() => router.push("/")}
                  className="p-4 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-800 border border-slate-200 transition text-left cursor-pointer"
                >
                  <h4 className="font-bold text-sm">🚪 Exit Wizard</h4>
                  <p className="text-xs text-slate-500 mt-1">
                    Close setup and go straight to the workspace. You can edit everything in Settings anytime.
                  </p>
                </button>
              </div>
            </div>
          )}

          {/* STEP 2: CLINIC INFORMATION */}
          {step === 2 && (
            <div className="space-y-5">
              <div className="border-b border-slate-200 pb-3">
                <h2 className="text-lg font-bold text-slate-900">Step 2 — Clinic Information</h2>
                <p className="text-xs text-slate-500">
                  Only <b>Clinic Name</b> is required. These details appear on your Prescriptions, Invoices, Receipts, and Patient PDF Reports.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Clinic Name <span className="text-red-600">* (Required)</span>
                  </label>
                  <input
                    type="text"
                    value={clinicName}
                    onChange={(e) => setClinicName(e.target.value)}
                    placeholder="e.g. SmileCare Multispeciality Dental Clinic"
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Chief Doctor Name (Optional)
                  </label>
                  <input
                    type="text"
                    value={doctorName}
                    onChange={(e) => setDoctorName(e.target.value)}
                    placeholder="e.g. Dr. Priya Sharma (BDS, MDS)"
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Clinic Registration Number (Optional)
                  </label>
                  <input
                    type="text"
                    value={registrationNumber}
                    onChange={(e) => setRegistrationNumber(e.target.value)}
                    placeholder="e.g. DCI-REG-2026-8841"
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    GST Number (Optional)
                  </label>
                  <input
                    type="text"
                    value={gstNumber}
                    onChange={(e) => setGstNumber(e.target.value)}
                    placeholder="e.g. 27AAAAA0000A1Z5"
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Clinic Phone / WhatsApp Number (Optional)
                  </label>
                  <input
                    type="tel"
                    value={clinicPhone}
                    onChange={(e) => setClinicPhone(e.target.value)}
                    placeholder="e.g. +91 9876543210"
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Alternate Phone (Optional)
                  </label>
                  <input
                    type="tel"
                    value={alternatePhone}
                    onChange={(e) => setAlternatePhone(e.target.value)}
                    placeholder="e.g. 022-26543210"
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Clinic Email (Optional)
                  </label>
                  <input
                    type="email"
                    value={clinicEmail}
                    onChange={(e) => setClinicEmail(e.target.value)}
                    placeholder="clinic@dentalcare.com"
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Website / Google Maps Link (Optional)
                  </label>
                  <input
                    type="text"
                    value={website}
                    onChange={(e) => setWebsite(e.target.value)}
                    placeholder="https://maps.google.com/..."
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Clinic Full Address (Printed on Prescriptions & Invoices)
                  </label>
                  <textarea
                    rows={2}
                    value={address}
                    onChange={(e) => setAddress(e.target.value)}
                    placeholder="Shop No. 4, Ground Floor, Medical Plaza, Main Road..."
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  />
                </div>

                <div className="md:col-span-2 flex items-center gap-4 bg-slate-50 p-3 rounded-xl border border-slate-200">
                  <div className="flex-1">
                    <label className="block text-xs font-semibold text-slate-700">
                      Clinic Logo (Optional — Printed on PDF headers)
                    </label>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleLogoUpload}
                      className="mt-1 text-xs text-slate-600"
                    />
                  </div>
                  {logoDataUrl && (
                    <img
                      src={logoDataUrl}
                      alt="Clinic Logo Preview"
                      className="h-14 w-14 object-contain rounded-lg border border-slate-300 bg-white p-1"
                    />
                  )}
                </div>
              </div>
            </div>
          )}

          {/* STEP 3: ADMINISTRATOR ACCOUNT */}
          {step === 3 && (
            <div className="space-y-5">
              <div className="border-b border-slate-200 pb-3">
                <h2 className="text-lg font-bold text-slate-900">Step 3 — Administrator / Doctor Account</h2>
                <p className="text-xs text-slate-500">
                  Create your main Administrator login. Pre-filled with ready-to-use credentials so you can also sign in with 1 click!
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Admin Username / Email <span className="text-red-600">*</span>
                  </label>
                  <input
                    type="text"
                    value={adminUsername}
                    onChange={(e) => setAdminUsername(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Full Name (Optional)
                  </label>
                  <input
                    type="text"
                    value={adminFullName}
                    onChange={(e) => setAdminFullName(e.target.value)}
                    placeholder="Dr. Full Name"
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Password <span className="text-red-600">*</span>
                  </label>
                  <input
                    type="password"
                    value={adminPassword}
                    onChange={(e) => setAdminPassword(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                    required
                  />
                  <span className="text-xs font-semibold mt-1 inline-block" style={{ color: pwStrength.color }}>
                    {pwStrength.label}
                  </span>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">
                    Confirm Password <span className="text-red-600">*</span>
                  </label>
                  <input
                    type="password"
                    value={adminConfirmPassword}
                    onChange={(e) => setAdminConfirmPassword(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Mobile Number (Optional)
                  </label>
                  <input
                    type="tel"
                    value={adminMobile}
                    onChange={(e) => setAdminMobile(e.target.value)}
                    placeholder="+91 9876543210"
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Security Recovery Question (Optional)
                  </label>
                  <input
                    type="text"
                    value={securityQuestion}
                    onChange={(e) => setSecurityQuestion(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  />
                </div>
              </div>

              <div className="p-4 rounded-xl bg-teal-50 border border-teal-200 flex flex-col sm:flex-row items-center justify-between gap-3">
                <div className="text-xs text-teal-900">
                  <b>Ready to start right now?</b> All remaining steps (4–13) already have smart clinic defaults pre-configured.
                </div>
                <button
                  type="button"
                  onClick={handleFinishSetup}
                  disabled={submitting}
                  className="px-4 py-2 rounded-lg bg-teal-700 hover:bg-teal-800 text-white font-bold text-xs whitespace-nowrap cursor-pointer"
                >
                  ⚡ Save & Open Dashboard Now
                </button>
              </div>
            </div>
          )}

          {/* STEP 4: CLINIC WORKING HOURS */}
          {step === 4 && (
            <div className="space-y-4">
              <div className="border-b border-slate-200 pb-3 flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-bold text-slate-900">Step 4 — Clinic Working Hours (Optional)</h2>
                  <p className="text-xs text-slate-500">
                    Configure each day independently for the Appointment Scheduler and Calendar views.
                  </p>
                </div>
              </div>

              <div className="space-y-2">
                {workingHours.map((dh, i) => (
                  <div
                    key={dh.day}
                    className="grid grid-cols-2 md:grid-cols-6 items-center gap-3 p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs"
                  >
                    <div className="font-bold text-slate-800">{dh.day}</div>
                    <label className="flex items-center gap-2 font-medium text-slate-700">
                      <input
                        type="checkbox"
                        checked={dh.is_closed}
                        onChange={(e) => {
                          const next = [...workingHours];
                          next[i] = { ...dh, is_closed: e.target.checked };
                          setWorkingHours(next);
                        }}
                      />
                      Closed
                    </label>
                    {!dh.is_closed ? (
                      <>
                        <div>
                          <span className="text-slate-500 block">Opens</span>
                          <input
                            type="time"
                            value={dh.open_time}
                            onChange={(e) => {
                              const next = [...workingHours];
                              next[i] = { ...dh, open_time: e.target.value };
                              setWorkingHours(next);
                            }}
                            className="border border-slate-300 rounded px-2 py-1 w-full"
                          />
                        </div>
                        <div>
                          <span className="text-slate-500 block">Closes</span>
                          <input
                            type="time"
                            value={dh.close_time}
                            onChange={(e) => {
                              const next = [...workingHours];
                              next[i] = { ...dh, close_time: e.target.value };
                              setWorkingHours(next);
                            }}
                            className="border border-slate-300 rounded px-2 py-1 w-full"
                          />
                        </div>
                        <div className="col-span-2">
                          <span className="text-slate-500 block">Lunch Break</span>
                          <input
                            type="text"
                            value={dh.lunch_break}
                            onChange={(e) => {
                              const next = [...workingHours];
                              next[i] = { ...dh, lunch_break: e.target.value };
                              setWorkingHours(next);
                            }}
                            className="border border-slate-300 rounded px-2 py-1 w-full"
                          />
                        </div>
                      </>
                    ) : (
                      <div className="col-span-4 text-slate-400 italic">Clinic Closed on {dh.day} (Emergency only)</div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* STEP 5: TREATMENT ROOMS / CHAIRS */}
          {step === 5 && (
            <div className="space-y-4">
              <div className="border-b border-slate-200 pb-3 flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-bold text-slate-900">Step 5 — Treatment Rooms / Dental Chairs</h2>
                  <p className="text-xs text-slate-500">
                    Define your operatories/chairs for appointment scheduling and chair utilization tracking.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() =>
                    setChairs([
                      ...chairs,
                      {
                        name: `Chair ${chairs.length + 1} - Operatory`,
                        room_number: `Room 10${chairs.length + 1}`,
                        color: "#0d9488",
                        is_active: true,
                      },
                    ])
                  }
                  className="px-3 py-1.5 rounded-lg bg-teal-700 text-white text-xs font-bold cursor-pointer"
                >
                  + Add Dental Chair
                </button>
              </div>

              <div className="space-y-3">
                {chairs.map((c, idx) => (
                  <div
                    key={idx}
                    className="grid grid-cols-1 md:grid-cols-5 items-center gap-3 p-3.5 rounded-xl bg-slate-50 border border-slate-200"
                  >
                    <div className="md:col-span-2">
                      <label className="text-xs text-slate-500 block">Chair / Operatory Name</label>
                      <input
                        type="text"
                        value={c.name}
                        onChange={(e) => {
                          const next = [...chairs];
                          next[idx] = { ...c, name: e.target.value };
                          setChairs(next);
                        }}
                        className="w-full border border-slate-300 rounded-lg px-3 py-1.5 text-sm"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-slate-500 block">Room Number</label>
                      <input
                        type="text"
                        value={c.room_number}
                        onChange={(e) => {
                          const next = [...chairs];
                          next[idx] = { ...c, room_number: e.target.value };
                          setChairs(next);
                        }}
                        className="w-full border border-slate-300 rounded-lg px-3 py-1.5 text-sm"
                      />
                    </div>
                    <div className="flex items-center gap-3">
                      <div>
                        <label className="text-xs text-slate-500 block">Color</label>
                        <input
                          type="color"
                          value={c.color}
                          onChange={(e) => {
                            const next = [...chairs];
                            next[idx] = { ...c, color: e.target.value };
                            setChairs(next);
                          }}
                          className="h-8 w-14 rounded cursor-pointer"
                        />
                      </div>
                      <label className="flex items-center gap-1.5 text-xs font-semibold mt-4">
                        <input
                          type="checkbox"
                          checked={c.is_active}
                          onChange={(e) => {
                            const next = [...chairs];
                            next[idx] = { ...c, is_active: e.target.checked };
                            setChairs(next);
                          }}
                        />
                        Active
                      </label>
                    </div>
                    <div className="text-right">
                      {chairs.length > 1 && (
                        <button
                          type="button"
                          onClick={() => setChairs(chairs.filter((_, i) => i !== idx))}
                          className="text-xs text-red-600 hover:underline"
                        >
                          Remove
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* STEP 6: STAFF (OPTIONAL) */}
          {step === 6 && (
            <div className="space-y-4">
              <div className="border-b border-slate-200 pb-3 flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-bold text-slate-900">Step 6 — Clinic Staff Accounts (Optional)</h2>
                  <p className="text-xs text-slate-500">
                    Add Receptionists, Associate Dentists, Assistants, or Hygienists now, or skip and add them anytime later.
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() =>
                      setStaff([
                        ...staff,
                        { name: "", username: "", password: "Password123!", role: "RECEPTIONIST" },
                      ])
                    }
                    className="px-3 py-1.5 rounded-lg bg-teal-700 text-white text-xs font-bold cursor-pointer"
                  >
                    + Add Staff Member
                  </button>
                  <button
                    type="button"
                    onClick={nextStep}
                    className="px-3 py-1.5 rounded-lg bg-slate-200 hover:bg-slate-300 text-slate-800 text-xs font-semibold cursor-pointer"
                  >
                    Skip for now →
                  </button>
                </div>
              </div>

              {staff.length === 0 ? (
                <div className="p-8 rounded-xl bg-slate-50 border border-dashed border-slate-300 text-center text-slate-500 text-sm">
                  No additional staff members added yet. Click <b>+ Add Staff Member</b> above or click <b>Next / Skip for now</b>.
                </div>
              ) : (
                <div className="space-y-3">
                  {staff.map((st, idx) => (
                    <div
                      key={idx}
                      className="grid grid-cols-1 md:grid-cols-5 gap-3 p-3.5 rounded-xl bg-slate-50 border border-slate-200 items-end"
                    >
                      <div>
                        <label className="text-xs text-slate-500 block">Full Name</label>
                        <input
                          type="text"
                          placeholder="e.g. Neha Verma"
                          value={st.name}
                          onChange={(e) => {
                            const next = [...staff];
                            next[idx] = { ...st, name: e.target.value };
                            setStaff(next);
                          }}
                          className="w-full border border-slate-300 rounded-lg px-2.5 py-1.5 text-sm"
                        />
                      </div>
                      <div>
                        <label className="text-xs text-slate-500 block">Username / Email</label>
                        <input
                          type="text"
                          placeholder="reception@dentalcare.com"
                          value={st.username}
                          onChange={(e) => {
                            const next = [...staff];
                            next[idx] = { ...st, username: e.target.value };
                            setStaff(next);
                          }}
                          className="w-full border border-slate-300 rounded-lg px-2.5 py-1.5 text-sm"
                        />
                      </div>
                      <div>
                        <label className="text-xs text-slate-500 block">Password</label>
                        <input
                          type="text"
                          value={st.password}
                          onChange={(e) => {
                            const next = [...staff];
                            next[idx] = { ...st, password: e.target.value };
                            setStaff(next);
                          }}
                          className="w-full border border-slate-300 rounded-lg px-2.5 py-1.5 text-sm"
                        />
                      </div>
                      <div>
                        <label className="text-xs text-slate-500 block">Role</label>
                        <select
                          value={st.role}
                          onChange={(e) => {
                            const next = [...staff];
                            next[idx] = { ...st, role: e.target.value };
                            setStaff(next);
                          }}
                          className="w-full border border-slate-300 rounded-lg px-2.5 py-1.5 text-sm bg-white"
                        >
                          <option value="RECEPTIONIST">Receptionist</option>
                          <option value="DENTIST">Dentist</option>
                          <option value="ASSISTANT">Dental Assistant</option>
                          <option value="HYGIENIST">Hygienist</option>
                          <option value="MANAGER">Clinic Manager</option>
                        </select>
                      </div>
                      <button
                        type="button"
                        onClick={() => setStaff(staff.filter((_, i) => i !== idx))}
                        className="text-xs text-red-600 hover:underline py-2"
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* STEP 7: APPOINTMENT SETTINGS */}
          {step === 7 && (
            <div className="space-y-5">
              <div className="border-b border-slate-200 pb-3">
                <h2 className="text-lg font-bold text-slate-900">Step 7 — Appointment Scheduler Settings (Optional)</h2>
                <p className="text-xs text-slate-500">Customize default slot duration, buffer time, and walk-in rules.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Default Appointment Duration</label>
                  <select
                    value={apptDuration}
                    onChange={(e) => setApptDuration(Number(e.target.value))}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
                  >
                    <option value={15}>15 minutes</option>
                    <option value={20}>20 minutes</option>
                    <option value={30}>30 minutes (Recommended)</option>
                    <option value={45}>45 minutes</option>
                    <option value={60}>60 minutes</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Chair Preparation Buffer Time</label>
                  <select
                    value={bufferMinutes}
                    onChange={(e) => setBufferMinutes(Number(e.target.value))}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
                  >
                    <option value={0}>No buffer (0 min)</option>
                    <option value={5}>5 minutes</option>
                    <option value={10}>10 minutes</option>
                    <option value={15}>15 minutes</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Max Future Booking Period</label>
                  <select
                    value={maxBookingDays}
                    onChange={(e) => setMaxBookingDays(Number(e.target.value))}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
                  >
                    <option value={30}>30 Days</option>
                    <option value={90}>90 Days (3 Months)</option>
                    <option value={180}>180 Days (6 Months)</option>
                    <option value={365}>365 Days (1 Year)</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
                <label className="flex items-center gap-3 p-3.5 rounded-xl bg-slate-50 border border-slate-200 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={allowWalkIns}
                    onChange={(e) => setAllowWalkIns(e.target.checked)}
                  />
                  <div>
                    <div className="text-sm font-bold text-slate-800">Allow Walk-in Patients</div>
                    <div className="text-xs text-slate-500">Enable instant walk-in queue & fast prescriptions</div>
                  </div>
                </label>

                <label className="flex items-center gap-3 p-3.5 rounded-xl bg-slate-50 border border-slate-200 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={allowDoubleBooking}
                    onChange={(e) => setAllowDoubleBooking(e.target.checked)}
                  />
                  <div>
                    <div className="text-sm font-bold text-slate-800">Allow Double Booking</div>
                    <div className="text-xs text-slate-500">Permit overlapping slots across multiple chairs</div>
                  </div>
                </label>

                <label className="flex items-center gap-3 p-3.5 rounded-xl bg-slate-50 border border-slate-200 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={requireConfirmation}
                    onChange={(e) => setRequireConfirmation(e.target.checked)}
                  />
                  <div>
                    <div className="text-sm font-bold text-slate-800">Require Confirmation</div>
                    <div className="text-xs text-slate-500">Mark new bookings as Pending until confirmed</div>
                  </div>
                </label>
              </div>
            </div>
          )}

          {/* STEP 8: PATIENT NUMBER FORMAT */}
          {step === 8 && (
            <div className="space-y-5">
              <div className="border-b border-slate-200 pb-3">
                <h2 className="text-lg font-bold text-slate-900">Step 8 — Patient ID Numbering Format (Optional)</h2>
                <p className="text-xs text-slate-500">
                  Choose how new patient registration numbers are automatically formatted.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-teal-50 border border-teal-200 flex items-center justify-between">
                <span className="text-xs font-bold uppercase tracking-wider text-teal-800">Live Patient ID Preview:</span>
                <span className="text-xl font-mono font-bold text-teal-900 bg-white px-4 py-1.5 rounded-lg border border-teal-300">
                  {samplePatientNumber}
                </span>
              </div>

              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setPatPrefix("PAT");
                    setPatIncludeYear(false);
                    setPatPadding(5);
                  }}
                  className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-xs font-semibold cursor-pointer"
                >
                  Preset: PAT-00001
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setPatPrefix("");
                    setPatIncludeYear(true);
                    setPatPadding(5);
                  }}
                  className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-xs font-semibold cursor-pointer"
                >
                  Preset: 2026-00001
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setPatPrefix("CLINIC");
                    setPatIncludeYear(false);
                    setPatPadding(3);
                  }}
                  className="px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-xs font-semibold cursor-pointer"
                >
                  Preset: CLINIC-001
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Editable Prefix</label>
                  <input
                    type="text"
                    value={patPrefix}
                    onChange={(e) => setPatPrefix(e.target.value.toUpperCase())}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Number Padding Digits</label>
                  <input
                    type="number"
                    min={3}
                    max={8}
                    value={patPadding}
                    onChange={(e) => setPatPadding(Number(e.target.value))}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  />
                </div>
                <div className="flex items-center pt-5">
                  <label className="flex items-center gap-2 text-sm font-semibold text-slate-700 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={patIncludeYear}
                      onChange={(e) => setPatIncludeYear(e.target.checked)}
                    />
                    Include Current Year ({new Date().getFullYear()})
                  </label>
                </div>
              </div>
            </div>
          )}

          {/* STEP 9: INVOICE SETTINGS */}
          {step === 9 && (
            <div className="space-y-5">
              <div className="border-b border-slate-200 pb-3">
                <h2 className="text-lg font-bold text-slate-900">Step 9 — Billing & Invoice Settings (Optional)</h2>
                <p className="text-xs text-slate-500">Configure invoice numbering, currency, and default payment mode.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Receipt / Invoice Prefix</label>
                  <input
                    type="text"
                    value={invPrefix}
                    onChange={(e) => setInvPrefix(e.target.value.toUpperCase())}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Currency</label>
                  <select
                    value={currency}
                    onChange={(e) => setCurrency(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
                  >
                    <option value="INR">INR (₹ Indian Rupee)</option>
                    <option value="USD">USD ($ US Dollar)</option>
                    <option value="EUR">EUR (€ Euro)</option>
                    <option value="GBP">GBP (£ British Pound)</option>
                    <option value="AED">AED (UAE Dirham)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Default Payment Method</label>
                  <select
                    value={defaultPaymentMethod}
                    onChange={(e) => setDefaultPaymentMethod(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
                  >
                    <option value="CASH">Cash</option>
                    <option value="UPI">UPI / QR Scan</option>
                    <option value="CARD">Credit / Debit Card</option>
                    <option value="BANK_TRANSFER">Bank Transfer / NEFT</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <label className="flex items-center gap-3 p-3.5 rounded-xl bg-slate-50 border border-slate-200 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={taxEnabled}
                    onChange={(e) => setTaxEnabled(e.target.checked)}
                  />
                  <div>
                    <div className="text-sm font-bold text-slate-800">Enable Tax / GST on Invoices</div>
                    <div className="text-xs text-slate-500">Display tax breakdown on printed & WhatsApp invoices</div>
                  </div>
                </label>

                {taxEnabled && (
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Default Tax / GST (%)</label>
                    <input
                      type="number"
                      step="0.5"
                      value={defaultTaxPercent}
                      onChange={(e) => setDefaultTaxPercent(Number(e.target.value))}
                      className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                    />
                  </div>
                )}
              </div>
            </div>
          )}

          {/* STEP 10: BACKUP SETTINGS */}
          {step === 10 && (
            <div className="space-y-5">
              <div className="border-b border-slate-200 pb-3">
                <h2 className="text-lg font-bold text-slate-900">Step 10 — Automated Database Backups (Optional)</h2>
                <p className="text-xs text-slate-500">
                  Protect all patient charts, odontograms, and billing history automatically on your computer.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Backup Schedule Frequency</label>
                  <select
                    value={backupFrequency}
                    onChange={(e) => setBackupFrequency(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
                  >
                    <option value="DAILY">Daily Automatic Backup (Recommended)</option>
                    <option value="WEEKLY">Weekly Backup</option>
                    <option value="MONTHLY">Monthly Backup</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Local Backup Folder</label>
                  <input
                    type="text"
                    value={backupFolder}
                    onChange={(e) => setBackupFolder(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <label className="flex items-center gap-3 p-3.5 rounded-xl bg-slate-50 border border-slate-200 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={encryptBackup}
                    onChange={(e) => setEncryptBackup(e.target.checked)}
                  />
                  <div>
                    <div className="text-sm font-bold text-slate-800">AES-256 Encrypted Backups</div>
                    <div className="text-xs text-slate-500">Encrypt backup archives for medical data privacy</div>
                  </div>
                </label>

                <label className="flex items-center gap-3 p-3.5 rounded-xl bg-slate-50 border border-slate-200 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={passwordProtectBackup}
                    onChange={(e) => setPasswordProtectBackup(e.target.checked)}
                  />
                  <div>
                    <div className="text-sm font-bold text-slate-800">Password Protect Backup File</div>
                    <div className="text-xs text-slate-500">Require a passphrase when restoring backups</div>
                  </div>
                </label>
              </div>
            </div>
          )}

          {/* STEP 11: NOTIFICATIONS */}
          {step === 11 && (
            <div className="space-y-5">
              <div className="border-b border-slate-200 pb-3">
                <h2 className="text-lg font-bold text-slate-900">Step 11 — Patient Notifications & Direct WhatsApp PDFs</h2>
                <p className="text-xs text-slate-500">
                  Choose which automated alerts and direct WhatsApp PDF deliveries are enabled.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <label className="flex items-center gap-3 p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={channelWhatsapp}
                    onChange={(e) => setChannelWhatsapp(e.target.checked)}
                  />
                  <div>
                    <div className="text-sm font-bold text-emerald-950">Direct WhatsApp PDF Delivery (Active)</div>
                    <div className="text-xs text-emerald-800">
                      Directly send Prescription, Invoice, Receipt & Patient Report PDFs to patient WhatsApp numbers
                    </div>
                  </div>
                </label>

                <label className="flex items-center gap-3 p-3.5 rounded-xl bg-slate-50 border border-slate-200 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={notifAppointment}
                    onChange={(e) => setNotifAppointment(e.target.checked)}
                  />
                  <div>
                    <div className="text-sm font-bold text-slate-800">Appointment Reminders</div>
                    <div className="text-xs text-slate-500">Remind patients before scheduled visits</div>
                  </div>
                </label>

                <label className="flex items-center gap-3 p-3.5 rounded-xl bg-slate-50 border border-slate-200 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={notifFollowup}
                    onChange={(e) => setNotifFollowup(e.target.checked)}
                  />
                  <div>
                    <div className="text-sm font-bold text-slate-800">Post-Treatment Follow-up</div>
                    <div className="text-xs text-slate-500">Check in after extractions, RCT, or implants</div>
                  </div>
                </label>

                <label className="flex items-center gap-3 p-3.5 rounded-xl bg-slate-50 border border-slate-200 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={notifPayment}
                    onChange={(e) => setNotifPayment(e.target.checked)}
                  />
                  <div>
                    <div className="text-sm font-bold text-slate-800">Payment & Balance Reminders</div>
                    <div className="text-xs text-slate-500">Send gentle reminders for pending invoice balances</div>
                  </div>
                </label>
              </div>
            </div>
          )}

          {/* STEP 12: PREFERENCES */}
          {step === 12 && (
            <div className="space-y-5">
              <div className="border-b border-slate-200 pb-3">
                <h2 className="text-lg font-bold text-slate-900">Step 12 — Display & Regional Preferences (Optional)</h2>
                <p className="text-xs text-slate-500">Set visual theme, date/time format, and clinic timezone.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Interface Theme</label>
                  <select
                    value={theme}
                    onChange={(e) => setTheme(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
                  >
                    <option value="light">Light Clinical Theme</option>
                    <option value="dark">Dark Mode</option>
                    <option value="system">Match Windows System</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Date Format</label>
                  <select
                    value={dateFormat}
                    onChange={(e) => setDateFormat(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
                  >
                    <option value="DD-MM-YYYY">DD-MM-YYYY (23-09-2026)</option>
                    <option value="MM-DD-YYYY">MM-DD-YYYY (09-23-2026)</option>
                    <option value="YYYY-MM-DD">YYYY-MM-DD (2026-09-23)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Time Format</label>
                  <select
                    value={timeFormat}
                    onChange={(e) => setTimeFormat(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
                  >
                    <option value="12h">12-Hour (09:00 AM - 08:00 PM)</option>
                    <option value="24h">24-Hour (09:00 - 20:00)</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* STEP 13: SECURITY */}
          {step === 13 && (
            <div className="space-y-5">
              <div className="border-b border-slate-200 pb-3">
                <h2 className="text-lg font-bold text-slate-900">Step 13 — Clinical Security & Audit Controls (Optional)</h2>
                <p className="text-xs text-slate-500">Configure record deletion safeguards and HIPAA audit logging.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Idle Session Timeout</label>
                  <select
                    value={sessionTimeout}
                    onChange={(e) => setSessionTimeout(Number(e.target.value))}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white"
                  >
                    <option value={30}>30 Minutes</option>
                    <option value={60}>1 Hour (Recommended)</option>
                    <option value={480}>8 Hours (Full Clinic Shift)</option>
                  </select>
                </div>

                <label className="flex items-center gap-3 p-3.5 rounded-xl bg-slate-50 border border-slate-200 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={requirePasswordForDelete}
                    onChange={(e) => setRequirePasswordForDelete(e.target.checked)}
                  />
                  <div>
                    <div className="text-sm font-bold text-slate-800">Protect Record Deletion</div>
                    <div className="text-xs text-slate-500">Confirm before archiving/deleting patient records</div>
                  </div>
                </label>

                <label className="flex items-center gap-3 p-3.5 rounded-xl bg-slate-50 border border-slate-200 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={enableAuditLog}
                    onChange={(e) => setEnableAuditLog(e.target.checked)}
                  />
                  <div>
                    <div className="text-sm font-bold text-slate-800">Enable Clinical Audit Trail</div>
                    <div className="text-xs text-slate-500">Record all logins, prescriptions, and invoice actions</div>
                  </div>
                </label>
              </div>
            </div>
          )}

          {/* STEP 14: REVIEW & FINISH */}
          {step === 14 && (
            <div className="space-y-5">
              <div className="border-b border-slate-200 pb-3">
                <h2 className="text-lg font-bold text-slate-900">Step 14 — Review & Finish Clinic Setup</h2>
                <p className="text-xs text-slate-500">
                  Everything looks great! Click <b>Finish Setup & Sign In</b> below to launch your clinic workspace.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200">
                  <span className="font-bold text-emerald-900">✓ Clinic Name:</span>{" "}
                  <span className="text-emerald-950">{clinicName}</span>
                  {doctorName && <div className="text-xs text-emerald-700 mt-0.5">Doctor: {doctorName}</div>}
                </div>

                <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200">
                  <span className="font-bold text-emerald-900">✓ Administrator Account:</span>{" "}
                  <span className="text-emerald-950">{adminUsername}</span>
                  <div className="text-xs text-emerald-700 mt-0.5">Auto-login enabled after finish</div>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200">
                  <span className="font-bold text-slate-800">✓ Working Hours:</span>{" "}
                  <span className="text-slate-600">
                    {workingHours.filter((d) => !d.is_closed).length} days open/week
                  </span>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200">
                  <span className="font-bold text-slate-800">✓ Treatment Rooms / Chairs:</span>{" "}
                  <span className="text-slate-600">{chairs.length} active chair(s)</span>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200">
                  <span className="font-bold text-slate-800">✓ Patient & Invoice Numbering:</span>{" "}
                  <span className="text-slate-600">
                    {samplePatientNumber} • {invPrefix} ({currency})
                  </span>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200">
                  <span className="font-bold text-slate-800">✓ Backups & Direct WhatsApp PDF:</span>{" "}
                  <span className="text-slate-600">
                    {backupFrequency} Encrypted Backup • WhatsApp {channelWhatsapp ? "Enabled" : "Off"}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Bottom Navigation Footer */}
        <div className="bg-slate-100 px-6 py-4 border-t border-slate-200 flex items-center justify-between">
          <div>
            {step > 1 && (
              <button
                type="button"
                onClick={prevStep}
                className="px-4 py-2 rounded-lg bg-white hover:bg-slate-200 text-slate-700 border border-slate-300 text-sm font-semibold transition cursor-pointer"
              >
                ← Previous
              </button>
            )}
          </div>

          <div className="flex items-center gap-3">
            {step > 3 && step < 14 && (
              <button
                type="button"
                onClick={nextStep}
                className="px-3.5 py-2 rounded-lg text-slate-600 hover:text-slate-900 text-xs font-semibold cursor-pointer"
              >
                Skip this step →
              </button>
            )}

            {step < 14 ? (
              <button
                type="button"
                onClick={nextStep}
                className="px-6 py-2.5 rounded-xl bg-teal-700 hover:bg-teal-800 text-white font-bold text-sm shadow transition cursor-pointer"
              >
                Next Step →
              </button>
            ) : (
              <button
                type="button"
                onClick={handleFinishSetup}
                disabled={submitting}
                className="px-8 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm shadow-lg transition cursor-pointer"
              >
                {submitting ? "Configuring Clinic & Signing In..." : "✓ Finish Setup & Sign In automatically"}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function TrueBool(v: boolean): boolean {
  return v;
}
