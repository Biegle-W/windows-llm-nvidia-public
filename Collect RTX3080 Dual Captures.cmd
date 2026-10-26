@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Prepare-RTX3080DualProbeUsb.ps1" -Mode Collect
pause
