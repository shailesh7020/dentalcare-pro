# DentalCare Pro – Cross-Platform Mobile Applications

Production-grade cross-platform mobile suite built with Flutter for Android and iOS, powering:
1. **Dentist App**: Chairside clinical workflow, 32-tooth interactive odontogram, voice-assisted clinical SOAP notes, intraoral photography, and digital signatures.
2. **Receptionist App**: Front desk management, QR-code patient check-in, walk-in registration, and mobile billing.
3. **Patient App**: Self-service appointment booking, prescription ledger, invoice review, document vault, clinic chat, and AI dental symptom guidance.

## Architecture
- **Clean Architecture**: Domain, Data, Presentation layers with BLoC state management.
- **Offline-First**: Hive & SQLite encrypted storage, mutation queue, and delta pull/push sync engine.
- **Biometric Security**: Face ID and Fingerprint hardware authentication with secure token storage.
- **Push Notifications**: Firebase Cloud Messaging (FCM) and Apple Push Notification Service (APNs).
