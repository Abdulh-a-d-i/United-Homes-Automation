from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from src.utils.db import create_tables
from src.api import appointments, technicians, webhooks
from src.api import auth as auth_router
from src.api import admin as admin_router
from src.api import calendar as calendar_router
from src.api import appointment_management


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


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
