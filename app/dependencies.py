from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from .settings import SECRET_KEY, ALGORITHM
from .models import TokenData
from .database import users_collection

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

async def get_user_by_email(email: str):
    return await users_collection.find_one({"email": email})

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        roles = payload.get("roles", [])
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email, roles=roles)
    except JWTError:
        raise credentials_exception

    user = await get_user_by_email(token_data.email)
    if not user:
        raise credentials_exception
    return user

def require_roles(*roles: str):
    async def checker(current_user: dict = Depends(get_current_user)):
        user_roles = current_user.get("roles", [])
        if not any(role in user_roles for role in roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted"
            )
        return current_user
    return checker
