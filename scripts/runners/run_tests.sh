#!/bin/bash

# Test Runner Script for Examtie Backend API
# This script runs comprehensive tests against the API

set -e

echo "🧪 Examtie Backend API Test Runner"
echo "=================================="

# Check if the server is running
echo "🔍 Checking if server is running..."
if curl -s http://localhost:8000/ > /dev/null; then
    echo "✅ Server is running at http://localhost:8000"
else
    echo "❌ Server is not running. Please start the server first with:"
    echo "   ./run_server.sh (Linux/Mac) or run_server.bat (Windows)"
    echo ""
    echo "💡 To start the server in the background:"
    echo "   nohup ./run_server.sh > server.log 2>&1 &"
    exit 1
fi

echo "📦 Installing test dependencies..."
pip install requests

echo "🧪 Running comprehensive API tests..."
python tests/test_comprehensive_admin.py

echo ""
echo "📝 Additional test files available:"
echo "   - tests/test_admin.py (basic admin tests)"
echo "   - tests/test_bulk_admin.py (bulk operations tests)"
echo "   - tests/test_final_admin.py (final comprehensive tests)"
echo ""
echo "🔧 To run individual tests:"
echo "   python tests/test_admin.py"
echo "   python tests/test_bulk_admin.py"
echo "   python tests/test_final_admin.py"
