# Start Django backend and React frontend servers in parallel

Write-Host "Starting Proof Buddy development servers..." -ForegroundColor Green

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
