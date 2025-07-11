# Examtie Backend API

A comprehensive FastAPI-based backend for the Examtie platform with user management, admin functionality, and quiz operations.

Note: instruction for running this with docker compose available at [Examtie/Examtie](https://github.com/Examtie/Examtie)


## Postman collection

https://botfin.postman.co/workspace/Regenxzz~d8dcf619-2b2f-45ed-a891-7c8b56d2d323/collection/27322087-68e42c25-f1b0-48ec-8d74-3e802c0efdb3?action=share&creator=27322087

## Api Docs

https://examtieapi.breadtm.xyz/docs

## Quick Start

### Development Server

```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

### Using Docker

```bash
docker build -t examtie-backend .
docker run -p 8000:8000 examtie-backend
```

## Setup Redis
```
redis-server
```

## Testing
```bash
pytest
```

## venv
```
python3 -m venv venv
source venv/bin/activate
```

## Features

- 🔐 **Authentication & Authorization**: JWT-based auth with role-based access control
- 👥 **User Management**: Registration, login, profile management
- 🛠️ **Admin Panel**: Comprehensive admin operations including bulk user management
- 📊 **Quiz System**: Quiz creation, management, and statistics
- 🔒 **Security**: Input validation, rate limiting, and secure password handling
- 📁 **File Storage**: Cloudflare R2 integration for file uploads
- 🧪 **Comprehensive Testing**: Multiple test suites with CI/CD integration
  
## CI/CD

### GitHub Actions
Testing with `pytest`

## API Endpoints

### Authentication
- `POST /register` - User registration
- `POST /login` - User login
- `GET /profile` - Get user profile
- `PUT /profile` - Update user profile

### Admin Operations
- `GET /admin/users` - List all users
- `GET /admin/users/{user_id}` - Get specific user
- `PUT /admin/users/{user_id}` - Update user
- `DELETE /admin/users/{user_id}` - Delete user
- `POST /admin/bulk/role-update` - Bulk role updates
- `POST /admin/bulk/delete-users` - Bulk user deletion

### System
- `GET /health` - Health check endpoint
- `GET /` - Root endpoint

## Configuration

Set these environment variables:

```bash
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=examtie
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Optional: Cloudflare R2 Storage
R2_ACCOUNT_ID=your-account-id
R2_ACCESS_KEY_ID=your-access-key
R2_SECRET_ACCESS_KEY=your-secret-key
R2_BUCKET_NAME=your-bucket-name
```

## Notes

- **Async Issues**: Some pytest-based tests may have event loop issues with Motor (MongoDB async driver) and FastAPI TestClient. The `test_api_async_working.py` suite uses requests in a thread pool and is more reliable.
- **Admin Credentials**: Default admin user is `admin@admin.com` with password `admin@admin.com`
- **MongoDB**: Tests require a running MongoDB instance
- **R2 Storage**: Optional Cloudflare R2 integration for file uploads
