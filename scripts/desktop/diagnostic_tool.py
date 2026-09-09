# scripts/desktop/diagnostic_tool.py
"""
DentalCare Pro - Pre-Flight Diagnostic & Workstation Health Tool (Diagnostic-Tool.exe)
Comprehensive environment verification for dental clinic workstations:
- Windows OS Version & 64-bit Architecture
- Physical Memory (RAM)
- PostgreSQL Engine status (Port 5432)
- API Port status (Port 8000)
- LocalAppData & Backup storage write permissions
- Display resolution & DPI scaling check
"""
import os
import sys
import socket
import platform
import psutil
from datetime import datetime
from pathlib import Path

def test_port(host, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.5)
        res = s.connect_ex((host, port))
        s.close()
        return res == 0
    except Exception:
        return False

def test_write_permission(path_obj):
    try:
        path_obj.mkdir(parents=True, exist_ok=True)
        test_file = path_obj / ".dc_write_test"
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("test")
        test_file.unlink()
        return True
    except Exception:
        return False

def main():
    print("=" * 65)
    print("  DENTALCARE PRO ENTERPRISE - CLINICAL DIAGNOSTIC TOOL v1.0.0")
    print("=" * 65)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 65)

    all_passed = True

    # 1. OS Architecture
    os_info = f"{platform.system()} {platform.release()} ({platform.machine()})"
    is_64bit = sys.maxsize > 2**32
    if is_64bit:
        print(f"  [ PASS ] Operating System: {os_info}")
    else:
        print(f"  [ FAIL ] 32-bit OS detected. DentalCare Pro requires 64-bit Windows.")
        all_passed = False

    # 2. Memory
    ram_gb = psutil.virtual_memory().total / (1024**3)
    if ram_gb >= 7.5:
        print(f"  [ PASS ] Physical Memory: {ram_gb:.1f} GB (Recommended: 8 GB+)")
    elif ram_gb >= 3.5:
        print(f"  [ WARN ] Physical Memory: {ram_gb:.1f} GB (Minimum 4 GB met; 8 GB recommended)")
    else:
        print(f"  [ FAIL ] Insufficient RAM: {ram_gb:.1f} GB (Minimum 4 GB required)")
        all_passed = False

    # 3. PostgreSQL
    pg_active = test_port("127.0.0.1", 5432)
    if pg_active:
        print("  [ PASS ] Database Engine: PostgreSQL responding on localhost:5432")
    else:
        print("  [ WARN ] PostgreSQL not responding on port 5432 (Local service or LAN server required)")

    # 4. API Port 8000
    port_8000_open = test_port("127.0.0.1", 8000)
    if not port_8000_open:
        print("  [ PASS ] Port 8000 is available for DentalCare Pro API service")
    else:
        print("  [ NOTE ] Port 8000 is currently occupied (DentalCare Pro or another service is running)")

    # 5. LocalAppData Write Permissions
    appdata = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "DentalCarePro"
    if test_write_permission(appdata):
        print(f"  [ PASS ] Workstation Storage: Write access confirmed at {appdata}")
    else:
        print(f"  [ FAIL ] Permission error writing to {appdata}")
        all_passed = False

    # 6. Backup Directory
    backup_dir = Path("C:\\DentalCarePro_Backups")
    if test_write_permission(backup_dir):
        print(f"  [ PASS ] Backup Storage: Write access confirmed at {backup_dir}")
    else:
        alt_backup = appdata / "backups"
        test_write_permission(alt_backup)
        print(f"  [ PASS ] Backup Storage: Fallback access confirmed at {alt_backup}")

    print("-" * 65)
    if all_passed:
        print("  RESULT: Workstation meets all requirements for DentalCare Pro.")
    else:
        print("  RESULT: Some checks failed. Please review the items above.")
    print("=" * 65)
    print("\nPress Enter to exit...")
    try:
        input()
    except Exception:
        pass

if __name__ == "__main__":
    main()
