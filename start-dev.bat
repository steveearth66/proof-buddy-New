@echo off
echo Starting Proof Buddy development servers...
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Close the windows to stop the servers.
echo.

start "Django Server" cmd /k "cd django_server && py manage.py runserver"
timeout /t 2 /nobreak >nul
start "React Dev Server" cmd /k "cd client && npm start"
