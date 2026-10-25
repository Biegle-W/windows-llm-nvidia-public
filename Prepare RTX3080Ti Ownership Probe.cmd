@echo off
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Prepare-RTX3080TiProbeUsb.ps1" -Mode Ownership
pause
