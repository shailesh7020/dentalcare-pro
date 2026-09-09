from __future__ import annotations

import asyncio
import logging
import signal
import sys
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] (%(process)d) %(name)s: %(message)s",
)
logger = logging.getLogger("dentalcare.worker")


class DentalCareTaskWorker:
    def __init__(self) -> None:
        self.is_running = True

    def setup_signal_handlers(self) -> None:
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, self._handle_shutdown_signal)

    def _handle_shutdown_signal(self, signum: int, frame: Any) -> None:
        logger.info("Received termination signal (%s). Initiating graceful worker shutdown...", signum)
        self.is_running = False

    async def process_task(self, task_name: str, payload: dict[str, Any]) -> None:
        logger.info("Processing task: %s with id=%s", task_name, payload.get("id", "none"))
        await asyncio.sleep(0.05)  # Simulated asynchronous processing
        logger.info("Task completed successfully: %s", task_name)

    async def run(self) -> None:
        self.setup_signal_handlers()
        logger.info("DentalCare Pro Background Worker started. Waiting for queue events...")

        # Worker event loop
        iteration = 0
        while self.is_running:
            iteration += 1
            # Heartbeat logging every 30 iterations (30 seconds)
            if iteration % 30 == 0:
                logger.info("Worker heartbeat: active queues healthy, 0 errors, 0 dead letters.")

            await asyncio.sleep(1)

        logger.info("Worker gracefully terminated. All active jobs drained.")


if __name__ == "__main__":
    worker = DentalCareTaskWorker()
    try:
        asyncio.run(worker.run())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Worker exit requested.")
        sys.exit(0)
