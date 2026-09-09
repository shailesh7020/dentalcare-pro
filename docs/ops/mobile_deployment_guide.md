# DentalCare Pro - Mobile Applications Production Deployment Guide

This guide details the release engineering, code signing, and distribution processes for the DentalCare Pro mobile application across Android (Google Play) and iOS (Apple App Store).

---

## 1. Release Build Prerequisites

Ensure your build environment contains:
- **Flutter SDK**: `v3.24.0` or higher
- **Dart SDK**: `v3.5.0` or higher
- **Android Studio** & Android SDK Platform 35
- **Xcode**: `v16.0` or higher (macOS runner required for iOS release builds)

---

## 2. Android Release Pipeline (Google Play Console)

### Step 2.1: KeyStore Configuration
Create an upload keystore for Play App Signing:
```bash
keytool -genkey -v -keystore android-upload-keystore.jks \
        -alias dentalcare-upload -keyalg RSA -keysize 2048 -validity 10000
```
Place keystore path, storePassword, and keyPassword into GitHub Secrets or `android/key.properties`.

### Step 2.2: Generate Android App Bundle (AAB)
```bash
cd apps/mobile
flutter build appbundle --release --obfuscate --split-debug-info=./build/app/outputs/symbols
```
The output artifact will be generated at:
`apps/mobile/build/app/outputs/bundle/release/app-release.aab`

### Step 2.3: Automated Distribution via Fastlane
```bash
bundle exec fastlane android deploy_internal
```
Promote from **Internal Testing Track** -> **Closed Beta (Clinician Pilot)** -> **Production Track**.

---

## 3. iOS Release Pipeline (App Store Connect)

### Step 3.1: Apple Developer Provisioning
1. Generate an **App Store Distribution Certificate** in Apple Developer Portal.
2. Create App ID: `com.dentalcarepro.app` with Push Notifications and Associated Domains enabled.
3. Generate an App Store Provisioning Profile.

### Step 3.2: Compile iOS Release IPA
```bash
cd apps/mobile
flutter build ipa --release --obfuscate --split-debug-info=./build/ios/outputs/symbols
```
The resulting archive will be located at:
`apps/mobile/build/ios/archive/Runner.xcarchive`

### Step 3.3: Upload to TestFlight & App Store
```bash
xcrun altool --upload-app --type ios --file "build/ios/ipa/DentalCarePro.ipa" \
             --username "apple-deploy@dentalcarepro.com" --password "app-specific-password"
```

---

## 4. Post-Release Verification Checklist

- [x] Verify biometric prompt unlocks clinician dashboard on physical Android 14+ and iOS 18+ devices.
- [x] Verify offline mode: switch to Airplane Mode, modify tooth #14 on odontogram, reconnect, and verify synchronization.
- [x] Validate deep linking from patient SMS notification directly into appointment details.
- [x] Confirm FCM/APNs push notification delivery within 3 seconds of appointment cancellation.
