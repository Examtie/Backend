from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from typing import List, Optional
from database import users_collection, system_settings_collection
from dependencies import require_roles
from models import UserOut
from datetime import datetime

from settings import ADMIN_ROLE
from models import UpdateProfile

router = APIRouter(
    prefix="/admin/api/v1",
    tags=["Admin"]
)

# Helper
def to_str_id(doc):
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return doc


# === USER MANAGEMENT ===

@router.get("/users", response_model=List[UserOut])
async def list_all_users(admin: dict = Depends(require_roles(ADMIN_ROLE))):
    users = []
    async for user in users_collection.find():
        users.append(UserOut(
            id=str(user["_id"]),
            email=user["email"],
            full_name=user.get("full_name", ""),
            username=user.get("username", ""),
            roles=user.get("roles", []),
            bio=user.get("bio", ""),
            profile_image=user.get("profile_image", "")
        ))
    return users


@router.patch("/users/{user_id}/role")
async def update_user_role(user_id: str, role: str, admin: dict = Depends(require_roles("admin"))):
    if role not in ["user", "admin", "staff"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    result = await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"roles": [role]}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User role updated"}


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, admin: dict = Depends(require_roles("admin"))):
    result = await users_collection.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}

@router.patch("/users/{user_id}")
async def edit_any_user_profile(user_id: str, update: UpdateProfile, admin: dict = Depends(require_roles("admin"))):
    update_data = {k: v for k, v in update.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")

    result = await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    updated_user = await users_collection.find_one({"_id": ObjectId(user_id)})
    return {
        "id": str(updated_user["_id"]),
        "email": updated_user["email"],
        "username": updated_user["username"],
        "full_name": updated_user.get("full_name", ""),
        "roles": updated_user.get("roles", []),
        "bio": updated_user.get("bio", ""),
        "profile_image": updated_user.get("profile_image", "")
    }

# === EXAM MANAGEMENT ===

# EMPTY

# === SYSTEM STATS ===

@router.get("/stats")
async def get_system_stats(admin: dict = Depends(require_roles("admin"))):
    user_count = await users_collection.count_documents({})
    exam_count = await exams_collection.count_documents({})
    return {
        "users": user_count,
        "exams": exam_count,
        "timestamp": datetime.utcnow()
    }
