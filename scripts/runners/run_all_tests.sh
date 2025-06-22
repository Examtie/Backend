#!/bin/bash

# Comprehensive test runner for Examtie Backend API
# This script runs all test suites and generates reports

echo "🚀 Starting Examtie Backend API Test Suite"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if server is running
echo -e "${BLUE}🔍 Checking if API server is running...${NC}"
if curl -s http://localhost:8000/ > /dev/null; then
    echo -e "${GREEN}✅ API server is running${NC}"
else
    echo -e "${RED}❌ API server is not running. Please start it first:${NC}"
    echo "   PYTHONPATH=/data/Examtie/Backend uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
    exit 1
fi

# Create test results directory
mkdir -p test_results

echo ""
echo -e "${BLUE}📊 Running Comprehensive API Tests...${NC}"
echo "=============================================="

# Run comprehensive tests
echo -e "${YELLOW}Running comprehensive functionality tests...${NC}"
python -m pytest tests/test_api_comprehensive.py -v --tb=short > test_results/comprehensive_results.txt 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Comprehensive tests PASSED${NC}"
else
    echo -e "${RED}❌ Comprehensive tests FAILED${NC}"
    echo "Check test_results/comprehensive_results.txt for details"
fi

echo ""
echo -e "${BLUE}🔒 Running Security Tests...${NC}"
echo "=============================================="

# Run security tests
echo -e "${YELLOW}Running security and authentication tests...${NC}"
python -m pytest tests/test_api_security.py -v --tb=short > test_results/security_results.txt 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Security tests PASSED${NC}"
else
    echo -e "${RED}❌ Security tests FAILED${NC}"
    echo "Check test_results/security_results.txt for details"
fi

echo ""
echo -e "${BLUE}⚡ Running Performance Tests...${NC}"
echo "=============================================="

# Run performance tests
echo -e "${YELLOW}Running performance and load tests...${NC}"
python -m pytest tests/test_api_performance.py -v -s --tb=short > test_results/performance_results.txt 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Performance tests PASSED${NC}"
else
    echo -e "${RED}❌ Performance tests FAILED${NC}"
    echo "Check test_results/performance_results.txt for details"
fi

echo ""
echo -e "${BLUE}🧪 Running Legacy Tests...${NC}"
echo "=============================================="

# Run existing legacy tests
echo -e "${YELLOW}Running existing comprehensive admin tests...${NC}"
python tests/test_comprehensive_admin.py > test_results/legacy_comprehensive.txt 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Legacy comprehensive tests PASSED${NC}"
else
    echo -e "${RED}❌ Legacy comprehensive tests FAILED${NC}"
    echo "Check test_results/legacy_comprehensive.txt for details"
fi

echo -e "${YELLOW}Running final admin tests...${NC}"
python tests/test_final_admin.py > test_results/legacy_final.txt 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Legacy final tests PASSED${NC}"
else
    echo -e "${RED}❌ Legacy final tests FAILED${NC}"
    echo "Check test_results/legacy_final.txt for details"
fi

echo ""
echo -e "${BLUE}📋 Test Summary${NC}"
echo "=============================================="

# Count total tests
TOTAL_TESTS=0
PASSED_TESTS=0

for result_file in test_results/*.txt; do
    if [ -f "$result_file" ]; then
        # Count pytest results
        PYTEST_PASSED=$(grep -c "PASSED" "$result_file" 2>/dev/null || echo 0)
        PYTEST_FAILED=$(grep -c "FAILED" "$result_file" 2>/dev/null || echo 0)
        
        # Count legacy test results
        LEGACY_SUCCESS=$(grep -c "✅" "$result_file" 2>/dev/null || echo 0)
        
        FILE_TOTAL=$((PYTEST_PASSED + PYTEST_FAILED + LEGACY_SUCCESS))
        FILE_PASSED=$((PYTEST_PASSED + LEGACY_SUCCESS))
        
        TOTAL_TESTS=$((TOTAL_TESTS + FILE_TOTAL))
        PASSED_TESTS=$((PASSED_TESTS + FILE_PASSED))
        
        echo "📄 $(basename "$result_file"): $FILE_PASSED/$FILE_TOTAL tests passed"
    fi
done

echo ""
if [ $TOTAL_TESTS -gt 0 ]; then
    PASS_RATE=$(( (PASSED_TESTS * 100) / TOTAL_TESTS ))
    echo -e "${BLUE}Overall Result: $PASSED_TESTS/$TOTAL_TESTS tests passed (${PASS_RATE}%)${NC}"
    
    if [ $PASS_RATE -ge 90 ]; then
        echo -e "${GREEN}🎉 EXCELLENT! API is performing well${NC}"
    elif [ $PASS_RATE -ge 75 ]; then
        echo -e "${YELLOW}⚠️  GOOD! Some issues to address${NC}"
    else
        echo -e "${RED}🚨 NEEDS ATTENTION! Multiple issues found${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  No test results found${NC}"
fi

echo ""
echo -e "${BLUE}📁 Test Results Location:${NC} ./test_results/"
echo -e "${BLUE}📚 API Documentation:${NC} http://localhost:8000/docs"
echo ""
echo -e "${GREEN}✨ Test suite completed!${NC}"
