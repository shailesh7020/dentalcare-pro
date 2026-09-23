# scripts/setup_cloudflare_tunnel.py
"""
DentalCare Pro - Automated Cloudflare Tunnel Setup Assistant for Windows
Configures secure zero-trust tunnel to allow remote mobile/tablet access
without opening router ports, dynamic DNS, or exposing PostgreSQL.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

CLOUDFLARED_CONFIG_DIR = Path("C:/ProgramData/cloudflared")


def check_cloudflared_installed() -> Path | None:
    """Check if cloudflared executable exists on system."""
    path = shutil.which("cloudflared.exe") or shutil.which("cloudflared")
    if path:
        return Path(path)

    well_known = [
        Path(r"C:\Program Files\cloudflared\cloudflared.exe"),
        Path(r"C:\Program Files (x86)\cloudflared\cloudflared.exe"),
        CLOUDFLARED_CONFIG_DIR / "cloudflared.exe",
    ]
    for p in well_known:
        if p.exists():
            return p
    return None


def generate_tunnel_config(
    tunnel_id: str,
    credentials_file: str,
    hostname: str,
    web_port: int = 3000,
    api_port: int = 8000,
) -> str:
    """Generate YAML ingress configuration for Cloudflare Tunnel."""
    return f"""# DentalCare Pro - Cloudflare Tunnel Config
tunnel: {tunnel_id}
credentials-file: {credentials_file}

ingress:
  # API and Swagger routing
  - hostname: {hostname}
    path: /api/*
    service: http://127.0.0.1:{api_port}
  - hostname: {hostname}
    path: /ws/*
    service: http://127.0.0.1:{api_port}
  # Frontend Next.js Web Application & Mobile Dashboard
  - hostname: {hostname}
    service: http://127.0.0.1:{web_port}
  # Catch-all rule
  - service: http_status:404
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="DentalCare Pro - Cloudflare Tunnel Setup Assistant")
    parser.add_argument("--hostname", default="clinic.dentalcarepro.com", help="Public domain/subdomain for clinic")
    parser.add_argument("--tunnel-name", default="dentalcare-clinic", help="Cloudflare tunnel name")
    parser.add_argument("--quick", action="store_true", help="Launch an instant ephemeral test tunnel (*.trycloudflare.com) without account setup")
    parser.add_argument("--dry-run", action="store_true", help="Print configuration without modifying files")
    args = parser.parse_args()

    print("\n===========================================================")
    print("DENTALCARE PRO – CLOUDFLARE REMOTE ACCESS ASSISTANT")
    print("===========================================================\n")

    bin_path = check_cloudflared_installed()
    if not bin_path:
        print("[!] Cloudflare Tunnel daemon (cloudflared.exe) is not detected in PATH.")
        print("    Install in 5 seconds with PowerShell / Command Prompt:")
        print("    winget install --id Cloudflare.cloudflared\n")
        print("    Or download MSI directly:")
        print("    https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.msi\n")
        if not args.dry_run:
            print("[*] Proceeding with configuration generation...\n")

    if args.quick:
        cmd = bin_path or "cloudflared"
        print("[*] Launching Quick Zero-Setup Tunnel to FastAPI backend (:8000)...")
        print("    This will provide a free, instant HTTPS URL (*.trycloudflare.com)")
        print("    to test mobile logins from outside the clinic network!\n")
        print(f"    Executing: {cmd} tunnel --url http://127.0.0.1:8000\n")
        try:
            subprocess.run([str(cmd), "tunnel", "--url", "http://127.0.0.1:8000"])
        except KeyboardInterrupt:
            print("\n[+] Quick tunnel stopped.")
        except FileNotFoundError:
            print("[!] cloudflared.exe not found. Please install via: winget install --id Cloudflare.cloudflared")
        return

    CLOUDFLARED_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config_file = CLOUDFLARED_CONFIG_DIR / "config.yml"
    cred_file = f"C:\\ProgramData\\cloudflared\\{args.tunnel_name}.json"

    config_content = generate_tunnel_config(
        tunnel_id=args.tunnel_name,
        credentials_file=cred_file,
        hostname=args.hostname,
        web_port=3000,
        api_port=8000,
    )

    if args.dry_run:
        print("[*] Dry-run mode. Proposed configuration:")
        print(config_content)
        return

    try:
        config_file.write_text(config_content, encoding="utf-8")
        print(f"[+] Wrote tunnel configuration to: {config_file}")
    except PermissionError:
        local_config = Path("cloudflare_tunnel_config.yml")
        local_config.write_text(config_content, encoding="utf-8")
        print(f"[!] Administrator rights required for C:\\ProgramData. Saved locally to: {local_config.resolve()}")

    print("\nNext Steps to start Remote Mobile Access:")
    print("1. Authenticate with Cloudflare (once):")
    print("   cloudflared.exe tunnel login")
    print("2. Create Named Tunnel:")
    print(f"   cloudflared.exe tunnel create {args.tunnel_name}")
    print("3. Route Public Subdomain:")
    print(f"   cloudflared.exe tunnel route dns {args.tunnel_name} {args.hostname}")
    print("4. Install as continuous Windows Background Service:")
    print("   cloudflared.exe service install")
    print("   net start cloudflared")
    print(f"\n[+] Mobile App Setup:")
    print(f"    In DentalCare Pro Mobile, open Server Connection settings (gear icon)")
    print(f"    and enter: https://{args.hostname}/api/v1")
    print(f"    Mobile devices on 4G/5G/cellular can now log in securely!\n")


if __name__ == "__main__":
    main()
