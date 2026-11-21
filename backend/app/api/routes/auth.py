from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import hash_password, verify_password, create_access_token
from backend.app.models.user import UserModel
from backend.app.repositories.user_repository import UserRepository
from backend.app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    UserUpdateRequest,
    AuthResponse,
    UserResponse
)
from backend.app.api.deps import get_current_user, get_current_user_optional

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _extract_initials(name: str) -> str:
    """Derive uppercase 1-2 character initials from user's full name."""
    if not name:
        return "FT"
    parts = name.strip().split()
    if len(parts) >= 2:
        return f"{parts[0][0]}{parts[-1][0]}".upper()
    elif parts:
        return parts[0][:2].upper()
    return "FT"


def _user_to_response(user: UserModel) -> UserResponse:
    """Format UserModel to public UserResponse, strictly omitting sensitive fields."""
    claims_count = len(user.claims) if user.claims else 0
    decisions_count = len(user.decisions) if user.decisions else 0
    joined_date = user.created_at.strftime("%B %Y") if user.created_at else "November 2026"
    created_at_iso = user.created_at.isoformat() if user.created_at else None

    return UserResponse(
        id=user.id,
        name=user.full_name,
        email=user.email,
        role=user.role or "Retail Investor & Decision Analyst",
        initials=_extract_initials(user.full_name),
        joinedDate=joined_date,
        isActive=user.is_active,
        createdAt=created_at_iso,
        stats={
            "claimsAnalysed": claims_count,
            "reportsGenerated": claims_count,
            "independentScore": 75 + min(decisions_count * 2, 20),
            "learningSessions": decisions_count
        }
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(reg: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user account with secure password hashing and persistence."""
    cleaned_name = reg.name.strip()
    cleaned_email = reg.email.strip().lower()

    if not cleaned_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name cannot be empty"
        )
    if not cleaned_email or "@" not in cleaned_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A valid email address is required"
        )
    if len(reg.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long"
        )

    user_repo = UserRepository(db)
    existing_user = user_repo.get_by_email(cleaned_email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email address already exists"
        )

    hashed_pw = hash_password(reg.password)
    new_user = user_repo.create(
        full_name=cleaned_name,
        email=cleaned_email,
        hashed_password=hashed_pw
    )

    token = create_access_token(user_id=new_user.id, email=new_user.email)
    return AuthResponse(
        success=True,
        token=token,
        token_type="bearer",
        user=_user_to_response(new_user)
    )


@router.post("/login", response_model=AuthResponse)
def login(creds: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate existing user with email and password, returning a signed JWT bearer token."""
    cleaned_email = creds.email.strip().lower()

    if not cleaned_email or not creds.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and password are required"
        )

    user_repo = UserRepository(db)
    user = user_repo.get_by_email(cleaned_email)

    if not user or not verify_password(creds.password, user.hashed_password):
        # Generic error message to prevent user enumeration
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive. Please contact support.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = create_access_token(user_id=user.id, email=user.email)
    return AuthResponse(
        success=True,
        token=token,
        token_type="bearer",
        user=_user_to_response(user)
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(user: UserModel = Depends(get_current_user)):
    """Retrieve currently authenticated user's persistent profile from SQLite."""
    return _user_to_response(user)


@router.put("/me", response_model=UserResponse)
def update_current_user_profile(
    update_data: UserUpdateRequest,
    user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update currently authenticated user's persistent profile in SQLite."""
    user_repo = UserRepository(db)
    if update_data.name:
        user.full_name = update_data.name.strip()
    if update_data.role:
        user.role = update_data.role.strip()
    user_repo.update(user)
    return _user_to_response(user)


@router.post("/logout")
def logout(current_user: Optional[UserModel] = Depends(get_current_user_optional)):
    """Stateless logout endpoint: instructs client to remove token from local storage."""
    return {
        "success": True,
        "message": "Successfully logged out. Please discard authorization token from client storage."
    }
