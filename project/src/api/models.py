from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime


class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_admin: bool = False
    created_at: Optional[datetime] = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class CreateUserRequest(BaseModel):
    email: EmailStr
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    skills: Optional[List[str]] = None


class UpdateUserRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    skills: Optional[List[str]] = None


class AppointmentOut(BaseModel):
    id: int
    calendar_event_id: Optional[str] = None
    technician_id: int
    technician_name: Optional[str] = None
    customer_name: str
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    service_type: str
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    start_time: datetime
    end_time: datetime
    duration_minutes: Optional[int] = 60
    status: str = "scheduled"
    notes: Optional[str] = None
    created_at: Optional[datetime] = None


class UpdateAppointmentStatus(BaseModel):
    status: str = Field(..., pattern="^(scheduled|completed|cancelled|no_show)$")


class CalendarConnectionStatus(BaseModel):
    connected: bool = False
    provider: Optional[str] = None
    email: Optional[str] = None


class UserDetailOut(BaseModel):
    id: int
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    is_admin: bool = False
    skills: Optional[List[str]] = None
    calendar: CalendarConnectionStatus = CalendarConnectionStatus()
    created_at: Optional[datetime] = None
