# Tailscale Secure Private Mesh Setup Guide

Tailscale provides an encrypted, peer-to-peer WireGuard network connecting your clinic server directly to the doctor's personal phone, iPad, or home laptop. It requires zero domain registration and zero router configuration.

---

## Benefits of Tailscale for Dental Clinics

- **Private Point-to-Point Encryption**: Traffic flows directly between your clinic server and your personal phone using WireGuard.
- **No Public Domain Required**: Works using private IP addresses in the `100.x.y.z` range.
- **Zero Configuration**: No DNS setup or Cloudflare account required.
- **Works Behind Dynamic IPs and CGNAT**: Connects through mobile carriers and home broadband without issues.

---

## Step 1: Install Tailscale on the Clinic Server (Windows)

1. Download Tailscale for Windows:  
   `https://tailscale.com/download/windows`
2. Install the MSI and launch the application from the Windows System Tray.
3. Sign in with your clinic administrator email (e.g. Google / Microsoft / Apple).
4. Run the helper script:
   ```cmd
   scripts\setup_tailscale.bat
   ```
5. The script will print the clinic server's private Tailscale IP (e.g. `100.85.120.45`).

---

## Step 2: Install Tailscale on Doctor's Mobile Phone or Tablet

1. Download the **Tailscale** app from the **Apple App Store** (iOS) or **Google Play Store** (Android).
2. Sign in with the **same account** used on the clinic server.
3. Toggle the switch to **Connected**.

---

## Step 3: Access DentalCare Pro Mobile Dashboard

Open Safari or Chrome on your phone and enter:
```
http://100.85.120.45:3000/mobile
```
*(Replace `100.85.120.45` with your server's actual Tailscale IP).*

You now have direct, ultra-fast encrypted access to today's schedule, patient profiles, and revenue summaries.
