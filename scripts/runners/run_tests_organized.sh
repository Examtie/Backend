#!/bin/bash

# Organized Test Runner for Examtie Backend
# This script runs tests from the new organized structure

set -e

echo "🧪 Examtie Backend Organized Test Runner"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if we're in the correct directory
if [[ ! -f "app/main.py" ]]; then
    echo "❌ Error: Please run this script from the Backend directory."
    exit 1
fi

# Check if server is running
echo -e "${BLUE}🔍 Checking if API server is running...${NC}"
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ API server is running${NC}"
    SERVER_RUNNING=true
else
    echo -e "${YELLOW}⚠️  API server not running. Please start it first with:${NC}"
    echo "   cd Backend && python -m uvicorn app.main:app --reload"
    echo ""
    echo -e "${YELLOW}Or run:${NC}"
    echo "   ./scripts/runners/run_server.sh"
    exit 1
fi

echo ""
echo -e "${BLUE}🧪 Running Unit Tests${NC}"
echo "======================"

# Run unit tests (these don't require a running server)
echo -e "${YELLOW}Running API simple tests...${NC}"
python -m pytest tests/unit/test_api_simple.py -v

echo -e "${YELLOW}Running security tests...${NC}"
python -m pytest tests/unit/test_api_security.py -v

echo -e "${YELLOW}Running performance tests...${NC}"
python -m pytest tests/unit/test_api_performance.py -v

echo ""
echo -e "${BLUE}🔗 Running Integration Tests${NC}"
echo "============================="

# Run integration tests (these require a running server)
echo -e "${YELLOW}Running admin integration tests...${NC}"
python tests/integration/test_admin.py

echo -e "${YELLOW}Running async integration tests...${NC}"
python tests/integration/test_async.py

echo -e "${YELLOW}Running general integration tests...${NC}"
python tests/integration/test_integration.py

echo ""
echo -e "${GREEN}🎉 All tests completed!${NC}"
echo ""
echo -e "${BLUE}📋 Test Structure:${NC}"
echo "   tests/unit/         - Unit tests (no server required)"
echo "   tests/integration/  - Integration tests (server required)"
echo "   tests/README.md     - Test documentation"
echo ""
echo -e "${BLUE}🔧 Runner Scripts:${NC}"
echo "   scripts/runners/    - All test and server runner scripts"
echo "   scripts/debug/      - Debug and troubleshooting scripts"
