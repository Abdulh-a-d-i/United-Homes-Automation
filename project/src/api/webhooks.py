from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
import json
from src.utils.db import (
    insert_appointment_cache,
    delete_appointment_cache,
    delete_route_cache
)

router = APIRouter()


class AppointmentWebhook(BaseModel):
    id: str
    calendar_id: str = None
    contact_id: str = None
    title: str
    start_time: str
    end_time: str
    address: str = None
    status: str


@router.post("/appointment-created")
def appointment_created(webhook: AppointmentWebhook):
    start_time = datetime.fromisoformat(webhook.start_time.replace("Z", "+00:00"))
    end_time = datetime.fromisoformat(webhook.end_time.replace("Z", "+00:00"))

    insert_appointment_cache(
        webhook.id,
        None,
        "",
        "",
        webhook.title or "",
        webhook.address or "",
        None,
        None,
        start_time,
        end_time,
        webhook.status or "confirmed"
    )

    return {"status": "success", "message": "Appointment cached"}


@router.post("/appointment-deleted")
def appointment_deleted(webhook: AppointmentWebhook):
    delete_appointment_cache(webhook.id)

    start_time = datetime.fromisoformat(webhook.start_time.replace("Z", "+00:00"))
    delete_route_cache(None, start_time.date())

    return {"status": "success", "message": "Appointment deleted from cache"}
