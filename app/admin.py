from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from typing import List, Optional
from app.database import users_collection, system_settings_collection
from app.dependencies import require_roles
from app.models import AdminUserOut, UpdateProfile, UpdateUserRole
from datetime import datetime
from fastapi import Query
from pydantic import BaseModel

from app.settings import ADMIN_ROLE, ALL_ROLES

# Bulk operation models
class BulkRoleUpdate(BaseModel):
    user_ids: List[str]
    role: str

class BulkDeleteRequest(BaseModel):
    user_ids: List[str]

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

@router.get("/users", response_model=List[AdminUserOut])
async def list_all_users(
    admin: dict = Depends(require_roles(ADMIN_ROLE)),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Number of users per page"),
    search: Optional[str] = Query(None, description="Search by email, username, or full name"),
    role: Optional[str] = Query(None, description="Filter by role")
):
    skip = (page - 1) * limit
    
    # Build query
    query = {}
    if search:
        query["$or"] = [
            {"email": {"$regex": search, "$options": "i"}},
            {"username": {"$regex": search, "$options": "i"}},
            {"full_name": {"$regex": search, "$options": "i"}}
        ]
    
    if role and role in ALL_ROLES:
        query["roles"] = {"$in": [role]}
    
    users = []
    cursor = users_collection.find(query).skip(skip).limit(limit).sort("created_at", -1)
    async for user in cursor:
        users.append(AdminUserOut(
            id=str(user["_id"]),
            email=user["email"],
            full_name=user.get("full_name", ""),
            username=user.get("username", ""),
            roles=user.get("roles", []),
            bio=user.get("bio", ""),
            profile_image=user.get("profile_image", ""),
            created_at=user.get("created_at")
        ))
    return users


@router.patch("/users/{user_id}/role")
async def update_user_role(user_id: str, role_update: UpdateUserRole, admin: dict = Depends(require_roles(ADMIN_ROLE))):
    # Validate role
    if role_update.role not in ALL_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {ALL_ROLES}")
    
    try:
        # Check if user exists first
        user = await users_collection.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update user role
        result = await users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"roles": [role_update.role]}}
        )
        
        return {
            "message": "User role updated successfully",
            "user_id": user_id,
            "new_role": role_update.role,
            "previous_roles": user.get("roles", [])
        }
    except Exception as e:
        if "Invalid ObjectId" in str(e):
            raise HTTPException(status_code=400, detail="Invalid user ID format")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, admin: dict = Depends(require_roles(ADMIN_ROLE))):
    try:
        result = await users_collection.delete_one({"_id": ObjectId(user_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        return {"message": "User deleted successfully"}
    except Exception as e:
        if "Invalid ObjectId" in str(e):
            raise HTTPException(status_code=400, detail="Invalid user ID format")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.patch("/users/{user_id}")
async def edit_any_user_profile(user_id: str, update: UpdateProfile, admin: dict = Depends(require_roles(ADMIN_ROLE))):
    update_data = {k: v for k, v in update.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")

    try:
        result = await users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")

        updated_user = await users_collection.find_one({"_id": ObjectId(user_id)})
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found after update")
            
        return {
            "id": str(updated_user["_id"]),
            "email": updated_user["email"],
            "username": updated_user["username"],
            "full_name": updated_user.get("full_name", ""),
            "roles": updated_user.get("roles", []),
            "bio": updated_user.get("bio", ""),
            "profile_image": updated_user.get("profile_image", "")
        }
    except Exception as e:
        if "Invalid ObjectId" in str(e):
            raise HTTPException(status_code=400, detail="Invalid user ID format")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/users/@data")
async def get_user_detail(
    user_id: Optional[str] = Query(None),
    username: Optional[str] = Query(None),
    admin: dict = Depends(require_roles(ADMIN_ROLE))
):
    if not user_id and not username:
        raise HTTPException(status_code=400, detail="Provide either 'user_id' or 'username'")

    query = {}
    if user_id:
        try:
            query["_id"] = ObjectId(user_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid user_id format")
    elif username:
        query["username"] = username

    user = await users_collection.find_one(query)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "username": user["username"],
        "full_name": user.get("full_name", ""),
        "roles": user.get("roles", []),
        "bio": user.get("bio", ""),
        "profile_image": user.get("profile_image", ""),
        "created_at": user.get("created_at")
    }

# === EXAM MANAGEMENT ===

# EMPTY

# === SYSTEM STATS ===

@router.get("/stats")
async def get_system_stats(admin: dict = Depends(require_roles(ADMIN_ROLE))):
    # Get total user count
    user_count = await users_collection.count_documents({})
    
    # Get user count by role
    role_stats = {}
    for role in ALL_ROLES:
        count = await users_collection.count_documents({"roles": {"$in": [role]}})
        role_stats[role] = count
    
    # TODO: Add exam_count when exams collection is implemented
    return {
        "users": {
            "total": user_count,
            "by_role": role_stats
        },
        "exams": 0,  # Placeholder until exams collection is implemented
        "timestamp": datetime.utcnow()
    }

@router.patch("/users/bulk/role")
async def bulk_update_user_roles(
    bulk_update: BulkRoleUpdate, 
    admin: dict = Depends(require_roles(ADMIN_ROLE))
):
    """Bulk update roles for multiple users"""
    if bulk_update.role not in ALL_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {ALL_ROLES}")
    
    if len(bulk_update.user_ids) > 50:  # Limit bulk operations
        raise HTTPException(status_code=400, detail="Cannot update more than 50 users at once")
    
    try:
        # Convert string IDs to ObjectIds
        object_ids = []
        for user_id in bulk_update.user_ids:
            try:
                object_ids.append(ObjectId(user_id))
            except Exception:
                raise HTTPException(status_code=400, detail=f"Invalid user ID format: {user_id}")
        
        # Bulk update
        result = await users_collection.update_many(
            {"_id": {"$in": object_ids}},
            {"$set": {"roles": [bulk_update.role]}}
        )
        
        return {
            "message": f"Successfully updated {result.modified_count} users",
            "requested_count": len(bulk_update.user_ids),
            "updated_count": result.modified_count,
            "new_role": bulk_update.role
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Bulk update error: {str(e)}")  # For debugging
        raise HTTPException(status_code=500, detail=f"Bulk update failed: {str(e)}")

@router.delete("/users/bulk")
async def bulk_delete_users(
    delete_request: BulkDeleteRequest,
    admin: dict = Depends(require_roles(ADMIN_ROLE))
):
    """Bulk delete multiple users"""
    if len(delete_request.user_ids) > 20:  # Limit bulk deletions for safety
        raise HTTPException(status_code=400, detail="Cannot delete more than 20 users at once")
    
    try:
        # Convert string IDs to ObjectIds
        object_ids = []
        for user_id in delete_request.user_ids:
            try:
                object_ids.append(ObjectId(user_id))
            except Exception:
                raise HTTPException(status_code=400, detail=f"Invalid user ID format: {user_id}")
        
        # Bulk delete
        result = await users_collection.delete_many({"_id": {"$in": object_ids}})
        
        return {
            "message": f"Successfully deleted {result.deleted_count} users",
            "requested_count": len(delete_request.user_ids),
            "deleted_count": result.deleted_count
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Bulk delete error: {str(e)}")  # For debugging
        raise HTTPException(status_code=500, detail=f"Bulk delete failed: {str(e)}")
