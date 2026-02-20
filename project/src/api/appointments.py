from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from src.utils.radar import geocode_address
from src.utils.db import get_techs_with_skill, get_technician, insert_appointment_cache, delete_route_cache
from src.utils.distance import calculate_distance, estimate_tech_location
# GHL COMMENTED OUT - replaced by direct calendar integration
# from src.utils.ghl import create_or_update_contact, create_appointment, check_calendar_availability

router = APIRouter()


class VerifyAddressRequest(BaseModel):
    messy_input: str


class VerifyAddressResponse(BaseModel):
    formatted_address: str
    latitude: float
    longitude: float
    confidence: str


class FindTechnicianRequest(BaseModel):
    service_type: str
    confirmed_latitude: float
    confirmed_longitude: float
    requested_datetime: datetime


class TechnicianInfo(BaseModel):
    id: int
    name: str
    distance_miles: float


class FindTechnicianResponse(BaseModel):
    success: bool
    technician: TechnicianInfo = None
    available: bool
    time_slot: str = None
    alternative_slots: list = None


class BookAppointmentRequest(BaseModel):
    customer_name: str
    customer_phone: str
    customer_email: str
    technician_id: int
    service_type: str
    address: str
    latitude: float
    longitude: float
    start_time: datetime
    duration_minutes: int


class BookAppointmentResponse(BaseModel):
    success: bool
    appointment_id: str = None
    technician: str = None
    time: str = None
    message: str


@router.post("/verify-address", response_model=VerifyAddressResponse)
def verify_address(request: VerifyAddressRequest):
    result = geocode_address(request.messy_input)
    if not result:
        raise HTTPException(status_code=400, detail="Address not found")

    return VerifyAddressResponse(
        formatted_address=result["formatted_address"],
        latitude=result["latitude"],
        longitude=result["longitude"],
        confidence=result["confidence"]
    )


@router.post("/find-technician-availability", response_model=FindTechnicianResponse)
def find_technician_availability(request: FindTechnicianRequest):
    techs = get_techs_with_skill(request.service_type)

    if not techs:
        return FindTechnicianResponse(
            success=False,
            available=False,
            message="No technicians available for this service type"
        )

    tech_scores = []

    for tech in techs:
        estimated_location = estimate_tech_location(tech["id"], request.requested_datetime)

        if not estimated_location:
            continue

        distance = calculate_distance(
            estimated_location["latitude"],
            estimated_location["longitude"],
            request.confirmed_latitude,
            request.confirmed_longitude
        )

        if distance <= tech["max_radius_miles"]:
            # GHL COMMENTED OUT - will be replaced by direct calendar check
            # is_available = check_calendar_availability(
            #     tech["ghl_calendar_id"],
            #     request.requested_datetime,
            #     60
            # )
            is_available = True

            tech_scores.append({
                "tech": tech,
                "distance": distance,
                "available": is_available
            })

    tech_scores.sort(key=lambda x: (not x["available"], x["distance"]))

    if not tech_scores:
        return FindTechnicianResponse(
            success=False,
            available=False,
            message="No technicians within service radius"
        )

    best_tech = tech_scores[0]

    if best_tech["available"]:
        return FindTechnicianResponse(
            success=True,
            technician=TechnicianInfo(
                id=best_tech["tech"]["id"],
                name=best_tech["tech"]["name"],
                distance_miles=round(best_tech["distance"], 2)
            ),
            available=True,
            time_slot=request.requested_datetime.isoformat()
        )
    else:
        alternative_slots = []
        base_time = request.requested_datetime
        for i in range(1, 4):
            alt_time = base_time + timedelta(hours=i)
            alternative_slots.append(alt_time.isoformat())

        return FindTechnicianResponse(
            success=True,
            technician=TechnicianInfo(
                id=best_tech["tech"]["id"],
                name=best_tech["tech"]["name"],
                distance_miles=round(best_tech["distance"], 2)
            ),
            available=False,
            alternative_slots=alternative_slots
        )


@router.post("/book-appointment", response_model=BookAppointmentResponse)
def book_appointment(request: BookAppointmentRequest):
    tech = get_technician(request.technician_id)

    if not tech:
        raise HTTPException(status_code=404, detail="Technician not found")

    end_time = request.start_time + timedelta(minutes=request.duration_minutes)

    # GHL COMMENTED OUT - replaced by direct calendar integration
    # contact_id = create_or_update_contact(
    #     request.customer_name,
    #     request.customer_phone,
    #     request.customer_email
    # )
    # if not contact_id:
    #     raise HTTPException(status_code=500, detail="Failed to create contact")
    #
    # appointment_id = create_appointment(
    #     tech["ghl_calendar_id"],
    #     contact_id,
    #     f"{request.service_type} - {request.customer_name}",
    #     request.start_time,
    #     end_time,
    #     request.address
    # )
    # if not appointment_id:
    #     raise HTTPException(status_code=500, detail="Failed to create appointment")

    import uuid
    appointment_id = str(uuid.uuid4())

    insert_appointment_cache(
        appointment_id,
        request.technician_id,
        request.customer_name,
        request.customer_phone,
        request.service_type,
        request.address,
        request.latitude,
        request.longitude,
        request.start_time,
        end_time,
        "scheduled"
    )

    delete_route_cache(request.technician_id, request.start_time.date())

    return BookAppointmentResponse(
        success=True,
        appointment_id=appointment_id,
        technician=tech["name"],
        time=request.start_time.isoformat(),
        message=f"Appointment booked with {tech['name']} at {request.start_time.isoformat()}"
    )
