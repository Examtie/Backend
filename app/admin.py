from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from bson import ObjectId
from typing import List, Optional
from app.database import users_collection, system_settings_collection, exam_files_collection
from app.dependencies import get_current_user, require_roles
from app.models import UserOut, ExamFileCreate, ExamFileUpdate, ExamFileOut, UpdateProfile, AdminUserOut, UpdateUserRole
from app.storage.r2_client import upload_to_r2
from datetime import datetime
from app.settings import ADMIN_ROLE, ALL_ROLES

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
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by email, username, or full name"),
    role: Optional[str] = Query(None, description="Filter by role")
):
    # Build query
    query = {}
    if search:
        query["$or"] = [
            {"email": {"$regex": search, "$options": "i"}},
            {"username": {"$regex": search, "$options": "i"}},
            {"full_name": {"$regex": search, "$options": "i"}}
        ]
    if role and role in ALL_ROLES:
        query["roles"] = role
    
    # Calculate skip
    skip = (page - 1) * limit
    
    users = []
    async for user in users_collection.find(query).skip(skip).limit(limit):
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

@router.get("/users/@data", response_model=AdminUserOut)
async def get_user_detail(
    admin: dict = Depends(require_roles(ADMIN_ROLE)),
    user_id: Optional[str] = Query(None, description="User ID"),
    username: Optional[str] = Query(None, description="Username")
):
    if not user_id and not username:
        raise HTTPException(status_code=400, detail="Either user_id or username must be provided")
    
    query = {}
    if user_id:
        try:
            query["_id"] = ObjectId(user_id)
        except:
            raise HTTPException(status_code=400, detail="Invalid user ID format")
    elif username:
        query["email"] = username  # Using email as username in login
    
    user = await users_collection.find_one(query)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return AdminUserOut(
        id=str(user["_id"]),
        email=user["email"],
        full_name=user.get("full_name", ""),
        username=user.get("username", ""),
        roles=user.get("roles", []),
        bio=user.get("bio", ""),        profile_image=user.get("profile_image", ""),
        created_at=user.get("created_at")
    )

@router.patch("/users/bulk/role")
async def bulk_update_user_roles(
    bulk_data: dict,
    admin: dict = Depends(require_roles(ADMIN_ROLE))
):
    user_ids = bulk_data.get("user_ids", [])
    role = bulk_data.get("role")
    
    if not user_ids:
        raise HTTPException(status_code=400, detail="user_ids is required")
    if not role or role not in ALL_ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {ALL_ROLES}")
    if len(user_ids) > 50:
        raise HTTPException(status_code=400, detail="Cannot update more than 50 users at once")
    
    try:
        object_ids = [ObjectId(uid) for uid in user_ids]
        result = await users_collection.update_many(
            {"_id": {"$in": object_ids}},
            {"$set": {"roles": [role]}}
        )
        return {
            "message": f"Successfully updated {result.modified_count} users",
            "updated_count": result.modified_count
        }
    except Exception as e:
        print(f"Bulk update error: {str(e)}")
        print(f"User IDs: {user_ids}")
        print(f"Role: {role}")
        raise HTTPException(status_code=500, detail=f"Failed to update user roles: {str(e)}")

@router.delete("/users/bulk")
async def bulk_delete_users(
    bulk_data: dict,
    admin: dict = Depends(require_roles(ADMIN_ROLE))
):
    user_ids = bulk_data.get("user_ids", [])
    
    if not user_ids:
        raise HTTPException(status_code=400, detail="user_ids is required")
    if len(user_ids) > 50:
        raise HTTPException(status_code=400, detail="Cannot delete more than 50 users at once")
    
    try:
        object_ids = [ObjectId(uid) for uid in user_ids]
        result = await users_collection.delete_many({"_id": {"$in": object_ids}})
        return {
            "message": f"Successfully deleted {result.deleted_count} users",
            "deleted_count": result.deleted_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to delete users")

@router.patch("/users/{user_id}/role")
async def update_user_role(
    user_id: str, 
    role_update: UpdateUserRole, 
    admin: dict = Depends(require_roles(ADMIN_ROLE))
):
    try:
        result = await users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"roles": [role_update.role]}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        return {"message": "User role updated successfully"}
    except Exception as e:
        if "invalid" in str(e).lower():
            raise HTTPException(status_code=400, detail="Invalid user ID format")
        raise HTTPException(status_code=500, detail="Failed to update user role")

@router.delete("/users/{user_id}")
async def delete_user(user_id: str, admin: dict = Depends(require_roles(ADMIN_ROLE))):
    try:
        result = await users_collection.delete_one({"_id": ObjectId(user_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        return {"message": "User deleted successfully"}
    except Exception as e:
        if "invalid" in str(e).lower():
            raise HTTPException(status_code=400, detail="Invalid user ID format")
        raise HTTPException(status_code=500, detail="Failed to delete user")

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
        return AdminUserOut(
            id=str(updated_user["_id"]),
            email=updated_user["email"],
            username=updated_user["username"],
            full_name=updated_user.get("full_name", ""),
            roles=updated_user.get("roles", []),
            bio=updated_user.get("bio", ""),
            profile_image=updated_user.get("profile_image", ""),
            created_at=updated_user.get("created_at")
        )
    except Exception as e:
        if "invalid" in str(e).lower():
            raise HTTPException(status_code=400, detail="Invalid user ID format")
        raise HTTPException(status_code=500, detail="Failed to update user profile")

# === EXAM MANAGEMENT ===

@router.post("/upload", response_model=ExamFileOut)
async def upload_exam_file(
    file: UploadFile = File(...),
    meta: ExamFileCreate = Depends(),
    admin=Depends(require_roles(ADMIN_ROLE)),
    current_user=Depends(get_current_user)
):
    file_url = await upload_to_r2(file)

    record = {
        "title": meta.title,
        "description": meta.description,
        "tags": meta.tags,
        "url": file_url,
        "uploaded_by": current_user["email"],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    result = await exam_files_collection.insert_one(record)
    record["id"] = str(result.inserted_id)
    record["url"] = file_url
    return ExamFileOut(**{**record, "id": str(result.inserted_id)})

@router.put("/exam-files/{file_id}", response_model=ExamFileOut)
async def update_exam_file(
    file_id: str,
    update_data: ExamFileUpdate,
    admin=Depends(require_roles(ADMIN_ROLE))
):
    update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
    if not update_dict:
        raise HTTPException(status_code=400, detail="No data provided")

    update_dict["updated_at"] = datetime.utcnow()
    try:
        result = await exam_files_collection.update_one(
            {"_id": ObjectId(file_id)},
            {"$set": update_dict}
        )

        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="File not found")

        updated = await exam_files_collection.find_one({"_id": ObjectId(file_id)})
        return ExamFileOut(
            id=str(updated["_id"]),
            title=updated["title"],
            description=updated["description"],
            tags=updated["tags"],
            url=updated["url"],
            uploaded_by=updated["uploaded_by"]
        )
    except Exception as e:
        if "invalid" in str(e).lower():
            raise HTTPException(status_code=400, detail="Invalid file ID format")
        raise HTTPException(status_code=500, detail="Failed to update exam file")

@router.get("/exam-files", response_model=List[ExamFileOut])
async def list_exam_files(
    admin: dict = Depends(require_roles(ADMIN_ROLE)),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page")
):
    skip = (page - 1) * limit
    files = []
    async for file_doc in exam_files_collection.find().skip(skip).limit(limit):
        files.append(ExamFileOut(
            id=str(file_doc["_id"]),
            title=file_doc["title"],
            description=file_doc["description"],
            tags=file_doc.get("tags", []),
            url=file_doc["url"],
            uploaded_by=file_doc["uploaded_by"]
        ))
    return files

@router.delete("/exam-files/{file_id}")
async def delete_exam_file(
    file_id: str,
    admin: dict = Depends(require_roles(ADMIN_ROLE))
):
    try:
        result = await exam_files_collection.delete_one({"_id": ObjectId(file_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="File not found")
        return {"message": "Exam file deleted successfully"}
    except Exception as e:
        if "invalid" in str(e).lower():
            raise HTTPException(status_code=400, detail="Invalid file ID format")
        raise HTTPException(status_code=500, detail="Failed to delete exam file")

# === SYSTEM STATS ===

@router.get("/stats")
async def get_system_stats(admin: dict = Depends(require_roles(ADMIN_ROLE))):
    user_count = await users_collection.count_documents({})
    exam_count = await exam_files_collection.count_documents({})
    
    # Get user counts by role
    user_roles_stats = {}
    for role in ALL_ROLES:
        count = await users_collection.count_documents({"roles": role})
        user_roles_stats[role] = count
    
    return {
        "users": {
            "total": user_count,
            "by_role": user_roles_stats
        },
        "exams": exam_count,
        "timestamp": datetime.utcnow()
    }
