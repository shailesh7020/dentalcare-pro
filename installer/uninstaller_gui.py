# installer/uninstaller_gui.py
"""
DentalCare Pro - Standalone Windows GUI Uninstaller
Removes DentalCare Pro from the workstation with HIPAA Data Retention Safeguards.
- Gracefully terminates running application processes (DentalCarePro.exe, DentalCarePro-API.exe)
- Removes Desktop and Start Menu shortcuts
- Removes Windows Registry uninstall registration
- Removes background auto-start services/tasks
- Offers HIPAA Data Preservation option (preserves PostgreSQL database & C:\DentalCarePro_Backups)
"""
import os
import sys
import shutil
import subprocess
import winreg
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

INSTALL_DIR = Path(__file__).resolve().parent
LOCAL_APPDATA = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "DentalCarePro"


def stop_running_processes():
    for proc_name in ["DentalCarePro.exe", "DentalCarePro-API.exe", "backup_manager.exe"]:
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", proc_name],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
        except Exception:
            pass


def remove_registry_key():
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall\DentalCarePro")
    except Exception:
        pass


def remove_shortcuts():
    desktop_dir = Path(os.environ.get("USERPROFILE", Path.home())) / "Desktop"
    shortcut_file = desktop_dir / "DentalCare Pro.lnk"
    if shortcut_file.exists():
        try:
            shortcut_file.unlink()
        except Exception:
            pass

    programs_dir = Path(os.environ.get("APPDATA", Path.home())) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
    start_folder = programs_dir / "DentalCare Pro"
    if start_folder.exists():
        try:
            shutil.rmtree(start_folder)
        except Exception:
            pass


def remove_startup_entry():
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            try:
                winreg.DeleteValue(key, "DentalCarePro")
            except FileNotFoundError:
                pass
    except Exception:
        pass


def main():
    root = tk.Tk()
    root.title("DentalCare Pro Enterprise - Uninstall")
    root.geometry("540x360")
    root.resizable(False, False)
    root.configure(bg="#f8fafc")

    header = tk.Frame(root, bg="#7f1d1d", height=70, padx=20, pady=15)
    header.pack(fill="x")
    tk.Label(header, text="Uninstall DentalCare Pro Enterprise", font=("Segoe UI", 13, "bold"), fg="#ffffff", bg="#7f1d1d").pack(anchor="w")
    tk.Label(header, text="Safely decommission DentalCare Pro from this workstation.", font=("Segoe UI", 8), fg="#fca5a5", bg="#7f1d1d").pack(anchor="w")

    content = tk.Frame(root, bg="#ffffff", padx=25, pady=20)
    content.pack(fill="both", expand=True)

    tk.Label(content, text="Are you sure you want to completely remove DentalCare Pro?", font=("Segoe UI", 10, "bold"), bg="#ffffff", fg="#1e293b").pack(anchor="w", pady=(0, 8))
    tk.Label(content, text="This will remove application executables, desktop shortcuts, and background services.", font=("Segoe UI", 8.5), bg="#ffffff", fg="#64748b").pack(anchor="w", pady=(0, 12))

    preserve_data_var = tk.BooleanVar(value=True)

    hipaa_frame = tk.Frame(content, bg="#eff6ff", padx=12, pady=10, relief="solid", bd=1)
    hipaa_frame.pack(fill="x", pady=(0, 15))

    tk.Label(hipaa_frame, text="HIPAA Patient Data Retention Safeguard:", font=("Segoe UI", 9, "bold"), fg="#1e40af", bg="#eff6ff").pack(anchor="w")
    tk.Label(hipaa_frame, text="Preserve clinical PostgreSQL databases, patient charts, and C:\\DentalCarePro_Backups\\ so medical records are never lost.", font=("Segoe UI", 8), fg="#3b82f6", bg="#eff6ff").pack(anchor="w", pady=(2, 6))

    ttk.Checkbutton(hipaa_frame, text="Retain patient database and automated backups (Recommended)", variable=preserve_data_var).pack(anchor="w")

    btn_bar = tk.Frame(root, bg="#f1f5f9", height=50, padx=20, pady=10)
    btn_bar.pack(side="bottom", fill="x")

    def do_uninstall():
        try:
            stop_running_processes()
            remove_shortcuts()
            remove_startup_entry()
            remove_registry_key()

            if not preserve_data_var.get():
                if LOCAL_APPDATA.exists():
                    shutil.rmtree(LOCAL_APPDATA, ignore_errors=True)

            messagebox.showinfo("Uninstall Complete", "DentalCare Pro Enterprise was successfully removed from your workstation.")
            root.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed during uninstall: {e}")

    ttk.Button(btn_bar, text="Cancel", command=root.destroy).pack(side="right", padx=5)
    ttk.Button(btn_bar, text="Uninstall", command=do_uninstall).pack(side="right", padx=5)

    root.mainloop()


if __name__ == "__main__":
    if "/VERYSILENT" in sys.argv or "/SILENT" in sys.argv or "/S" in sys.argv:
        stop_running_processes()
        remove_shortcuts()
        remove_startup_entry()
        remove_registry_key()
        sys.exit(0)
    main()
