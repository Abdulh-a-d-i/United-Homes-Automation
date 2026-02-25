from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.utils.db import create_tables
from src.api import appointments, technicians, webhooks
from src.api import auth as auth_router
from src.api import admin as admin_router
from src.api import calendar as calendar_router
from src.api import appointment_management
from src.api import retell_webhooks
from src.api import call_logs
import os
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def send_daily_schedules():
    """Send each technician their next-day schedule at 6 PM ET."""
    from src.utils.db import get_all_technicians, get_appointments_paginated
    from src.utils.mail_service import send_technician_daily_schedule

    eastern = ZoneInfo("America/New_York")
    now = datetime.now(eastern)
    tomorrow = (now + timedelta(days=1)).date()
    tomorrow_start = datetime.combine(tomorrow, datetime.min.time())
    tomorrow_end = datetime.combine(tomorrow, datetime.max.time())
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    schedule_url = f"{frontend_url}/schedule"

    techs = get_all_technicians()
    logging.info(f"Sending daily schedules to {len(techs)} technicians for {tomorrow}")

    for tech in techs:
        if not tech.get("email"):
            continue
        try:
            result = get_appointments_paginated(
                page=1,
                page_size=50,
                technician_id=tech["id"],
                date_from=str(tomorrow_start),
                date_to=str(tomorrow_end),
                time_filter="upcoming"
            )
            appt_list = []
            for a in result["appointments"]:
                appt_list.append({
                    "start_time": str(a["start_time"]).split(" ")[1][:5] if " " in str(a["start_time"]) else str(a["start_time"]),
                    "end_time": str(a["end_time"]).split(" ")[1][:5] if " " in str(a["end_time"]) else str(a["end_time"]),
                    "service_type": a["service_type"],
                    "customer_name": a["customer_name"],
                    "customer_phone": a.get("customer_phone", ""),
                    "address": a.get("address", "")
                })

            send_technician_daily_schedule(
                tech_email=tech["email"],
                tech_name=tech["name"],
                schedule_date=str(tomorrow),
                appointments=appt_list,
                schedule_url=schedule_url
            )
            logging.info(f"Schedule sent to {tech['name']} ({tech['email']}): {len(appt_list)} appointments")
        except Exception as e:
            logging.error(f"Failed to send schedule to {tech['name']}: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()

    # Start daily schedule email scheduler (6 PM ET)
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        send_daily_schedules,
        CronTrigger(hour=18, minute=0, timezone=ZoneInfo("America/New_York")),
        id="daily_schedule_email",
        name="Send technician daily schedules at 6 PM ET",
        replace_existing=True
    )
    scheduler.start()
    logging.info("Scheduler started: daily schedule emails at 6 PM ET")

    yield

    scheduler.shutdown()



app = FastAPI(title="United Home Services API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    auth_router.router,
    prefix="/api/auth",
    tags=["auth"]
)

app.include_router(
    admin_router.router,
    prefix="/api/admin",
    tags=["admin"]
)

app.include_router(
    calendar_router.router,
    prefix="/api/calendar",
    tags=["calendar"]
)

app.include_router(
    appointment_management.router,
    prefix="/api/appointment-management",
    tags=["appointment-management"]
)

app.include_router(
    appointments.router,
    prefix="/api/appointments",
    tags=["appointments"]
)

app.include_router(
    technicians.router,
    prefix="/api/technicians",
    tags=["technicians"]
)

app.include_router(
    webhooks.router,
    prefix="/api/webhooks",
    tags=["webhooks"]
)

app.include_router(
    retell_webhooks.router,
    prefix="/api/webhooks",
    tags=["retell-webhooks"]
)

app.include_router(
    call_logs.router,
    prefix="/api/call-logs",
    tags=["call-logs"]
)

# GHL sync router commented out
# from src.api import sync
# app.include_router(
#     sync.router,
#     prefix="/api/sync",
#     tags=["sync"]
# )


@app.get("/")
def health_check():
    return {"status": "ok"}
