from fastapi import APIRouter
from typing import List, Optional
import json
from src.utils.db import get_all_technicians

router = APIRouter()


class TechnicianResponse:
    pass


from pydantic import BaseModel


class TechnicianOut(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    skills: list
    home_latitude: Optional[float] = None
    home_longitude: Optional[float] = None
    max_radius_miles: int
    status: str
    calendar_connected: Optional[bool] = False
    calendar_provider: Optional[str] = None
    calendar_email: Optional[str] = None


@router.get("/", response_model=List[TechnicianOut])
def get_technicians():
    techs = get_all_technicians()
    result = []
    for tech in techs:
        skills = tech.get("skills", [])
        if isinstance(skills, str):
            skills = json.loads(skills)
        result.append(TechnicianOut(
            id=tech["id"],
            name=tech["name"],
            email=tech.get("email", ""),
            phone=tech.get("phone", ""),
            skills=skills if skills else [],
            home_latitude=float(tech["home_latitude"]) if tech.get("home_latitude") else None,
            home_longitude=float(tech["home_longitude"]) if tech.get("home_longitude") else None,
            max_radius_miles=tech.get("max_radius_miles", 20),
            status=tech.get("status", "active"),
            calendar_connected=tech.get("calendar_connected", False),
            calendar_provider=tech.get("calendar_provider"),
            calendar_email=tech.get("calendar_email")
        ))
    return result
