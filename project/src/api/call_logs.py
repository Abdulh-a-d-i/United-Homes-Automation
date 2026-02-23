import logging
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from src.utils.auth import require_admin
from src.utils.db import (
    get_call_logs_paginated,
    get_call_log_by_call_id,
    get_call_stats
)

router = APIRouter()


@router.get("/list")
async def list_call_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    direction: str = Query(None),
    call_status: str = Query(None),
    date_from: str = Query(None),
    date_to: str = Query(None),
    search: str = Query(None),
    current_user: dict = Depends(require_admin)
):
    try:
        result = get_call_logs_paginated(
            page=page,
            page_size=page_size,
            direction=direction,
            call_status=call_status,
            date_from=date_from,
            date_to=date_to,
            search=search
        )
        logs_out = []
        for log in result["logs"]:
            duration = log.get("duration_seconds") or 0
            mins = duration // 60
            secs = duration % 60

            customer_name = None
            dv = log.get("dynamic_variables")
            if dv and isinstance(dv, dict):
                customer_name = dv.get("customer_name")

            logs_out.append({
                "id": log["id"],
                "call_id": log["call_id"],
                "agent_id": log.get("agent_id"),
                "direction": log.get("direction"),
                "from_number": log.get("from_number"),
                "to_number": log.get("to_number"),
                "call_status": log.get("call_status"),
                "disconnection_reason": log.get("disconnection_reason"),
                "duration_seconds": duration,
                "duration_display": f"{mins}m {secs}s",
                "recording_url": log.get("recording_url"),
                "has_transcript": bool(log.get("transcript")),
                "has_analysis": bool(log.get("call_analysis")),
                "customer_name": customer_name,
                "created_at": str(log.get("created_at", ""))
            })
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": logs_out,
                "pagination": {
                    "total": result["total"],
                    "page": result["page"],
                    "page_size": result["page_size"],
                    "total_pages": result["total_pages"]
                }
            }
        )
    except Exception as e:
        logging.error(f"List call logs error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch call logs")


@router.get("/stats")
async def call_log_stats(current_user: dict = Depends(require_admin)):
    try:
        stats = get_call_stats()
        stats_out = {}
        for k, v in stats.items():
            if isinstance(v, Decimal):
                stats_out[k] = round(float(v), 1)
            elif isinstance(v, float):
                stats_out[k] = round(v, 1)
            elif isinstance(v, int):
                stats_out[k] = v
            else:
                stats_out[k] = str(v) if v is not None else 0
        return JSONResponse(
            status_code=200,
            content={"success": True, "data": stats_out}
        )
    except Exception as e:
        logging.error(f"Call stats error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch call stats")


@router.get("/{call_id}")
async def get_call_detail(
    call_id: str,
    current_user: dict = Depends(require_admin)
):
    try:
        log = get_call_log_by_call_id(call_id)
        if not log:
            raise HTTPException(status_code=404, detail="Call log not found")

        duration = log.get("duration_seconds") or 0
        mins = duration // 60
        secs = duration % 60

        customer_name = None
        dv = log.get("dynamic_variables")
        if dv and isinstance(dv, dict):
            customer_name = dv.get("customer_name")

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "id": log["id"],
                    "call_id": log["call_id"],
                    "agent_id": log.get("agent_id"),
                    "call_type": log.get("call_type"),
                    "direction": log.get("direction"),
                    "from_number": log.get("from_number"),
                    "to_number": log.get("to_number"),
                    "call_status": log.get("call_status"),
                    "disconnection_reason": log.get("disconnection_reason"),
                    "duration_seconds": duration,
                    "duration_display": f"{mins}m {secs}s",
                    "recording_url": log.get("recording_url"),
                    "transcript": log.get("transcript"),
                    "transcript_object": log.get("transcript_object"),
                    "call_analysis": log.get("call_analysis"),
                    "customer_name": customer_name,
                    "metadata": log.get("metadata"),
                    "created_at": str(log.get("created_at", ""))
                }
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Get call detail error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch call detail")
