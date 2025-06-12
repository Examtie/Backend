from fastapi import APIRouter, Depends, HTTPException
from database import users_collection, exams_collection
from dependencies import require_roles
from bson import ObjectId

from settings import ADMIN_ROLE

router = APIRouter(prefix="/admin", tags=[ADMIN_ROLE])

@router.get("/users")
async def get_all_users(admin=Depends(require_roles(ADMIN_ROLE))):
    users = []
    async for user in users_collection.find():
        user["_id"] = str(user["_id"])
        users.append(user)
    return users

@router.patch("/users/{user_id}")
async def update_user_role(user_id: str, role: str, admin=Depends(require_roles(ADMIN_ROLE))):
    result = await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"roles": [role]}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Role updated"}

@router.get("/stats")
async def get_stats(admin=Depends(require_roles(ADMIN_ROLE))):
    user_count = await users_collection.count_documents({})
    exam_count = await exams_collection.count_documents({})
    return {
        "users": user_count,
        "exams": exam_count
    }
