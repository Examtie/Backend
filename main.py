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
class UserIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: Optional[str] = None
    roles: List[str] = ["user"]

class UserOut(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str] = None
    roles: List[str] = []

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    roles: List[str] = []

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

# Initialize FastAPI app
app = FastAPI(title="FastAPI MongoDB Auth")

@app.post("/register", response_model=UserOut)
async def register(user_in: UserIn):
    if await get_user_by_email(user_in.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    user_data = user_in.dict()
    user_data.update({
        "hashed_password": hash_password(user_data.pop("password")),
        "created_at": datetime.utcnow()
    })
    result = await users_collection.insert_one(user_data)
    return UserOut(
        id=str(result.inserted_id),
        email=user_data["email"],
        full_name=user_data.get("full_name"),
        roles=user_data.get("roles", [])
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
                roles=u.get("roles", [])
            )
        )
    return users

@app.get("/dashboard")
async def dashboard(user: dict = Depends(require_roles("user", "admin"))):
    return {"message": f"Welcome {user.get('email')}!", "roles": user.get("roles", [])}

# Run with `python main.py`
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
