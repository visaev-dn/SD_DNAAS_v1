#!/bin/bash

echo "🚀 Starting Lab Automation Framework Servers..."

# Function to check if a port is in use
check_port() {
    lsof -i :$1 > /dev/null 2>&1
}

# Start API Server (Port 5000)
echo "📡 Starting API Server on port 5000..."
if check_port 5000; then
    echo "✅ API Server already running on port 5000"
else
    python3 api_server.py --debug &
    echo "✅ API Server started"
fi

# Wait a moment for API server to start
sleep 2

# Start React Development Server (Port 8080)
echo "🌐 Starting React Development Server on port 8080..."
if check_port 8080; then
    echo "✅ React Server already running on port 8080"
else
    cd frontend
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    npm run dev &
    echo "✅ React Server started"
fi

echo ""
echo "🎉 Both servers are running!"
echo ""
echo "📱 Open your browser and go to:"
echo "   🌐 React App: http://localhost:8080"
echo "   📡 API Server: http://localhost:5000/api/health"
echo ""
echo "🌙 Dark Mode: Click the moon/sun icon in the header to toggle dark mode!"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Wait for user to stop
wait 