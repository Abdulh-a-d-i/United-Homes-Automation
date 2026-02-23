import logging
import traceback
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from src.utils.auth import get_current_user, require_admin
from src.utils.db import (
    get_appointments_paginated,
    get_appointment_by_id,
    update_appointment_status as db_update_status,
    get_appointment_stats,
    create_appointment as db_create_appointment,
    get_technician_by_user_id
)
from src.api.models import UpdateAppointmentStatus, CreateAppointmentRequest

router = APIRouter()


# ============================================================
# ADMIN ENDPOINTS
# ============================================================

@router.get("/admin/list")
async def admin_list_appointments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    technician_id: int = Query(None),
    status: str = Query(None),
    date_from: str = Query(None),
    date_to: str = Query(None),
    search: str = Query(None),
    time_filter: str = Query(None),
    current_user: dict = Depends(require_admin)
):
    try:
        result = get_appointments_paginated(
            page=page,
            page_size=page_size,
            technician_id=technician_id,
            status_filter=status,
            date_from=date_from,
            date_to=date_to,
            search=search,
            time_filter=time_filter
        )
        appointments_out = []
        for a in result["appointments"]:
            appointments_out.append({
                "id": a["id"],
                "calendar_event_id": a.get("calendar_event_id"),
                "technician_id": a["technician_id"],
                "technician_name": a.get("technician_name"),
                "customer_name": a["customer_name"],
                "customer_phone": a.get("customer_phone"),
                "customer_email": a.get("customer_email"),
                "service_type": a["service_type"],
                "address": a.get("address"),
                "start_time": str(a["start_time"]),
                "end_time": str(a["end_time"]),
                "duration_minutes": a.get("duration_minutes"),
                "status": a["status"],
                "notes": a.get("notes"),
                "created_at": str(a.get("created_at", ""))
            })
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": appointments_out,
                "pagination": {
                    "total": result["total"],
                    "page": result["page"],
                    "page_size": result["page_size"],
                    "total_pages": result["total_pages"]
                }
            }
        )
    except Exception as e:
        logging.error(f"List appointments error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to fetch appointments")


@router.get("/admin/stats")
async def admin_appointment_stats(current_user: dict = Depends(require_admin)):
    try:
        stats = get_appointment_stats()
        return JSONResponse(
            status_code=200,
            content={"success": True, "data": stats}
        )
    except Exception as e:
        logging.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch stats")


@router.put("/admin/{appointment_id}/status")
async def admin_update_status(
    appointment_id: int,
    request: UpdateAppointmentStatus,
    current_user: dict = Depends(require_admin)
):
    try:
        success = db_update_status(appointment_id, request.status)
        if not success:
            raise HTTPException(status_code=404, detail="Appointment not found")

        if request.status == "cancelled":
            try:
                appt = get_appointment_by_id(appointment_id)
                if appt and appt.get("customer_email"):
                    from src.utils.mail_service import send_cancellation_email
                    send_cancellation_email(
                        customer_email=appt["customer_email"],
                        customer_name=appt["customer_name"],
                        service_type=appt["service_type"],
                        start_time=str(appt["start_time"])
                    )
            except Exception as mail_err:
                logging.error(f"Cancellation email failed: {mail_err}")

        return JSONResponse(
            status_code=200,
            content={"success": True, "message": f"Appointment status updated to {request.status}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Update status error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update status")


# ============================================================
# USER ENDPOINTS (technician's own appointments)
# ============================================================

@router.get("/my/upcoming")
async def my_upcoming_appointments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    try:
        tech = get_technician_by_user_id(current_user["id"])
        tech_id = tech["id"] if tech else None

        result = get_appointments_paginated(
            page=page,
            page_size=page_size,
            technician_id=tech_id,
            time_filter="upcoming"
        )
        appointments_out = []
        for a in result["appointments"]:
            appointments_out.append({
                "id": a["id"],
                "technician_name": a.get("technician_name"),
                "customer_name": a["customer_name"],
                "customer_phone": a.get("customer_phone"),
                "customer_email": a.get("customer_email"),
                "service_type": a["service_type"],
                "address": a.get("address"),
                "start_time": str(a["start_time"]),
                "end_time": str(a["end_time"]),
                "status": a["status"],
                "notes": a.get("notes")
            })
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": appointments_out,
                "pagination": {
                    "total": result["total"],
                    "page": result["page"],
                    "page_size": result["page_size"],
                    "total_pages": result["total_pages"]
                }
            }
        )
    except Exception as e:
        logging.error(f"My upcoming appointments error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch appointments")


@router.get("/my/past")
async def my_past_appointments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    try:
        tech = get_technician_by_user_id(current_user["id"])
        tech_id = tech["id"] if tech else None

        result = get_appointments_paginated(
            page=page,
            page_size=page_size,
            technician_id=tech_id,
            time_filter="past"
        )
        appointments_out = []
        for a in result["appointments"]:
            appointments_out.append({
                "id": a["id"],
                "technician_name": a.get("technician_name"),
                "customer_name": a["customer_name"],
                "service_type": a["service_type"],
                "address": a.get("address"),
                "start_time": str(a["start_time"]),
                "end_time": str(a["end_time"]),
                "status": a["status"]
            })
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": appointments_out,
                "pagination": {
                    "total": result["total"],
                    "page": result["page"],
                    "page_size": result["page_size"],
                    "total_pages": result["total_pages"]
                }
            }
        )
    except Exception as e:
        logging.error(f"My past appointments error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch appointments")


@router.post("/my/create")
async def my_create_appointment(
    request: CreateAppointmentRequest,
    current_user: dict = Depends(get_current_user)
):
    try:
        tech = get_technician_by_user_id(current_user["id"])
        if not tech:
            raise HTTPException(status_code=400, detail="No technician profile found")

        from src.utils.radar import geocode_address
        geo_result = geocode_address(request.address)
        latitude = geo_result["latitude"] if geo_result else None
        longitude = geo_result["longitude"] if geo_result else None

        start_time = datetime.fromisoformat(request.start_time)
        end_time = start_time + timedelta(minutes=request.duration_minutes)

        appt = db_create_appointment({
            "technician_id": tech["id"],
            "customer_name": request.customer_name,
            "customer_phone": request.customer_phone,
            "customer_email": request.customer_email,
            "service_type": request.service_type,
            "address": request.address,
            "latitude": latitude,
            "longitude": longitude,
            "start_time": start_time,
            "end_time": end_time,
            "duration_minutes": request.duration_minutes,
            "status": "scheduled",
            "notes": request.notes
        })

        if not appt:
            raise HTTPException(status_code=500, detail="Failed to create appointment")

        try:
            if request.customer_email:
                from src.utils.mail_service import send_booking_confirmation
                send_booking_confirmation(
                    customer_email=request.customer_email,
                    customer_name=request.customer_name,
                    technician_name=tech["name"],
                    service_type=request.service_type,
                    start_time=str(start_time),
                    address=request.address
                )
            from src.utils.mail_service import send_admin_booking_notification
            send_admin_booking_notification(
                customer_name=request.customer_name,
                technician_name=tech["name"],
                service_type=request.service_type,
                start_time=str(start_time),
                address=request.address
            )
        except Exception as mail_err:
            logging.error(f"Booking email failed: {mail_err}")

        return JSONResponse(
            status_code=201,
            content={
                "success": True,
                "message": "Appointment created",
                "data": {
                    "id": appt["id"],
                    "technician_name": tech["name"],
                    "customer_name": request.customer_name,
                    "service_type": request.service_type,
                    "start_time": str(start_time),
                    "end_time": str(end_time),
                    "status": "scheduled"
                }
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Create appointment error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to create appointment")


@router.post("/my/{appointment_id}/cancel")
async def my_cancel_appointment(
    appointment_id: int,
    current_user: dict = Depends(get_current_user)
):
    try:
        appt = get_appointment_by_id(appointment_id)
        if not appt:
            raise HTTPException(status_code=404, detail="Appointment not found")

        tech = get_technician_by_user_id(current_user["id"])
        if not tech or appt["technician_id"] != tech["id"]:
            raise HTTPException(status_code=403, detail="Not your appointment")

        success = db_update_status(appointment_id, "cancelled")
        if not success:
            raise HTTPException(status_code=500, detail="Failed to cancel")

        try:
            if appt.get("customer_email"):
                from src.utils.mail_service import send_cancellation_email
                send_cancellation_email(
                    customer_email=appt["customer_email"],
                    customer_name=appt["customer_name"],
                    service_type=appt["service_type"],
                    start_time=str(appt["start_time"])
                )
        except Exception as mail_err:
            logging.error(f"Cancellation email failed: {mail_err}")

        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "Appointment cancelled"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Cancel appointment error: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel appointment")


# ============================================================
# SHARED ENDPOINTS (both admin and user can access)
# ============================================================

@router.get("/{appointment_id}")
async def get_appointment_detail(
    appointment_id: int,
    current_user: dict = Depends(get_current_user)
):
    try:
        appt = get_appointment_by_id(appointment_id)
        if not appt:
            raise HTTPException(status_code=404, detail="Appointment not found")

        if not current_user.get("is_admin"):
            tech = get_technician_by_user_id(current_user["id"])
            if not tech or appt["technician_id"] != tech["id"]:
                raise HTTPException(status_code=403, detail="Access denied")

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "id": appt["id"],
                    "calendar_event_id": appt.get("calendar_event_id"),
                    "technician_id": appt["technician_id"],
                    "technician_name": appt.get("technician_name"),
                    "customer_name": appt["customer_name"],
                    "customer_phone": appt.get("customer_phone"),
                    "customer_email": appt.get("customer_email"),
                    "service_type": appt["service_type"],
                    "address": appt.get("address"),
                    "latitude": float(appt["latitude"]) if appt.get("latitude") else None,
                    "longitude": float(appt["longitude"]) if appt.get("longitude") else None,
                    "start_time": str(appt["start_time"]),
                    "end_time": str(appt["end_time"]),
                    "duration_minutes": appt.get("duration_minutes"),
                    "status": appt["status"],
                    "notes": appt.get("notes"),
                    "created_at": str(appt.get("created_at", ""))
                }
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Get appointment error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch appointment")
