import os
import logging
import traceback
import hmac
import hashlib
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from src.utils.db import upsert_call_log
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

RETELL_API_KEY = os.getenv("RETELL_API_KEY", "")


def verify_retell_signature(payload_bytes: bytes, signature: str) -> bool:
    if not RETELL_API_KEY or not signature:
        return False
    computed = hmac.new(
        RETELL_API_KEY.encode("utf-8"),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(computed, signature)


@router.post("/retell")
async def retell_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("x-retell-signature", "")

    if RETELL_API_KEY and signature:
        if not verify_retell_signature(body, signature):
            logging.warning("Invalid Retell webhook signature")
            raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event = payload.get("event")
    call = payload.get("call", {})

    if not event or not call.get("call_id"):
        return JSONResponse(status_code=204, content=None)

    logging.info(f"Retell webhook: {event} for call {call.get('call_id')}")

    call_data = {
        "call_id": call.get("call_id"),
        "agent_id": call.get("agent_id"),
        "call_type": call.get("call_type"),
        "direction": call.get("direction"),
        "from_number": call.get("from_number"),
        "to_number": call.get("to_number"),
        "call_status": call.get("call_status"),
        "disconnection_reason": call.get("disconnection_reason"),
        "start_timestamp": call.get("start_timestamp"),
        "end_timestamp": call.get("end_timestamp"),
        "recording_url": call.get("recording_url"),
        "transcript": call.get("transcript"),
        "transcript_object": call.get("transcript_object"),
        "metadata": call.get("metadata"),
        "retell_llm_dynamic_variables": call.get("retell_llm_dynamic_variables")
    }

    if event == "call_analyzed":
        call_data["call_analysis"] = call.get("call_analysis")

    try:
        upsert_call_log(call_data)
    except Exception as e:
        logging.error(f"Failed to store call log: {e}")
        traceback.print_exc()

    return JSONResponse(status_code=204, content=None)
