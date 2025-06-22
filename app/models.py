from typing import List, Optional, Literal
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime

from app.settings import ALL_ROLES

class UserIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str
    username: str = Field(min_length=3, max_length=30)
    roles: List[Literal["user", "admin", "staff"]] = ["user"]
    
    @field_validator("roles", mode="before")
    @classmethod
    def validate_roles(cls, v):
        if isinstance(v, list):
            for role in v:
                if role not in ALL_ROLES:
                    raise ValueError(f"Role '{role}' is not allowed. Choose from {ALL_ROLES}.")
        elif v not in ALL_ROLES:
            raise ValueError(f"Role '{v}' is not allowed. Choose from {ALL_ROLES}.")
        return v

class UserOut(BaseModel):
    id: Optional[str] = None
    email: EmailStr
    full_name: str
    username: str
    roles: List[str]
    bio: Optional[str] = ""
    profile_image: Optional[str] = ""
    token: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class MeReturn(BaseModel):
    id: Optional[str] = None
    email: EmailStr
    full_name: str
    username: str
    roles: List[str]
    bio: Optional[str] = ""
    profile_image: Optional[str] = ""

class TokenData(BaseModel):
    email: Optional[str] = None
    roles: List[Literal["user", "admin", "staff"]] = ["user"]

class UpdateProfile(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    profile_image: Optional[str] = None

class ExamFileCreate(BaseModel):
    title: str = Field(..., json_schema_extra={"example": "Midterm Physics"})
    description: str = Field(..., json_schema_extra={"example": "Grade 11 physics midterm"})
    tags: List[str] = Field(default_factory=list)

class ExamFileUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None

class ExamFileOut(BaseModel):
    id: str
    title: str
    description: str
    tags: List[str]
    url: str
    uploaded_by: str

class AdminUserOut(BaseModel):
    id: Optional[str] = None
    email: EmailStr
    full_name: str
    username: str
    roles: List[str]
    bio: Optional[str] = ""
    profile_image: Optional[str] = ""
    created_at: Optional[datetime] = None

class UpdateUserRole(BaseModel):
    role: Literal["user", "admin", "staff", "seller"]
    
    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        if v not in ALL_ROLES:
            raise ValueError(f"Role '{v}' is not allowed. Choose from {ALL_ROLES}.")
        return v
