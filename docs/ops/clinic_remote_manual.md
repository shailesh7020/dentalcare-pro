# DentalCare Pro – Clinic Remote Access User Manual

This manual provides role-specific instructions for clinic owners, senior dentists, and reception managers accessing DentalCare Pro from home or on mobile devices.

---

## 1. Quick Reference for Doctors & Clinic Owners

### How to Check Today's Schedule on Your Phone
1. Open your mobile browser (Safari on iPhone, Chrome on Android).
2. Navigate to your clinic remote URL (e.g. `https://clinic.brightsmile.com/mobile` or Tailscale IP `http://100.x.y.z:3000/mobile`).
3. Log in with your email and password.
4. If 2FA is enabled, enter your 6-digit authenticator code.
5. The **Mobile Dashboard** displays:
   - **Today's Visits**: Patient names, appointment times, chair operatory, and chief complaints.
   - **Quick Actions**: Tap **✓ Confirm** to mark arrival, **📅 Reschedule** to change time, or **📝 Note** to record clinical observations.
   - **Revenue**: Today's collections broken down by UPI and Cash.

### Adding Notes from Home
- Tap **📝 Note** on any patient card.
- Type in post-operative observations, lab instructions, or internal reminders.
- Tap **Save Note**. The note synchronizes immediately to the clinic server on-premise.

---

## 2. Remote Security Rules & Limitations

To protect patient medical records and financial books from accidental deletions or remote account tampering, DentalCare Pro enforces **Strict Remote Guardrails**:

### What You CAN Do Remotely:
- ✓ View schedules for today, tomorrow, and the entire week
- ✓ Look up patient medical histories, contact details, and dental records
- ✓ Review clinical treatment plans and SOAP notes
- ✓ View digital odontograms and tooth history
- ✓ View issued prescriptions and medicine dosages
- ✓ Check invoice balances, payment receipts, and revenue summaries
- ✓ Monitor low-stock inventory alerts
- ✓ Confirm, reschedule, or cancel appointments
- ✓ Add clinical notes and update patient phone numbers

### What is STRICTLY PROHIBITED Remotely (On-Premise Server Only):
- ❌ **Deleting patient profiles**: Must be performed on the physical clinic computer.
- ❌ **Deleting invoices or changing tax calculations**: Financial audit integrity is strictly locked to the on-premise clinic server.
- ❌ **Deleting clinical treatments or procedure logs**: Prevent unauthorized erasure of medical history.
- ❌ **Restoring database backups or database administration**: Prevents remote tampering with clinic storage.

*If a user attempts a prohibited remote action, the application displays a clear security message: "Prohibited remote action: Destructive deletions can only be performed on-premise on the clinic server."*

---

## 3. Two-Factor Authentication (2FA) Setup

Clinic administrators and doctors can activate 2FA for extra remote protection:

1. In DentalCare Pro, navigate to **Settings** > **Security & Remote Access**.
2. Click **Enable 2FA**.
3. Scan the displayed QR code with your authenticator app (Google Authenticator, Microsoft Authenticator, Apple Passwords, or 1Password).
4. Enter the 6-digit code shown on your phone to confirm.
5. Save your 8 emergency backup recovery codes in a secure location.
