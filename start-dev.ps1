# Start Django backend and React frontend servers in parallel

Write-Host "Starting Proof Buddy development servers..." -ForegroundColor Green

# Kill any processes running on port 8000 (Django)
Write-Host "Checking for processes on port 8000..." -ForegroundColor Yellow
$port8000 = netstat -ano | findstr :8000 | findstr LISTENING
if ($port8000) {
    $pid8000 = ($port8000 -split '\s+')[-1]
    Write-Host "Killing process $pid8000 on port 8000..." -ForegroundColor Yellow
    taskkill /PID $pid8000 /F | Out-Null
}

# Kill any processes running on port 3000 (React)
Write-Host "Checking for processes on port 3000..." -ForegroundColor Yellow
$port3000 = netstat -ano | findstr :3000 | findstr LISTENING
if ($port3000) {
    $pid3000 = ($port3000 -split '\s+')[-1]
    Write-Host "Killing process $pid3000 on port 3000..." -ForegroundColor Yellow
    taskkill /PID $pid3000 /F | Out-Null
}

Start-Sleep -Seconds 1

# Start Django server in new PowerShell window
Write-Host "Launching Django server on http://localhost:8000..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\django_server'; py manage.py runserver"

# Wait a moment before starting frontend to avoid port conflicts
Start-Sleep -Seconds 2

# Start React dev server in new PowerShell window
Write-Host "Launching React dev server on http://localhost:3000..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\client'; npm start"

Write-Host "`nBoth servers are starting in separate windows." -ForegroundColor Green
Write-Host "Backend: http://localhost:8000" -ForegroundColor Yellow
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Yellow
Write-Host "`nClose the PowerShell windows to stop the servers." -ForegroundColor Gray
