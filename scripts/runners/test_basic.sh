#!/bin/bash

# Test runner script for basic functionality without external dependencies
# This version runs tests that don't require MongoDB

set -e

echo "🧪 Examtie Backend Basic Test Runner"
echo "===================================="

echo "🔍 Running basic functionality tests..."

# Run basic unit tests that don't require database
echo "📝 Testing basic API functionality..."
python -m pytest tests/test_api_simple.py::TestExamtieAPISimple::test_root_endpoint -v
python -m pytest tests/test_api_simple.py::TestExamtieAPISimple::test_unauthorized_access -v
python -m pytest tests/test_api_simple.py::TestExamtieAPISimple::test_invalid_token -v

echo ""
echo "🎉 Basic tests passed!"
echo "✅ API structure working"
echo "✅ Authentication checks working"
echo "✅ Error handling working"
echo ""
echo "📋 To run full integration tests:"
echo "   1. Start MongoDB: docker run -d -p 27017:27017 mongo:6.0"
echo "   2. Run: ./test_runner.sh"
