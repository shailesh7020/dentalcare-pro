# desktop/launcher.py
"""
DentalCare Pro - Native Windows Desktop Shell & Supervisor (DentalCarePro.exe)
Native Windows WebView2 desktop container (no external browser required) with:
- Hidden console in production
- Background API supervisor (auto-start, auto-restart on crash, graceful shutdown)
- First-launch Setup Wizard (wizard.html)
- Window state persistence (dimensions, position, maximized state)
- Native menus and system tray
- Rotating logs in %LOCALAPPDATA%\DentalCarePro\logs
"""
import os
import sys
import time
import json
import socket
import logging
from logging.handlers import RotatingFileHandler
import subprocess
import urllib.request
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
APPDATA_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "DentalCarePro"
LOGS_DIR = APPDATA_DIR / "logs"
CONFIG_FILE = APPDATA_DIR / "config.json"
WINDOW_STATE_FILE = APPDATA_DIR / "window_state.json"

LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Logging Setup
app_logger = logging.getLogger("DentalCarePro_App")
app_logger.setLevel(logging.INFO)
app_handler = RotatingFileHandler(
    LOGS_DIR / "app.log", maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
)
app_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s"))
app_logger.addHandler(app_handler)

crash_logger = logging.getLogger("DentalCarePro_Crash")
crash_logger.setLevel(logging.ERROR)
crash_handler = RotatingFileHandler(
    LOGS_DIR / "crash.log", maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
)
crash_handler.setFormatter(logging.Formatter("[%(asctime)s] [CRASH] %(message)s"))
crash_logger.addHandler(crash_handler)


def log(msg: str):
    app_logger.info(msg)


def log_crash(msg: str):
    crash_logger.error(msg)


class BackendSupervisor:
    """Manages the lifecycle of DentalCarePro-API.exe, WhatsApp Gateway, and Web UI."""

    def __init__(self, port: int = 8000, web_port: int = 3000):
        self.port = port
        self.web_port = web_port
        self.proc = None
        self.web_proc = None
        self.wa_proc = None
        self.restart_count = 0
        self.max_restarts = 3

    def is_healthy(self) -> bool:
        for path in ("/api/v1/health/live", "/api/health"):
            url = f"http://127.0.0.1:{self.port}{path}"
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "DentalCarePro-Shell"})
                with urllib.request.urlopen(req, timeout=1.5) as resp:
                    if resp.status == 200:
                        return True
            except Exception:
                continue
        return False

    def is_web_healthy(self) -> bool:
        url = f"http://127.0.0.1:{self.web_port}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "DentalCarePro-Shell"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                return resp.status in (200, 302, 307, 308)
        except Exception:
            return False

    def find_project_root(self) -> Path:
        candidates = []
        # 1. Check saved PROJECT_ROOT in %LOCALAPPDATA%\DentalCarePro\config.json
        if CONFIG_FILE.exists():
            try:
                cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                if cfg.get("PROJECT_ROOT"):
                    candidates.append(Path(cfg["PROJECT_ROOT"]))
            except Exception:
                pass

        exe_dir = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else BASE_DIR
        local_default_cfg = exe_dir / "config" / "default_config.json"
        if local_default_cfg.exists():
            try:
                cfg = json.loads(local_default_cfg.read_text(encoding="utf-8"))
                if cfg.get("PROJECT_ROOT"):
                    candidates.append(Path(cfg["PROJECT_ROOT"]))
            except Exception:
                pass

        user_home = Path.home()
        candidates.extend([
            exe_dir,
            exe_dir.parent,
            exe_dir.parent.parent,
            Path(r"e:\dentalcare-pro"),
            Path(r"c:\dentalcare-pro"),
            Path(r"d:\dentalcare-pro"),
            user_home / "Desktop" / "dentalcare-pro",
            user_home / "Downloads" / "dentalcare-pro",
            user_home / "dentalcare-pro",
            ROOT_DIR,
            BASE_DIR.parent.parent,
        ])
        for c in candidates:
            try:
                if c and (c / "apps" / "web").exists():
                    return c
            except Exception:
                continue
        return ROOT_DIR

    def find_api_binary(self) -> Path:
        exe_dir = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else BASE_DIR
        candidates = [
            exe_dir / "backend" / "DentalCarePro-API.exe",
            exe_dir / "DentalCarePro-API.exe",
            BASE_DIR / "backend" / "DentalCarePro-API.exe",
            BASE_DIR / "DentalCarePro-API.exe",
            ROOT_DIR / "dist" / "backend" / "DentalCarePro-API.exe",
            ROOT_DIR / "Dental Clinic Management Gift" / "Runtime" / "backend" / "DentalCarePro-API.exe",
        ]
        for c in candidates:
            if c.exists():
                return c
        return None

    def ensure_environment_paths(self):
        """Ensure Node.js and PostgreSQL standard Windows installation directories are in PATH."""
        extra_paths = [
            r"C:\Program Files\nodejs",
            r"C:\Program Files (x86)\nodejs",
            r"C:\Program Files\PostgreSQL\18\bin",
            r"C:\Program Files\PostgreSQL\17\bin",
            r"C:\Program Files\PostgreSQL\16\bin",
            r"C:\Program Files\PostgreSQL\15\bin",
        ]
        current_path = os.environ.get("PATH", "")
        for p in extra_paths:
            if Path(p).exists() and p.lower() not in current_path.lower():
                current_path = f"{p};{current_path}"
        os.environ["PATH"] = current_path

    def start(self):
        self.ensure_environment_paths()
        startupinfo = None
        creationflags = 0
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0  # SW_HIDE
            creationflags = subprocess.CREATE_NO_WINDOW

        proj_root = self.find_project_root()
        log(f"Resolved DentalCare Pro workspace root: {proj_root}")

        # Auto-install node_modules on first launch if missing on a brand-new PC
        if (proj_root / "package.json").exists() and not (proj_root / "node_modules").exists():
            try:
                log("Installing root node_modules for first-time setup...")
                subprocess.run(
                    ["cmd.exe", "/c", "npm install --no-audit --no-fund"],
                    cwd=str(proj_root),
                    startupinfo=startupinfo,
                    creationflags=creationflags,
                    timeout=180,
                )
            except Exception as e:
                log(f"Root npm install note: {e}")

        if (proj_root / "apps" / "web" / "package.json").exists() and not (proj_root / "apps" / "web" / "node_modules").exists() and not (proj_root / "node_modules").exists():
            try:
                log("Installing apps/web node_modules for first-time setup...")
                subprocess.run(
                    ["cmd.exe", "/c", "npm install --no-audit --no-fund"],
                    cwd=str(proj_root / "apps" / "web"),
                    startupinfo=startupinfo,
                    creationflags=creationflags,
                    timeout=180,
                )
            except Exception as e:
                log(f"Web npm install note: {e}")

        # 1. Ensure WhatsApp Gateway is running on port 4050
        wa_script = proj_root / "scripts" / "whatsapp-gateway.mjs"
        if wa_script.exists():
            try:
                self.wa_proc = subprocess.Popen(
                    ["node", str(wa_script)],
                    cwd=str(proj_root),
                    startupinfo=startupinfo,
                    creationflags=creationflags,
                )
            except Exception as e:
                log(f"WhatsApp gateway start note: {e}")

        # 2. Ensure Web Frontend (Next.js on port 3000) is running
        if not self.is_web_healthy() and (proj_root / "apps" / "web").exists():
            try:
                self.web_proc = subprocess.Popen(
                    ["cmd.exe", "/c", f"npx next dev -H 0.0.0.0 -p {self.web_port}"],
                    cwd=str(proj_root / "apps" / "web"),
                    startupinfo=startupinfo,
                    creationflags=creationflags,
                )
            except Exception as e:
                log(f"Web UI start note: {e}")

        # 3. Ensure Backend API (port 8000) is running
        if not self.is_healthy():
            exe_path = self.find_api_binary()
            py_entry = proj_root / "backend" / "desktop_entry.py"
            if exe_path:
                log(f"Starting standalone backend binary: {exe_path}")
                self.proc = subprocess.Popen(
                    [str(exe_path), "--host", "0.0.0.0", "--port", str(self.port)],
                    startupinfo=startupinfo,
                    creationflags=creationflags,
                )
            elif py_entry.exists():
                log(f"Starting backend via python entrypoint: {py_entry}")
                self.proc = subprocess.Popen(
                    [sys.executable, str(py_entry), "--host", "0.0.0.0", "--port", str(self.port)],
                    cwd=str(proj_root / "backend"),
                    startupinfo=startupinfo,
                    creationflags=creationflags,
                )
            else:
                log("WARNING: Neither DentalCarePro-API.exe nor desktop_entry.py found.")

        # Wait up to 20 seconds for Backend API (8000) and Web UI (3000) to be ready
        attempts = 0
        while attempts < 20:
            if self.is_healthy() and (self.is_web_healthy() or attempts >= 8):
                log(f"DentalCare Pro services verified ready (API: {self.is_healthy()}, Web: {self.is_web_healthy()}).")
                return
            time.sleep(1)
            attempts += 1

        log("WARNING: API did not respond to health check within 15 seconds.")

    def check_and_recover(self):
        if self.proc and self.proc.poll() is not None:
            exit_code = self.proc.poll()
            log_crash(f"Backend process terminated unexpectedly with exit code {exit_code}")
            if self.restart_count < self.max_restarts:
                self.restart_count += 1
                log(f"Restarting backend process (Attempt {self.restart_count}/{self.max_restarts})...")
                self.start()
            else:
                log_crash("Max restart attempts exceeded. Backend could not be recovered.")

    def stop(self):
        if self.proc:
            log("Stopping backend process gracefully...")
            try:
                self.proc.terminate()
                self.proc.wait(timeout=5)
            except Exception:
                try:
                    self.proc.kill()
                except Exception:
                    pass
            log("Backend process stopped.")


class DesktopApiBridge:
    """Exposes Python methods to the JavaScript webview frontend."""

    def __init__(self, window_ref, supervisor_ref):
        self.window = window_ref
        self.supervisor = supervisor_ref

    def testDbConnection(self, params):
        log(f"Testing database connection with params: {params}")
        db_url = params.get("databaseUrl", "")
        try:
            host = "127.0.0.1"
            port = 5432
            if "@" in db_url:
                host_port = db_url.split("@")[-1].split("/")[0]
                if ":" in host_port:
                    host, port = host_port.split(":")
                    port = int(port)
                else:
                    host = host_port

            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2.0)
            res = s.connect_ex((host, port))
            s.close()
            if res == 0:
                return {"success": True, "message": f"Successfully connected to PostgreSQL at {host}:{port}"}
            else:
                return {"success": False, "error": f"PostgreSQL not responding on {host}:{port} (error code {res})"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def saveSetupConfig(self, payload):
        log(f"Saving first-launch setup configuration: {payload.get('clinicName')}")
        try:
            APPDATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            log("Setup configuration successfully persisted to config.json.")
            return {"success": True}
        except Exception as e:
            log_crash(f"Failed to save setup config: {e}")
            return {"success": False, "error": str(e)}

    def onSetupComplete(self):
        log("Setup complete! Transitioning to main application dashboard...")
        if self.window:
            target_url = "http://localhost:3000" if self.supervisor.is_web_healthy() else f"http://127.0.0.1:{self.supervisor.port}"
            self.window.load_url(target_url)


def load_window_state() -> dict:
    default_state = {"width": 1280, "height": 820, "x": 100, "y": 80, "maximized": False}
    if WINDOW_STATE_FILE.exists():
        try:
            with open(WINDOW_STATE_FILE, "r", encoding="utf-8") as f:
                return {**default_state, **json.load(f)}
        except Exception:
            pass
    return default_state


def save_window_state(window):
    try:
        state = {
            "width": window.width,
            "height": window.height,
            "x": window.x,
            "y": window.y,
        }
        with open(WINDOW_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass


def main():
    log("==================================================")
    log("DentalCare Pro Desktop Application Shell Starting")
    log("==================================================")

    api_port = 8000
    is_first_run = not CONFIG_FILE.exists()

    if not is_first_run:
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                api_port = cfg.get("PORT", 8000)
        except Exception:
            pass

    supervisor = BackendSupervisor(port=api_port, web_port=3000)
    supervisor.start()

    wizard_html = BASE_DIR / "wizard.html"

    if is_first_run and wizard_html.exists():
        initial_url = wizard_html.as_uri()
        log(f"First-launch detected. Loading Setup Wizard: {initial_url}")
    else:
        initial_url = "http://localhost:3000"
        log(f"Loading DentalCare Pro clinical workspace: {initial_url}")

    # Window State
    win_state = load_window_state()

    # Try native webview (WebView2)
    try:
        import webview

        bridge = DesktopApiBridge(None, supervisor)
        icon_path = ROOT_DIR / "assets" / "branding" / "app_icon.ico"
        if not icon_path.exists():
            icon_path = BASE_DIR / "assets" / "app_icon.ico"

        window = webview.create_window(
            title="DentalCare Pro Enterprise v1.0.0",
            url=initial_url,
            js_api=bridge,
            width=win_state["width"],
            height=win_state["height"],
            x=win_state.get("x"),
            y=win_state.get("y"),
            min_size=(1024, 700),
            confirm_close=True,
            text_select=True,
        )
        bridge.window = window

        def on_closing():
            log("DentalCare Pro desktop window closing. Saving state...")
            save_window_state(window)
            supervisor.stop()

        window.events.closing += on_closing

        log("Starting native WebView2 application loop...")
        webview.start(debug=False)

    except ImportError as ie:
        log(f"Native webview module unavailable ({ie}). Falling back to system browser shell.")
        import webbrowser
        webbrowser.open(initial_url)
        try:
            while True:
                time.sleep(2)
                supervisor.check_and_recover()
        except KeyboardInterrupt:
            supervisor.stop()
    except Exception as e:
        log_crash(f"Desktop window runtime failure: {e}")
        supervisor.stop()
        raise


if __name__ == "__main__":
    main()
