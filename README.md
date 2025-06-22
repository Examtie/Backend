# Examtie Backend API

A comprehensive FastAPI-based backend for the Examtie platform with user management, admin functionality, and quiz operations.

## Features

- 🔐 **Authentication & Authorization**: JWT-based auth with role-based access control
- 👥 **User Management**: Registration, login, profile management
- 🛠️ **Admin Panel**: Comprehensive admin operations including bulk user management
- 📊 **Quiz System**: Quiz creation, management, and statistics
- 🔒 **Security**: Input validation, rate limiting, and secure password handling
- 📁 **File Storage**: Cloudflare R2 integration for file uploads
- 🧪 **Comprehensive Testing**: Multiple test suites with CI/CD integration

## Quick Start

### Development Server

```bash
cd Backend
pip install -r requirements.txt
python setup_database.py  # Initialize database
cd app
python -m uvicorn main:app --reload
```

### Using Docker

```bash
cd Backend
docker build -t examtie-backend .
docker run -p 8000:8000 examtie-backend
```

## Testing

### Quick Test Run
```bash
./test_runner.sh  # Comprehensive test with server startup
```

### Run All Tests
```bash
./run_all_tests.sh  # All test suites
```

### Individual Test Suites
```bash
# Basic API tests (non-async, fast)
python -m pytest tests/test_api_simple.py::TestExamtieAPISimple::test_root_endpoint -v
python -m pytest tests/test_api_simple.py::TestExamtieAPISimple::test_unauthorized_access -v

# Integration tests (requires running server)
python tests/test_final_admin.py

# Legacy comprehensive tests
python tests/test_comprehensive_admin.py

# Performance and security tests
python tests/test_api_performance.py
python tests/test_api_security.py

# PyTest-based tests (may have async issues with Motor/MongoDB)
python -m pytest tests/test_api_pytest.py -v
```

## CI/CD Pipeline

This project includes a comprehensive GitHub Actions workflow (`.github/workflows/ci.yml`) that:

- **Multi-Python Version Testing**: Tests against Python 3.9, 3.10, and 3.11
- **MongoDB Service**: Runs tests against a real MongoDB instance
- **Comprehensive Test Suite**: Runs all test suites and generates reports
- **Security Scanning**: Bandit security analysis and dependency vulnerability checks
- **Code Quality**: Black formatting, Flake8 linting, and MyPy type checking
- **Artifact Collection**: Saves test results and security reports

### CI/CD Features

1. **Automated Testing**: All tests run on every push and pull request
2. **Test Isolation**: Each test suite runs in isolation with proper cleanup
3. **Result Artifacts**: Test results and logs are saved for review
4. **Security Checks**: Automated security scanning with Bandit and Safety
5. **Code Quality**: Automated code formatting and linting checks

## CI/CD

### GitHub Actions
The project includes comprehensive CI/CD with GitHub Actions:

- 🧪 **Automated Testing**: Runs on Python 3.9, 3.10, and 3.11
- 🔒 **Security Scanning**: Bandit and Safety checks
- 🐳 **Docker Build**: Automated container builds
- 🚀 **Deployment**: Staging and production deployment workflows

### Workflows
- **Backend CI/CD** (`.github/workflows/backend.yml`):
  - Unit tests with MongoDB service
  - Integration tests with live server
  - Security vulnerability scanning
  - Docker image building
  - Automated deployment pipelines

### Running CI Tests Locally
```bash
# Install dependencies
pip install -r requirements.txt
pip install bandit safety flake8

# Run linting
flake8 app/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics

# Run security scans
bandit -r app/ --severity-level medium
safety check --file requirements.txt

# Run full test suite
./test_runner.sh
```

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

## Database Setup

```bash
python setup_database.py
```

This creates:
- Admin user: `admin@admin.com` / `admin@admin.com`
- Test users and sample data

## Project Structure

```
Backend/
├── app/
│   ├── main.py          # FastAPI application
│   ├── models.py        # Pydantic models
│   ├── database.py      # MongoDB connection
│   ├── auth.py          # Authentication logic
│   ├── admin.py         # Admin endpoints
│   ├── user.py          # User endpoints
│   └── storage/         # File storage integration
├── tests/               # Test suites
├── requirements.txt     # Dependencies
└── Dockerfile          # Container configuration
```

## Development

### Setup Development Environment
```bash
./setup_dev_environment.sh
```

### Running Tests Locally
```bash
# Start the server
uvicorn app.main:app --reload

# In another terminal, run tests
./run_all_tests_comprehensive.sh
```

## Notes

- **Async Issues**: Some pytest-based tests may have event loop issues with Motor (MongoDB async driver) and FastAPI TestClient. The `test_api_async_working.py` suite uses requests in a thread pool and is more reliable.
- **Admin Credentials**: Default admin user is `admin@admin.com` with password `admin@admin.com`
- **MongoDB**: Tests require a running MongoDB instance
- **R2 Storage**: Optional Cloudflare R2 integration for file uploads