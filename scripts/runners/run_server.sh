#!/bin/bash

# Examtie Backend Setup and Run Script
# This script sets up the backend environment and runs the FastAPI server

set -e  # Exit on any error

echo "🚀 Examtie Backend Setup and Run Script"
echo "========================================"

# Check if we're in the Backend directory
if [[ ! -f "requirements.txt" ]]; then
    echo "❌ Error: requirements.txt not found. Please run this script from the Backend directory."
    exit 1
fi

echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo "📦 Installing additional dependencies for database setup..."
pip install bcrypt

echo "🗄️ Setting up database..."
python setup_database.py

echo "🔧 Starting FastAPI server..."
echo "📍 Server will be available at: http://localhost:8000"
echo "📖 API documentation will be available at: http://localhost:8000/docs"
echo "🔍 Alternative docs at: http://localhost:8000/redoc"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server
cd app
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
