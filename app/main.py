from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.settings import ALL_ROLES, REDIS_URL, BOOTSTRAP_ADMIN_EMAIL, BOOTSTRAP_ADMIN_USERNAME, BOOTSTRAP_ADMIN_FULLNAME, BOOTSTRAP_ADMIN_PASSWORD
from app.models import UserOut, UpdateProfile, Token
from app.database import users_collection
from app.dependencies import get_current_user, require_roles, get_user_by_email
from app.auth import verify_password, create_access_token, hash_password

app = FastAPI(
    title="Examtie Backend API", 
    version="1.0.0", 
    description="Project NSC",
    root_path="/api",
    swagger_ui_oauth2_redirect_url="/docs/oauth2-redirect",
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": True,
    }
)

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
from app.market import router as market_router
from app.public import router as public_router
from app.aix import router as ai_router
from app.mock_api import router as mock_exam_router

import logging
from app.database import client as mongo_client, redis_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("startup")

# ------------
# STARTUP EVENTS
# ------------

@app.on_event("startup")
async def check_backend_dependencies():
    """Verify MongoDB and Redis connections on startup and log the results."""
    # MongoDB
    try:
        await mongo_client.admin.command("ping")
        logger.info("✅ MongoDB connection successful")
    except Exception as exc:
        logger.exception("❌ MongoDB connection failed: %s", exc)

    # Redis
    try:
        await redis_client.ping()
        logger.info("✅ Redis connection successful")
    except Exception as exc:
        logger.exception(f"❌ Redis connection failed {REDIS_URL}: %s", exc)

    # Ensure there is at least one admin user; if not, create a temporary one
    try:
        from app.database import users_collection
        admin_exists = await users_collection.find_one({"roles": {"$in": ["admin"]}})
        if not admin_exists:
            # Also check by email to avoid duplicates if roles changed
            existing = await users_collection.find_one({"email": BOOTSTRAP_ADMIN_EMAIL})
            if existing and "admin" not in existing.get("roles", []):
                await users_collection.update_one({"_id": existing["_id"]}, {"$addToSet": {"roles": "admin"}})
                logger.info("✅ Promoted existing bootstrap admin email to admin role: %s", BOOTSTRAP_ADMIN_EMAIL)
            elif not existing:
                doc = {
                    "email": BOOTSTRAP_ADMIN_EMAIL,
                    "username": BOOTSTRAP_ADMIN_USERNAME,
                    "full_name": BOOTSTRAP_ADMIN_FULLNAME,
                    "hashed_password": hash_password(BOOTSTRAP_ADMIN_PASSWORD),
                    "roles": ["admin"],
                    "bio": "Temporary admin account (set env to customize)",
                    "profile_image": "https://jwt.io/_next/image?url=%2F_next%2Fstatic%2Fmedia%2Fjwt-flower.f20616b0.png&w=3840&q=75",
                    "created_at": __import__("datetime").datetime.utcnow(),
                }
                await users_collection.insert_one(doc)
                logger.info("✅ Created bootstrap admin account: %s / username: %s", BOOTSTRAP_ADMIN_EMAIL, BOOTSTRAP_ADMIN_USERNAME)
        else:
            logger.info("✅ Admin user already exists; bootstrap admin not needed")
    except Exception as exc:
        logger.exception("❌ Failed to ensure bootstrap admin: %s", exc)

# ------------
# APP ROUTERS
# ------------

app.include_router(admin_router)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(market_router)
app.include_router(public_router)
app.include_router(ai_router)
app.include_router(mock_exam_router)

@app.post("/token", response_model=Token, tags=["Authentication"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token endpoint for authentication.
    Use this endpoint to authenticate and get an access token for the API.
    """
    user = await get_user_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.get("hashed_password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user["email"], "roles": user.get("roles", [])}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/")
async def landing_api():
    return {"message": "Examtie Backend API - Server is running", "status": "ok", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring and CI/CD"""
    try:
        # Test database connection
        await users_collection.count_documents({}, limit=1)
        return {
            "status": "healthy",
            "message": "API is running and database is connected",
            "version": "1.0.0",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": "Database connection failed",
            "error": str(e),
            "version": "1.0.0",
            "database": "disconnected"
        }