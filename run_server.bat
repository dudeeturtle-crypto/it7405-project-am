@echo off
setlocal
set ROOT=%~dp0
set PYTHON=%ROOT%.venv\Scripts\python.exe
if not exist "%PYTHON%" (
  echo Python not found at %PYTHON%
  echo Ensure your virtualenv is created at .venv and try again.
  exit /b 1
)
"%PYTHON%" "%ROOT%manage.py" runserver 127.0.0.1:8001
endlocal
