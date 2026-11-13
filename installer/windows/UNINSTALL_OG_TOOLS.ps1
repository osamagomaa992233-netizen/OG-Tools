$ErrorActionPreference='Stop'
$install=Join-Path $env:LOCALAPPDATA 'OGTools'
$plugin=Join-Path $env:APPDATA 'Adobe\UXP\Plugins\External\com.ogtools.personal.premiere_0.8.0'
$startup=Join-Path ([Environment]::GetFolderPath('Startup')) 'OGTools_AutoStart.vbs'
$desktop=Join-Path ([Environment]::GetFolderPath('Desktop')) 'OG Tools Launcher.vbs'
foreach($file in @($startup,$desktop)){if(Test-Path $file){Remove-Item $file -Force}}
if(Test-Path $plugin){Remove-Item $plugin -Recurse -Force}
Write-Host 'Panel and autostart removed. Close running OG Tools engine from Task Manager before deleting engine files.'
Write-Host "Engine directory retained at $install to preserve logs. Delete it manually if desired."
