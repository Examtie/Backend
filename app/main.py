from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.settings import ALL_ROLES

from app.models import UserOut,UpdateProfile
from app.database import users_collection
from app.dependencies import get_current_user, require_roles, get_user_by_email

app = FastAPI(title="Examtie Backend API", version="1.0.0", description="Project NSC")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

## ROUTER ##
from app.admin import router as admin_router
from app.authention import router as auth_router
from app.user import router as user_router

app.include_router(admin_router)
app.include_router(auth_router)
app.include_router(user_router)
############

@app.get("/")
async def landing_api():
    return {"niga56":"Server Running by Hamster!!"}