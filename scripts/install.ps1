# Installs LKB Orbit for the current user (no admin needed):
#   - copies the exe to %LOCALAPPDATA%\Programs\LKB Orbit
#   - adds Start Menu + Desktop shortcuts
#   - enables start-with-Windows
#   - registers an uninstall entry (Settings > Apps)
# Run from the repo root after building:  .\scripts\install.ps1
$ErrorActionPreference = 'Stop'

$src = Join-Path (Split-Path $PSScriptRoot -Parent) "dist\LKB Orbit.exe"
if (-not (Test-Path $src)) { throw "Build first: dist\LKB Orbit.exe not found. Run: pyinstaller 'LKB Orbit.spec'" }

# stop any running instance
Get-Process 'LKB Orbit' -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep 1

$dir = Join-Path $env:LOCALAPPDATA "Programs\LKB Orbit"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$exe = Join-Path $dir "LKB Orbit.exe"
Copy-Item $src $exe -Force

$ws = New-Object -ComObject WScript.Shell

$sm = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\LKB Orbit.lnk"
$s = $ws.CreateShortcut($sm); $s.TargetPath = $exe; $s.IconLocation = "$exe,0"
$s.Description = "Convert any file with a drag + Shift"; $s.WorkingDirectory = $dir; $s.Save()

$desk = [Environment]::GetFolderPath('Desktop')
$dlnk = Join-Path $desk "LKB Orbit.lnk"
$d = $ws.CreateShortcut($dlnk); $d.TargetPath = $exe; $d.IconLocation = "$exe,0"; $d.WorkingDirectory = $dir; $d.Save()

Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run" -Name "LKB Orbit" -Value "`"$exe`""

$un = Join-Path $dir "uninstall.ps1"
@"
Get-Process 'LKB Orbit' -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Remove-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Run' -Name 'LKB Orbit' -ErrorAction SilentlyContinue
Remove-Item 'HKCU:\Software\Classes\*\shell\LKB Orbit' -Recurse -ErrorAction SilentlyContinue
Remove-Item '$sm' -ErrorAction SilentlyContinue
Remove-Item '$dlnk' -ErrorAction SilentlyContinue
Remove-Item 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\LKBOrbit' -Recurse -ErrorAction SilentlyContinue
Start-Sleep 1
Remove-Item '$dir' -Recurse -Force -ErrorAction SilentlyContinue
"@ | Set-Content -Path $un -Encoding UTF8

$uk = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\LKBOrbit"
New-Item -Path $uk -Force | Out-Null
Set-ItemProperty $uk DisplayName "LKB Orbit"
Set-ItemProperty $uk DisplayVersion "0.1.2"
Set-ItemProperty $uk Publisher "Lohith Krishna Bhagavan"
Set-ItemProperty $uk DisplayIcon $exe
Set-ItemProperty $uk InstallLocation $dir
Set-ItemProperty $uk EstimatedSize ([int]((Get-Item $exe).Length / 1024))
Set-ItemProperty $uk UninstallString "powershell -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$un`""
Set-ItemProperty $uk NoModify 1
Set-ItemProperty $uk NoRepair 1

Write-Host "Installed to $exe"
Write-Host "Start Menu + Desktop shortcuts added; starts with Windows; uninstall via Settings > Apps."
Start-Process $exe
