#!/bin/bash

# Development Environment Setup Script for Examtie Backend
# This script sets up the complete development environment

echo "🚀 Setting up Examtie Backend Development Environment"
echo "====================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${BLUE}🐍 Checking Python version...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.8"

if [ "$(echo "$PYTHON_VERSION >= $REQUIRED_VERSION" | bc -l 2>/dev/null)" = "1" ] || python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
    echo -e "${GREEN}✅ Python version is sufficient: $(python3 --version)${NC}"
else
    echo -e "${RED}❌ Python 3.8+ is required. Current version: $(python3 --version)${NC}"
    exit 1
fi

# Install Python dependencies
echo ""
echo -e "${BLUE}📦 Installing Python dependencies...${NC}"
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Dependencies installed successfully${NC}"
else
    echo -e "${RED}❌ Failed to install dependencies${NC}"
    exit 1
fi

# Create .env file if it doesn't exist
echo ""
echo -e "${BLUE}⚙️  Setting up environment configuration...${NC}"
if [ ! -f .env ]; then
    echo "Creating .env file with default configuration..."
    cat > .env << EOF
# Database Configuration
MONGO_URI=mongodb+srv://backend_Examtie:e2F6vyiceg7fNoxi@jackmadev.cn1sf.mongodb.net
DATABASE_NAME=Examtie

# Security Configuration
SECRET_KEY=niga56
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Optional: Cloudflare R2 Configuration (for file uploads)
# R2_REGION=auto
# R2_ENDPOINT_URL=https://your-account-id.r2.cloudflarestorage.com
# R2_ACCESS_KEY=your-access-key
# R2_SECRET_KEY=your-secret-key
# R2_BUCKET_NAME=your-bucket-name
EOF
    echo -e "${GREEN}✅ Created .env file with default configuration${NC}"
else
    echo -e "${YELLOW}⚠️  .env file already exists, skipping creation${NC}"
fi

# Setup database
echo ""
echo -e "${BLUE}🗄️  Setting up database...${NC}"
python setup_database.py

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Database setup completed${NC}"
else
    echo -e "${RED}❌ Database setup failed${NC}"
    exit 1
fi

# Create necessary directories
echo ""
echo -e "${BLUE}📁 Creating necessary directories...${NC}"
mkdir -p test_results
mkdir -p logs
echo -e "${GREEN}✅ Directories created${NC}"

# Check if server can start
echo ""
echo -e "${BLUE}🔧 Testing server startup...${NC}"
timeout 10s python -c "
import sys
sys.path.insert(0, '.')
from app.main import app
print('✅ Server can be imported successfully')
" 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Server startup test passed${NC}"
else
    echo -e "${RED}❌ Server startup test failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 Development environment setup completed!${NC}"
echo ""
echo -e "${BLUE}🚀 To start the development server:${NC}"
echo "   ./run_server.sh"
echo ""
echo -e "${BLUE}🧪 To run tests:${NC}"
echo "   ./run_all_tests.sh"
echo ""
echo -e "${BLUE}📚 To view API documentation:${NC}"
echo "   Start the server and visit: http://localhost:8000/docs"
echo ""
echo -e "${BLUE}🔑 Default admin credentials:${NC}"
echo "   Email: admin@admin.com"
echo "   Password: admin@admin.com"
echo ""
echo -e "${BLUE}📋 Available commands:${NC}"
echo "   ./run_server.sh          - Start development server"
echo "   ./run_all_tests.sh       - Run comprehensive test suite"
echo "   ./run_tests.sh           - Run basic tests"
echo "   python setup_database.py - Reset/setup database"
echo ""
echo -e "${GREEN}✨ Happy coding!${NC}"
