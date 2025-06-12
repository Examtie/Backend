import os
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from passlib.context import CryptContext
from jose import JWTError, jwt
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

from typing import Literal
from pydantic import validator

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "myapp")
SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Initialize MongoDB client
client = AsyncIOMotorClient(MONGO_URI)
db = client[DATABASE_NAME]
users_collection = db.get_collection("users")

# Security utilities
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# Pydantic models
ALLOWED_ROLES = {"admin", "staff", "user"}

class UserIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str
    username: str = Field(min_length=3,max_length=30)
    roles: List[Literal["user", "admin", "staff"]] = ["user"]

    @validator("roles", pre=True, each_item=True)
    def validate_roles(cls, v):
        if v not in ALLOWED_ROLES:
            raise ValueError(f"Role '{v}' is not allowed. Choose from {ALLOWED_ROLES}.")
        return v

class UserOut(BaseModel):
    id: Optional[str] = None
    email: EmailStr
    full_name: str
    username: str
    roles: List[str]
    bio: Optional[str] = ""
    profile_image: Optional[str] = ""


class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    roles: List[Literal["user", "admin", "staff"]] = ["user"]
    

class UpdateProfile(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    profile_image: Optional[str] = None


# Utility functions

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_user_by_email(email: str) -> Optional[dict]:
    return await users_collection.find_one({"email": email})

async def authenticate_user(email: str, password: str) -> Optional[dict]:
    user = await get_user_by_email(email)
    if not user or not verify_password(password, user.get("hashed_password", "")):
        return None
    return user

# Dependency to get current user
async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        roles: List[str] = payload.get("roles", [])
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email, roles=roles)
    except JWTError:
        raise credentials_exception
    user = await get_user_by_email(token_data.email)
    if not user:
        raise credentials_exception
    return user

# Role-based access dependency



def require_roles(*roles: str):
    def checker(current_user: dict = Depends(get_current_user)) -> dict:
        user_roles = current_user.get("roles", [])
        if not any(role in user_roles for role in roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted"
            )
        return current_user
    return checker

async def get_user_by_username(username: str) -> Optional[dict]:
    return await users_collection.find_one({"username": username})

# Initialize FastAPI app
app = FastAPI(title="FastAPI MongoDB Auth")


@app.put("/users/me", response_model=UserOut)
async def update_profile(update: UpdateProfile, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in update.dict().items() if v is not None}

    if update_data:
        await users_collection.update_one(
            {"_id": current_user["_id"]},
            {"$set": update_data}
        )
    
    updated_user = await get_user_by_email(current_user["email"])
    return UserOut(
        id=str(updated_user["_id"]),
        email=updated_user["email"],
        full_name=updated_user.get("full_name", ""),
        username=updated_user["username"],
        roles=updated_user.get("roles", []),
        bio=updated_user.get("bio", ""),
        profile_image=updated_user.get("profile_image", "")
    )


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
        username=user_data.get("username"),
        full_name=user_data.get("full_name"),
        roles=user_data.get("roles", []),
        bio=user_data.get("bio", ""),
        profile_image=user_data.get("profile_image", "")
    )



@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
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
        id=str(current_user.get("_id")),
        email=current_user.get("email"),
        username=current_user.get("username"),
        full_name=current_user.get("full_name"),
        roles=current_user.get("roles", [])
    )

@app.get("/admin/users", response_model=List[UserOut])
async def list_users(admin: dict = Depends(require_roles("admin"))):
    users = []
    cursor = users_collection.find()
    async for u in cursor:
        users.append(
            UserOut(
                id=str(u.get("_id")),
                email=u.get("email"),
                full_name=u.get("full_name"),
                username=u.get("username"),
                roles=u.get("roles", [])
            )
        )
    return users

@app.get("/dashboard")
async def dashboard(user: dict = Depends(require_roles(ALLOWED_ROLES))):
    return {"message": f"Welcome {user.get('email')}!", "roles": user.get("roles", [])}

# Run with `python main.py`
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", port=8000, reload=True)
