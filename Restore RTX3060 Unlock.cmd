@echo off
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Set-GpuBootMode.ps1" -Mode 3060 -Elevate
if errorlevel 1 pause
