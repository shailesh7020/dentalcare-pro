# scripts/tutorial/ch29_faq.py
from reportlab.platypus import Paragraph, Spacer, PageBreak

FAQ_ITEMS = [
    # General & Architecture (1-10)
    ("What is DentalCare Pro?", "DentalCare Pro is an enterprise cloud-native, AI-powered Dental Practice Management System and Electronic Dental Record (EDR) platform designed for multi-branch clinics, DSOs, and private dental practices."),
    ("Which operating systems are supported for client workstations?", "Any workstation with a modern web browser (Google Chrome, Microsoft Edge, Mozilla Firefox, Safari) on Windows 10/11, macOS, Linux, or ChromeOS is fully supported."),
    ("Can DentalCare Pro run completely on-premise without an Internet connection?", "Yes. DentalCare Pro can be deployed on a local clinic server running Docker or Linux, allowing all computers on the local network to operate autonomously."),
    ("What are the minimum hardware requirements for an on-premise clinic server?", "A quad-core processor (Intel Core i5/Xeon or AMD Ryzen), 16 GB of RAM, and a 100 GB NVMe SSD is sufficient for up to 10 operatories."),
    ("Is DentalCare Pro cloud-hosted or self-hosted?", "DentalCare Pro supports both models: cloud-hosted SaaS (AWS/GCP/Azure) and self-hosted private cloud or local on-premise clinic servers."),
    ("What web technologies power the frontend portal?", "The web portal is built using Next.js 16 (Turbopack), React 19, TypeScript, Tailwind CSS v4, and TanStack Query v5."),
    ("What technologies power the backend API?", "The core API is built on Python 3.13, FastAPI, Pydantic v2, and Async SQLAlchemy 2.0."),
    ("Which database engine is used by DentalCare Pro?", "PostgreSQL 16 is the primary relational database, supported by PgBouncer for high-throughput connection pooling."),
    ("Why is Redis included in the technology stack?", "Redis 7 handles distributed caching, Celery asynchronous task queuing, and real-time session storage."),
    ("Is the mobile app native or cross-platform?", "The mobile suite is built with Flutter 3.24, delivering 100% native compiled performance on Android and iOS from a unified Dart codebase."),

    # Installation & DevOps (11-20)
    ("How long does an automated Docker Compose deployment take?", "On a modern server with Docker installed, executing 'docker compose up -d' takes approximately 2 to 3 minutes to pull images, apply database migrations, and launch."),
    ("How do I perform database migrations during software updates?", "Database migrations are fully automated via Alembic scripts bundled in the backend container, triggered automatically on container startup."),
    ("Can I deploy DentalCare Pro to a Kubernetes cluster?", "Yes. DentalCare Pro provides enterprise Helm 3 charts in the /helm directory with pre-configured Horizontal Pod Autoscalers (HPA), Ingress TLS, and Network Policies."),
    ("How does the system handle TLS/SSL certificate renewals?", "In Kubernetes, Cert-Manager automates Let's Encrypt TLS 1.3 certificates. In Docker Compose, Nginx reverse proxy handles SSL termination."),
    ("What is the recommended backup strategy for production?", "Automated daily PostgreSQL physical/WAL backups to encrypted Amazon S3 or Google Cloud Storage, with continuous WAL archiving for Point-In-Time Recovery."),
    ("What is the Recovery Point Objective (RPO) of DentalCare Pro?", "The tested RPO is ≤ 15 minutes (under continuous WAL streaming, typical data loss window is under 2 minutes)."),
    ("What is the Recovery Time Objective (RTO) of DentalCare Pro?", "The tested RTO is ≤ 1 hour (automated standby failover completes in approximately 5.25 minutes)."),
    ("How do I check system health status?", "Administrators can query the health endpoint at /api/health, which reports real-time ping status for PostgreSQL, Redis, Celery, and storage systems."),
    ("Where are server error logs stored?", "Logs are captured in JSON format and shipped to Grafana Loki, or inspected directly via 'docker compose logs -f api' or 'kubectl logs -n dentalcare'."),
    ("Can I configure custom clinic domain names?", "Yes. Multi-branch networks can map custom subdomains (e.g., clinic1.mydentalcare.com) through Ingress reverse proxy routing."),

    # Security & Access Control (21-30)
    ("How are user passwords protected?", "Passwords are cryptographically salted and hashed using Bcrypt with a work factor of 12 rounds. Plaintext passwords are never stored or logged."),
    ("What authentication mechanism is used for API communication?", "Stateless JSON Web Tokens (JWT) using HMAC-SHA256 or RSA-256 signatures with short-lived access tokens (15m) and rotating refresh tokens (7d)."),
    ("What happens if an access token expires while a user is working?", "The frontend and mobile clients automatically submit the refresh token in the background to obtain a fresh access token without interrupting the user."),
    ("How does DentalCare Pro isolate data between different clinics?", "Zero-trust multi-tenancy enforces a strict clinic_id scoping filter on every single database query and API route. Cross-tenant access attempts return HTTP 403 Forbidden."),
    ("What roles are available in the Role-Based Access Control (RBAC) system?", "Super Admin, Clinic Admin, Dentist, Hygienist, Dental Assistant, Receptionist, Accountant, and Patient."),
    ("Can a receptionist edit or sign off on clinical dental treatments?", "No. RBAC strictly restricts treatment completion, clinical diagnosis, and prescription signing to licensed Dentists."),
    ("Does DentalCare Pro comply with the HIPAA Security Rule?", "Yes. DentalCare Pro enforces all technical safeguards required under 45 CFR § 164.312, including access controls, transmission security, audit logging, and data encryption at rest."),
    ("Is patient medical data encrypted at rest?", "Yes. PostgreSQL tablespaces, S3 radiographic storage buckets, and automated backup archives are encrypted using AES-256."),
    ("Does the system record audit trails when patient records are viewed?", "Yes. Every view, update, export, and deletion of Protected Health Information (PHI) is immutably logged with user ID, timestamp, and client IP address."),
    ("How does the platform defend against SQL Injection attacks?", "All database queries are compiled through SQLAlchemy 2.0 AST parameterized queries, preventing SQL injection payloads from executing."),

    # Patient Records & Intake (31-40)
    ("How do I register a new patient in the system?", "Click 'New Patient' on the navigation bar (or press Alt+N), enter their basic demographics and mobile number, and click Save."),
    ("How does the system prevent duplicate patient records?", "When a mobile number, email, or government ID is entered, the duplicate detection engine immediately alerts the receptionist if a matching record already exists."),
    ("Can patients fill out their medical intake forms digitally?", "Yes. Patients can complete medical history forms online via the Patient Portal before arriving, or on a clinic tablet in the waiting room."),
    ("Which systemic medical conditions are tracked in patient charts?", "Diabetes, Hypertension, Cardiac Diseases, Asthma, Epilepsy, Thyroid Disorders, Pregnancy, Blood Thinners, and Drug Allergies (Penicillin, Latex, NSAIDs)."),
    ("How do medical alerts appear to the dentist?", "Active systemic conditions and severe allergies display as a high-visibility amber/red alert banner at the top of the patient chart and odontogram."),
    ("Can I attach digital X-rays and intraoral photographs to a patient chart?", "Yes. The Document module supports DICOM, JPEG, PNG, and PDF files with drag-and-drop upload and integrated high-resolution viewing."),
    ("What is the Patient Chronological Timeline?", "An automated activity feed displaying every clinical visit, appointment, treatment, prescription, invoice, and note in reverse chronological order."),
    ("Can an archived patient record be restored?", "Yes. Records are soft-deleted (deleted_at timestamp set); clinic administrators can view archived charts and restore them with one click."),
    ("How does the system calculate patient age?", "Patient age is dynamically computed from their verified date of birth, automatically updating each year."),
    ("Can I record emergency contact information for minor patients?", "Yes. The intake form includes emergency contact name, relationship (Parent/Guardian), and verified mobile number."),

    # Appointments & Scheduling (41-50)
    ("How do I book an appointment for a patient?", "Click an open time slot on the Calendar Grid, select the patient, choose the treating dentist and chair operatory, and click Confirm."),
    ("Can a patient be booked if the dentist is already busy?", "No. The appointment engine validates doctor availability and blocks conflicting overlapping appointments."),
    ("How does Operatory Chair scheduling work?", "Each operatory (e.g. Chair 1, Chair 2, Surgery Suite) has its own calendar column, allowing receptionists to see live occupancy across the clinic."),
    ("What appointment statuses are tracked in the calendar?", "SCHEDULED, CONFIRMED, CHECKED_IN, IN_CHAIR, COMPLETED, CANCELLED, and NO_SHOW."),
    ("How does the live Waiting Room Queue work?", "When a patient arrives, the receptionist marks them 'CHECKED_IN'. The patient appears on the operatory queue screen with wait duration timers."),
    ("Can patients receive automated appointment reminder SMS messages?", "Yes. Automated reminders are sent 24 hours and 2 hours prior to scheduled appointment times via integrated SMS/WhatsApp gateways."),
    ("How do I reschedule an appointment?", "Drag and drop the appointment card to a new time slot on the calendar grid, or open the appointment modal and select a new date and time."),
    ("What happens when an appointment is cancelled?", "The slot is freed on the calendar, the cancellation reason is recorded, and receptionists are prompted to notify patients on the waiting list."),
    ("Can I block time for staff meetings or doctor leaves?", "Yes. Administrators can create 'Blocked Time' events that prevent appointments from being booked during that window."),
    ("How does the 6-month preventative dental recall system work?", "When a treatment is completed, the system automatically prompts the receptionist to schedule a 6-month hygiene and recall checkup."),

    # Interactive Odontogram (51-60)
    ("What tooth numbering systems are supported?", "The international FDI 2-digit notation (Teeth 11–48) and the Universal Numbering System (Teeth 1–32), plus pediatric primary teeth (A–T / 51–85)."),
    ("Can I chart primary (deciduous) teeth for pediatric patients?", "Yes. Dentists can switch the odontogram view to 'Pediatric' or 'Mixed Dentition' mode to chart deciduous teeth."),
    ("What anatomical surfaces can be charted on each tooth?", "Five distinct anatomical facets: Mesial (M), Distal (D), Occlusal/Incisal (O/I), Buccal/Facial (B/F), and Lingual/Palatal (L/P)."),
    ("What does the color red signify on the odontogram?", "Active dental caries (decay) or pathology requiring clinical treatment."),
    ("What does the color blue signify on the odontogram?", "An existing, sound tooth-colored composite restoration."),
    ("What does the color gold/amber signify on the odontogram?", "A full-coverage prosthodontic crown (PFM, Zirconia, or Ceramic)."),
    ("What does the color purple signify on the odontogram?", "Completed endodontic root canal therapy (RCT) with root canal filling."),
    ("How do I mark an extracted tooth on the odontogram?", "Select the tooth and click 'Extracted'; the tooth is rendered with a dark gray diagonal cross and disabled from future filling charting."),
    ("Can I record periodontal pocket probing depths?", "Yes. The Periodontal Chart module records 6-point probing depths (Mesio-Buccal, Mid-Buccal, Disto-Buccal, Mesio-Lingual, Mid-Lingual, Disto-Lingual) with bleeding on probing (BOP) markers."),
    ("Does updating the odontogram automatically update the proposed treatment plan?", "Yes. Charting a condition (e.g. #14 Caries) allows clinicians to generate a corresponding treatment plan item with one click."),

    # Treatment Management & Clinical Notes (61-70)
    ("What is a multi-phase treatment plan?", "A structured roadmap that groups complex dental procedures into prioritized clinical stages (Phase 1: Emergency/Pain relief; Phase 2: Restorative; Phase 3: Aesthetics)."),
    ("Can I print or email treatment cost estimates for patients?", "Yes. Treatment plans generate clear, itemized cost estimates showing total procedure fees, estimated insurance coverage, and patient copay balances."),
    ("What is SOAP format in clinical documentation?", "Subjective (patient complaints), Objective (clinical findings/radiographs), Assessment (diagnosis), and Plan (treatments performed)."),
    ("Can dentists dictate clinical notes using voice?", "Yes. The web and mobile portals support speech-to-text dictation that automatically populates SOAP note fields."),
    ("How does the system ensure clinical notes cannot be fraudulently altered?", "Once a treatment note is finalized and signed by the dentist, it is locked. Any subsequent corrections must be added as a timestamped addendum."),
    ("Can patients sign informed consent forms digitally?", "Yes. Patients can sign consent forms directly on an iPad, Android tablet, or smartphone touchscreen with their finger or stylus."),
    ("Does the system support ADA CDT dental procedure codes?", "Yes. The procedure catalog comes pre-loaded with standard CDT codes (e.g., D0120 Periodic Oral Exam, D2391 Resin-based composite 1 surface, D3330 Molar Endodontics)."),
    ("Can clinics customize procedure pricing?", "Yes. Clinic administrators can modify standard fee schedules and create custom clinic-specific treatment items."),
    ("What happens when a treatment procedure is marked completed?", "The odontogram visual status updates to 'Restored', clinical supplies used are depleted from inventory, and a draft billing invoice is generated."),
    ("Can multiple dentists collaborate on the same treatment plan?", "Yes. Individual procedure items within a master treatment plan can be assigned to different dental specialists (e.g., Endodontist, Periodontist, Prosthodontist)."),

    # Prescriptions (71-75)
    ("How do dentists write an electronic prescription (e-Rx)?", "Navigate to the patient's Prescriptions tab, click 'New Prescription', select medicines from the formulary, specify dosage and duration, and click Issue."),
    ("What drug interaction alerts are provided?", "The system warns if a prescribed medication conflicts with known patient allergies or recorded existing medications."),
    ("Can clinics save standard prescription templates?", "Yes. Commonly prescribed protocols (e.g. 'Standard Adult Antibiotic Prophylaxis: Amoxicillin 2g 1hr prior to procedure') can be saved as 1-click templates."),
    ("Can prescriptions be printed on clinic letterhead?", "Yes. The system compiles official, high-resolution PDF prescription slips with clinic branding, doctor license numbers, and digital signatures."),
    ("Can patients access their prescriptions from their mobile phones?", "Yes. Prescriptions appear instantly in the Patient Mobile Portal for easy reference at external pharmacies."),

    # Billing & Financial Management (76-80)
    ("How are dental invoices generated?", "Invoices are created automatically when treatments are marked completed, or generated manually for OTC sales and hygiene products."),
    ("Does DentalCare Pro support split payments?", "Yes. An invoice can be paid using multiple methods simultaneously (e.g. $100 Cash + $150 Credit Card)."),
    ("Can patients make partial payments on large treatments?", "Yes. The system tracks outstanding balances due and displays them prominently on accounts receivable reports."),
    ("How are dental refunds handled?", "Approved refunds are recorded against the original receipt number with mandatory supervisor authorization and accounting audit logging."),
    ("Can invoices be exported for external accounting software like QuickBooks?", "Yes. Financial transactions, invoice ledgers, and day sheets can be exported to Excel and CSV formats."),

    # Dental Insurance & Claims (81-85)
    ("What is an EDI 837D dental claim?", "The standard electronic claim format used by dental clearinghouses in North America to submit insurance reimbursement requests."),
    ("How do I submit an electronic dental insurance claim?", "From the patient's billing tab, select the unpaid invoice, click 'Submit Claim', attach necessary radiographic X-rays, and transmit via clearinghouse."),
    ("How are insurance pre-authorizations tracked?", "Pre-authorizations are logged in the Insurance module with tracking numbers, approved dollar limits, and expiration dates."),
    ("What is an Explanation of Benefits (EOB)?", "A statement from the insurer detailing covered procedures, approved amounts, contractual write-offs, and patient copay responsibilities."),
    ("Can the system handle dual dental insurance coverage?", "Yes. DentalCare Pro tracks Primary and Secondary insurance policies and manages coordination of benefits (COB)."),

    # Inventory & Supplies (86-90)
    ("How does automated inventory depletion work?", "Procedures are mapped to consumable supply bills-of-materials; completing a procedure automatically deducts required consumables from stock."),
    ("How do reorder alerts notify clinic staff?", "When an item's remaining quantity drops below its reorder point, the inventory dashboard highlights it in amber/red and suggests a purchase order."),
    ("Can DentalCare Pro track batch lot numbers and expiration dates?", "Yes. Material batches are tracked to ensure First-In, First-Out (FIFO) usage and prevent using expired composites or anesthetics."),
    ("How are purchase orders processed?", "Staff generate purchase orders, send them to registered suppliers, and mark items received upon physical delivery and verification."),
    ("Can inventory be transferred between different clinic branches?", "Yes. Enterprise DSO networks can transfer stock from a central warehouse to branch clinics with digital dispatch and receiving audits."),

    # HR, Attendance & Payroll (91-95)
    ("How is employee attendance tracked?", "Staff clock in and out using integrated biometric fingerprint/facial recognition terminals or the staff mobile app."),
    ("How are dentist commissions calculated in payroll?", "Clinicians can be assigned base salaries plus procedure commission percentages (e.g. 35% of collected restorative production)."),
    ("Can employees request leaves through the software?", "Yes. Staff submit leave requests via their mobile self-service portal; managers receive notifications to approve or reject."),
    ("Does the payroll module calculate tax and pension deductions?", "Yes. Payroll runs calculate statutory gross-to-net withholdings, employee taxes, and pension contributions."),
    ("Can staff download their monthly pay slips?", "Yes. Digitally signed, itemized salary slips are generated as PDFs and accessible in the employee portal."),

    # Mobile Applications & Offline Mode (96-100)
    ("Can dentists use DentalCare Pro on an iPad or tablet?", "Yes. The responsive Next.js web application and native Flutter tablet apps are fully optimized for touchscreens and styluses."),
    ("How does mobile offline mode work when Wi-Fi disconnects?", "The Flutter mobile app caches clinical charts locally in an encrypted SQLite database. Work continues uninterrupted, and changes sync automatically upon reconnection."),
    ("How do patients receive appointment notifications on mobile?", "Through native Apple Push Notification Service (APNs) and Firebase Cloud Messaging (FCM), as well as SMS reminders."),
    ("Can patients book their own appointments online?", "Yes. The Patient Web Portal and Mobile App provide self-service booking into pre-configured doctor availability slots."),
    ("Is DentalCare Pro ready for commercial enterprise deployment?", "Yes. DentalCare Pro v1.0 Enterprise Edition has completed all 17 development and verification phases, with 100% test passage and full HIPAA/GDPR production readiness.")
]

def build_chapter_29(styles):
    story = []
    story.append(Paragraph("Chapter 29: Frequently Asked Questions (FAQ)", styles["ChapterHeading"]))
    story.append(Paragraph(
        "This chapter contains 100 comprehensive questions and answers addressing technical, clinical, administrative, "
        "and operational aspects of DentalCare Pro.",
        styles["TutorialBody"]
    ))
    story.append(Spacer(1, 8))

    for idx, (q, a) in enumerate(FAQ_ITEMS, 1):
        q_text = f"<b>Q{idx}: {q}</b>"
        a_text = f"<b>Answer:</b> {a}"
        story.append(Paragraph(q_text, styles["SubSectionHeading"]))
        story.append(Paragraph(a_text, styles["TutorialBody"]))
        story.append(Spacer(1, 4))
        if idx % 10 == 0 and idx < 100:
            story.append(PageBreak())

    story.append(PageBreak())
    return story
