from fastapi import APIRouter
from src.utils.sync import sync_calendar_appointments, sync_technicians_from_ghl

router = APIRouter()


@router.post("/sync-appointments")
def manual_sync_appointments():
    result = sync_calendar_appointments()
    return {"status": "success", "data": result}


@router.post("/sync-technicians")
def manual_sync_technicians():
    result = sync_technicians_from_ghl()
    return {"status": "success", "data": result}


@router.post("/sync-all")
def sync_all():
    tech_result = sync_technicians_from_ghl()
    appt_result = sync_calendar_appointments()
    
    return {
        "status": "success",
        "data": {
            "technicians": tech_result,
            "appointments": appt_result
        }
    }
