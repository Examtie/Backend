"""
Database setup and seeding script for Examtie Backend
"""
import asyncio
import bcrypt
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "examtie")

async def setup_database():
    """Set up database with initial admin user and sample data"""
    print("🔧 Setting up database...")
    
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DATABASE_NAME]
    
    users_collection = db.get_collection("users")
    exam_files_collection = db.get_collection("exam_files")
    
    try:
        # Check if admin user already exists
        existing_admin = await users_collection.find_one({"email": "admin@admin.com"})
        
        if not existing_admin:
            print("👤 Creating admin user...")
            
            # Hash password
            password = "admin@admin.com"
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            admin_user = {
                "email": "admin@admin.com",
                "username": "admin",
                "full_name": "System Administrator",
                "hashed_password": hashed_password,
                "roles": ["admin"],
                "bio": "System Administrator",
                "profile_image": "https://jwt.io/_next/image?url=%2F_next%2Fstatic%2Fmedia%2Fjwt-flower.f20616b0.png&w=3840&q=75",
                "created_at": datetime.utcnow()
            }
            
            result = await users_collection.insert_one(admin_user)
            print(f"✅ Admin user created with ID: {result.inserted_id}")
        else:
            print("✅ Admin user already exists")
        
        # Create some sample users
        sample_users = [
            {
                "email": "user1@example.com",
                "username": "user1",
                "full_name": "Regular User One",
                "hashed_password": bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
                "roles": ["user"],
                "bio": "Regular user for testing",
                "profile_image": "https://jwt.io/_next/image?url=%2F_next%2Fstatic%2Fmedia%2Fjwt-flower.f20616b0.png&w=3840&q=75",
                "created_at": datetime.utcnow()
            },
            {
                "email": "staff@example.com",
                "username": "staff1",
                "full_name": "Staff Member",
                "hashed_password": bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
                "roles": ["staff"],
                "bio": "Staff member for testing",
                "profile_image": "https://jwt.io/_next/image?url=%2F_next%2Fstatic%2Fmedia%2Fjwt-flower.f20616b0.png&w=3840&q=75",
                "created_at": datetime.utcnow()
            }
        ]
        
        for user in sample_users:
            existing = await users_collection.find_one({"email": user["email"]})
            if not existing:
                result = await users_collection.insert_one(user)
                print(f"✅ Created user: {user['email']} with ID: {result.inserted_id}")
            else:
                print(f"✅ User already exists: {user['email']}")
        
        # Create some sample exam files (without actual files)
        sample_exam_files = [
            {
                "title": "Sample Math Exam",
                "description": "Grade 10 Mathematics Final Exam",
                "tags": ["math", "grade10", "final"],
                "url": "https://example.com/sample-math-exam.pdf",
                "uploaded_by": "admin@admin.com",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "title": "Physics Midterm",
                "description": "Grade 11 Physics Midterm Examination",
                "tags": ["physics", "grade11", "midterm"],
                "url": "https://example.com/physics-midterm.pdf",
                "uploaded_by": "admin@admin.com",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        
        for exam_file in sample_exam_files:
            existing = await exam_files_collection.find_one({"title": exam_file["title"]})
            if not existing:
                result = await exam_files_collection.insert_one(exam_file)
                print(f"✅ Created exam file: {exam_file['title']} with ID: {result.inserted_id}")
            else:
                print(f"✅ Exam file already exists: {exam_file['title']}")
        
        # Print summary
        user_count = await users_collection.count_documents({})
        exam_count = await exam_files_collection.count_documents({})
        admin_count = await users_collection.count_documents({"roles": "admin"})
        user_role_count = await users_collection.count_documents({"roles": "user"})
        staff_count = await users_collection.count_documents({"roles": "staff"})
        
        print("\n📊 Database Setup Summary:")
        print(f"   👥 Total users: {user_count}")
        print(f"      - Admins: {admin_count}")
        print(f"      - Users: {user_role_count}")
        print(f"      - Staff: {staff_count}")
        print(f"   📁 Total exam files: {exam_count}")
        print(f"   🗄️ Database: {DATABASE_NAME}")
        print(f"   🔗 MongoDB URI: {MONGO_URI}")
        
        print("\n🔑 Admin Credentials:")
        print(f"   📧 Email: admin@admin.com")
        print(f"   🔒 Password: admin@admin.com")
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
    finally:
        client.close()
        print("\n✅ Database setup completed!")

if __name__ == "__main__":
    asyncio.run(setup_database())
