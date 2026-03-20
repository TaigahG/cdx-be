from fastapi import APIRouter, Request, Response, HTTPException, status, Depends
from sqlalchemy.orm import Session
from jwt.exceptions import PyJWTError as JWTError
from datetime import datetime
import os

from database import get_db
from models import User
from redis_client import get_redis
from auth.jwt_utils import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    REFRESH_TOKEN_EXPIRE_DAYS,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from auth.magic_client import magic
from auth.dependencies import get_current_user

router = APIRouter()

# Cookie settings
IS_PRODUCTION = os.getenv("ENVIRONMENT") == "production"
COOKIE_SECURE = IS_PRODUCTION          # True in prod (HTTPS), False in dev
COOKIE_SAMESITE = "lax"
ACCESS_MAX_AGE = ACCESS_TOKEN_EXPIRE_MINUTES * 60          # 15 min in seconds
REFRESH_MAX_AGE = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60  # 7 days in seconds


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    """Helper to set both auth cookies with consistent settings"""
    response.set_cookie(
        key="accessToken",
        value=access_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=ACCESS_MAX_AGE,
    )
    response.set_cookie(
        key="refreshToken",
        value=refresh_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=REFRESH_MAX_AGE,
    )


def _clear_auth_cookies(response: Response):
    """Helper to clear both auth cookies"""
    response.delete_cookie("accessToken")
    response.delete_cookie("refreshToken")


@router.post("/login")
def login(request: Request, response: Response, db: Session = Depends(get_db)):
    """
    Validate Magic DID token, create/find user, issue JWT cookies.
    
    Flow:
    1. Frontend sends DID token in Authorization header
    2. We validate it with Magic Admin SDK
    3. Extract user identity (issuer = permanent user ID)
    4. Create user in DB if first login
    5. Mint access + refresh JWTs
    6. Store refresh token in Redis
    7. Set HttpOnly cookies
    """
    # --- Extract DID token from header ---
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header"
        )
    
    did_token = auth_header.split(" ")[1]
    
    try:
        # --- Validate DID token with Magic ---
        magic.Token.validate(did_token)
        
        # --- Extract user identity ---
        issuer = magic.Token.get_issuer(did_token)
        user_metadata = magic.User.get_metadata_by_issuer(issuer)
        
        email = user_metadata.data.get("email")
        public_address = user_metadata.data.get("public_address")
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Magic authentication failed: {str(e)}"
        )
    
    # --- Find or create user ---
    # Look up by email (works for both self-registered AND invited users)
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        # Brand new user — self-registration via Magic Link
        # No company, no role yet — they'll set that up after
        user = User(
            id=issuer,
            email=email,
            username=email.split("@")[0],
            first_name="",
            last_name="",
            wallet_address=public_address,
            is_active=True,
            joined_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Existing user — either returning or invited user's first login
        # Fill in wallet address if missing (invited user case)
        if not user.wallet_address and public_address:
            user.wallet_address = public_address
        # Mark invitation as accepted on first Magic login
        if user.invited_by and not user.invitation_accepted_at:
            user.invitation_accepted_at = datetime.utcnow()
        user.last_login = datetime.utcnow()
        db.commit()
    
    # --- Mint JWT tokens (use the DB user ID, not the issuer) ---
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    
    # --- Store refresh token in Redis ---
    r = get_redis()
    r.setex(
        f"refresh:{user.id}",
        REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,  # TTL in seconds
        refresh_token,
    )
    
    # --- Set cookies ---
    _set_auth_cookies(response, access_token, refresh_token)
    
    return {
        "message": "Login successful",
        "is_new_user": user.company_id is None,  # Frontend uses this to redirect to onboarding
    }


@router.post("/refresh")
def refresh(request: Request, response: Response):
    """
    Refresh the access token using the refresh token cookie.
    
    Flow:
    1. Read refresh token from cookie
    2. Verify JWT signature + expiry
    3. Check it matches what's stored in Redis (not revoked)
    4. Mint new access token
    5. Set new access token cookie
    """
    refresh_token = request.cookies.get("refreshToken")
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token"
        )
    
    try:
        payload = verify_refresh_token(refresh_token)
        user_id = payload.get("user_id")
    except JWTError:
        _clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # --- Verify against Redis (prevents use of revoked tokens) ---
    r = get_redis()
    stored_token = r.get(f"refresh:{user_id}")
    
    if not stored_token or stored_token != refresh_token:
        _clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token revoked or invalid"
        )
    
    # --- Mint new access token ---
    new_access_token = create_access_token(user_id)
    
    response.set_cookie(
        key="accessToken",
        value=new_access_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=ACCESS_MAX_AGE,
    )
    
    return {"message": "Access token refreshed"}


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    """
    Returns current user info. Protected by auth dependency.
    Also used by frontend to check if session is valid.
    """
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "wallet_address": current_user.wallet_address,
        "company_id": current_user.company_id,
        "role": current_user.role,
        "is_onboarded": current_user.company_id is not None,
    }


@router.delete("/logout")
def logout(request: Request, response: Response):
    """
    Logout: delete refresh token from Redis + clear cookies.
    
    Even if the token is invalid/expired, we still clear cookies.
    """
    refresh_token = request.cookies.get("refreshToken")
    
    if refresh_token:
        try:
            payload = verify_refresh_token(refresh_token)
            user_id = payload.get("user_id")
            
            # Delete from Redis
            r = get_redis()
            r.delete(f"refresh:{user_id}")
        except JWTError:
            pass  # Token invalid, but we still clear cookies
    
    _clear_auth_cookies(response)
    
    return {"message": "Logged out successfully"}


# ============================================================
# DEV ONLY — Remove before production deployment
# ============================================================

@router.post("/dev-login")
def dev_login(
    response: Response,
    email: str = "test@chaindox.com",
    db: Session = Depends(get_db),
):
    """
    DEV ONLY — Bypass Magic Link, create a test user and issue tokens.
    
    Use this to test the full auth flow from Swagger (/docs):
      1. POST /auth/dev-login → sets cookies
      2. GET  /auth/me         → returns user info
      3. POST /auth/refresh    → refreshes access token
      4. DELETE /auth/logout   → clears session
    
    Also test protected resource routes:
      5. GET /api/companies/   → should work with cookie
    """


    if os.getenv("ENVIRONMENT") == "production":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    
    user = db.query(User).filter(User.email == email).first()
    user_id = user.id if user else f"dev_{email.split('@')[0]}"

    
    if not user:
        user = User(
            id=user_id,
            email=email,
            username=email.split("@")[0],
            first_name="Dev",
            last_name="User",
            wallet_address=None,
            is_active=True,
            joined_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        user.last_login = datetime.utcnow()
        db.commit()
    
    # Mint tokens
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)

    # Store refresh token in Redis
    r = get_redis()
    r.setex(
        f"refresh:{user_id}",
        REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        refresh_token,
    )
    
    # Set cookies
    _set_auth_cookies(response, access_token, refresh_token)
    
    return {
        "message": "Dev login successful",
        "user_id": user_id,
        "email": email,
        "note": "REMOVE THIS ENDPOINT BEFORE PRODUCTION",
    }
