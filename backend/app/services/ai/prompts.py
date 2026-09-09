from __future__ import annotations

SOAP_SYSTEM_PROMPT = """You are an expert dental clinical assistant.
Your job is to generate a comprehensive, structured SOAP note (Subjective, Objective, Assessment, Plan) based on appointment records, clinical procedures, odontogram status, and clinician notes.
You must adhere strictly to dental clinical standards (ADA/AAOMS/FDI).
Output must be structured as JSON with keys: "subjective", "objective", "assessment", "plan".
Never output medical advice that overrides the clinician.
"""

PATIENT_SUMMARY_SYSTEM_PROMPT = """You are an expert dental informatics assistant.
Summarize the patient's medical and dental record.
Highlight any high-risk medical alerts (e.g. penicillin allergy, latex sensitivity, bleeding disorders/anticoagulants, uncontrolled diabetes, cardiovascular disease).
Output must be structured as JSON with keys: "summary", "risks" (list of objects with category, severity, title, details), "recommended_recall_months".
"""
SUMMARY_SYSTEM_PROMPT = PATIENT_SUMMARY_SYSTEM_PROMPT


PRESCRIPTION_SYSTEM_PROMPT = """You are an AI dental pharmacotherapy assistant.
Given a diagnosis, treatment, and patient history (allergies, medical conditions):
Suggest appropriate evidence-based dental medications (antibiotics, analgesics, anti-inflammatories, mouthwashes).
Check strictly for allergy contraindications (especially penicillin, NSAIDs).
Output must be a JSON list of objects with keys: "medicine_name", "generic_name", "dosage", "frequency", "duration", "instructions", "rationale".
All suggestions are advisory and require human dentist approval.
"""

DOCUMENTATION_SYSTEM_PROMPT = """You are an AI dental clinical documentation specialist.
Generate formal, compliant documentation:
- Specialist Referral Letters
- Medical Leave / Rest Certificates
- Post-Operative Care Instructions
- Discharge Summaries
- Patient Treatment Plan Presentations
Ensure professional clinical tone and patient safety clarity.
"""

SEARCH_SYSTEM_PROMPT = """You are an AI clinical database assistant.
Parse the user's natural language query into structured database filters.
Supported filters include: condition (e.g., DIABETES, HYPERTENSION), procedure, status, date_range.
Output must be JSON with keys: "intent", "filters", "explanation".
"""


def format_soap_prompt(
    patient_info: str,
    complaint: str,
    observations: str,
    procedures: str,
    teeth_info: str,
    clinician_notes: str | None = None,
) -> str:
    return f"""Generate a detailed dental SOAP note for the following patient visit:

PATIENT CONTEXT:
{patient_info}

CHIEF COMPLAINT:
{complaint}

CLINICAL OBSERVATIONS & EXAM:
{observations}

PROCEDURES PERFORMED:
{procedures}

AFFECTED TEETH / ODONTOGRAM:
{teeth_info}

CLINICIAN RAW BULLET NOTES:
{clinician_notes or "None provided"}

Output format: JSON with "subjective", "objective", "assessment", "plan".
"""


def format_patient_summary_prompt(
    patient_demographics: str,
    medical_history: str,
    allergies: str,
    past_treatments: str,
    active_prescriptions: str,
) -> str:
    return f"""Synthesize clinical summary and highlight medical risk alerts:

PATIENT:
{patient_demographics}

MEDICAL CONDITIONS:
{medical_history}

ALLERGIES & ADVERSE REACTIONS:
{allergies}

TREATMENT HISTORY:
{past_treatments}

ACTIVE MEDICATIONS:
{active_prescriptions}

Output format: JSON with "summary", "risks", "recommended_recall_months".
"""


def format_prescription_prompt(
    patient_info: str,
    allergies: str,
    diagnosis: str,
    procedures: str,
    medical_history: str,
) -> str:
    return f"""Suggest evidence-based dental medications for:

DIAGNOSIS:
{diagnosis}

PROCEDURE COMPLETED:
{procedures}

PATIENT ALLERGIES (CRITICAL CHECK):
{allergies}

UNDERLYING MEDICAL CONDITIONS:
{medical_history}

PATIENT DEMOGRAPHICS:
{patient_info}

Output format: JSON list of objects with "medicine_name", "generic_name", "dosage", "frequency", "duration", "instructions", "rationale".
"""


def format_doc_prompt(
    doc_type: str,
    patient_info: str,
    treatment_info: str,
    recipient: str | None,
    custom_notes: str | None,
) -> str:
    return f"""Generate a formal dental {doc_type}:

PATIENT DETAILS:
{patient_info}

CLINICAL / TREATMENT SUMMARY:
{treatment_info}

RECIPIENT / ATTENDING DOCTOR:
{recipient or "Healthcare Provider / Specialist"}

ADDITIONAL CLINICAL NOTES:
{custom_notes or "Standard protocol"}
"""


def format_search_prompt(query: str) -> str:
    return f"""Convert the following natural language query into clinical search filters:
QUERY: "{query}"

Output format: JSON with "intent", "filters", "explanation".
"""
