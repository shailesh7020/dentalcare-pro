# installer/uninstaller_gui.py
"""
DentalCare Pro - Standalone Windows GUI Uninstaller
Removes DentalCare Pro from the workstation while offering HIPAA Data Retention Safeguards.
"""
import os
import sys
import shutil
import winreg
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox

INSTALL_DIR = Path(__file__).resolve().parent
LOCAL_APPDATA = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "DentalCarePro"

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

def main():
    root = tk.Tk()
    root.title("DentalCare Pro - Uninstall")
    root.geometry("520x340")
    root.resizable(False, False)
    root.configure(bg="#f8fafc")

    header = tk.Frame(root, bg="#7f1d1d", height=70, padx=20, pady=15)
    header.pack(fill="x")
    tk.Label(header, text="Uninstall DentalCare Pro Enterprise", font=("Segoe UI", 13, "bold"), fg="#ffffff", bg="#7f1d1d").pack(anchor="w")

    content = tk.Frame(root, bg="#ffffff", padx=25, pady=20)
    content.pack(fill="both", expand=True)

    tk.Label(content, text="Are you sure you want to completely remove DentalCare Pro?", font=("Segoe UI", 10, "bold"), bg="#ffffff", fg="#1e293b").pack(anchor="w", pady=(0, 10))

    preserve_data_var = tk.BooleanVar(value=True)

    hipaa_frame = tk.Frame(content, bg="#eff6ff", padx=12, pady=10, relief="solid", bd=1)
    hipaa_frame.pack(fill="x", pady=(0, 15))

    tk.Label(hipaa_frame, text="HIPAA Patient Data Retention Safeguard:", font=("Segoe UI", 9, "bold"), fg="#1e40af", bg="#eff6ff").pack(anchor="w")
    tk.Label(hipaa_frame, text="Preserve clinical databases, treatment plans, and backups so patient history is not lost.", font=("Segoe UI", 8), fg="#3b82f6", bg="#eff6ff").pack(anchor="w", pady=(2, 6))

    ttk.Checkbutton(hipaa_frame, text="Retain patient database and backups (Recommended)", variable=preserve_data_var).pack(anchor="w")

    btn_bar = tk.Frame(root, bg="#f1f5f9", height=50, padx=20, pady=10)
    btn_bar.pack(side="bottom", fill="x")

    def do_uninstall():
        try:
            remove_shortcuts()
            remove_registry_key()

            if not preserve_data_var.get():
                if LOCAL_APPDATA.exists():
                    shutil.rmtree(LOCAL_APPDATA, ignore_errors=True)

            messagebox.showinfo("Uninstall Complete", "DentalCare Pro Enterprise was successfully removed.")
            root.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed during uninstall: {e}")

    ttk.Button(btn_bar, text="Cancel", command=root.destroy).pack(side="right", padx=5)
    ttk.Button(btn_bar, text="Uninstall", command=do_uninstall).pack(side="right", padx=5)

    root.mainloop()

if __name__ == "__main__":
    main()
