from datetime import datetime, timedelta, timezone
from typing import Any, Optional
import sqlite3

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.app.config import settings
from backend.app.database import get_db

security_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt with automatic salt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(days=settings.refresh_token_expire_days)
    )
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str, expected_type: str = "access") -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type (expected {expected_type})",
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please authenticate again.",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
        )


def check_lockout(username: str, conn: sqlite3.Connection) -> tuple[bool, Optional[str]]:
    row = conn.execute(
        "SELECT failed_attempts, locked_until FROM login_attempts WHERE username = ?",
        (username,),
    ).fetchone()
    if not row:
        return False, None

    locked_until_str = row["locked_until"]
    if locked_until_str:
        locked_until = datetime.fromisoformat(locked_until_str)
        if datetime.now(timezone.utc) < locked_until:
            remaining_mins = int((locked_until - datetime.now(timezone.utc)).total_seconds() // 60) + 1
            return True, f"Account is temporarily locked due to repeated failed logins. Try again in {remaining_mins} minutes."
        else:
            # Lockout expired, reset
            conn.execute(
                "UPDATE login_attempts SET failed_attempts = 0, locked_until = NULL WHERE username = ?",
                (username,),
            )
            conn.commit()
    return False, None


def record_failed_attempt(username: str, conn: sqlite3.Connection) -> None:
    row = conn.execute(
        "SELECT failed_attempts FROM login_attempts WHERE username = ?",
        (username,),
    ).fetchone()
    now_utc = datetime.now(timezone.utc)

    if not row:
        conn.execute(
            "INSERT INTO login_attempts (username, failed_attempts, locked_until) VALUES (?, 1, NULL)",
            (username,),
        )
    else:
        new_attempts = row["failed_attempts"] + 1
        if new_attempts >= settings.max_login_attempts:
            lockout_expiry = (now_utc + timedelta(minutes=settings.lockout_duration_minutes)).isoformat()
            conn.execute(
                "UPDATE login_attempts SET failed_attempts = ?, locked_until = ? WHERE username = ?",
                (new_attempts, lockout_expiry, username),
            )
        else:
            conn.execute(
                "UPDATE login_attempts SET failed_attempts = ? WHERE username = ?",
                (new_attempts, username),
            )
    conn.commit()


def reset_failed_attempts(username: str, conn: sqlite3.Connection) -> None:
    conn.execute(
        "UPDATE login_attempts SET failed_attempts = 0, locked_until = NULL WHERE username = ?",
        (username,),
    )
    conn.commit()


def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> dict:
    if not auth or not auth.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(auth.credentials, expected_type="access")
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token claims",
        )

    with get_db() as conn:
        user = conn.execute(
            "SELECT id, username, role, display_name, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account no longer exists",
            )
        return dict(user)


def require_role(allowed_roles: list[str]):
    def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: requires one of {allowed_roles} roles",
            )
        return current_user

    return role_checker
