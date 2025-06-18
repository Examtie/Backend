from fastapi import APIRouter, Depends
from app.models import MeReturn,UpdateProfile
from app.database import users_collection
from app.dependencies import get_current_user, require_roles, get_user_by_email

from app.settings import ALL_ROLES

router = APIRouter(
    prefix="/user/api/v1",
    tags=["User"]
)

@router.get("/@me", response_model=MeReturn)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return MeReturn(
        id=str(current_user["_id"]),
        email=current_user["email"],
        username=current_user["username"],
        full_name=current_user["full_name"],
        roles=current_user.get("roles", []),
        bio=current_user.get("bio", ""),
        profile_image=current_user.get("profile_image", "")
    )

@router.put("/@me", response_model=MeReturn)
async def update_profile(update: UpdateProfile, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in update.dict().items() if v is not None}
    if update_data:
        await users_collection.update_one({"_id": current_user["_id"]}, {"$set": update_data})
    updated_user = await get_user_by_email(current_user["email"])
    return MeReturn(
        id=str(updated_user["_id"]),
        email=updated_user["email"],
        username=updated_user["username"],
        full_name=updated_user.get("full_name", ""),
        roles=updated_user.get("roles", []),
        bio=updated_user.get("bio", ""),
        profile_image=updated_user.get("profile_image", "")
    )


@router.get("/dashboard")
async def dashboard(user: dict = Depends(require_roles(ALL_ROLES))):
    return {
        "message": f"Welcome {user.get('email')}!",
        "roles": user.get("roles", [])
    }