from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
import json
from src.utils.db import (
    insert_appointment_cache, 
    delete_appointment_cache, 
    delete_route_cache,
    upsert_technician_from_ghl
)

router = APIRouter()


class AppointmentWebhook(BaseModel):
    id: str
    calendar_id: str
    contact_id: str
    title: str
    start_time: str
    end_time: str
    address: str = None
    status: str


class StaffWebhook(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    calendar_id: Optional[str] = None
    tags: Optional[List[str]] = []
    custom_fields: Optional[dict] = {}


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


@router.post("/staff-created")
def staff_created(webhook: StaffWebhook):
    skills = []
    home_lat = None
    home_lng = None
    
    if "technician" in [tag.lower() for tag in webhook.tags]:
        if webhook.custom_fields:
            skills_str = webhook.custom_fields.get("skills", "[]")
            if isinstance(skills_str, str):
                skills = json.loads(skills_str) if skills_str else []
            else:
                skills = skills_str
            
            home_lat = webhook.custom_fields.get("home_latitude")
            home_lng = webhook.custom_fields.get("home_longitude")
        
        skills_json = json.dumps(skills) if skills else None
        
        tech = upsert_technician_from_ghl(
            ghl_user_id=webhook.id,
            ghl_calendar_id=webhook.calendar_id or "",
            name=webhook.name,
            email=webhook.email,
            phone=webhook.phone or "",
            skills=skills_json,
            home_latitude=home_lat,
            home_longitude=home_lng
        )
        
        return {
            "status": "success", 
            "message": f"Technician {webhook.name} synced to database",
            "technician_id": tech["id"] if tech else None
        }
    
    return {"status": "skipped", "message": "User does not have technician tag"}
