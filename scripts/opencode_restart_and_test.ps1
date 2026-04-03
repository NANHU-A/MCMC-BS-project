<#
PowerShell helper to backup opencode config, optionally restart identifiable opencode-related services/processes,
and run basic connectivity / config checks.

Safe mode: this script will NOT forcibly restart arbitrary processes without explicit confirmation.
Run as Administrator when restarting services or querying ports.

Usage:
  Open an elevated PowerShell and run:
    .\scripts\opencode_restart_and_test.ps1

What it does:
  - Backups the opencode.json (adds timestamped .bak)
  - Validates JSON syntax
  - Detects processes listening on ports 12306 and 11434 (common MCP / provider ports)
  - Lists processes whose command line or path contains "opencode"
  - If any Windows Service with name/displayname containing "opencode" is found, offers to restart it
  - For ordinary processes, offers to stop (kill) them and shows their executable path; does NOT auto-restart unless a start command is known
  - Runs simple HTTP checks against localhost:12306 and localhost:11434 and reports status
  - Writes a short report to scripts/opencode_restart_and_test.log

#>

Set-StrictMode -Version Latest
cls

function Timestamp() { return (Get-Date).ToString('yyyyMMdd-HHmmss') }

$reportPath = Join-Path -Path (Get-Location) -ChildPath 'scripts\opencode_restart_and_test.log'
"`n===== Opencode Restart & Test - $(Get-Date) =====`n" | Out-File -FilePath $reportPath -Encoding utf8 -Append

$configPath = Join-Path -Path $env:USERPROFILE -ChildPath '.config\opencode\opencode.json'
Write-Host "Using config path: $configPath"
"Using config path: $configPath" | Out-File -FilePath $reportPath -Encoding utf8 -Append

if (-Not (Test-Path $configPath)) {
    Write-Warning "Config file not found at $configPath. Aborting backup and validation steps."
    "Config file not found at $configPath" | Out-File -FilePath $reportPath -Encoding utf8 -Append
} else {
    # Backup
    $bak = "$configPath.bak.$(Timestamp)"
    Copy-Item -Path $configPath -Destination $bak -Force
    Write-Host "Backed up config to: $bak"
    "Backed up config to: $bak" | Out-File -FilePath $reportPath -Encoding utf8 -Append

    # Validate JSON
    try {
        $json = Get-Content $configPath -Raw | ConvertFrom-Json
        Write-Host "Config JSON parsed successfully"
        "Config JSON parsed successfully" | Out-File -FilePath $reportPath -Encoding utf8 -Append
    } catch {
        Write-Error "JSON parse error: $_"
        "JSON parse error: $_" | Out-File -FilePath $reportPath -Encoding utf8 -Append
        Write-Host "Please fix the JSON before proceeding. Exiting."
        exit 1
    }
}

# Detect listeners on common ports
$ports = @(12306,11434)
foreach ($p in $ports) {
    try {
        # Get-NetTCPConnection may require admin; fall back to netstat
        $conn = Get-NetTCPConnection -LocalPort $p -ErrorAction Stop
        if ($conn) {
            $pid = $conn.OwningProcess
            $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
            if ($proc) {
                Write-Host "Port $p is LISTENING by process: $($proc.ProcessName) (PID $pid)"
                "Port $p listening by $($proc.ProcessName) (PID $pid)" | Out-File -FilePath $reportPath -Encoding utf8 -Append
            }
        }
    } catch {
        # fallback netstat parse
        $ns = netstat -ano | Select-String ":$p\s"
        if ($ns) {
            $line = $ns[-1].Line
            $tokens = $line -split '\s+' | Where-Object { $_ -ne '' }
            $pid = $tokens[-1]
            try { $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue } catch { $proc = $null }
            Write-Host "(netstat) Port $p: $line"
            "(netstat) Port $p: $line" | Out-File -FilePath $reportPath -Encoding utf8 -Append
            if ($proc) { 
                Write-Host "  -> Process: $($proc.ProcessName) (Path: $($proc.Path))"
                " -> Process: $($proc.ProcessName) (Path: $($proc.Path))" | Out-File -FilePath $reportPath -Encoding utf8 -Append
            }
        } else {
            Write-Host "Port $p: no listener detected"
            "Port $p: no listener detected" | Out-File -FilePath $reportPath -Encoding utf8 -Append
        }
    }
}

# Find candidate processes referencing opencode
Write-Host "Searching for processes with 'opencode' in command line or path..."
"Searching for processes with 'opencode' in command line or path..." | Out-File -FilePath $reportPath -Encoding utf8 -Append

$matches = @()
try {
    $procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and ($_.CommandLine -match 'opencode' -or $_.CommandLine -match 'opencode.json') }
    foreach ($p in $procs) { $matches += $p }
} catch {
    # best effort
}

if ($matches.Count -eq 0) {
    Write-Host "No processes found with 'opencode' in their command line."
    "No processes found with 'opencode' in command line." | Out-File -FilePath $reportPath -Encoding utf8 -Append
} else {
    foreach ($m in $matches) {
        $pid = $m.ProcessId
        $cmd = $m.CommandLine
        Write-Host "PID $pid : $cmd"
        "PID $pid : $cmd" | Out-File -FilePath $reportPath -Encoding utf8 -Append
    }
}

# Search for Windows services with name/display containing 'opencode'
Write-Host "Searching Windows services with 'opencode' in name/displayname..."
"Searching Windows services with 'opencode' in name/displayname..." | Out-File -FilePath $reportPath -Encoding utf8 -Append
$svcMatches = Get-Service | Where-Object { $_.Name -match 'opencode' -or $_.DisplayName -match 'opencode' }
if ($svcMatches.Count -gt 0) {
    foreach ($s in $svcMatches) {
        Write-Host "Service: $($s.Name) - Status: $($s.Status)"
        "Service: $($s.Name) - Status: $($s.Status)" | Out-File -FilePath $reportPath -Encoding utf8 -Append
    }
    $doRestart = Read-Host "Restart these services now? (y/N)"
    if ($doRestart -match '^[yY]') {
        foreach ($s in $svcMatches) {
            try {
                Restart-Service -Name $s.Name -Force -ErrorAction Stop
                Write-Host "Restarted service $($s.Name)"
                "Restarted service $($s.Name)" | Out-File -FilePath $reportPath -Encoding utf8 -Append
            } catch {
                Write-Error "Failed to restart $($s.Name): $_"
                "Failed to restart $($s.Name): $_" | Out-File -FilePath $reportPath -Encoding utf8 -Append
            }
        }
    } else { Write-Host "Skipping service restart."; "Skipping service restart." | Out-File -FilePath $reportPath -Encoding utf8 -Append }
} else { Write-Host "No opencode Windows services found."; "No opencode Windows services found." | Out-File -FilePath $reportPath -Encoding utf8 -Append }

# For non-service processes found earlier, offer soft-restart (stop only)
if ($matches.Count -gt 0) {
    $ans = Read-Host "Stop (kill) listed opencode-related processes? This will terminate them; you may need to restart manually. (y/N)"
    if ($ans -match '^[yY]') {
        foreach ($m in $matches) {
            $pid = $m.ProcessId
            try {
                Stop-Process -Id $pid -Force -ErrorAction Stop
                Write-Host "Stopped PID $pid"
                "Stopped PID $pid" | Out-File -FilePath $reportPath -Encoding utf8 -Append
            } catch {
                Write-Error "Failed to stop PID $pid: $_"
                "Failed to stop PID $pid: $_" | Out-File -FilePath $reportPath -Encoding utf8 -Append
            }
        }
    } else { Write-Host "Skipping process stop."; "Skipping process stop." | Out-File -FilePath $reportPath -Encoding utf8 -Append }
}

# Wait a short moment for services/processes to settle
Start-Sleep -Seconds 2

# Run HTTP checks
function HttpCheck($url) {
    try {
        $resp = Invoke-WebRequest -Uri $url -UseBasicParsing -Method GET -TimeoutSec 5
        Write-Host "HTTP $url -> $($resp.StatusCode)"
        "HTTP $url -> $($resp.StatusCode)" | Out-File -FilePath $reportPath -Encoding utf8 -Append
    } catch {
        Write-Warning "HTTP $url -> failed: $_"
        "HTTP $url -> failed: $_" | Out-File -FilePath $reportPath -Encoding utf8 -Append
    }
}

$testUrls = @('http://127.0.0.1:12306/mcp','http://127.0.0.1:11434','http://127.0.0.1:11434/v1')
foreach ($u in $testUrls) { HttpCheck $u }

Write-Host "Test complete. Report saved to: $reportPath"
"Test complete. Report saved to: $reportPath" | Out-File -FilePath $reportPath -Encoding utf8 -Append

exit 0
