# backend/desktop_entry.py
"""
DentalCare Pro - Desktop Application Backend Entrypoint & Service Supervisor
Production-grade headless launcher for the FastAPI backend on Windows.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import secrets
import signal
import sys

# Ensure backend root is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Windows AppData Directory Setup
APPDATA_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "DentalCarePro"
LOGS_DIR = APPDATA_DIR / "logs"
DATA_DIR = APPDATA_DIR / "data"
BACKUPS_DIR = APPDATA_DIR / "backups"
CONFIG_FILE = APPDATA_DIR / "config.json"

for d in (APPDATA_DIR, LOGS_DIR, DATA_DIR, BACKUPS_DIR):
    d.mkdir(parents=True, exist_ok=True)

# Configure Rotating File Logger
log_file = LOGS_DIR / "backend.log"
logger = logging.getLogger("dentalcare.desktop")
logger.setLevel(logging.INFO)

file_handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8")
file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
logger.addHandler(file_handler)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
logger.addHandler(console_handler)


def load_desktop_configuration() -> dict:
    """Load or generate production configuration for desktop runtime."""
    defaults = {
        "ENVIRONMENT": "production",
        "DATABASE_URL": "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/dentalcare",
        "SECRET_KEY": secrets.token_urlsafe(32),
        "JWT_SECRET": secrets.token_urlsafe(32),
        "JWT_ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "15",
        "REFRESH_TOKEN_EXPIRE_DAYS": "7",
        "REDIS_URL": "redis://127.0.0.1:6379/0",
        "CORS_ORIGINS": json.dumps(["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000", "http://127.0.0.1:8000", "app://dentalcare.local"]),
        "STORAGE_BACKEND": "local",
        "STORAGE_LOCAL_PATH": str(DATA_DIR),
        "PORT": 8000,
        "HOST": "127.0.0.1",
    }

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                user_config = json.load(f)
                defaults.update(user_config)
                logger.info(f"Loaded desktop configuration from {CONFIG_FILE}")
        except Exception as e:
            logger.warning(f"Failed to read {CONFIG_FILE}, using defaults: {e}")
    else:
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(defaults, f, indent=2)
            logger.info(f"Created default desktop configuration at {CONFIG_FILE}")
        except Exception as e:
            logger.warning(f"Could not save default {CONFIG_FILE}: {e}")

    # Inject into environment
    for k, v in defaults.items():
        if k not in os.environ and v is not None:
            os.environ[k] = str(v)

    return defaults


def run_migrations():
    """Apply Alembic migrations programmatically."""
    logger.info("Executing database migrations...")
    try:
        from alembic import command
        from alembic.config import Config

        alembic_cfg_path = BASE_DIR / "alembic.ini"
        if not alembic_cfg_path.exists():
            alembic_cfg_path = Path(sys._MEIPASS) / "alembic.ini" if hasattr(sys, "_MEIPASS") else BASE_DIR / "alembic.ini"

        cfg = Config(str(alembic_cfg_path))
        cfg.set_main_option("script_location", str(BASE_DIR / "migrations"))
        cfg.set_main_option("sqlalchemy.url", os.environ.get("DATABASE_URL"))
        command.upgrade(cfg, "head")
        logger.info("Database migrations successfully applied!")
        return True
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        return False


def run_health_check() -> dict:
    """Verify backend and database readiness."""
    status = {"status": "ok", "app": "DentalCare Pro API", "version": "1.0.0"}
    try:
        import urllib.request
        port = os.environ.get("PORT", 8000)
        req = urllib.request.Request(f"http://127.0.0.1:{port}/api/health", headers={"User-Agent": "DentalCarePro-Desktop"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            status["server"] = "running"
            status["details"] = data
    except Exception as e:
        status["server"] = "stopped"
        status["error"] = str(e)
    return status


def start_uvicorn(host: str, port: int):
    """Launch Uvicorn ASGI server."""
    import uvicorn
    logger.info(f"Starting DentalCare Pro API server on {host}:{port}")

    config = uvicorn.Config(
        "app.main:app",
        host=host,
        port=port,
        log_level="info",
        access_log=True,
        loop="asyncio",
    )
    server = uvicorn.Server(config)

    # Windows signal handling
    def handle_exit(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        server.should_exit = True

    try:
        signal.signal(signal.SIGINT, handle_exit)
        signal.signal(signal.SIGTERM, handle_exit)
    except Exception:
        pass

    server.run()


def main():
    parser = argparse.ArgumentParser(description="DentalCare Pro Desktop Application API Server")
    parser.add_argument("--host", default=None, help="Bind host (default 127.0.0.1)")
    parser.add_argument("--port", type=int, default=None, help="Bind port (default 8000)")
    parser.add_argument("--migrate", action="store_true", help="Run database migrations and exit")
    parser.add_argument("--health-check", action="store_true", help="Check if API server is running")
    parser.add_argument("--config-path", action="store_true", help="Print configuration file path")

    args = parser.parse_args()

    config = load_desktop_configuration()

    if args.config_path:
        print(str(CONFIG_FILE))
        return

    if args.health_check:
        res = run_health_check()
        print(json.dumps(res, indent=2))
        sys.exit(0 if res.get("server") == "running" else 1)

    if args.migrate:
        success = run_migrations()
        sys.exit(0 if success else 1)

    # Auto-run migrations on startup
    run_migrations()

    host = args.host or config.get("HOST", "127.0.0.1")
    port = args.port or int(config.get("PORT", 8000))
    start_uvicorn(host, port)


if __name__ == "__main__":
    main()
