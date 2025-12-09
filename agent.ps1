# --- CẤU HÌNH ---
$server_url = "http://127.0.0.1:8080"
$agent_id = $null

# --- HÀM CHỨC NĂNG ---

function Register-Agent {
    # Lấy tên máy tính hiện tại
    $hostname = $env:COMPUTERNAME
    
    Write-Host "[*] Sending registration request to $server_url..." -ForegroundColor Cyan
    
    try {
        # Gửi Request POST để xin ID
        $response = Invoke-RestMethod -Uri "$server_url/reg" -Method POST -Body @{name=$hostname}
        return $response
    }
    catch {
        Write-Host "[-] Connection failed: $_" -ForegroundColor Red
        return $null
    }
}

# --- MAIN ---
# 1. Thử đăng ký
$id = Register-Agent

if ($id) {
    $agent_id = $id
    Write-Host "[+] Registered successfully! My ID is: $agent_id" -ForegroundColor Green
} else {
    Write-Host "[-] Registration failed. Exiting."
    exit
}

# (Tạm dừng để bạn kịp nhìn thấy kết quả khi test)
Read-Host "Press Enter to exit..."