import logging
import traceback
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from src.utils.auth import get_current_user, require_admin
from src.utils.db import (
    get_appointments_paginated,
    get_appointment_by_id,
    update_appointment_status as db_update_status,
    get_appointment_stats
)
from src.api.models import UpdateAppointmentStatus

router = APIRouter()


@router.get("/list")
async def list_appointments(
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


@router.get("/upcoming")
async def upcoming_appointments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    try:
        result = get_appointments_paginated(
            page=page,
            page_size=page_size,
            time_filter="upcoming"
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
            content={"success": True, "data": appointments_out,
                     "pagination": {"total": result["total"], "page": result["page"],
                                    "page_size": result["page_size"], "total_pages": result["total_pages"]}}
        )
    except Exception as e:
        logging.error(f"Upcoming appointments error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch appointments")


@router.get("/past")
async def past_appointments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    try:
        result = get_appointments_paginated(
            page=page,
            page_size=page_size,
            time_filter="past"
        )
        appointments_out = []
        for a in result["appointments"]:
            appointments_out.append({
                "id": a["id"],
                "technician_name": a.get("technician_name"),
                "customer_name": a["customer_name"],
                "service_type": a["service_type"],
                "start_time": str(a["start_time"]),
                "status": a["status"]
            })
        return JSONResponse(
            status_code=200,
            content={"success": True, "data": appointments_out,
                     "pagination": {"total": result["total"], "page": result["page"],
                                    "page_size": result["page_size"], "total_pages": result["total_pages"]}}
        )
    except Exception as e:
        logging.error(f"Past appointments error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch appointments")


@router.get("/stats")
async def appointment_stats(current_user: dict = Depends(require_admin)):
    try:
        stats = get_appointment_stats()
        return JSONResponse(
            status_code=200,
            content={"success": True, "data": stats}
        )
    except Exception as e:
        logging.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch stats")


@router.get("/{appointment_id}")
async def get_appointment(
    appointment_id: int,
    current_user: dict = Depends(get_current_user)
):
    try:
        appt = get_appointment_by_id(appointment_id)
        if not appt:
            raise HTTPException(status_code=404, detail="Appointment not found")
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


@router.put("/{appointment_id}/status")
async def update_status(
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


@router.post("/{appointment_id}/cancel")
async def cancel_appointment(
    appointment_id: int,
    current_user: dict = Depends(get_current_user)
):
    try:
        success = db_update_status(appointment_id, "cancelled")
        if not success:
            raise HTTPException(status_code=404, detail="Appointment not found")
        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "Appointment cancelled"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Cancel appointment error: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel appointment")
