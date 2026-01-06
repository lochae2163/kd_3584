#!/bin/bash

# Start Frontend Server Script
# Run this from the project root: ./start_frontend.sh

cd /Users/punlochan/kd_3584/frontend/public

echo "🌐 Starting frontend server..."
echo "📍 URL: http://localhost:8080"
echo "🏠 Dashboard: http://localhost:8080/index.html"
echo "🏆 DKP Leaderboard: http://localhost:8080/contribution.html"
echo "⚙️  Admin Panel: http://localhost:8080/admin.html"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python3 -m http.server 8080
