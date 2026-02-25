import logging
import uuid
from typing import Optional
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta

from src.utils.radar import geocode_address
from src.utils.db import get_techs_with_skill, get_technician, insert_appointment, delete_route_cache
from src.utils.distance import calculate_distance, estimate_tech_location
from src.utils.api_key_auth import verify_retell_api_key

router = APIRouter()


@router.post("/get-current-datetime")
def get_current_datetime(_auth=Depends(verify_retell_api_key)):
    """Return the current date and time in Eastern Time for the agent."""
    eastern = ZoneInfo("America/New_York")
    now = datetime.now(eastern)
    return {
        "current_date": now.strftime("%A, %B %d, %Y"),
        "current_time": now.strftime("%I:%M %p ET"),
        "iso_date": now.strftime("%Y-%m-%d"),
        "day_of_week": now.strftime("%A"),
    }


@router.post("/simulate-manager-check")
def simulate_manager_check(_auth=Depends(verify_retell_api_key)):
    """Simulate a manager approval check with a 5-second delay.

    This endpoint exists solely to create a realistic pause on the call
    while the agent pretends to check with a manager about a discount.
    """
    import time
    time.sleep(5)
    return {
        "approved": True,
        "message": "Manager approved an additional 10% discount.",
    }


class VerifyAddressRequest(BaseModel):
    messy_input: str


class VerifyAddressResponse(BaseModel):
    formatted_address: str
    latitude: float
    longitude: float
    confidence: Optional[str] = None


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
def verify_address(request: VerifyAddressRequest, _auth=Depends(verify_retell_api_key)):
    try:
        result = geocode_address(request.messy_input)
        if not result:
            raise HTTPException(status_code=400, detail="Could not verify this address. Please try a more specific address or zip code.")

        return VerifyAddressResponse(
            formatted_address=result["formatted_address"],
            latitude=result["latitude"],
            longitude=result["longitude"],
            confidence=result.get("confidence")
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Verify address error: {e}")
        raise HTTPException(status_code=500, detail="Address verification failed. Please try again.")


@router.post("/find-technician-availability", response_model=FindTechnicianResponse)
def find_technician_availability(request: FindTechnicianRequest, _auth=Depends(verify_retell_api_key)):
    try:
        logging.info(f"[AVAILABILITY] Request: service={request.service_type}, lat={request.confirmed_latitude}, lng={request.confirmed_longitude}, time={request.requested_datetime}")

        techs = get_techs_with_skill(request.service_type)

        logging.info(f"[AVAILABILITY] Found {len(techs)} techs for '{request.service_type}': {[(t['id'], t['name'], t.get('skills')) for t in techs]}")

        if not techs:
            logging.warning(f"[AVAILABILITY] No techs at all for '{request.service_type}'")
            return FindTechnicianResponse(
                success=False,
                available=False,
                message="No technicians available for this service type"
            )

        tech_scores = []

        for tech in techs:
            # Skip techs without home coordinates
            if not tech.get("home_latitude") or not tech.get("home_longitude"):
                logging.warning(f"Tech {tech['name']} (id={tech['id']}) has no home coordinates, skipping")
                continue

            estimated_location = estimate_tech_location(tech["id"], request.requested_datetime)

            if not estimated_location:
                # Fallback to home location if estimate fails
                estimated_location = {
                    "latitude": float(tech["home_latitude"]),
                    "longitude": float(tech["home_longitude"])
                }

            distance = calculate_distance(
                estimated_location["latitude"],
                estimated_location["longitude"],
                request.confirmed_latitude,
                request.confirmed_longitude
            )

            max_radius = tech.get("max_radius_miles") or 50  # Default 50mi if not set

            if distance <= max_radius:
                is_available = True

                tech_scores.append({
                    "tech": tech,
                    "distance": distance,
                    "available": is_available
                })

        tech_scores.sort(key=lambda x: (not x["available"], x["distance"]))

        if not tech_scores:
            # No techs in radius — log distances and tell the agent
            logging.warning(f"[AVAILABILITY] No techs within radius for {request.service_type}. Distances:")
            for tech in techs:
                if not tech.get("home_latitude") or not tech.get("home_longitude"):
                    logging.warning(f"  {tech['name']} (id={tech['id']}): NO COORDINATES")
                    continue
                dist = calculate_distance(
                    float(tech["home_latitude"]), float(tech["home_longitude"]),
                    request.confirmed_latitude, request.confirmed_longitude
                )
                max_r = tech.get("max_radius_miles") or 50
                logging.warning(
                    "  %s (id=%d): %.1f miles away, max_radius=%dmi -- TOO FAR",
                    tech["name"], tech["id"], dist, max_r,
                )

            return FindTechnicianResponse(
                success=False,
                available=False,
                message="No technicians available in your area. All our technicians are outside service range for this location."
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
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Find technician availability error: {e}")
        return FindTechnicianResponse(
            success=False,
            available=False,
            message="Error checking availability. Please try again."
        )
@router.post("/book-appointment", response_model=BookAppointmentResponse)
def book_appointment(request: BookAppointmentRequest, _auth=Depends(verify_retell_api_key)):
    logging.info(f"[BOOKING] Request: customer={request.customer_name}, phone={request.customer_phone}, tech_id={request.technician_id}, service={request.service_type}, time={request.start_time}, address={request.address}")

    try:
        tech = get_technician(request.technician_id)
        logging.info(f"[BOOKING] Tech lookup: {'found ' + tech['name'] if tech else 'NOT FOUND'} (id={request.technician_id})")

        if not tech:
            raise HTTPException(status_code=404, detail="Technician not found")

        end_time = request.start_time + timedelta(minutes=request.duration_minutes)

        appointment_id = str(uuid.uuid4())
        logging.info(f"[BOOKING] Generated appointment_id={appointment_id}")

        insert_appointment(
            calendar_event_id=appointment_id,
            technician_id=request.technician_id,
            customer_name=request.customer_name,
            customer_phone=request.customer_phone,
            customer_email=request.customer_email,
            service_type=request.service_type,
            address=request.address,
            latitude=request.latitude,
            longitude=request.longitude,
            start_time=request.start_time,
            end_time=end_time,
            duration_minutes=request.duration_minutes,
            status="scheduled"
        )

        delete_route_cache(request.technician_id, request.start_time.date())

        logging.info(f"[BOOKING] SUCCESS: {request.customer_name} booked with {tech['name']} for {request.service_type} at {request.start_time}")

        return BookAppointmentResponse(
            success=True,
            appointment_id=appointment_id,
            technician=tech["name"],
            time=request.start_time.isoformat(),
            message=f"Appointment booked with {tech['name']}"
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"[BOOKING] ERROR: {e}")
        return BookAppointmentResponse(
            success=False,
            message=f"Failed to book appointment: {str(e)}"
        )


class CancelByPhoneRequest(BaseModel):
    phone_number: str
    cancellation_reason: str = None


@router.post("/cancel-appointment")
def cancel_appointment_by_phone(request: CancelByPhoneRequest, _auth=Depends(verify_retell_api_key)):
    from src.utils.db import get_db_connection
    from psycopg2.extras import RealDictCursor

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT id, customer_name, service_type, start_time, status
            FROM appointments
            WHERE customer_phone = %s AND status = 'scheduled'
            AND start_time > CURRENT_TIMESTAMP
            ORDER BY start_time ASC LIMIT 1
        """, (request.phone_number,))
        appt = cur.fetchone()

        if not appt:
            cur.execute("""
                SELECT id, customer_name, service_type, start_time, status
                FROM appointments_cache
                WHERE customer_phone = %s AND status IN ('scheduled', 'confirmed')
                AND start_time > CURRENT_TIMESTAMP
                ORDER BY start_time ASC LIMIT 1
            """, (request.phone_number,))
            appt = cur.fetchone()

        if not appt:
            return {"success": False, "message": "No upcoming appointment found for this phone number"}

        table = "appointments"
        cur.execute(f"""
            UPDATE {table} SET status = 'cancelled' WHERE id = %s
        """, (appt["id"],))
        conn.commit()

        return {
            "success": True,
            "message": f"Appointment for {appt['customer_name']} on {appt['start_time']} has been cancelled",
            "cancelled_appointment": {
                "customer_name": appt["customer_name"],
                "service_type": appt["service_type"],
                "start_time": str(appt["start_time"])
            }
        }
    except Exception as e:
        conn.rollback()
        return {"success": False, "message": f"Failed to cancel: {str(e)}"}
    finally:
        cur.close()
        conn.close()


class BookRedoRequest(BaseModel):
    order_id: str
    issue_description: str


@router.post("/book-redo-appointment")
def book_redo_appointment(request: BookRedoRequest, _auth=Depends(verify_retell_api_key)):
    from src.utils.db import get_db_connection
    from psycopg2.extras import RealDictCursor

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT a.id, a.customer_name, a.customer_phone, a.customer_email,
                   a.service_type, a.address, a.latitude, a.longitude,
                   a.technician_id, t.name as technician_name
            FROM appointments a
            LEFT JOIN technicians t ON t.id = a.technician_id
            WHERE a.customer_phone = %s OR CAST(a.id AS TEXT) = %s
            ORDER BY a.created_at DESC LIMIT 1
        """, (request.order_id, request.order_id))
        original = cur.fetchone()

        if not original:
            cur.execute("""
                SELECT id, customer_name, customer_phone, service_type,
                       address, latitude, longitude, technician_id
                FROM appointments_cache
                WHERE customer_phone = %s OR CAST(id AS TEXT) = %s
                ORDER BY created_at DESC LIMIT 1
            """, (request.order_id, request.order_id))
            original = cur.fetchone()

        if not original:
            return {"success": False, "message": "No previous appointment found with that ID or phone number"}

        redo_time = datetime.now() + timedelta(days=2)
        redo_time = redo_time.replace(hour=10, minute=0, second=0, microsecond=0)
        end_time = redo_time + timedelta(hours=1)

        cur.execute("""
            INSERT INTO appointments
            (calendar_event_id, technician_id, customer_name, customer_phone,
             customer_email, service_type, address, latitude, longitude,
             start_time, end_time, duration_minutes, status, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            str(uuid.uuid4()),
            original["technician_id"],
            original["customer_name"],
            original["customer_phone"],
            original.get("customer_email"),
            original["service_type"],
            original["address"],
            original.get("latitude"),
            original.get("longitude"),
            redo_time,
            end_time,
            60,
            "scheduled",
            f"REDO - {request.issue_description}"
        ))
        redo_appt = cur.fetchone()
        conn.commit()

        return {
            "success": True,
            "message": f"Redo appointment booked for {original['customer_name']} at {original['address']} on {redo_time.strftime('%B %d at %I:%M %p')}",
            "redo_appointment": {
                "id": redo_appt["id"],
                "customer_name": original["customer_name"],
                "address": original["address"],
                "service_type": original["service_type"],
                "date": redo_time.strftime("%B %d at %I:%M %p"),
                "technician": original.get("technician_name", "Same technician")
            }
        }
    except Exception as e:
        conn.rollback()
        return {"success": False, "message": f"Failed to book redo: {str(e)}"}
    finally:
        cur.close()
        conn.close()
