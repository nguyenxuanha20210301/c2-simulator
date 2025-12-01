import socketio
import time
import platform 

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