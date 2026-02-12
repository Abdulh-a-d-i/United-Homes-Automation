from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.utils.db import create_tables
from src.api import appointments, technicians, webhooks


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


app = FastAPI(title="AI Receptionist API", lifespan=lifespan)


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


@app.get("/")
def health_check():
    return {"status": "ok"}
