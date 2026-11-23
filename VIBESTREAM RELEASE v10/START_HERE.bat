@echo off
cd /d "%~dp0"
powershell.exe -NoExit -ExecutionPolicy Bypass -File "%~dp0START_AND_BUILD.ps1"
