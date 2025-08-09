import os
from dotenv import load_dotenv

# Load environment variables from the Backend directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "myapp")

REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_DB = os.getenv("REDIS_DB", "0")
# Redis connection URL. If REDIS_URL is not provided, default to a local instance.
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
CACHE_EXPIRE_SECONDS = int(os.getenv("CACHE_EXPIRE_SECONDS", 3600))

SECRET_KEY = os.getenv("SECRET_KEY", "niga56")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES_SECONDS", 43200)) # 30 days (30 * 24 * 60 minutes)

STREAK_TTL_SECONDS = int(os.getenv("STREAK_TTL_SECONDS", 60 * 60 * 24 * 60))  # 60 days default

TPYTHON_API_KEY = os.getenv("TPYTHON_API_KEY", "sk-niga")

Azure_API_KEY = os.getenv("AZURE_API_KEY", "sk-niga")
Azure_Endpoint = os.getenv("AZURE_ENDPOINT", "https://azure.cognitiveservices.azure.com/")
Azure_API_Version = os.getenv("AZURE_API_VERSION", "2024-12-01-preview")
Azure_Model = os.getenv("AZURE_MODE", "examtieai")

ADMIN_ROLE = "admin"
USER_ROLE = "user"
STAFF_ROLE = "staff"
SELLER_ROLE = "seller"


ALL_ROLES = [ADMIN_ROLE, USER_ROLE, STAFF_ROLE, SELLER_ROLE]

# Temporary bootstrap admin (created on startup if no admin exists)
BOOTSTRAP_ADMIN_EMAIL = os.getenv("BOOTSTRAP_ADMIN_EMAIL", "admin@example.com")
BOOTSTRAP_ADMIN_USERNAME = os.getenv("BOOTSTRAP_ADMIN_USERNAME", "admin")
BOOTSTRAP_ADMIN_FULLNAME = os.getenv("BOOTSTRAP_ADMIN_FULLNAME", "Administrator")
BOOTSTRAP_ADMIN_PASSWORD = os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "ChangeMe123!")
