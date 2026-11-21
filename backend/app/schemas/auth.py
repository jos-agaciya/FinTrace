from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=1, description="User password")


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, description="User full name")
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="User password (min 6 characters)")


class UserUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, description="Updated user full name")
    role: Optional[str] = Field(None, description="Updated user persona / role")


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str = "Retail Investor & Decision Analyst"
    initials: str = "FT"
    joinedDate: str = "November 2026"
    isActive: bool = True
    createdAt: Optional[str] = None
    stats: Dict[str, Any] = Field(default_factory=lambda: {
        "claimsAnalysed": 0,
        "reportsGenerated": 0,
        "independentScore": 75,
        "learningSessions": 0
    })

    model_config = {
        "from_attributes": True
    }


# Backward-compatible alias for existing imports
AuthUser = UserResponse


class AuthResponse(BaseModel):
    success: bool = True
    token: str
    token_type: str = "bearer"
    user: UserResponse
