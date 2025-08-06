#!/usr/bin/env python3
"""
Smart Server Startup Script
Automatically handles port conflicts and dependency issues
"""

import subprocess
import sys
import os
import time
import signal
from port_manager import check_port, kill_process_by_pid, find_free_port

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'flask-socketio',
        'flask-sqlalchemy', 
        'PyJWT',
        'flask-login'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing dependencies: {', '.join(missing_packages)}")
        print("Installing missing packages...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install'] + missing_packages, check=True)
            print("✅ Dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False
    
    return True

def start_api_server(port=5001):
    """Start API server with smart port management"""
    print(f"🚀 Starting API server on port {port}...")
    
    # Check if port is in use
    in_use, processes = check_port(port)
    if in_use:
        print(f"🔴 Port {port} is in use. Attempting to free it...")
        for process in processes:
            parts = process.split()
            if len(parts) >= 2:
                pid = parts[1]
                kill_process_by_pid(pid)
        
        # Wait a moment and check again
        time.sleep(2)
        in_use, _ = check_port(port)
        if in_use:
            print(f"⚠️ Port {port} still in use, trying alternative port...")
            new_port = find_free_port(port + 1, 10)
            if new_port:
                port = new_port
                print(f"🔄 Using port {port} instead")
            else:
                print("❌ No free ports found")
                return False
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    # Start the server
    try:
        cmd = [sys.executable, 'api_server.py', '--port', str(port)]
        print(f"🔧 Running: {' '.join(cmd)}")
        process = subprocess.Popen(cmd)
        
        # Wait a moment and check if it started successfully
        time.sleep(3)
        if process.poll() is None:  # Still running
            print(f"✅ API server started successfully on port {port}")
            return process
        else:
            print("❌ API server failed to start")
            return False
    except Exception as e:
        print(f"❌ Error starting API server: {e}")
        return False

def start_frontend(port=8080):
    """Start frontend with smart port management"""
    print(f"🚀 Starting frontend on port {port}...")
    
    # Check if port is in use
    in_use, processes = check_port(port)
    if in_use:
        print(f"🔴 Port {port} is in use. Attempting to free it...")
        for process in processes:
            parts = process.split()
            if len(parts) >= 2:
                pid = parts[1]
                kill_process_by_pid(pid)
        
        # Wait a moment and check again
        time.sleep(2)
        in_use, _ = check_port(port)
        if in_use:
            print(f"⚠️ Port {port} still in use, trying alternative port...")
            new_port = find_free_port(port + 1, 10)
            if new_port:
                port = new_port
                print(f"🔄 Using port {port} instead")
            else:
                print("❌ No free ports found")
                return False
    
    # Start the frontend
    try:
        os.chdir('frontend')
        cmd = ['npm', 'run', 'dev', '--', '--port', str(port)]
        print(f"🔧 Running: {' '.join(cmd)}")
        process = subprocess.Popen(cmd)
        
        # Wait a moment and check if it started successfully
        time.sleep(5)
        if process.poll() is None:  # Still running
            print(f"✅ Frontend started successfully on port {port}")
            return process
        else:
            print("❌ Frontend failed to start")
            return False
    except Exception as e:
        print(f"❌ Error starting frontend: {e}")
        return False

def main():
    """Main startup function"""
    print("🔧 Smart Server Startup")
    print("=" * 40)
    
    # Clean up any existing processes
    print("🧹 Cleaning up existing processes...")
    subprocess.run(['python3', 'port_manager.py', 'clean'], check=False)
    
    # Start API server
    api_process = start_api_server(5001)
    if not api_process:
        print("❌ Failed to start API server")
        return
    
    # Wait a moment for API server to fully start
    time.sleep(3)
    
    # Start frontend
    frontend_process = start_frontend(8080)
    if not frontend_process:
        print("❌ Failed to start frontend")
        api_process.terminate()
        return
    
    print("\n🎉 Both servers started successfully!")
    print("📋 Server URLs:")
    print("  - API Server: http://localhost:5001")
    print("  - Frontend: http://localhost:8080")
    print("\n💡 Press Ctrl+C to stop both servers")
    
    try:
        # Keep both processes running
        while True:
            time.sleep(1)
            # Check if either process died
            if api_process.poll() is not None:
                print("❌ API server stopped unexpectedly")
                break
            if frontend_process.poll() is not None:
                print("❌ Frontend stopped unexpectedly")
                break
    except KeyboardInterrupt:
        print("\n🛑 Stopping servers...")
        api_process.terminate()
        frontend_process.terminate()
        print("✅ Servers stopped")

if __name__ == "__main__":
    main() 