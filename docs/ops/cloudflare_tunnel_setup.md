# Cloudflare Tunnel Setup Guide for DentalCare Pro

This guide explains how to set up **Cloudflare Tunnel (`cloudflared`)** on the clinic's Windows server to enable secure, zero-trust remote access from iPhones, Android devices, and home laptops without opening any router ports.

---

## Why Cloudflare Tunnel?

1. **Zero Open Ports**: You never configure port forwarding on your clinic Wi-Fi router.
2. **Automatic SSL/TLS**: Valid HTTPS certificates are handled automatically.
3. **DDoS & Web Application Protection**: Cloudflare absorbs unauthorized scanning and bot traffic.
4. **PostgreSQL Protection**: PostgreSQL port 5432 remains on localhost (`127.0.0.1`) and is **never** accessible over the internet.

---

## Step 1: Install `cloudflared` on Windows

You can install `cloudflared` in one of two ways:

### Option A: Windows Package Manager (winget)
Open Windows PowerShell as Administrator and run:
```powershell
winget install --id Cloudflare.cloudflared
```

### Option B: Direct MSI Download
1. Download the latest MSI from Cloudflare:  
   `https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.msi`
2. Run the installer. It will install to `C:\Program Files (x86)\cloudflared\cloudflared.exe`.

---

## Step 2: Authenticate and Create Tunnel

1. Open PowerShell and login to your free Cloudflare account:
   ```powershell
   cloudflared tunnel login
   ```
   *A browser window will open. Select your clinic domain name (e.g. `brightsmileclinic.com`).*

2. Create a named tunnel for your clinic:
   ```powershell
   cloudflared tunnel create dentalcare-clinic
   ```
   *Note the Tunnel UUID and credentials file location (usually `C:\Users\<user>\.cloudflared\<UUID>.json`).*

---

## Step 3: Run the DentalCare Pro Setup Assistant

DentalCare Pro provides an automated script to configure the tunnel ingress rules:

```powershell
python scripts/setup_cloudflare_tunnel.py --hostname clinic.brightsmileclinic.com --tunnel-name dentalcare-clinic
```

This creates the configuration file at `C:\ProgramData\cloudflared\config.yml`:

```yaml
tunnel: dentalcare-clinic
credentials-file: C:\ProgramData\cloudflared\dentalcare-clinic.json

ingress:
  # Route API traffic to FastAPI daemon (port 8000)
  - hostname: clinic.brightsmileclinic.com
    path: /api/*
    service: http://127.0.0.1:8000

  # Route WebSocket sync
  - hostname: clinic.brightsmileclinic.com
    path: /ws/*
    service: http://127.0.0.1:8000

  # Route Web UI and Mobile Dashboard (port 3000)
  - hostname: clinic.brightsmileclinic.com
    service: http://127.0.0.1:3000

  # Catch-all
  - service: http_status:404
```

---

## Step 4: Route DNS to the Tunnel

Run:
```powershell
cloudflared tunnel route dns dentalcare-clinic clinic.brightsmileclinic.com
```

---

## Step 5: Install and Start as Windows Service

Install the tunnel to start automatically when the clinic server boots:
```powershell
cloudflared service install
net start cloudflared
```

---

## Step 6: Access from Mobile Devices

Open Safari or Chrome on your mobile phone and navigate to:
```
https://clinic.brightsmileclinic.com/mobile
```
Log in using your doctor credentials. You will be greeted by the touch-optimized mobile dashboard.
