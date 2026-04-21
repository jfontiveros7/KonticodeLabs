Set-Location "$PSScriptRoot"

$projectRoot = (Get-Location).Path
$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    Write-Error "Python executable not found at $pythonExe"
    exit 1
}

# Stop only existing main.py processes from this project to avoid port conflicts.
Get-CimInstance Win32_Process |
    Where-Object {
        $_.Name -eq "python.exe" -and
        $_.CommandLine -like "*$projectRoot*main.py*"
    } |
    ForEach-Object {
        Stop-Process -Id $_.ProcessId -Force
        Write-Host "Stopped stale process $($_.ProcessId)"
    }

Remove-Item Env:PORT -ErrorAction SilentlyContinue

Write-Host "Starting app on http://127.0.0.1:5000"
& $pythonExe "main.py"
