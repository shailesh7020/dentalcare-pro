# DentalCare Pro – Windows Installer & Desktop User Guide

**Document Version**: 1.0.0 (Production Release)  
**Target Platform**: Windows 10 & Windows 11 (64-bit)  
**Target Users**: Clinic Administrators, IT Specialists, Dentists, Receptionists  

---

## 1. System Requirements

| Specification | Minimum Requirement | Recommended Specification |
| :--- | :--- | :--- |
| **Operating System** | Windows 10 (64-bit, Version 21H2+) | Windows 11 Professional (64-bit) |
| **Processor (CPU)** | Intel Core i3 / AMD Ryzen 3 (Dual-Core) | Intel Core i5 / AMD Ryzen 5 (Quad-Core or better) |
| **Memory (RAM)** | 8 GB RAM | 16 GB RAM |
| **Storage (Disk)** | 10 GB available SSD space | 50 GB NVMe SSD space (for radiographs and backups) |
| **Display Resolution**| 1366 x 768 pixels | 1920 x 1080 (Full HD) or higher |
| **Database Engine** | PostgreSQL 15 or 16 (Local or Network) | PostgreSQL 16 64-bit with automated WAL backups |

---

## 2. Step-by-Step Installation Procedure

### Step 2.1: Run the Installer
1. Download `DentalCarePro-Setup-1.0.0.exe`.
2. Right-click the installer and select **Run as administrator** (or run as standard user; the installer automatically adapts to standard user privileges).
3. The modern Inno Setup wizard displays the welcome screen with the DentalCare Pro clinical badge.

### Step 2.2: Accept the Commercial License
Review the enterprise healthcare license agreement terms and click **I accept the agreement** $\rightarrow$ **Next**.

### Step 2.3: Select Destination Folder
- Default path: `C:\Program Files\DentalCare Pro` (for machine-wide installs) or `%LOCALAPPDATA%\Programs\DentalCare Pro` (for single-user installs).
- Click **Next**.

### Step 2.4: Select Additional Tasks
- [x] **Create a desktop shortcut** (Recommended)
- [x] **Automatically launch DentalCare Pro on Windows startup** (Optional for dedicated reception computers)

### Step 2.5: Database Verification
The installer automatically inspects your Windows registry and background services:
- **If PostgreSQL 16 is detected**: The installer links to the local service automatically.
- **If PostgreSQL is not detected**: A guidance prompt appears offering instructions to install local PostgreSQL 16 or configure a central clinic network server.

### Step 2.6: Complete Installation & Launch
Click **Install**. Once files are copied, the installer automatically runs initial database migration checks and presents the final completion screen with a checkbox to **Launch DentalCare Pro**.

---

## 3. First-Launch Configuration Wizard

When DentalCare Pro starts for the first time, it displays the **Practice Setup Wizard**:

1. **Clinic Profile**:
   - Enter your **Clinic Name** (e.g., *Apex Family Dental Care*).
   - Enter your **Branch Code** (e.g., *MAIN-01*).
2. **Super Administrator Account**:
   - Enter your **Full Name** (e.g., *Dr. Sarah Jenkins*).
   - Enter your **Admin Login Email** (e.g., *admin@apex-dental.com*).
   - Enter a secure **Master Password** (minimum 8 characters, salted with Bcrypt).
3. **Database & Network Settings**:
   - **Local Workstation**: Leave default `postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/dentalcare`.
   - **Multi-Operatory Network**: Enter your clinic server's IP address: `postgresql+asyncpg://postgres:password@192.168.1.50:5432/dentalcare`.
   - Click **Test Connection** to verify database connectivity.
4. **Local Preferences**:
   - Select your **Timezone** and **Backup Storage Location** (default `C:\DentalCarePro_Backups`).
5. Click **Complete Setup & Launch**. The wizard initializes your database schema, seeds the clinic owner account, and opens the main login portal!

---

## 4. Upgrading Without Data Loss

When upgrading to newer releases (e.g. v1.0.1, v1.1.0):
1. Close any running instances of DentalCare Pro.
2. Run the new `DentalCarePro-Setup-X.X.X.exe`.
3. The installer detects the existing installation, updates the application binaries, runs Alembic migrations automatically, and preserves all clinic patient data, radiographs, and settings located in `%LOCALAPPDATA%\DentalCarePro`.

---

## 5. Safe Uninstallation & Data Preservation

If you ever need to uninstall DentalCare Pro:
1. Open **Windows Settings** $\rightarrow$ **Apps** $\rightarrow$ **Installed apps** (or Control Panel $\rightarrow$ Programs and Features).
2. Select **DentalCare Pro** and click **Uninstall**.
3. **HIPAA Data Preservation Safeguard**: During uninstallation, you will be prompted:
   > *"Do you want to retain your clinic patient data and backups at C:\Users\...\AppData\Local\DentalCarePro?"*
   - Click **YES** to preserve your clinical records and historical patient files.
   - Click **NO** only if permanently decommissioning the workstation.
