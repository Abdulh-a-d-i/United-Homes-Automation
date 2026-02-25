"""Authentication API -- login, password reset, profile."""
import os
import logging
import traceback

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from src.utils.jwt_utils import (
    create_access_token,
    create_password_reset_token,
    verify_password_reset_token,
)
from src.utils.auth import get_current_user
from src.utils.db import login_user, update_user_password
from src.api.models import (
    UserRegister,
    UserLogin,
    UserOut,
    LoginResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)

router = APIRouter()


@router.post("/register")
async def register(user: UserRegister):
    """
    Registration is disabled. Users are created by admins only
    via /api/admin/users/create.
    """
    raise HTTPException(
        status_code=403,
        detail="Self-registration is disabled. Contact your administrator."
    )


@router.post("/login", response_model=LoginResponse)
async def login(user: UserLogin):
    try:
        db_user = login_user({
            "email": user.email.lower().strip(),
            "password": user.password
        })
        if db_user == "deactivated":
            raise HTTPException(status_code=403, detail="Account is deactivated. Contact admin.")
        if not db_user:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        token = create_access_token({"user_id": db_user["id"]})

        return LoginResponse(
            access_token=token,
            user=UserOut(
                id=db_user["id"],
                username=db_user["username"],
                email=db_user["email"],
                first_name=db_user.get("first_name"),
                last_name=db_user.get("last_name"),
                is_admin=db_user.get("is_admin", False),
                created_at=db_user.get("created_at")
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Login error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Login failed")


@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    try:
        token = create_password_reset_token(request.email)
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        reset_link = f"{frontend_url}/reset-password?token={token}"

        from src.utils.mail_service import send_password_reset_email
        send_password_reset_email(request.email, reset_link)

        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "Password reset email sent"}
        )
    except Exception as e:
        logging.error(f"Forgot password error: {e}")
        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "Password reset email sent"}
        )


@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    try:
        email = verify_password_reset_token(request.token)
        if not email:
            raise HTTPException(status_code=400, detail="Invalid or expired token")

        update_user_password(email, request.new_password)

        return JSONResponse(
            status_code=200,
            content={"success": True, "message": "Password reset successful"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Reset password error: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Password reset failed")


@router.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "data": {
                "id": current_user["id"],
                "username": current_user["username"],
                "email": current_user["email"],
                "first_name": current_user.get("first_name"),
                "last_name": current_user.get("last_name"),
                "phone": current_user.get("phone"),
                "is_admin": current_user.get("is_admin", False),
                "created_at": str(current_user.get("created_at", ""))
            }
        }
    )
