#!/bin/bash
# Quick Port Management Commands

# Function to check port status
check_port() {
    echo "🔍 Checking port $1..."
    python3 port_manager.py check $1
}

# Function to kill processes on port
kill_port() {
    echo "🔫 Killing processes on port $1..."
    python3 port_manager.py kill $1
}

# Function to find free port
find_free() {
    echo "🔍 Finding free port starting from $1..."
    python3 port_manager.py free $1
}

# Function to clean all development processes
clean_all() {
    echo "🧹 Cleaning all development processes..."
    python3 port_manager.py clean
}

# Function to start servers smartly
start_servers() {
    echo "🚀 Starting servers with smart port management..."
    python3 smart_start.py
}

# Main command dispatcher
case "$1" in
    "check")
        check_port $2
        ;;
    "kill")
        kill_port $2
        ;;
    "free")
        find_free $2
        ;;
    "clean")
        clean_all
        ;;
    "start")
        start_servers
        ;;
    *)
        echo "🔧 Quick Port Management"
        echo "Usage:"
        echo "  ./quick_ports.sh check <port>  - Check if port is in use"
        echo "  ./quick_ports.sh kill <port>   - Kill processes using port"
        echo "  ./quick_ports.sh free <start>  - Find free port starting from <start>"
        echo "  ./quick_ports.sh clean         - Clean all development processes"
        echo "  ./quick_ports.sh start         - Start servers with smart management"
        echo ""
        echo "Examples:"
        echo "  ./quick_ports.sh check 5001"
        echo "  ./quick_ports.sh kill 8080"
        echo "  ./quick_ports.sh free 8080"
        echo "  ./quick_ports.sh clean"
        echo "  ./quick_ports.sh start"
        ;;
esac 