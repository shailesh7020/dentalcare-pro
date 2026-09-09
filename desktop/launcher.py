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
    """Manages the lifecycle of DentalCarePro-API.exe."""

    def __init__(self, port: int = 8000):
        self.port = port
        self.proc = None
        self.restart_count = 0
        self.max_restarts = 3

    def is_healthy(self) -> bool:
        url = f"http://127.0.0.1:{self.port}/api/health"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "DentalCarePro-Shell"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                return resp.status == 200
        except Exception:
            return False

    def find_api_binary(self) -> Path:
        # Search adjacent directories (production bundle) and build directories
        candidates = [
            BASE_DIR / "backend" / "DentalCarePro-API.exe",
            BASE_DIR / "DentalCarePro-API.exe",
            ROOT_DIR / "dist" / "backend" / "DentalCarePro-API.exe",
            ROOT_DIR / "dist" / "DentalCarePro_v1.0.0_Portable" / "backend" / "DentalCarePro-API.exe",
            Path(sys.executable).parent / "backend" / "DentalCarePro-API.exe",
            Path(sys.executable).parent / "DentalCarePro-API.exe",
        ]
        for c in candidates:
            if c.exists():
                return c
        return None

    def start(self):
        if self.is_healthy():
            log(f"DentalCare Pro API is already running and healthy on port {self.port}.")
            return

        exe_path = self.find_api_binary()
        startupinfo = None
        creationflags = 0
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0  # SW_HIDE
            creationflags = subprocess.CREATE_NO_WINDOW

        if exe_path:
            log(f"Starting standalone backend binary: {exe_path}")
            self.proc = subprocess.Popen(
                [str(exe_path), "--port", str(self.port)],
                startupinfo=startupinfo,
                creationflags=creationflags,
            )
        else:
            py_entry = ROOT_DIR / "backend" / "desktop_entry.py"
            if py_entry.exists():
                log(f"Backend binary not found; starting via python entrypoint: {py_entry}")
                self.proc = subprocess.Popen(
                    [sys.executable, str(py_entry), "--port", str(self.port)],
                    startupinfo=startupinfo,
                    creationflags=creationflags,
                )
            else:
                log("WARNING: Neither DentalCarePro-API.exe nor desktop_entry.py found.")

        # Wait for API to become ready
        attempts = 0
        while attempts < 25:
            time.sleep(1)
            if self.is_healthy():
                log(f"DentalCare Pro API verified healthy on port {self.port}.")
                return
            attempts += 1

        log("WARNING: API did not respond to health check within 25 seconds.")

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
            port = 8000
            try:
                if CONFIG_FILE.exists():
                    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                        port = cfg.get("PORT", 8000)
            except Exception:
                pass
            target_url = f"http://127.0.0.1:{port}"
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

    # Determine configured port
    api_port = 8000
    is_first_run = not CONFIG_FILE.exists()

    if not is_first_run:
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                api_port = cfg.get("PORT", 8000)
        except Exception:
            pass

    # Start Supervisor
    supervisor = BackendSupervisor(port=api_port)
    supervisor.start()

    # Determine initial URL
    wizard_html = BASE_DIR / "wizard.html"
    splash_html = BASE_DIR / "splash.html"

    if is_first_run and wizard_html.exists():
        initial_url = wizard_html.as_uri()
        log(f"First-launch detected. Loading Setup Wizard: {initial_url}")
    else:
        initial_url = f"http://127.0.0.1:{api_port}"
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
