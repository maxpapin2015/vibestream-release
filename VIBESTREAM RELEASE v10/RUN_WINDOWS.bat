@echo off
cd /d "%~dp0"
title VibeStream Launcher
color 0A

echo ========================================================
echo   VibeStream - Free Desktop Music Player
echo ========================================================

set "PY_EXE="
where py >nul 2>&1
if %errorlevel% equ 0 (
    py -3 --version >nul 2>&1
    if %errorlevel% equ 0 set "PY_EXE=py -3"
)

if "%PY_EXE%"=="" (
    where python >nul 2>&1
    if %errorlevel% equ 0 set "PY_EXE=python"
)

if "%PY_EXE%"=="" (
    color 0C
    echo [ERROR] Python 3.10+ was not found in PATH!
    echo Download Python from https://www.python.org/downloads/
    echo Check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo [OK] Using: %PY_EXE%

if not exist ".venv\Scripts\python.exe" (
    echo [1/3] Creating virtual environment (.venv)...
    %PY_EXE% -m venv .venv
    if errorlevel 1 (
        color 0C
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

echo [2/3] Installing dependencies...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    color 0C
    echo [ERROR] Failed to install dependencies. Check your internet connection.
    pause
    exit /b 1
)

echo [3/3] Starting VibeStream...
".venv\Scripts\python.exe" main.py
if errorlevel 1 (
    color 0C
    echo [ERROR] VibeStream exited with code %errorlevel%.
    pause
)
