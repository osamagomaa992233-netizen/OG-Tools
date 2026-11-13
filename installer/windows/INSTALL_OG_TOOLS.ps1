# One-click personal Windows setup. Only installs files under user's own profile.
# No admin elevation required unless winget packages require it.
$ErrorActionPreference='Stop'
$Source=(Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$Target=Join-Path $env:LOCALAPPDATA 'OGTools'
$PluginRoot=Join-Path $env:APPDATA 'Adobe\UXP\Plugins\External'
$PluginFolder=Join-Path $PluginRoot 'com.ogtools.personal.premiere_0.8.0'
$Log=Join-Path $Target 'install.log'
$hasPortable=Test-Path (Join-Path $Source 'engine-bin\OGToolsEngine\OGToolsEngine.exe')
$Startup=Join-Path ([Environment]::GetFolderPath('Startup')) 'OGTools_AutoStart.vbs'
function Say([string]$Message){Write-Host $Message;Add-Content -Path $Log -Value $Message -Encoding UTF8}
function Find-Python {
  foreach($p in @((Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'),(Join-Path $env:LOCALAPPDATA 'Programs\Python\Python311\python.exe'))){if(Test-Path $p){return $p}}
  $py=Get-Command py -ErrorAction SilentlyContinue
  if($py){return 'py'}
  $p=Get-Command python -ErrorAction SilentlyContinue
  if($p){return $p.Source}
  return $null
}
function Install-SourceEngine {
  $python=Find-Python
  if(-not $python){
    if(-not (Get-Command winget -ErrorAction SilentlyContinue)) {throw 'Windows App Installer/winget required to install Python automatically. Use the GitHub-built portable bundle instead.'}
    Say 'Installing Python automatically (Windows may request permission)...'
    & winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements
    if($LASTEXITCODE -ne 0) { throw 'Automatic Python installation failed.' }
    $python=Find-Python
    if(-not $python) {throw 'Python was installed but cannot be found. Sign out and back in, then rerun.'}
  }
  $venv=Join-Path $Target '.venv\Scripts\python.exe'
  if(-not (Test-Path $venv)){
    Say 'Creating isolated OG Tools Python environment...'
    if($python -eq 'py'){& py -3 -m venv (Join-Path $Target '.venv')}
    else {& $python -m venv (Join-Path $Target '.venv')}
    if($LASTEXITCODE -ne 0){throw 'Cannot create virtual environment.'}
  }
  Say 'Installing image processing and offline Arabic transcription libraries...'
  & $venv -m pip install --disable-pip-version-check --upgrade 'pillow>=10,<13' faster-whisper
  if($LASTEXITCODE -ne 0){throw 'Could not install local AI dependencies. Check internet / Windows Defender and rerun.'}
}
function Ensure-FFmpeg {
  if(Test-Path (Join-Path $Target 'engine-bin\ffmpeg.exe')) {return}
  if(Get-Command ffmpeg -ErrorAction SilentlyContinue){return}
  Say 'Downloading FFmpeg essentials from gyan.dev (free software; bundled licenses vary by build)...'
  $zip=Join-Path $env:TEMP 'og_ffmpeg_essentials.zip'
  $unpacked=Join-Path $env:TEMP 'og_ffmpeg_unpacked'
  if(Test-Path $unpacked){Remove-Item -Recurse -Force $unpacked}
  Invoke-WebRequest -Uri 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip' -OutFile $zip -UseBasicParsing
  Expand-Archive -Path $zip -DestinationPath $unpacked -Force
  $ff=Get-ChildItem $unpacked -Recurse -Filter ffmpeg.exe -File | Select-Object -First 1
  $probe=Get-ChildItem $unpacked -Recurse -Filter ffprobe.exe -File | Select-Object -First 1
  if(-not $ff -or -not $probe){throw 'FFmpeg archive did not include ffmpeg.exe and ffprobe.exe'}
  $bin=Join-Path $Target 'engine-bin';New-Item -Path $bin -ItemType Directory -Force | Out-Null
  Copy-Item $ff.FullName (Join-Path $bin 'ffmpeg.exe') -Force
  Copy-Item $probe.FullName (Join-Path $bin 'ffprobe.exe') -Force
  Remove-Item $zip -Force -ErrorAction SilentlyContinue
  Remove-Item $unpacked -Recurse -Force -ErrorAction SilentlyContinue
}
try {
  New-Item -ItemType Directory -Path $Target,$PluginRoot -Force | Out-Null
  Say 'OG Tools v0.8 personal setup starting.'
  # Copy only the engine / plugin / local launcher — never modify user's Premiere projects.
  New-Item -ItemType Directory -Path (Join-Path $Target 'engine') -Force | Out-Null
  Copy-Item -Path (Join-Path $Source 'engine\*') -Destination (Join-Path $Target 'engine') -Recurse -Force
  Copy-Item (Join-Path $Source 'installer\windows\START_ENGINE_HIDDEN.cmd') $Target -Force
  if($hasPortable){
    Say 'Using prebuilt standalone Windows engine.'
    New-Item -ItemType Directory -Path (Join-Path $Target 'engine-bin') -Force | Out-Null
    Copy-Item -Path (Join-Path $Source 'engine-bin\*') -Destination (Join-Path $Target 'engine-bin') -Recurse -Force
  } else {Install-SourceEngine}
  Ensure-FFmpeg
  # Manual UXP External folder path (not the officially validated CCX workflow).
  if(Test-Path $PluginFolder){Remove-Item $PluginFolder -Recurse -Force}
  New-Item -ItemType Directory -Path $PluginFolder -Force|Out-Null
  Copy-Item -Path (Join-Path $Source 'plugin\*') -Destination $PluginFolder -Recurse -Force
  # No console window remains: Windows Script Host starts the engine silently at login.
  $runner=Join-Path $Target 'START_ENGINE_HIDDEN.cmd'
  # Chr(34) quotes paths with spaces correctly in VBScript.
  $runnerVB=$runner.Replace('"','""')
  $vbs='Set sh = CreateObject("WScript.Shell")' + "`r`n" + 'sh.Run Chr(34) & "' + $runnerVB + '" & Chr(34), 0, False' + "`r`n"
  Set-Content -Path $Startup -Value $vbs -Encoding ASCII
  $launcher=Join-Path ([Environment]::GetFolderPath('Desktop')) 'OG Tools Launcher.vbs'
  Copy-Item $Startup $launcher -Force
  # Starting twice on the same port is avoided when an earlier engine is online.
  $engineUp=$false
  try {$h=Invoke-RestMethod -Uri 'http://127.0.0.1:8734/api/health' -TimeoutSec 2;$engineUp=($h.ok -eq $true)} catch {}
  if(-not $engineUp){Start-Process -FilePath 'wscript.exe' -ArgumentList ('"'+$Startup+'"') -WindowStyle Hidden}
  $healthy=$false
  for($i=0;$i -lt 15;$i++){
    Start-Sleep -Seconds 1
    try{$h=Invoke-RestMethod -Uri 'http://127.0.0.1:8734/api/health' -TimeoutSec 2;if($h.ok -eq $true){$healthy=$true;break}}catch{}
  }
  if(-not $healthy){throw 'Engine not reachable after launch. Check engine.log. Installation NOT confirmed.'}
  Say 'Engine HTTP health check passed.'
  Say ('Plugin copied to: '+$PluginFolder)
  Say 'Startup launcher configured.'
  Say 'Setup is complete. Close and reopen Premiere, then check Window > UXP Plugins.'
  Say 'Warning: UXP External-folder loading has not been validated in Premiere 2026; if Premiere does not list the panel, UDT or a CCX package may be required.'
  Say 'Whisper model weights are not included. The first caption job downloads a model.'
  Write-Host ''
  Write-Host 'OG TOOLS SETUP FINISHED. Press Enter to close.'
  [void][Console]::ReadLine()
} catch {
  Say ('SETUP ERROR: '+$_)
  Write-Host 'Read install.log at:' $Log
  Write-Host 'Press Enter to close.'
  [void][Console]::ReadLine()
  exit 1
}
