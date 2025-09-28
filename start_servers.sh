#!/bin/bash

# Lab Automation Framework - Server Startup Script
# Clear port configuration and startup management

echo "🚀 Starting Lab Automation Framework Servers..."

# Port Configuration
API_PORT=5001
FRONTEND_PORT=8080

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Load nvm and Node.js environment
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion

# Use the default Node.js version
nvm use default > /dev/null 2>&1

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${RED}❌ Port $port is already in use${NC}"
        return 1
    else
        echo -e "${GREEN}✅ Port $port is available${NC}"
        return 0
    fi
}

# Function to kill processes on port
kill_port() {
    local port=$1
    echo -e "${YELLOW}🔄 Killing processes on port $port...${NC}"
    lsof -ti:$port | xargs kill -9 2>/dev/null || true
    sleep 2
}

# Clean up any existing processes
echo -e "${BLUE}🧹 Cleaning up existing processes...${NC}"
kill_port $API_PORT
kill_port $FRONTEND_PORT

# Check ports are available
echo -e "${BLUE}🔍 Checking port availability...${NC}"
if ! check_port $API_PORT; then
    echo -e "${RED}❌ Cannot start API server - port $API_PORT is busy${NC}"
    exit 1
fi

if ! check_port $FRONTEND_PORT; then
    echo -e "${RED}❌ Cannot start frontend - port $FRONTEND_PORT is busy${NC}"
    exit 1
fi

# Start API Server (using BD Editor API)
echo -e "${BLUE}🔧 Starting BD Editor API Server on port $API_PORT...${NC}"
python3 bd_editor_api.py &
API_PID=$!

# Wait for API server to start
echo -e "${YELLOW}⏳ Waiting for API server to start...${NC}"
sleep 5

# Check if API server is running
if curl -s http://localhost:$API_PORT/api/health > /dev/null; then
    echo -e "${GREEN}✅ API Server is running on http://localhost:$API_PORT${NC}"
else
    echo -e "${RED}❌ API Server failed to start${NC}"
    kill $API_PID 2>/dev/null || true
    exit 1
fi

# Start Frontend (if in frontend directory)
if [ -d "frontend" ]; then
    echo -e "${BLUE}🌐 Starting React Frontend on port $FRONTEND_PORT...${NC}"
    cd frontend
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}📦 Installing frontend dependencies...${NC}"
        npm install
    fi
    
    # Start the development server
    npm run dev -- --port $FRONTEND_PORT &
    FRONTEND_PID=$!
    cd ..
    
    # Wait for frontend to start
    echo -e "${YELLOW}⏳ Waiting for frontend to start...${NC}"
    sleep 10
    
    # Check if frontend is running
    if curl -s http://localhost:$FRONTEND_PORT > /dev/null; then
        echo -e "${GREEN}✅ Frontend is running on http://localhost:$FRONTEND_PORT${NC}"
    else
        echo -e "${RED}❌ Frontend failed to start${NC}"
        kill $FRONTEND_PID 2>/dev/null || true
        kill $API_PID 2>/dev/null || true
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  Frontend directory not found, skipping frontend startup${NC}"
fi

# Display final status
echo -e "${GREEN}🎉 All servers started successfully!${NC}"
echo -e "${BLUE}📋 Server Status:${NC}"
echo -e "  🔧 API Server: http://localhost:$API_PORT"
echo -e "  🌐 Frontend: http://localhost:$FRONTEND_PORT"
echo -e "  📊 Dashboard: http://localhost:$FRONTEND_PORT"
echo -e "  🔨 Builder: http://localhost:$FRONTEND_PORT/builder"
echo -e "  🌐 Topology: http://localhost:$FRONTEND_PORT/topology"
echo -e ""
echo -e "${YELLOW}💡 To stop all servers, run: pkill -f 'python.*api_server' && pkill -f 'vite'${NC}"
echo -e "${YELLOW}💡 Or use Ctrl+C to stop this script${NC}"

# Keep script running and handle cleanup
trap 'echo -e "\n${YELLOW}🛑 Shutting down servers...${NC}"; kill $API_PID 2>/dev/null || true; kill $FRONTEND_PID 2>/dev/null || true; exit 0' INT

# Wait for user to stop
wait 