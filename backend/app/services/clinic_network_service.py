from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any, ClassVar
from uuid import UUID

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

logger = logging.getLogger("dentalcare.network")


class ClinicNetworkService:
    # clinic_id -> dict of workstation_id -> {"ws": WebSocket, "role": str, "connected_at": datetime, "ip": str}
    _workstations: ClassVar[dict[UUID, dict[str, dict[str, Any]]]] = {}

    @classmethod
    async def connect_workstation(
        cls,
        websocket: WebSocket,
        clinic_id: UUID,
        workstation_id: str,
        role: str,
        client_ip: str = "127.0.0.1",
    ) -> None:
        await websocket.accept()
        if clinic_id not in cls._workstations:
            cls._workstations[clinic_id] = {}

        cls._workstations[clinic_id][workstation_id] = {
            "ws": websocket,
            "role": role.upper(),
            "connected_at": datetime.now(UTC),
            "client_ip": client_ip,
        }
        logger.info(
            "Workstation connected: clinic=%s, id=%s, role=%s, ip=%s",
            clinic_id,
            workstation_id,
            role,
            client_ip,
        )

        # Notify other workstations of new node
        await cls.broadcast_event(
            clinic_id=clinic_id,
            event_type="WORKSTATION_CONNECTED",
            payload={"workstation_id": workstation_id, "role": role, "client_ip": client_ip},
            exclude_id=workstation_id,
        )

    @classmethod
    async def disconnect_workstation(cls, clinic_id: UUID, workstation_id: str) -> None:
        if clinic_id in cls._workstations and workstation_id in cls._workstations[clinic_id]:
            role = cls._workstations[clinic_id][workstation_id]["role"]
            del cls._workstations[clinic_id][workstation_id]
            logger.info("Workstation disconnected: clinic=%s, id=%s", clinic_id, workstation_id)
            if not cls._workstations[clinic_id]:
                del cls._workstations[clinic_id]

            await cls.broadcast_event(
                clinic_id=clinic_id,
                event_type="WORKSTATION_DISCONNECTED",
                payload={"workstation_id": workstation_id, "role": role},
            )

    @classmethod
    async def broadcast_event(
        cls,
        clinic_id: UUID,
        event_type: str,
        payload: dict[str, Any],
        target_role: str | None = None,
        exclude_id: str | None = None,
    ) -> int:
        if clinic_id not in cls._workstations:
            return 0

        message = {
            "type": event_type,
            "timestamp": datetime.now(UTC).isoformat(),
            "data": payload,
        }
        text_data = json.dumps(message)

        sent = 0
        dead_connections = []
        for ws_id, ws_meta in cls._workstations[clinic_id].items():
            if exclude_id and ws_id == exclude_id:
                continue
            if target_role and ws_meta["role"] != target_role.upper():
                continue

            ws: WebSocket = ws_meta["ws"]
            try:
                await ws.send_text(text_data)
                sent += 1
            except (WebSocketDisconnect, RuntimeError, OSError):
                dead_connections.append(ws_id)

        for ws_id in dead_connections:
            if ws_id in cls._workstations.get(clinic_id, {}):
                del cls._workstations[clinic_id][ws_id]

        return sent

    @classmethod
    def get_active_workstations(cls, clinic_id: UUID) -> list[dict[str, Any]]:
        clinic_map = cls._workstations.get(clinic_id, {})
        result = []
        for ws_id, meta in clinic_map.items():
            result.append(
                {
                    "workstation_id": ws_id,
                    "role": meta["role"],
                    "client_ip": meta["client_ip"],
                    "connected_at": meta["connected_at"].isoformat(),
                }
            )
        return result
