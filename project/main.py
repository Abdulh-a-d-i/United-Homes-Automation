from fastapi import FastAPI
import uvicorn
from contextlib import asynccontextmanager
from src.utils.db import create_tables
from src.api import appointments, technicians, webhooks


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


app = FastAPI(title="AI Receptionist API", docs_url="/api/docs",lifespan=lifespan)

app.include_router(
    appointments.router,
    tags=["appointments"]
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


@app.get("/")
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
