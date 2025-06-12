from motor.motor_asyncio import AsyncIOMotorClient
from .settings import MONGO_URI, DATABASE_NAME

client = AsyncIOMotorClient(MONGO_URI)
db = client[DATABASE_NAME]
users_collection = db.get_collection("users")
