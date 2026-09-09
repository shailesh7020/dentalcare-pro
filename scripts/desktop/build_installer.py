# scripts/desktop/build_installer.py
"""
Master Desktop & Installer Packaging Script for DentalCare Pro.
Assembles backend, desktop shell, tutorial documentation, portable ZIP,
and invokes Inno Setup compiler if present.
"""
import os
import sys
import shutil
import hashlib
import subprocess
from pathlib import Path

ROOT_DIR = Path(r"e:\dentalcare-pro").resolve()
DIST_DIR = ROOT_DIR / "dist"
INSTALLER_DIR = DIST_DIR / "installer"
PORTABLE_DIR = DIST_DIR / "DentalCarePro_v1.0.0_Portable"

def calculate_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def build_portable_distribution():
    print("\n--- Assembling Portable Distribution ---")
    if PORTABLE_DIR.exists():
        shutil.rmtree(PORTABLE_DIR)
    PORTABLE_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Copy main launcher
    launcher_exe = DIST_DIR / "DentalCarePro.exe"
    if launcher_exe.exists():
        shutil.copy(launcher_exe, PORTABLE_DIR / "DentalCarePro.exe")
    
    # 2. Copy backend
    backend_dest = PORTABLE_DIR / "backend"
    backend_dest.mkdir(parents=True, exist_ok=True)
    backend_exe = DIST_DIR / "backend" / "DentalCarePro-API.exe"
    if backend_exe.exists():
        shutil.copy(backend_exe, backend_dest / "DentalCarePro-API.exe")

    # 3. Copy documentation & assets
    shutil.copy(ROOT_DIR / "Project-tutorial.pdf", PORTABLE_DIR / "Project-tutorial.pdf")
    shutil.copy(ROOT_DIR / "LICENSE", PORTABLE_DIR / "LICENSE")
    shutil.copy(ROOT_DIR / "README.md", PORTABLE_DIR / "README.md")
    
    # Copy branding assets
    shutil.copytree(ROOT_DIR / "assets" / "branding", PORTABLE_DIR / "assets" / "branding", dirs_exist_ok=True)

    # 4. Create ZIP archive
    zip_output = DIST_DIR / "DentalCarePro-v1.0.0-Portable"
    shutil.make_archive(str(zip_output), "zip", PORTABLE_DIR)
    zip_file = DIST_DIR / "DentalCarePro-v1.0.0-Portable.zip"
    print(f"Created Portable Archive: {zip_file} ({zip_file.stat().st_size / (1024*1024):.2f} MB)")

def compile_inno_setup():
    print("\n--- Compiling Inno Setup Installer ---")
    iss_file = ROOT_DIR / "installer" / "DentalCarePro_Setup.iss"
    INSTALLER_DIR.mkdir(parents=True, exist_ok=True)

    # Search for iscc.exe in standard paths
    possible_paths = [
        Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"),
        Path(r"C:\Program Files\Inno Setup 6\ISCC.exe"),
        Path(r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe"),
    ]
    iscc_bin = shutil.which("iscc")
    if not iscc_bin:
        for p in possible_paths:
            if p.exists():
                iscc_bin = str(p)
                break

    if iscc_bin:
        print(f"Using Inno Setup Compiler: {iscc_bin}")
        cmd = [iscc_bin, str(iss_file)]
        res = subprocess.run(cmd)
        if res.returncode == 0:
            print("Successfully compiled Inno Setup Installer!")
        else:
            print(f"Inno Setup compilation returned code {res.returncode}")
    else:
        print("Inno Setup Compiler (ISCC.exe) not found in system PATH or Program Files.")
        print(f"The installer script is fully configured and saved at: {iss_file}")
        print("To compile the installer on any Windows machine with Inno Setup, run:")
        print(f"  ISCC.exe {iss_file}")

def generate_checksums():
    print("\n--- Generating SHA256 Checksums ---")
    checksum_file = DIST_DIR / "checksums.sha256"
    lines = []
    for f in DIST_DIR.glob("*.*"):
        if f.is_file() and f.name != "checksums.sha256":
            h = calculate_sha256(f)
            lines.append(f"{h}  {f.name}\n")
            print(f"  {f.name}: {h}")
    checksum_file.write_text("".join(lines), encoding="utf-8")
    print(f"Wrote checksums to: {checksum_file}")

def main():
    print("==================================================")
    print("  DentalCare Pro Master Desktop Installer Packager")
    print("==================================================")
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    build_portable_distribution()
    compile_inno_setup()
    generate_checksums()
    print("\nMaster Packaging Pipeline Completed Successfully!")

if __name__ == "__main__":
    main()
