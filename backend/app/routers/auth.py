from datetime import datetime, timezone
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models.schemas import TokenResponse, UserLoginRequest, UserPublic, UserRegisterRequest
from backend.app.security import (
    check_lockout,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    hash_password,
    record_failed_attempt,
    reset_failed_attempts,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register_patient(payload: UserRegisterRequest):
    """Patient self-registration endpoint with bcrypt hashing."""
    with get_db() as conn:
        existing = conn.execute("SELECT id FROM users WHERE username = ?", (payload.username,)).fetchone()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This username is already taken. Please select another.",
            )

        now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password_hash, role, display_name, created_at) VALUES (?, ?, 'patient', ?, ?)",
            (payload.username, hash_password(payload.password), payload.display_name, now_iso),
        )
        conn.commit()
        user_id = cursor.lastrowid
        row = conn.execute("SELECT id, username, role, display_name, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row)


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLoginRequest, response: Response):
    """
    Authenticate user, enforce brute-force lockout, return in-memory access token,
    and set httpOnly Secure refresh token cookie.
    """
    username = payload.username.strip()
    with get_db() as conn:
        is_locked, lock_msg = check_lockout(username, conn)
        if is_locked:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=lock_msg)

        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if not user or not verify_password(payload.password, user["password_hash"]):
            record_failed_attempt(username, conn)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password.",
            )

        # Successful login, reset failed attempts
        reset_failed_attempts(username, conn)

        token_claims = {
            "sub": str(user["id"]),
            "username": user["username"],
            "role": user["role"],
            "display_name": user["display_name"],
        }
        access_token = create_access_token(token_claims)
        refresh_token = create_refresh_token(token_claims)

        # Set refresh token in httpOnly, Secure cookie
        response.set_cookie(
            key="carelens_refresh_token",
            value=refresh_token,
            httponly=True,
            secure=settings.cookie_secure,
            samesite=settings.cookie_samesite,
            max_age=settings.refresh_token_expire_days * 86400,
            path="/",
        )

        user_public = UserPublic(
            id=user["id"],
            username=user["username"],
            role=user["role"],
            display_name=user["display_name"],
            created_at=user["created_at"],
        )
        return TokenResponse(access_token=access_token, token_type="bearer", user=user_public)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token_endpoint(
    response: Response,
    carelens_refresh_token: str = Cookie(None),
):
    """Silent token refresh using httpOnly refresh cookie."""
    if not carelens_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing from cookie.",
        )

    payload = decode_token(carelens_refresh_token, expected_type="refresh")
    user_id = payload.get("sub")

    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        token_claims = {
            "sub": str(user["id"]),
            "username": user["username"],
            "role": user["role"],
            "display_name": user["display_name"],
        }
        new_access_token = create_access_token(token_claims)
        new_refresh_token = create_refresh_token(token_claims)

        response.set_cookie(
            key="carelens_refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=settings.cookie_secure,
            samesite=settings.cookie_samesite,
            max_age=settings.refresh_token_expire_days * 86400,
            path="/",
        )

        user_public = UserPublic(
            id=user["id"],
            username=user["username"],
            role=user["role"],
            display_name=user["display_name"],
            created_at=user["created_at"],
        )
        return TokenResponse(access_token=new_access_token, token_type="bearer", user=user_public)


@router.post("/logout")
def logout(response: Response):
    """Clear refresh cookie on logout."""
    response.delete_cookie(key="carelens_refresh_token", path="/")
    return {"message": "Successfully logged out."}


@router.get("/me", response_model=UserPublic)
def get_me(current_user: dict = Depends(get_current_user)):
    """Fetch current authenticated user profile."""
    return UserPublic(**current_user)
