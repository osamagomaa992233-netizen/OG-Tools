@echo off
setlocal
cd /d "%~dp0"
set "PATH=%~dp0engine-bin;%PATH%"
if exist "%~dp0engine-bin\OGToolsEngine\OGToolsEngine.exe" (
  "%~dp0engine-bin\OGToolsEngine\OGToolsEngine.exe" --port 8734 >> "%LOCALAPPDATA%\OGTools\engine.log" 2>&1
) else (
  if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" -m engine.server --port 8734 >> "%LOCALAPPDATA%\OGTools\engine.log" 2>&1
  ) else (
    echo Could not find OGToolsEngine.exe or Python environment >> "%LOCALAPPDATA%\OGTools\engine.log"
  )
)
