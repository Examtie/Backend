from fastapi import FastAPI, Depends

from settings import ALL_ROLES

from models import UserOut,UpdateProfile
from database import users_collection
from dependencies import get_current_user, require_roles, get_user_by_email

app = FastAPI(title="Examtie Backend API", version="1.0.0", description="Project NSC")

## ROUTER ##
from admin import router as admin_router
from authention import router as auth_router
from user import router as user_router

app.include_router(admin_router)
app.include_router(auth_router)
app.include_router(user_router)
############

@app.get("/")
async def landing_api():
    return {"niga56":"Server Running by Hamster!!"}