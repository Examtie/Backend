import os
from dotenv import load_dotenv

# Load environment variables from the Backend directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "myapp")

REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_DB = os.getenv("REDIS_DB", "0")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

SECRET_KEY = os.getenv("SECRET_KEY", "niga56")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 43200 # 30 days (30 * 24 * 60 minutes)

ADMIN_ROLE = "admin"
USER_ROLE = "user"
STAFF_ROLE = "staff"
SELLER_ROLE = "seller"

if REDIS_PASSWORD:
    REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_URL}/{REDIS_DB}"
else:
    REDIS_URL = f"redis://{REDIS_URL}/{REDIS_DB}"
    
ALL_ROLES = [ADMIN_ROLE, USER_ROLE, STAFF_ROLE, SELLER_ROLE]