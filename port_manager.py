#!/usr/bin/env python3
"""
Port Management Utility
Helps track and resolve port conflicts
"""

import subprocess
import sys
import os
import signal
import time

def check_port(port):
    """Check if a port is in use and return details"""
    try:
        result = subprocess.run(['lsof', '-i', f':{port}'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:  # Has header + data
                return True, lines[1:]  # Return True and process details
        return False, []
    except Exception as e:
        print(f"Error checking port {port}: {e}")
        return False, []

def kill_process_by_pid(pid):
    """Kill a process by PID"""
    try:
        os.kill(int(pid), signal.SIGTERM)
        time.sleep(1)
        # Check if still running
        try:
            os.kill(int(pid), 0)  # Check if process exists
            os.kill(int(pid), signal.SIGKILL)  # Force kill
            print(f"⚠️ Force killed process {pid}")
        except OSError:
            print(f"✅ Successfully killed process {pid}")
    except Exception as e:
        print(f"❌ Failed to kill process {pid}: {e}")

def kill_processes_by_name(name_pattern):
    """Kill processes by name pattern"""
    try:
        result = subprocess.run(['pkill', '-f', name_pattern], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Killed processes matching '{name_pattern}'")
        else:
            print(f"ℹ️ No processes found matching '{name_pattern}'")
    except Exception as e:
        print(f"❌ Error killing processes: {e}")

def find_free_port(start_port, max_attempts=10):
    """Find a free port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        in_use, _ = check_port(port)
        if not in_use:
            return port
    return None

def main():
    """Main port management interface"""
    if len(sys.argv) < 2:
        print("🔧 Port Management Utility")
        print("Usage:")
        print("  python3 port_manager.py check <port>     - Check if port is in use")
        print("  python3 port_manager.py kill <port>      - Kill processes using port")
        print("  python3 port_manager.py free <start>     - Find free port starting from <start>")
        print("  python3 port_manager.py clean            - Kill common development processes")
        return

    command = sys.argv[1]

    if command == "check" and len(sys.argv) >= 3:
        port = sys.argv[2]
        in_use, processes = check_port(port)
        if in_use:
            print(f"🔴 Port {port} is in use by:")
            for process in processes:
                parts = process.split()
                if len(parts) >= 2:
                    cmd, pid = parts[0], parts[1]
                    print(f"  - {cmd} (PID: {pid})")
        else:
            print(f"🟢 Port {port} is free")

    elif command == "kill" and len(sys.argv) >= 3:
        port = sys.argv[2]
        in_use, processes = check_port(port)
        if in_use:
            print(f"🔴 Port {port} is in use. Killing processes...")
            for process in processes:
                parts = process.split()
                if len(parts) >= 2:
                    pid = parts[1]
                    kill_process_by_pid(pid)
        else:
            print(f"🟢 Port {port} is already free")

    elif command == "free" and len(sys.argv) >= 3:
        start_port = int(sys.argv[2])
        free_port = find_free_port(start_port)
        if free_port:
            print(f"🟢 Found free port: {free_port}")
        else:
            print(f"🔴 No free ports found starting from {start_port}")

    elif command == "clean":
        print("🧹 Cleaning up common development processes...")
        patterns = [
            "python.*api_server",
            "node.*vite",
            "node.*dev",
            "python.*flask"
        ]
        for pattern in patterns:
            kill_processes_by_name(pattern)
        
        # Kill specific ports
        ports_to_clean = [5001, 8080, 8081, 3000, 3001]
        for port in ports_to_clean:
            in_use, processes = check_port(port)
            if in_use:
                print(f"🔴 Cleaning port {port}...")
                for process in processes:
                    parts = process.split()
                    if len(parts) >= 2:
                        pid = parts[1]
                        kill_process_by_pid(pid)

    else:
        print("❌ Invalid command. Use 'check', 'kill', 'free', or 'clean'")

if __name__ == "__main__":
    main() 