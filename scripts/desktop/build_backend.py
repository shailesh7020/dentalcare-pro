# scripts/desktop/build_backend.py
import os
import subprocess
import sys
from pathlib import Path

def build_backend():
    root_dir = Path(r"e:\dentalcare-pro").resolve()
    backend_dir = root_dir / "backend"
    spec_file = backend_dir / "dentalcare_api.spec"
    dist_dir = root_dir / "dist" / "backend"
    build_dir = root_dir / "build" / "backend"

    dist_dir.mkdir(parents=True, exist_ok=True)
    build_dir.mkdir(parents=True, exist_ok=True)

    print("==================================================")
    print("  Building DentalCare Pro Standalone API Executable")
    print("==================================================")
    print(f"Spec file: {spec_file}")
    print(f"Dist dir:  {dist_dir}")

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        f"--distpath={dist_dir}",
        f"--workpath={build_dir}",
        str(spec_file),
    ]

    print("Running command:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=str(backend_dir))
    if result.returncode != 0:
        print(f"ERROR: PyInstaller failed with exit code {result.returncode}")
        sys.exit(result.returncode)

    exe_path = dist_dir / "DentalCarePro-API.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print("--------------------------------------------------")
        print(f"SUCCESS: Built {exe_path} ({size_mb:.2f} MB)")
        print("--------------------------------------------------")
    else:
        print(f"ERROR: Expected binary not found at {exe_path}")
        sys.exit(1)

if __name__ == "__main__":
    build_backend()
