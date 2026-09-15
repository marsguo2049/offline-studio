@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  python scripts\install.py %*
) else (
  py -3 scripts\install.py %*
)
if errorlevel 1 (
  echo Installation failed. See the error above.
  pause
  exit /b 1
)
pause
