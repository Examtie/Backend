from motor.motor_asyncio import AsyncIOMotorClient
from app.settings import MONGO_URI, DATABASE_NAME

client = AsyncIOMotorClient(MONGO_URI)
db = client[DATABASE_NAME]

users_collection = db.get_collection("users")
system_settings_collection = db.get_collection("system_settings")