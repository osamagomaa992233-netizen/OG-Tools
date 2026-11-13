@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (echo First run START_OG_TOOLS_WINDOWS.bat & pause & exit /b 1)
echo Installing optional whisper captions, rembg and OpenCV. These can download model weights on first use.
.venv\Scripts\python.exe -m pip install faster-whisper "rembg[cpu]" opencv-python auto-editor yt-dlp
if errorlevel 1 pause
