"use client";

import Link from "next/link";
import { useState } from "react";
import type { ClinicalDocType } from "../types";

export default function AIDocumentsPage() {
  const [docType, setDocType] = useState<ClinicalDocType>("REFERRAL_LETTER");
  const [patientName, setPatientName] = useState("Riya Kapoor");
  const [patientAgeGender, setPatientAgeGender] = useState("29 / Female");
  const [clinicianName, setClinicianName] = useState("Dr. Ananya Shah, MDS");
  const [recipient, setRecipient] = useState("Dr. M. K. Rao (Maxillofacial Surgeon)");
  const [diagnosis, setDiagnosis] = useState("Impacted Mandibular Left Third Molar (Tooth #38 - Pell & Gregory Class II Position B)");
  const [leaveDays, setLeaveDays] = useState("2");
  const [isGenerating, setIsGenerating] = useState(false);
  const [copied, setCopied] = useState(false);
  const [printed, setPrinted] = useState(false);

  // Template generators
  const getDocumentBody = () => {
    switch (docType) {
      case "REFERRAL_LETTER":
        return `Dear Dr. M. K. Rao,

I am referring Ms. Riya Kapoor (29/F) for specialized surgical evaluation and management of an impacted mandibular left third molar (#38).

Clinical Findings:
The patient reports recurrent episodes of pericoronitis, local tenderness, and partial food impaction in the lower left quadrant. An orthopantomogram (OPG) reveals tooth #38 with mesioangular impaction, Class II Position B, with roots in close anatomical proximity to the inferior alveolar nerve canal.

Medical History:
Patient is otherwise healthy with no known drug allergies. Blood pressure 118/76 mmHg.

Enclosed are the diagnostic periapical and panoramic digital radiographs for your review. Kindly advise and treat as appropriate. Thank you for your collegial collaboration.

Warm regards,
Dr. Ananya Shah, MDS
DentalCare Pro Clinic`;

      case "MEDICAL_CERTIFICATE":
        return `MEDICAL FITNESS & LEAVE CERTIFICATE

Date: September 8, 2026
Reference: DC-MEDCERT-2026-089

This is to certify that Ms. Riya Kapoor (Age: 29 years, Gender: Female) was attended to at DentalCare Pro on 08-Sep-2026.

Diagnosis:
Acute pericoronitis associated with impacted tooth #38 requiring surgical debridement and operative intervention.

Clinical Advice:
Following the dental surgical procedure, the patient has been advised complete rest and excused from work/academic duties for a period of ${leaveDays} day(s), from 08-Sep-2026 to 09-Sep-2026.

The patient is expected to be fit to resume normal duties on 10-Sep-2026, subject to routine clinical recovery.

Dr. Ananya Shah, MDS
Dental Surgeon | Reg. No: D-48291
DentalCare Pro Clinic`;

      case "POST_OP_INSTRUCTIONS":
        return `POST-OPERATIVE SURGICAL CARE INSTRUCTIONS

Patient Name: Ms. Riya Kapoor
Procedure: Minor Oral Surgery / Debridement (#38)
Date: September 8, 2026

Please follow these critical home-care instructions to ensure rapid, complication-free healing:

1. GAUZE PRESSURE: Keep the gauze pack firmly in place for 45-60 minutes. Do not chew on the gauze.
2. SPITTING & SUCKING: DO NOT spit, rinse vigorously, or drink through a straw for the first 24 hours. Swallowing saliva is completely safe.
3. COLD THERAPY: Apply an ice pack wrapped in a clean cloth to the cheek outside the surgical site: 15 minutes ON, 15 minutes OFF for the first 12 hours to minimize swelling.
4. DIET: Stick to soft, cool, or lukewarm foods (yogurt, smooth soups, smoothies) for the first 48 hours. Avoid hot, spicy, crunchy, or acidic foods.
5. ORAL HYGIENE: After 24 hours, begin gentle warm saline rinses (1/2 tsp salt in 1 glass lukewarm water) after meals. Avoid brushing directly over the surgical site for 3 days.
6. MEDICATIONS: Take prescribed pain relievers and antibiotics exactly as directed.
7. EMERGENCY CONTACT: If you experience persistent bleeding not controlled by gauze pressure, severe throbbing pain unresolved by medication, or high fever (>101°F), contact DentalCare Pro immediately at +91 98765 43210.`;

      case "DISCHARGE_SUMMARY":
        return `CLINICAL TREATMENT & DISCHARGE SUMMARY

Patient: Ms. Riya Kapoor (UHID: DC-PAT-1082)
Treating Clinician: Dr. Ananya Shah, MDS
Discharge Status: Stable, Outpatient Discharge

1. Admission / Visit Reason: Recurrent pain and swelling lower left jaw.
2. Diagnosis: Pericoronitis secondary to mesioangular impaction of tooth #38.
3. Procedures Rendered: Operculectomy, irrigation with 0.2% Chlorhexidine and Betadine, working diagnosis established, referral initiated.
4. Prescriptions Issued:
   - Cap. Amoxicillin 500mg (1 tid x 5 days)
   - Tab. Ibuprofen 400mg + Paracetamol 325mg (1 tid PRN x 3 days)
5. Complications: None. Hemostasis achieved.
6. Follow-up: Review in 5 days or prior to specialist appointment.`;

      default:
        return "Select a document type to preview the AI generated draft.";
    }
  };

  const [documentContent, setDocumentContent] = useState(getDocumentBody());

  const handleDocTypeChange = (type: ClinicalDocType) => {
    setDocType(type);
    // update content based on choice
    setTimeout(() => {
      if (type === "REFERRAL_LETTER") {
        setDocumentContent(`Dear Dr. M. K. Rao,

I am referring Ms. Riya Kapoor (29/F) for specialized surgical evaluation and management of an impacted mandibular left third molar (#38).

Clinical Findings:
The patient reports recurrent episodes of pericoronitis, local tenderness, and partial food impaction in the lower left quadrant. An orthopantomogram (OPG) reveals tooth #38 with mesioangular impaction, Class II Position B, with roots in close anatomical proximity to the inferior alveolar nerve canal.

Medical History:
Patient is otherwise healthy with no known drug allergies. Blood pressure 118/76 mmHg.

Enclosed are the diagnostic periapical and panoramic digital radiographs for your review. Kindly advise and treat as appropriate. Thank you for your collegial collaboration.

Warm regards,
Dr. Ananya Shah, MDS
DentalCare Pro Clinic`);
      } else if (type === "MEDICAL_CERTIFICATE") {
        setDocumentContent(`MEDICAL FITNESS & LEAVE CERTIFICATE

Date: September 8, 2026
Reference: DC-MEDCERT-2026-089

This is to certify that Ms. Riya Kapoor (Age: 29 years, Gender: Female) was attended to at DentalCare Pro on 08-Sep-2026.

Diagnosis:
Acute pericoronitis associated with impacted tooth #38 requiring surgical debridement and operative intervention.

Clinical Advice:
Following the dental surgical procedure, the patient has been advised complete rest and excused from work/academic duties for a period of ${leaveDays} day(s), from 08-Sep-2026 to 09-Sep-2026.

The patient is expected to be fit to resume normal duties on 10-Sep-2026, subject to routine clinical recovery.

Dr. Ananya Shah, MDS
Dental Surgeon | Reg. No: D-48291
DentalCare Pro Clinic`);
      } else if (type === "POST_OP_INSTRUCTIONS") {
        setDocumentContent(`POST-OPERATIVE SURGICAL CARE INSTRUCTIONS

Patient Name: Ms. Riya Kapoor
Procedure: Minor Oral Surgery / Debridement (#38)
Date: September 8, 2026

Please follow these critical home-care instructions to ensure rapid, complication-free healing:

1. GAUZE PRESSURE: Keep the gauze pack firmly in place for 45-60 minutes. Do not chew on the gauze.
2. SPITTING & SUCKING: DO NOT spit, rinse vigorously, or drink through a straw for the first 24 hours. Swallowing saliva is completely safe.
3. COLD THERAPY: Apply an ice pack wrapped in a clean cloth to the cheek outside the surgical site: 15 minutes ON, 15 minutes OFF for the first 12 hours to minimize swelling.
4. DIET: Stick to soft, cool, or lukewarm foods for the first 48 hours.
5. ORAL HYGIENE: After 24 hours, begin gentle warm saline rinses after meals.
6. MEDICATIONS: Take prescribed pain relievers and antibiotics exactly as directed.
7. EMERGENCY CONTACT: Contact DentalCare Pro at +91 98765 43210 if uncontrolled bleeding occurs.`);
      } else {
        setDocumentContent(`CLINICAL TREATMENT & DISCHARGE SUMMARY

Patient: Ms. Riya Kapoor (UHID: DC-PAT-1082)
Treating Clinician: Dr. Ananya Shah, MDS
Discharge Status: Stable, Outpatient Discharge

1. Admission / Visit Reason: Recurrent pain and swelling lower left jaw.
2. Diagnosis: Pericoronitis secondary to mesioangular impaction of tooth #38.
3. Procedures Rendered: Operculectomy, irrigation with 0.2% Chlorhexidine and Betadine.
4. Prescriptions Issued: Amoxicillin 500mg, Ibuprofen 400mg.
5. Complications: None. Hemostasis achieved.`);
      }
    }, 50);
  };

  const handleRegenerate = () => {
    setIsGenerating(true);
    setTimeout(() => {
      setIsGenerating(false);
    }, 500);
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(documentContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handlePrint = () => {
    window.print();
    setPrinted(true);
    setTimeout(() => setPrinted(false), 2000);
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-4 md:p-8">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div>
            <div className="flex items-center gap-2 text-sm text-slate-400 mb-1">
              <Link href="/" className="hover:text-cyan-400">Dashboard</Link>
              <span>/</span>
              <Link href="/ai" className="hover:text-cyan-400">AI Hub</Link>
              <span>/</span>
              <span className="text-slate-200">Documents</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white flex items-center gap-3">
              ✍️ AI Clinical Documentation Generator
            </h1>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={handleCopy}
              className="px-3 py-1.5 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 rounded border border-slate-700 transition"
            >
              {copied ? "✓ Copied" : "📋 Copy Text"}
            </button>
            <button
              type="button"
              onClick={handlePrint}
              className="px-3 py-1.5 text-xs font-medium bg-cyan-600 hover:bg-cyan-500 text-white rounded shadow transition"
            >
              🖨️ Print / PDF
            </button>
            <Link
              href="/ai"
              className="px-3 py-1.5 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 transition"
            >
              Back to Hub
            </Link>
          </div>
        </div>

        {/* Form & Preview Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Controls */}
          <div className="lg:col-span-5 space-y-4">
            <div className="bg-slate-800/80 border border-slate-700/70 rounded-xl p-5 space-y-4 shadow-lg">
              <h2 className="text-base font-semibold text-slate-200 border-b border-slate-700/60 pb-2">
                Document Configuration
              </h2>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Document Type</label>
                <select
                  value={docType}
                  onChange={(e) => handleDocTypeChange(e.target.value as ClinicalDocType)}
                  className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                >
                  <option value="REFERRAL_LETTER">Specialist Referral Letter</option>
                  <option value="MEDICAL_CERTIFICATE">Medical Leave Certificate</option>
                  <option value="POST_OP_INSTRUCTIONS">Post-Operative Instructions</option>
                  <option value="DISCHARGE_SUMMARY">Discharge / Treatment Summary</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Patient Name</label>
                <input
                  type="text"
                  value={patientName}
                  onChange={(e) => setPatientName(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Age / Gender</label>
                <input
                  type="text"
                  value={patientAgeGender}
                  onChange={(e) => setPatientAgeGender(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Attending Clinician</label>
                <input
                  type="text"
                  value={clinicianName}
                  onChange={(e) => setClinicianName(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                />
              </div>

              {docType === "REFERRAL_LETTER" && (
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Referred Specialist</label>
                  <input
                    type="text"
                    value={recipient}
                    onChange={(e) => setRecipient(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                  />
                </div>
              )}

              {docType === "MEDICAL_CERTIFICATE" && (
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1">Leave Duration (Days)</label>
                  <input
                    type="number"
                    min="1"
                    max="14"
                    value={leaveDays}
                    onChange={(e) => setLeaveDays(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-1.5 text-sm text-slate-200 focus:outline-none focus:border-cyan-500"
                  />
                </div>
              )}

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Clinical Indication / Diagnosis</label>
                <textarea
                  rows={3}
                  value={diagnosis}
                  onChange={(e) => setDiagnosis(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <button
                type="button"
                onClick={handleRegenerate}
                disabled={isGenerating}
                className="w-full py-2.5 px-4 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-medium rounded-lg text-sm transition shadow-md flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {isGenerating ? "Formatting Letterhead..." : "⚡ Regenerate Document Draft"}
              </button>
            </div>
          </div>

          {/* Letterhead Preview */}
          <div className="lg:col-span-7 space-y-4">
            <div className="bg-white text-slate-900 rounded-xl p-8 shadow-2xl border border-slate-200 min-h-[550px] flex flex-col justify-between font-serif">
              {/* Header Letterhead */}
              <div>
                <div className="flex items-center justify-between border-b-2 border-slate-800 pb-4 mb-6">
                  <div>
                    <h2 className="text-xl font-bold tracking-tight text-slate-900 uppercase font-sans">
                      DentalCare Pro Clinic
                    </h2>
                    <p className="text-xs text-slate-600 font-sans">
                      Advanced Multi-Specialty Dental Center & Oral Surgery Unit
                    </p>
                    <p className="text-[11px] text-slate-500 font-sans">
                      124 Health Avenue, Suite 400 · Ph: +91 98765 43210 · info@dentalcarepro.com
                    </p>
                  </div>
                  <div className="w-12 h-12 rounded-lg bg-cyan-700 flex items-center justify-center text-white font-bold text-lg font-sans shadow">
                    DC
                  </div>
                </div>

                {/* Document Body (Editable) */}
                <textarea
                  rows={16}
                  value={documentContent}
                  onChange={(e) => setDocumentContent(e.target.value)}
                  className="w-full bg-transparent border-none text-slate-800 text-sm leading-relaxed focus:outline-none resize-none font-mono"
                />
              </div>

              {/* Signature Block */}
              <div className="pt-6 border-t border-slate-200 flex items-end justify-between font-sans">
                <div className="text-[11px] text-slate-500">
                  <p>Electronically drafted & certified via DentalCare Pro CDS.</p>
                  <p>Clinic UID: DC-TENANT-BRIGHTSMILE-01</p>
                </div>
                <div className="text-right">
                  <div className="w-36 border-b border-slate-900 mb-1"></div>
                  <p className="text-xs font-semibold text-slate-900">{clinicianName}</p>
                  <p className="text-[11px] text-slate-600">Attending Dental Clinician</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
