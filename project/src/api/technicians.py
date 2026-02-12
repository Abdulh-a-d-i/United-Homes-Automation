from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
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
    ghl_user_id: str
    ghl_calendar_id: str


class TechnicianResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    skills: List[str]
    home_latitude: float
    home_longitude: float
    max_radius_miles: int
    status: str


@router.get("/", response_model=List[TechnicianResponse])
def get_technicians():
    techs = get_all_technicians()
    return [
        TechnicianResponse(
            id=tech["id"],
            name=tech["name"],
            email=tech["email"],
            phone=tech["phone"],
            skills=tech["skills"],
            home_latitude=float(tech["home_latitude"]),
            home_longitude=float(tech["home_longitude"]),
            max_radius_miles=tech["max_radius_miles"],
            status=tech["status"]
        )
        for tech in techs
    ]


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
        request.ghl_user_id,
        request.ghl_calendar_id
    )
    
    return TechnicianResponse(
        id=tech["id"],
        name=tech["name"],
        email=tech["email"],
        phone=tech["phone"],
        skills=tech["skills"],
        home_latitude=float(tech["home_latitude"]),
        home_longitude=float(tech["home_longitude"]),
        max_radius_miles=tech["max_radius_miles"],
        status=tech["status"]
    )
