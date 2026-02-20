from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
import json
from src.utils.db import insert_technician, get_all_technicians

router = APIRouter()


class TechnicianCreate(BaseModel):
    name: str
    email: str
    phone: str
    skills: List[str]
    home_latitude: float
    home_longitude: float
    user_id: Optional[int] = None


class TechnicianResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    skills: list
    home_latitude: float
    home_longitude: float
    max_radius_miles: int
    status: str
    calendar_connected: Optional[bool] = False
    calendar_provider: Optional[str] = None
    calendar_email: Optional[str] = None


@router.get("/", response_model=List[TechnicianResponse])
def get_technicians():
    techs = get_all_technicians()
    result = []
    for tech in techs:
        skills = tech.get("skills", [])
        if isinstance(skills, str):
            skills = json.loads(skills)
        home_lat = tech.get("home_latitude")
        home_lng = tech.get("home_longitude")
        if home_lat is None or home_lng is None:
            continue
        result.append(TechnicianResponse(
            id=tech["id"],
            name=tech["name"],
            email=tech["email"],
            phone=tech["phone"],
            skills=skills if skills else [],
            home_latitude=float(home_lat),
            home_longitude=float(home_lng),
            max_radius_miles=tech["max_radius_miles"],
            status=tech["status"],
            calendar_connected=tech.get("calendar_connected", False),
            calendar_provider=tech.get("calendar_provider"),
            calendar_email=tech.get("calendar_email")
        ))
    return result


@router.post("/", response_model=TechnicianResponse)
def create_technician(request: TechnicianCreate):
    skills_json = json.dumps(request.skills)

    tech = insert_technician(
        request.name,
        request.email,
        request.phone,
        skills_json,
        request.home_latitude,
        request.home_longitude,
        user_id=request.user_id
    )

    skills = tech.get("skills", [])
    if isinstance(skills, str):
        skills = json.loads(skills)

    return TechnicianResponse(
        id=tech["id"],
        name=tech["name"],
        email=tech["email"],
        phone=tech["phone"],
        skills=skills if skills else [],
        home_latitude=float(tech["home_latitude"]),
        home_longitude=float(tech["home_longitude"]),
        max_radius_miles=tech["max_radius_miles"],
        status=tech["status"],
        calendar_connected=tech.get("calendar_connected", False),
        calendar_provider=tech.get("calendar_provider"),
        calendar_email=tech.get("calendar_email")
    )
