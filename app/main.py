from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime
from bson import ObjectId
from typing import List

from settings import ALL_ROLES

from models import UserIn, UserOut, Token, UpdateProfile
from database import users_collection
from auth import hash_password, verify_password, create_access_token
from dependencies import get_current_user, require_roles, get_user_by_email, get_user_by_username

app = FastAPI(title="FastAPI MongoDB Auth")

@app.post("/register", response_model=UserOut)
async def register(user_in: UserIn):
    if await get_user_by_email(user_in.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    if user_in.username and await get_user_by_username(user_in.username):
        raise HTTPException(status_code=400, detail="Username already taken")

    user_data = user_in.dict()
    user_data.update({
        "hashed_password": hash_password(user_data.pop("password")),
        "created_at": datetime.utcnow(),
        "bio": "New to Examtie!",
        "profile_image": "https://jwt.io/_next/image?url=%2F_next%2Fstatic%2Fmedia%2Fjwt-flower.f20616b0.png&w=3840&q=75"
    })

    result = await users_collection.insert_one(user_data)
    return UserOut(
        id=str(result.inserted_id),
        email=user_data["email"],
        username=user_data["username"],
        full_name=user_data["full_name"],
        roles=user_data["roles"],
        bio=user_data["bio"],
        profile_image=user_data["profile_image"]
    )

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await get_user_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.get("hashed_password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user["email"], "roles": user.get("roles", [])}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=UserOut)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return UserOut(
        id=str(current_user["_id"]),
        email=current_user["email"],
        username=current_user["username"],
        full_name=current_user["full_name"],
        roles=current_user.get("roles", []),
        bio=current_user.get("bio", ""),
        profile_image=current_user.get("profile_image", "")
    )

@app.put("/users/me", response_model=UserOut)
async def update_profile(update: UpdateProfile, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in update.dict().items() if v is not None}
    if update_data:
        await users_collection.update_one({"_id": current_user["_id"]}, {"$set": update_data})
    updated_user = await get_user_by_email(current_user["email"])
    return UserOut(
        id=str(updated_user["_id"]),
        email=updated_user["email"],
        username=updated_user["username"],
        full_name=updated_user.get("full_name", ""),
        roles=updated_user.get("roles", []),
        bio=updated_user.get("bio", ""),
        profile_image=updated_user.get("profile_image", "")
    )

@app.get("/admin/users", response_model=List[UserOut])
async def list_users(admin: dict = Depends(require_roles("admin"))):
    users = []
    async for u in users_collection.find():
        users.append(UserOut(
            id=str(u["_id"]),
            email=u["email"],
            username=u["username"],
            full_name=u.get("full_name", ""),
            roles=u.get("roles", []),
            bio=u.get("bio", ""),
            profile_image=u.get("profile_image", "")
        ))
    return users

@app.get("/dashboard")
async def dashboard(user: dict = Depends(require_roles(ALL_ROLES))):
    return {
        "message": f"Welcome {user.get('email')}!",
        "roles": user.get("roles", [])
    }

