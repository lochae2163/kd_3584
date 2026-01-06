#!/bin/bash

# Start Backend Server Script
# Run this from the backend folder: ./start_backend.sh

cd /Users/punlochan/kd_3584/backend

echo "🚀 Starting backend server..."
echo "📍 URL: http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

/Users/punlochan/kd_3584/backend/venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
