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
