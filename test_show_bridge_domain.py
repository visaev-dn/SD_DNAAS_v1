import paramiko
import yaml
from pathlib import Path
import time

DEVICE_NAME = 'DNAAS-LEAF-B14'
SERVICE_NAME = 'g_visaev_v123'
OUTPUT_FILE = f'test_output_{DEVICE_NAME}_{SERVICE_NAME}.txt'

# Load device info from devices.yaml
def load_device_info(device_name):
    devices_file = Path('devices.yaml')
    with open(devices_file, 'r') as f:
        devices_data = yaml.safe_load(f)
    defaults = devices_data.get('defaults', {})
    device_data = devices_data.get(device_name, {})
    info = {
        'hostname': device_data.get('mgmt_ip'),
        'username': device_data.get('username', defaults.get('username')),
        'password': device_data.get('password', defaults.get('password')),
        'port': device_data.get('ssh_port', defaults.get('ssh_port', 22)),
    }
    return info

def main():
    device_info = load_device_info(DEVICE_NAME)
    if not device_info['hostname']:
        print(f"No hostname for {DEVICE_NAME}")
        return
    
    print(f"Connecting to {DEVICE_NAME} ({device_info['hostname']})...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        hostname=device_info['hostname'],
        port=device_info['port'],
        username=device_info['username'],
        password=device_info['password'],
        look_for_keys=False,
        allow_agent=False,
        timeout=15
    )
    
    # Use interactive shell like our deployment
    shell = ssh.invoke_shell()
    shell.settimeout(10)
    output = ''
    
    # Wait for initial prompt
    time.sleep(1)
    try:
        initial_output = shell.recv(4096).decode(errors='ignore')
        output += initial_output
        print(f"Initial prompt: {initial_output.strip()}")
    except Exception as e:
        print(f"Warning: Timeout getting initial output: {e}")
    
    # Try the command in interactive shell
    command = f"show network-services bridge-domain {SERVICE_NAME}"
    print(f"Running: {command}")
    shell.send(command + '\n')
    time.sleep(2)
    
    try:
        response = shell.recv(4096).decode(errors='ignore')
        output += response
        print(f"Response: {response}")
    except Exception as e:
        print(f"Warning: Timeout getting response: {e}")
    
    # Also try with exec_command for comparison
    print("\n--- Also trying exec_command for comparison ---")
    stdin, stdout, stderr = ssh.exec_command(command, timeout=10)
    exec_output = stdout.read().decode()
    exec_error = stderr.read().decode()
    
    ssh.close()
    
    print(f"Saving output to {OUTPUT_FILE}")
    with open(OUTPUT_FILE, 'w') as f:
        f.write(f"=== INTERACTIVE SHELL TEST ===\n")
        f.write(f"Command: {command}\n")
        f.write(f"Full interactive output:\n{output}\n")
        f.write(f"\n=== EXEC_COMMAND TEST ===\n")
        f.write(f"Command: {command}\n")
        f.write(f"STDOUT:\n{exec_output}\n")
        f.write(f"STDERR:\n{exec_error}\n")
    
    print("Done.")

if __name__ == '__main__':
    main() 