# DentalCare Pro – Clinic Desktop Deployment Guide

This guide outlines the two primary deployment topologies for installing DentalCare Pro across dental practices.

---

## Topology A: Single-Workstation Solo Clinic (All-in-One)

Ideal for solo dental practices or single-operatory clinics operating on one computer.

```
+-------------------------------------------------------------+
|               Solo Clinic Windows Workstation               |
|                                                             |
|  [ DentalCarePro.exe ] (Desktop Shell & Tray)               |
|            |                                                |
|  [ DentalCarePro-API.exe ] (FastAPI Core Engine on :8000)   |
|            |                                                |
|  [ PostgreSQL 16 Database ] (Local Service on 127.0.0.1)    |
|            |                                                |
|  [ %LOCALAPPDATA%\DentalCarePro ] (Patient Files & Data)    |
+-------------------------------------------------------------+
```

### Installation Steps:
1. Install PostgreSQL 16 on the workstation with a default password.
2. Run `DentalCarePro-Setup-1.0.0.exe`.
3. In the Setup Wizard, leave database host as `127.0.0.1` and click Complete Setup.
4. The clinic is fully operational immediately.

---

## Topology B: Multi-Operatory Dental Clinic LAN (Centralized Server)

Ideal for clinics with 2 to 20 operatories (Reception, Operatory 1, Operatory 2, Doctor Office, Billing Desk).

```
               +-------------------------------------------+
               |        Central Clinic Server / NAS        |
               |                                           |
               |  - PostgreSQL 16 (Port 5432)              |
               |  - Automated Daily Offsite Backups        |
               |  - IP: 192.168.1.100                      |
               +-------------------------------------------+
                                     |
               +---------------------+---------------------+
               | (Local Gigabit Clinic LAN Network)        |
               |                                           |
+---------------------------+             +---------------------------+
|  Reception Workstation    |             |  Operatory 1 Workstation  |
|  [ DentalCarePro.exe ]    |             |  [ DentalCarePro.exe ]    |
|  Points to 192.168.1.100  |             |  Points to 192.168.1.100  |
+---------------------------+             +---------------------------+
               |                                           |
+---------------------------+             +---------------------------+
|  Operatory 2 (Dentist)    |             |  Billing & Insurance Desk |
|  [ DentalCarePro.exe ]    |             |  [ DentalCarePro.exe ]    |
|  Points to 192.168.1.100  |             |  Points to 192.168.1.100  |
+---------------------------+             +---------------------------+
```

### Setup Instructions:
1. **Server Setup**: Install PostgreSQL 16 on the designated clinic server (or NAS). In `postgresql.conf`, set `listen_addresses = '*'`. In `pg_hba.conf`, add `host all all 192.168.1.0/24 scram-sha-256`.
2. **Workstation Setup**: Install `DentalCarePro-Setup-1.0.0.exe` on each receptionist and operatory computer.
3. In the First-Launch Wizard on each workstation, enter:
   `postgresql+asyncpg://postgres:password@192.168.1.100:5432/dentalcare`
4. All computers share synchronized real-time patient charts, appointments, waiting queues, and odontograms.
