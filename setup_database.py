#!/usr/bin/env python3
"""
Database Setup Script for Examtie Backend
This script initializes the MongoDB database with necessary collections and creates the default admin user.
"""
import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.auth import hash_password
from app.database import (
    users_collection, 
    system_settings_collection,
    exam_files_collection,
    exam_categories_collection,
    bookmarks_collection,
    exam_questions_collection,
    exam_submissions_collection,
    market_items_collection,
    quizzes_collection,
    quiz_answers_collection,
    client as mongo_client,
    redis_client
)

async def test_connections():
    """Test database connections"""
    print("🔍 Testing database connections...")
    
    # Test MongoDB
    try:
        await mongo_client.admin.command("ping")
        print("✅ MongoDB connection successful")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return False
    
    # Test Redis
    try:
        await redis_client.ping()
        print("✅ Redis connection successful")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False
    
    return True

async def create_admin_user():
    """Create the default admin user if it doesn't exist"""
    print("👤 Setting up admin user...")
    
    admin_email = "admin@admin.com"
    admin_password = "admin@admin.com"
    
    # Check if admin user already exists
    existing_admin = await users_collection.find_one({"email": admin_email})
    if existing_admin:
        print(f"✅ Admin user already exists: {admin_email}")
        return
    
    # Create admin user
    admin_user = {
        "email": admin_email,
        "username": "admin",
        "full_name": "System Administrator",
        "hashed_password": hash_password(admin_password),
        "roles": ["admin"],
        "bio": "System Administrator",
        "profile_image": "https://jwt.io/_next/image?url=%2F_next%2Fstatic%2Fmedia%2Fjwt-flower.f20616b0.png&w=3840&q=75",
        "created_at": datetime.utcnow()
    }
    
    result = await users_collection.insert_one(admin_user)
    print(f"✅ Admin user created with ID: {result.inserted_id}")
    print(f"   Email: {admin_email}")
    print(f"   Password: {admin_password}")

async def create_indexes():
    """Create necessary database indexes for performance"""
    print("🔧 Creating database indexes...")
    
    try:
        # Users collection indexes
        await users_collection.create_index("email", unique=True)
        await users_collection.create_index("username")
        
        # Exam files collection indexes
        await exam_files_collection.create_index("category")
        await exam_files_collection.create_index("created_at")
        
        # Bookmarks collection indexes
        await bookmarks_collection.create_index([("user_id", 1), ("exam_file_id", 1)], unique=True)
        
        # Exam submissions collection indexes
        await exam_submissions_collection.create_index("user_id")
        await exam_submissions_collection.create_index("exam_file_id")
        await exam_submissions_collection.create_index("created_at")
        
        # Market items collection indexes
        await market_items_collection.create_index("seller_id")
        await market_items_collection.create_index("created_at")
        
        # Quiz collection indexes
        await quizzes_collection.create_index("created_by")
        await quizzes_collection.create_index("created_at")
        await quizzes_collection.create_index("title")
        
        # Quiz answers collection indexes
        await quiz_answers_collection.create_index("user_id")
        await quiz_answers_collection.create_index("quiz_id")
        await quiz_answers_collection.create_index([("user_id", 1), ("quiz_id", 1)], unique=True)
        await quiz_answers_collection.create_index("submitted_at")
        
        print("✅ Database indexes created successfully")
    except Exception as e:
        print(f"⚠️ Some indexes may already exist: {e}")

async def clear_redis_cache():
    """Clear Redis cache for fresh start"""
    print("🧹 Clearing Redis cache...")
    
    try:
        await redis_client.flushdb()
        print("✅ Redis cache cleared")
    except Exception as e:
        print(f"⚠️ Redis cache clear failed: {e}")

async def setup_test_data():
    """Setup basic test data if in test environment"""
    database_name = os.getenv("DATABASE_NAME", "")
    
    if "test" in database_name.lower():
        print("🧪 Setting up test data...")
        
        # Create a test category
        test_category = {
            "name": "Test Category",
            "description": "Category for testing purposes",
            "created_at": datetime.utcnow()
        }
        
        existing_category = await exam_categories_collection.find_one({"name": "Test Category"})
        if not existing_category:
            await exam_categories_collection.insert_one(test_category)
            print("✅ Test category created")
        
        # Create system settings if needed
        system_settings = {
            "app_name": "Examtie",
            "version": "1.0.0",
            "maintenance_mode": False,
            "updated_at": datetime.utcnow()
        }
        
        existing_settings = await system_settings_collection.find_one({})
        if not existing_settings:
            await system_settings_collection.insert_one(system_settings)
            print("✅ System settings created")

async def main():
    """Main setup function"""
    print("🚀 Starting Examtie Database Setup")
    print("=" * 40)
    
    # Test connections first
    if not await test_connections():
        print("❌ Database connection tests failed. Please check your configuration.")
        sys.exit(1)
    
    try:
        # Create admin user
        await create_admin_user()
        
        # Create database indexes
        await create_indexes()
        
        # Clear Redis cache
        await clear_redis_cache()
        
        # Setup test data if in test environment
        await setup_test_data()
        
        print("\n✅ Database setup completed successfully!")
        print("🎉 You can now start the API server")
        
    except Exception as e:
        print(f"\n❌ Database setup failed: {e}")
        sys.exit(1)
    
    finally:
        # Close connections
        try:
            await redis_client.close()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(main())
