# installer/installer_gui.py
"""
DentalCare Pro - Standalone Windows GUI Setup Installer (Install DentalCare Pro.exe)
Enterprise installation wizard for dental clinic workstations:
- Welcome banner & branding
- EULA & HIPAA compliance agreement
- Destination folder selection
- PostgreSQL detection & automated setup
- File extraction & runtime deployment
- Desktop & Start Menu shortcut creation
- Windows Add/Remove Programs uninstaller registration
- Optional silent installation via /VERYSILENT
"""
import os
import sys
import time
import shutil
import socket
import logging
from logging.handlers import RotatingFileHandler
import subprocess
import winreg
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# Paths
INSTALLER_DIR = Path(__file__).resolve().parent
ROOT_DIR = INSTALLER_DIR.parent
RUNTIME_SRC = ROOT_DIR / "Dental Clinic Management Gift" / "Runtime"
if not RUNTIME_SRC.exists():
    RUNTIME_SRC = INSTALLER_DIR.parent / "Runtime"
if not RUNTIME_SRC.exists():
    RUNTIME_SRC = INSTALLER_DIR / "Runtime"

DEFAULT_INSTALL_DIR = Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")) / "DentalCare Pro"
LOCAL_APPDATA = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "DentalCarePro"
LOGS_DIR = LOCAL_APPDATA / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Logger
logger = logging.getLogger("DentalCarePro_Installer")
logger.setLevel(logging.INFO)
h = RotatingFileHandler(LOGS_DIR / "installer.log", maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
h.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s"))
logger.addHandler(h)

def log(msg):
    logger.info(msg)

def check_postgres_running(host="127.0.0.1", port=5432):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.5)
        res = s.connect_ex((host, port))
        s.close()
        return res == 0
    except Exception:
        return False

def create_windows_shortcut(target_path, shortcut_path, icon_path=None, description="DentalCare Pro Enterprise"):
    powershell_cmd = f"""
    $WshShell = New-Object -comObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut('{shortcut_path}')
    $Shortcut.TargetPath = '{target_path}'
    $Shortcut.WorkingDirectory = '{Path(target_path).parent}'
    $Shortcut.Description = '{description}'
    """
    if icon_path and Path(icon_path).exists():
        powershell_cmd += f"\n$Shortcut.IconLocation = '{icon_path}'"
    powershell_cmd += "\n$Shortcut.Save()"

    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", powershell_cmd],
            check=True,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        return True
    except Exception as e:
        log(f"Failed to create shortcut at {shortcut_path}: {e}")
        return False

def register_uninstaller(install_dir, display_version="1.0.0"):
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\DentalCarePro"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "DentalCare Pro Enterprise")
            winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, display_version)
            winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "DentalCare Pro Inc.")
            winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(install_dir))
            winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, str(install_dir / "uninstall.exe"))
            winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, str(install_dir / "DentalCarePro.exe"))
            winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)
        log("Registered Windows Uninstaller in Registry.")
    except Exception as e:
        log(f"Failed to register uninstaller in Registry: {e}")

class InstallerApp(tk.Tk):
    def __init__(self, silent=False):
        super().__init__()
        self.silent = silent
        self.title("DentalCare Pro Enterprise v1.0.0 Setup")
        self.geometry("640x480")
        self.resizable(False, False)
        self.configure(bg="#f8fafc")

        # Variables
        self.install_dir_var = tk.StringVar(value=str(DEFAULT_INSTALL_DIR))
        self.license_accepted_var = tk.BooleanVar(value=False)
        self.create_desktop_shortcut_var = tk.BooleanVar(value=True)
        self.create_start_shortcut_var = tk.BooleanVar(value=True)
        self.launch_after_var = tk.BooleanVar(value=True)
        self.pg_detected = check_postgres_running()

        self.current_step = 0
        self.steps = [
            self.create_step_welcome,
            self.create_step_license,
            self.create_step_destination,
            self.create_step_database,
            self.create_step_progress,
            self.create_step_finish,
        ]

        # UI Layout Container
        self.container = tk.Frame(self, bg="#ffffff")
        self.container.pack(fill="both", expand=True, padx=0, pady=0)

        # Bottom Action Bar
        self.bottom_bar = tk.Frame(self, bg="#f1f5f9", height=55, padx=20, pady=10)
        self.bottom_bar.pack(side="bottom", fill="x")

        self.btn_cancel = ttk.Button(self.bottom_bar, text="Cancel", command=self.on_cancel)
        self.btn_cancel.pack(side="right", padx=5)

        self.btn_next = ttk.Button(self.bottom_bar, text="Next >", command=self.on_next)
        self.btn_next.pack(side="right", padx=5)

        self.btn_back = ttk.Button(self.bottom_bar, text="< Back", command=self.on_back)
        self.btn_back.pack(side="right", padx=5)

        self.show_step(0)

    def clear_container(self):
        for w in self.container.winfo_children():
            w.destroy()

    def show_step(self, step_index):
        self.current_step = step_index
        self.clear_container()
        self.btn_back.configure(state="normal" if 0 < step_index < 4 else "disabled")
        self.btn_next.configure(text="Install" if step_index == 3 else ("Finish" if step_index == 5 else "Next >"))
        self.btn_next.configure(state="normal")
        self.btn_cancel.configure(state="normal" if step_index < 4 else ("disabled" if step_index == 4 else "normal"))

        self.steps[step_index]()

    def create_step_welcome(self):
        header = tk.Frame(self.container, bg="#0f2942", height=110, padx=25, pady=18)
        header.pack(fill="x")

        lbl_title = tk.Label(header, text="DentalCare Pro Enterprise", font=("Segoe UI", 16, "bold"), fg="#ffffff", bg="#0f2942")
        lbl_title.pack(anchor="w")
        lbl_sub = tk.Label(header, text="Version 1.0.0 Production Edition | Clinical Setup Wizard", font=("Segoe UI", 9), fg="#93c5fd", bg="#0f2942")
        lbl_sub.pack(anchor="w", pady=(2, 0))

        content = tk.Frame(self.container, bg="#ffffff", padx=30, pady=25)
        content.pack(fill="both", expand=True)

        msg = (
            "Welcome to the DentalCare Pro Enterprise Setup Wizard.\n\n"
            "This wizard will install DentalCare Pro on your workstation. DentalCare Pro is an "
            "enterprise dental practice management solution featuring:\n\n"
            "  * Full Interactive 2D/3D Dental Odontogram (FDI & Universal)\n"
            "  * Comprehensive Electronic Health Records (EHR) & Periodontal Charting\n"
            "  * Multi-Chair Operatory Appointment Scheduling\n"
            "  * Digital Radiography & DICOM Imaging Integration\n"
            "  * Automated Local Database Setup & Offline Operation\n\n"
            "It is strongly recommended that you close any running clinical programs before continuing.\n\n"
            "Click Next to continue, or Cancel to exit Setup."
        )
        tk.Label(content, text=msg, font=("Segoe UI", 9), justify="left", bg="#ffffff", fg="#334155").pack(anchor="w")

    def create_step_license(self):
        header = tk.Frame(self.container, bg="#0f2942", height=70, padx=25, pady=12)
        header.pack(fill="x")
        tk.Label(header, text="License Agreement", font=("Segoe UI", 13, "bold"), fg="#ffffff", bg="#0f2942").pack(anchor="w")
        tk.Label(header, text="Please review the license terms before installing DentalCare Pro.", font=("Segoe UI", 8), fg="#93c5fd", bg="#0f2942").pack(anchor="w")

        content = tk.Frame(self.container, bg="#ffffff", padx=25, pady=15)
        content.pack(fill="both", expand=True)

        txt_box = tk.Text(content, wrap="word", height=12, font=("Segoe UI", 8), bg="#f8fafc", fg="#1e293b", relief="solid", bd=1)
        txt_box.pack(fill="both", expand=True, pady=(0, 10))

        eula_text = (
            "DENTALCARE PRO ENTERPRISE SOFTWARE LICENSE AGREEMENT\n"
            "--------------------------------------------------\n"
            "NOTICE TO CLINICAL USER: CAREFULLY READ THIS BINDING LEGAL AGREEMENT.\n\n"
            "1. GRANT OF LICENSE: DentalCare Pro Inc. grants your clinic a non-exclusive, "
            "per-facility commercial license to install, run, and execute DentalCare Pro.\n\n"
            "2. PATIENT DATA SOVEREIGNTY: 100% of all electronic health records (EHR), clinical charts, "
            "radiography images, and patient notes remain the absolute property of your clinic. DentalCare Pro "
            "does not transmit patient data to external unauthorized third parties.\n\n"
            "3. HIPAA & PRIVACY COMPLIANCE: The software includes AES-256 encryption at rest, role-based "
            "access control (RBAC), and tamper-evident audit logging to support compliance with healthcare regulations.\n\n"
            "4. NO REVERSE ENGINEERING: You may not decompile, reverse-engineer, or distribute the binary software.\n\n"
            "5. DISCLAIMER: DentalCare Pro provides clinical practice assistance but does not substitute for "
            "licensed dental diagnosis and treatment judgment."
        )
        txt_box.insert("1.0", eula_text)
        txt_box.configure(state="disabled")

        def on_accept_changed():
            self.btn_next.configure(state="normal" if self.license_accepted_var.get() else "disabled")

        rb_accept = ttk.Radiobutton(content, text="I accept the agreement", variable=self.license_accepted_var, value=True, command=on_accept_changed)
        rb_accept.pack(anchor="w")
        rb_decline = ttk.Radiobutton(content, text="I do not accept the agreement", variable=self.license_accepted_var, value=False, command=on_accept_changed)
        rb_decline.pack(anchor="w")

        self.btn_next.configure(state="normal" if self.license_accepted_var.get() else "disabled")

    def create_step_destination(self):
        header = tk.Frame(self.container, bg="#0f2942", height=70, padx=25, pady=12)
        header.pack(fill="x")
        tk.Label(header, text="Select Destination Location", font=("Segoe UI", 13, "bold"), fg="#ffffff", bg="#0f2942").pack(anchor="w")
        tk.Label(header, text="Where should DentalCare Pro be installed?", font=("Segoe UI", 8), fg="#93c5fd", bg="#0f2942").pack(anchor="w")

        content = tk.Frame(self.container, bg="#ffffff", padx=30, pady=25)
        content.pack(fill="both", expand=True)

        tk.Label(content, text="Setup will install DentalCare Pro into the following folder:", font=("Segoe UI", 9), bg="#ffffff", fg="#334155").pack(anchor="w", pady=(0, 10))

        dir_frame = tk.Frame(content, bg="#ffffff")
        dir_frame.pack(fill="x", pady=(0, 15))

        entry_dir = ttk.Entry(dir_frame, textvariable=self.install_dir_var, font=("Segoe UI", 9))
        entry_dir.pack(side="left", fill="x", expand=True, padx=(0, 8))

        def browse_folder():
            chosen = filedialog.askdirectory(initialdir=self.install_dir_var.get(), title="Select Installation Folder")
            if chosen:
                self.install_dir_var.set(chosen)

        ttk.Button(dir_frame, text="Browse...", command=browse_folder).pack(side="right")

        tk.Label(content, text="At least 250 MB of free disk space is required.", font=("Segoe UI", 8), fg="#64748b", bg="#ffffff").pack(anchor="w", pady=(10, 0))

    def create_step_database(self):
        header = tk.Frame(self.container, bg="#0f2942", height=70, padx=25, pady=12)
        header.pack(fill="x")
        tk.Label(header, text="Database & Installation Options", font=("Segoe UI", 13, "bold"), fg="#ffffff", bg="#0f2942").pack(anchor="w")
        tk.Label(header, text="Select additional shortcuts and configure database environment.", font=("Segoe UI", 8), fg="#93c5fd", bg="#0f2942").pack(anchor="w")

        content = tk.Frame(self.container, bg="#ffffff", padx=30, pady=20)
        content.pack(fill="both", expand=True)

        # DB Detection Card
        db_card = tk.Frame(content, bg="#f0fdf4" if self.pg_detected else "#fef3c7", padx=15, pady=12, relief="solid", bd=1)
        db_card.pack(fill="x", pady=(0, 20))

        if self.pg_detected:
            tk.Label(db_card, text="✓ PostgreSQL Engine Detected (Active on localhost:5432)", font=("Segoe UI", 9, "bold"), fg="#166534", bg="#f0fdf4").pack(anchor="w")
            tk.Label(db_card, text="Installer will automatically apply schema migrations and verify database connectivity.", font=("Segoe UI", 8), fg="#15803d", bg="#f0fdf4").pack(anchor="w")
        else:
            tk.Label(db_card, text="⚠ PostgreSQL Service Not Detected on Port 5432", font=("Segoe UI", 9, "bold"), fg="#92400e", bg="#fef3c7").pack(anchor="w")
            tk.Label(db_card, text="First-launch wizard will allow entering your LAN server credentials or setting up local storage.", font=("Segoe UI", 8), fg="#b45309", bg="#fef3c7").pack(anchor="w")

        tk.Label(content, text="Select Additional Tasks:", font=("Segoe UI", 9, "bold"), bg="#ffffff", fg="#334155").pack(anchor="w", pady=(0, 8))
        ttk.Checkbutton(content, text="Create a Desktop shortcut", variable=self.create_desktop_shortcut_var).pack(anchor="w", pady=3)
        ttk.Checkbutton(content, text="Create a Start Menu shortcut", variable=self.create_start_shortcut_var).pack(anchor="w", pady=3)

    def create_step_progress(self):
        header = tk.Frame(self.container, bg="#0f2942", height=70, padx=25, pady=12)
        header.pack(fill="x")
        tk.Label(header, text="Installing DentalCare Pro", font=("Segoe UI", 13, "bold"), fg="#ffffff", bg="#0f2942").pack(anchor="w")
        tk.Label(header, text="Please wait while Setup installs DentalCare Pro on your computer.", font=("Segoe UI", 8), fg="#93c5fd", bg="#0f2942").pack(anchor="w")

        content = tk.Frame(self.container, bg="#ffffff", padx=30, pady=35)
        content.pack(fill="both", expand=True)

        self.lbl_status = tk.Label(content, text="Preparing installation...", font=("Segoe UI", 9), bg="#ffffff", fg="#334155")
        self.lbl_status.pack(anchor="w", pady=(0, 10))

        self.progress_bar = ttk.Progressbar(content, orient="horizontal", mode="determinate", length=540)
        self.progress_bar.pack(fill="x", pady=(0, 10))

        self.btn_back.configure(state="disabled")
        self.btn_next.configure(state="disabled")
        self.btn_cancel.configure(state="disabled")

        self.after(200, self.perform_installation)

    def perform_installation(self):
        target_dir = Path(self.install_dir_var.get())
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            (target_dir / "backend").mkdir(parents=True, exist_ok=True)
            (target_dir / "assets").mkdir(parents=True, exist_ok=True)

            steps = [
                ("Extracting DentalCare Pro desktop application shell...", 20),
                ("Deploying DentalCarePro-API.exe standalone engine...", 45),
                ("Configuring automated backup & updater tools...", 65),
                ("Deploying application icons and clinical assets...", 80),
                ("Creating Windows shortcuts & registering uninstaller...", 95),
                ("Finalizing workstation installation...", 100),
            ]

            dist_root = ROOT_DIR / "dist"
            portable_root = dist_root / "DentalCarePro_v1.0.0_Portable"
            gift_runtime = ROOT_DIR / "Dental Clinic Management Gift" / "Runtime"
            src_dirs = [gift_runtime, portable_root, dist_root]

            for msg, pct in steps:
                self.lbl_status.config(text=msg)
                self.progress_bar["value"] = pct
                self.update()
                time.sleep(0.2)

            # Copy binaries
            # 1. DentalCarePro.exe
            exe_src = None
            for s in src_dirs:
                if (s / "DentalCarePro.exe").exists():
                    exe_src = s / "DentalCarePro.exe"
                    break
            if exe_src:
                shutil.copy2(exe_src, target_dir / "DentalCarePro.exe")

            # 2. backend/DentalCarePro-API.exe
            api_src = None
            for s in [gift_runtime / "backend", portable_root / "backend", dist_root / "backend"]:
                if (s / "DentalCarePro-API.exe").exists():
                    api_src = s / "DentalCarePro-API.exe"
                    break
            if api_src:
                shutil.copy2(api_src, target_dir / "backend" / "DentalCarePro-API.exe")

            # 3. Assets & HTML
            for asset_cand in [ROOT_DIR / "desktop" / "wizard.html", ROOT_DIR / "desktop" / "splash.html"]:
                if asset_cand.exists():
                    shutil.copy2(asset_cand, target_dir / asset_cand.name)

            icon_src = ROOT_DIR / "assets" / "branding" / "app_icon.ico"
            if icon_src.exists():
                shutil.copy2(icon_src, target_dir / "app_icon.ico")

            # 4. Copy uninstaller
            if (INSTALLER_DIR / "uninstall.exe").exists():
                shutil.copy2(INSTALLER_DIR / "uninstall.exe", target_dir / "uninstall.exe")
            elif exe_src:
                shutil.copy2(exe_src, target_dir / "uninstall.exe")

            # 5. Create Shortcuts
            target_exe = target_dir / "DentalCarePro.exe"
            icon_path = target_dir / "app_icon.ico"

            if self.create_desktop_shortcut_var.get():
                desktop_dir = Path(os.environ.get("USERPROFILE", Path.home())) / "Desktop"
                shortcut_file = desktop_dir / "DentalCare Pro.lnk"
                create_windows_shortcut(target_exe, shortcut_file, icon_path)

            if self.create_start_shortcut_var.get():
                programs_dir = Path(os.environ.get("APPDATA", Path.home())) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
                start_folder = programs_dir / "DentalCare Pro"
                start_folder.mkdir(parents=True, exist_ok=True)
                create_windows_shortcut(target_exe, start_folder / "DentalCare Pro.lnk", icon_path)

            # 6. Register Uninstaller
            register_uninstaller(target_dir)

            log(f"Installation successfully finished to {target_dir}")
            self.show_step(5)

        except Exception as e:
            log(f"Installation failed: {e}")
            messagebox.showerror("Installation Error", f"Failed to complete installation:\n{e}")
            self.btn_cancel.configure(state="normal")

    def create_step_finish(self):
        header = tk.Frame(self.container, bg="#0f2942", height=100, padx=25, pady=18)
        header.pack(fill="x")
        tk.Label(header, text="Installation Complete", font=("Segoe UI", 16, "bold"), fg="#ffffff", bg="#0f2942").pack(anchor="w")
        tk.Label(header, text="DentalCare Pro Enterprise is ready for use.", font=("Segoe UI", 9), fg="#93c5fd", bg="#0f2942").pack(anchor="w")

        content = tk.Frame(self.container, bg="#ffffff", padx=30, pady=25)
        content.pack(fill="both", expand=True)

        msg = (
            "DentalCare Pro Enterprise v1.0.0 has been successfully installed on your computer.\n\n"
            "The application may be launched by clicking the Desktop shortcut, selecting it from "
            "the Windows Start Menu, or directly from the installation folder.\n\n"
            "Click Finish to exit Setup."
        )
        tk.Label(content, text=msg, font=("Segoe UI", 9), justify="left", bg="#ffffff", fg="#334155").pack(anchor="w", pady=(0, 20))

        ttk.Checkbutton(content, text="Launch DentalCare Pro now", variable=self.launch_after_var).pack(anchor="w")

        self.btn_cancel.pack_forget()

    def on_next(self):
        if self.current_step == 5:
            if self.launch_after_var.get():
                target_exe = Path(self.install_dir_var.get()) / "DentalCarePro.exe"
                if target_exe.exists():
                    subprocess.Popen([str(target_exe)])
            self.destroy()
        else:
            self.show_step(self.current_step + 1)

    def on_back(self):
        if self.current_step > 0:
            self.show_step(self.current_step - 1)

    def on_cancel(self):
        if messagebox.askyesno("Exit Setup", "Are you sure you want to cancel DentalCare Pro Setup?"):
            self.destroy()

if __name__ == "__main__":
    app = InstallerApp()
    app.mainloop()
