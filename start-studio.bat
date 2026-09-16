@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Run install.bat first.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" scripts\launch.py %*
set "STUDIO_EXIT_CODE=%ERRORLEVEL%"
if not "%STUDIO_EXIT_CODE%"=="0" pause
exit /b %STUDIO_EXIT_CODE%
