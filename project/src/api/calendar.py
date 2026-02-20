import os
import logging
import traceback
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from google_auth_oauthlib.flow import Flow
from src.utils.auth import get_current_user
from src.utils.db import (
    get_technician_by_user_id,
    save_calendar_credentials,
    get_calendar_credentials,
    disconnect_calendar as db_disconnect
)
from src.services.google_calendar import GoogleCalendarService
from src.services.outlook_calendar import OutlookCalendarService
from dotenv import load_dotenv
import msal

load_dotenv()

router = APIRouter()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
GOOGLE_SCOPES = ["https://www.googleapis.com/auth/calendar"]

MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID")
MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET")
MICROSOFT_TENANT_ID = os.getenv("MICROSOFT_TENANT_ID", "common")
MICROSOFT_REDIRECT_URI = os.getenv("MICROSOFT_REDIRECT_URI")
MICROSOFT_SCOPES = ["Calendars.ReadWrite", "User.Read"]

_oauth_state_store = {}


@router.get("/google/connect")
async def google_connect(current_user: dict = Depends(get_current_user)):
    try:
        tech = get_technician_by_user_id(current_user["id"])
        if not tech:
            raise HTTPException(status_code=404, detail="No technician profile found")
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "redirect_uris": [GOOGLE_REDIRECT_URI],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
            },
            scopes=GOOGLE_SCOPES,
            redirect_uri=GOOGLE_REDIRECT_URI
        )
        auth_url, state = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent"
        )
        _oauth_state_store[state] = {
            "user_id": current_user["id"],
            "tech_id": tech["id"],
            "provider": "google"
        }
        return JSONResponse(
            status_code=200,
            content={"success": True, "auth_url": auth_url}
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Google connect error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to start Google OAuth")


@router.get("/google/callback")
async def google_callback(code: str = Query(...), state: str = Query(...)):
    try:
        state_data = _oauth_state_store.pop(state, None)
        if not state_data:
            raise HTTPException(status_code=400, detail="Invalid OAuth state")

        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "redirect_uris": [GOOGLE_REDIRECT_URI],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
            },
            scopes=GOOGLE_SCOPES,
            redirect_uri=GOOGLE_REDIRECT_URI
        )
        flow.fetch_token(code=code)
        credentials = flow.credentials

        calendar_email = ""
        try:
            from googleapiclient.discovery import build
            oauth2_service = build("oauth2", "v2", credentials=credentials)
            user_info = oauth2_service.userinfo().get().execute()
            calendar_email = user_info.get("email", "")
        except Exception:
            pass

        creds_dict = {
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_expiry": credentials.expiry.isoformat() if credentials.expiry else None,
            "scopes": list(credentials.scopes) if credentials.scopes else GOOGLE_SCOPES
        }
        save_calendar_credentials(state_data["tech_id"], "google", calendar_email, creds_dict)

        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        return RedirectResponse(url=f"{frontend_url}/settings?calendar=connected")
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Google callback error: {e}")
        traceback.print_exc()
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        return RedirectResponse(url=f"{frontend_url}/settings?calendar=error")


@router.get("/outlook/connect")
async def outlook_connect(current_user: dict = Depends(get_current_user)):
    try:
        tech = get_technician_by_user_id(current_user["id"])
        if not tech:
            raise HTTPException(status_code=404, detail="No technician profile found")
        app = msal.ConfidentialClientApplication(
            MICROSOFT_CLIENT_ID,
            authority=f"https://login.microsoftonline.com/{MICROSOFT_TENANT_ID}",
            client_credential=MICROSOFT_CLIENT_SECRET
        )
        import uuid
        state = str(uuid.uuid4())
        auth_url = app.get_authorization_request_url(
            MICROSOFT_SCOPES,
            redirect_uri=MICROSOFT_REDIRECT_URI,
            state=state
        )
        _oauth_state_store[state] = {
            "user_id": current_user["id"],
            "tech_id": tech["id"],
            "provider": "outlook"
        }
        return JSONResponse(
            status_code=200,
            content={"success": True, "auth_url": auth_url}
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Outlook connect error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to start Outlook OAuth")


@router.get("/outlook/callback")
async def outlook_callback(code: str = Query(...), state: str = Query(...)):
    try:
        state_data = _oauth_state_store.pop(state, None)
        if not state_data:
            raise HTTPException(status_code=400, detail="Invalid OAuth state")

        app = msal.ConfidentialClientApplication(
            MICROSOFT_CLIENT_ID,
            authority=f"https://login.microsoftonline.com/{MICROSOFT_TENANT_ID}",
            client_credential=MICROSOFT_CLIENT_SECRET
        )
        result = app.acquire_token_by_authorization_code(
            code,
            scopes=MICROSOFT_SCOPES,
            redirect_uri=MICROSOFT_REDIRECT_URI
        )
        if "access_token" not in result:
            raise HTTPException(status_code=400, detail="Failed to get token")

        calendar_email = ""
        try:
            import requests as req
            headers = {"Authorization": f"Bearer {result['access_token']}"}
            me = req.get("https://graph.microsoft.com/v1.0/me", headers=headers).json()
            calendar_email = me.get("mail", me.get("userPrincipalName", ""))
        except Exception:
            pass

        from datetime import timedelta, datetime, timezone
        creds_dict = {
            "access_token": result["access_token"],
            "refresh_token": result.get("refresh_token", ""),
            "token_expiry": (
                datetime.now(timezone.utc) + timedelta(seconds=result.get("expires_in", 3600))
            ).isoformat(),
            "scopes": MICROSOFT_SCOPES
        }
        save_calendar_credentials(state_data["tech_id"], "outlook", calendar_email, creds_dict)

        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        return RedirectResponse(url=f"{frontend_url}/settings?calendar=connected")
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Outlook callback error: {e}")
        traceback.print_exc()
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        return RedirectResponse(url=f"{frontend_url}/settings?calendar=error")


@router.post("/disconnect")
async def disconnect_calendar(current_user: dict = Depends(get_current_user)):
    try:
        tech = get_technician_by_user_id(current_user["id"])
        if not tech:
            raise HTTPException(status_code=404, detail="No technician profile found")
        db_disconnect(tech["id"])
        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "Calendar disconnected"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Disconnect error: {e}")
        raise HTTPException(status_code=500, detail="Failed to disconnect calendar")


@router.get("/status")
async def calendar_status(current_user: dict = Depends(get_current_user)):
    try:
        tech = get_technician_by_user_id(current_user["id"])
        if not tech:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "data": {"connected": False, "provider": None, "email": None}
                }
            )
        creds = get_calendar_credentials(tech["id"])
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "data": {
                    "connected": creds.get("calendar_connected", False) if creds else False,
                    "provider": creds.get("calendar_provider") if creds else None,
                    "email": creds.get("calendar_email") if creds else None
                }
            }
        )
    except Exception as e:
        logging.error(f"Calendar status error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get calendar status")


@router.get("/events")
async def list_calendar_events(
    days: int = Query(7, ge=1, le=90),
    current_user: dict = Depends(get_current_user)
):
    try:
        tech = get_technician_by_user_id(current_user["id"])
        if not tech:
            raise HTTPException(status_code=404, detail="No technician profile found")
        creds = get_calendar_credentials(tech["id"])
        if not creds or not creds.get("calendar_connected"):
            raise HTTPException(status_code=400, detail="No calendar connected")

        from datetime import datetime, timedelta
        now = datetime.utcnow()
        end = now + timedelta(days=days)

        provider = creds["calendar_provider"]
        credentials_dict = creds["calendar_credentials"]

        if provider == "google":
            service = GoogleCalendarService(credentials_dict)
        elif provider == "outlook":
            service = OutlookCalendarService(credentials_dict)
        else:
            raise HTTPException(status_code=400, detail="Unknown calendar provider")

        events = service.list_events(now, end)

        updated_creds = service.get_updated_credentials()
        save_calendar_credentials(tech["id"], provider, creds["calendar_email"], updated_creds)

        return JSONResponse(
            status_code=200,
            content={"success": True, "data": events}
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"List events error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Failed to fetch calendar events")
