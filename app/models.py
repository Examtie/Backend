from typing import List, Optional, Literal
from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime

from app.settings import ALL_ROLES

class UserIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str
    username: str = Field(min_length=3, max_length=30)
    roles: List[Literal["user", "admin", "staff"]] = ["user"]

    @validator("roles", pre=True, each_item=True)
    def validate_roles(cls, v):
        if v not in ALL_ROLES:
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
    token: str

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

    @validator("role")
    def validate_role(cls, v):
        if v not in ALL_ROLES:
            raise ValueError(f"Role '{v}' is not allowed. Choose from {ALL_ROLES}.")
        return v
