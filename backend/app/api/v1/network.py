from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, Field

from app.dependencies.auth import current_user
from app.models.identity import User
from app.services.clinic_network_service import ClinicNetworkService

router = APIRouter(prefix="/network", tags=["Multi-Workstation Clinic Network"])


class BroadcastRequest(BaseModel):
    clinic_id: UUID
    event_type: str = Field(..., description="e.g. PATIENT_CHECKIN, CHAIR_STATUS, URGENT_ALERT")
    payload: dict[str, Any] = Field(default_factory=dict)
    target_role: str | None = Field(default=None, description="RECEPTION, DENTIST, ASSISTANT, MANAGER, ADMIN")


@router.websocket("/ws/clinic/{clinic_id}")
async def clinic_websocket_endpoint(
    websocket: WebSocket,
    clinic_id: UUID,
    workstation_id: str = Query(..., description="Unique workstation computer ID or hostname"),
    workstation_role: str = Query(default="RECEPTION", description="RECEPTION, DENTIST, ASSISTANT, MANAGER, ADMIN"),
):
    client_ip = websocket.client.host if websocket.client else "127.0.0.1"
    await ClinicNetworkService.connect_workstation(
        websocket=websocket,
        clinic_id=clinic_id,
        workstation_id=workstation_id,
        role=workstation_role,
        client_ip=client_ip,
    )
    try:
        while True:
            text = await websocket.receive_text()
            try:
                msg = json.loads(text)
                msg_type = msg.get("type", "PING")
                if msg_type == "PING":
                    await websocket.send_text(json.dumps({"type": "PONG"}))
                elif msg_type == "BROADCAST":
                    await ClinicNetworkService.broadcast_event(
                        clinic_id=clinic_id,
                        event_type=msg.get("event", "CLINIC_EVENT"),
                        payload=msg.get("data", {}),
                        target_role=msg.get("target_role"),
                        exclude_id=workstation_id,
                    )
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        await ClinicNetworkService.disconnect_workstation(clinic_id=clinic_id, workstation_id=workstation_id)


@router.get("/workstations/{clinic_id}")
async def list_workstations(
    clinic_id: UUID,
    user: User = Depends(current_user),
) -> list[dict[str, Any]]:
    return ClinicNetworkService.get_active_workstations(clinic_id=clinic_id)


@router.post("/broadcast")
async def send_broadcast(
    body: BroadcastRequest,
    user: User = Depends(current_user),
) -> dict[str, Any]:
    sent = await ClinicNetworkService.broadcast_event(
        clinic_id=body.clinic_id,
        event_type=body.event_type,
        payload=body.payload,
        target_role=body.target_role,
    )
    return {"status": "broadcast_sent", "recipients_count": sent}
