@echo off
setlocal
cd /d "%~dp0"
set PYTHON=py -3
%PYTHON% --version >NUL 2>&1
if errorlevel 1 (
  set PYTHON=python
  python --version >NUL 2>&1
)
%PYTHON% --version >NUL 2>&1
if errorlevel 1 (
  echo Python 3.11+ is needed. Install it from python.org or winget.
  pause
  exit /b 1
)
if not exist .venv\Scripts\python.exe (
  %PYTHON% -m venv .venv
  if errorlevel 1 (echo Could not create Python environment. & pause & exit /b 1)
)
.venv\Scripts\python.exe -c "import PIL" >NUL 2>&1
if errorlevel 1 (
  echo Installing first-run Pillow dependency...
  .venv\Scripts\python.exe -m pip install pillow
  if errorlevel 1 (pause & exit /b 1)
)
where ffmpeg >NUL 2>&1
if errorlevel 1 (
  echo WARNING: FFmpeg not on PATH. Motion and media tools need FFmpeg.
  echo Try: winget install Gyan.FFmpeg
)
echo.
echo =================================================
echo    OG TOOLS Local Engine for Premiere Pro 2026
echo    Address: http://127.0.0.1:8734

echo    Keep this window open while using OG Tools.
echo =================================================
echo.
.venv\Scripts\python.exe -m engine.server --port 8734
if errorlevel 1 pause
