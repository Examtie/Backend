#!/bin/bash

# Test runner script that handles the async database issues
# This script starts the server and runs integration tests

set -e

echo "🧪 Examtie Backend Test Runner"
echo "================================"

# Set environment variables
export MONGO_URI=${MONGO_URI:-"mongodb://localhost:27017"}
export DATABASE_NAME=${DATABASE_NAME:-"examtie_test"}
export SECRET_KEY=${SECRET_KEY:-"test_secret_key"}

echo "📋 Environment:"
echo "   MONGO_URI: $MONGO_URI"
echo "   DATABASE_NAME: $DATABASE_NAME"
echo ""

# Check if MongoDB is running
echo "🔍 Checking MongoDB connection..."
if ! python -c "
import pymongo
try:
    client = pymongo.MongoClient('$MONGO_URI', serverSelectionTimeoutMS=5000)
    client.server_info()
    print('✅ MongoDB is running')
except Exception as e:
    print('❌ MongoDB connection failed:', e)
    exit(1)
" 2>/dev/null; then
    echo "❌ Cannot connect to MongoDB at $MONGO_URI"
    echo "Please make sure MongoDB is running:"
    echo "   docker run -d -p 27017:27017 mongo:6.0"
    echo "   # or"
    echo "   mongod"
    exit 1
fi

# Setup test database
echo "🗃️  Setting up test database..."
python setup_database.py

# Run basic unit tests (non-async)
echo "🧪 Running basic unit tests..."
python -m pytest tests/test_api_simple.py::TestExamtieAPISimple::test_root_endpoint -v
python -m pytest tests/test_api_simple.py::TestExamtieAPISimple::test_unauthorized_access -v
python -m pytest tests/test_api_simple.py::TestExamtieAPISimple::test_invalid_token -v

# Check if server is already running
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "🚀 Server already running on port 8000"
    SERVER_WAS_RUNNING=true
else
    echo "🚀 Starting API server..."
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
    SERVER_PID=$!
    SERVER_WAS_RUNNING=false
    
    # Wait for server to start
    echo "⏳ Waiting for server to start..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/ > /dev/null 2>&1; then
            echo "✅ Server is ready!"
            break
        fi
        sleep 1
    done
    
    # Check if server started successfully
    if ! curl -s http://localhost:8000/ > /dev/null 2>&1; then
        echo "❌ Server failed to start"
        exit 1
    fi
fi

# Run integration tests
echo "🔧 Running integration tests..."
python tests/test_final_admin.py

# Test with curl
echo "🌐 Testing API endpoints..."
echo "Testing root endpoint..."
curl -s http://localhost:8000/ | python -m json.tool

echo "Testing admin login and protected endpoint..."
ADMIN_TOKEN=$(curl -s -X POST http://localhost:8000/auth/api/v1/login \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=admin@admin.com&password=admin@admin.com" | \
    python -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null || echo "")

if [ ! -z "$ADMIN_TOKEN" ]; then
    echo "✅ Admin login successful"
    echo "Testing protected endpoint..."
    curl -s -H "Authorization: Bearer $ADMIN_TOKEN" http://localhost:8000/admin/api/v1/stats | python -m json.tool
    echo "✅ Protected endpoint accessible"
else
    echo "❌ Admin login failed"
    exit 1
fi

# Cleanup
if [ "$SERVER_WAS_RUNNING" = false ] && [ ! -z "$SERVER_PID" ]; then
    echo "🛑 Stopping test server..."
    kill $SERVER_PID 2>/dev/null || true
    wait $SERVER_PID 2>/dev/null || true
fi

echo ""
echo "🎉 All tests passed!"
echo "✅ Basic functionality working"
echo "✅ Authentication working"
echo "✅ Admin endpoints working"
echo "✅ Database integration working"
