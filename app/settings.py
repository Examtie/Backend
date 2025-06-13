import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "myapp")
SECRET_KEY = os.getenv("SECRET_KEY", "niga56")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 # 1 hour

ADMIN_ROLE = "admin"
USER_ROLE = "user"
STAFF_ROLE = "staff"
SELLER_ROLE = "seller"

ALL_ROLES = [ADMIN_ROLE, USER_ROLE, STAFF_ROLE, SELLER_ROLE]