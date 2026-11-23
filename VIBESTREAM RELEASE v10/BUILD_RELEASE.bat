@echo off
cd /d "%~dp0"
title VIBESTREAM RELEASE Builder
color 0B

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
    echo [ERROR] Python 3.10+ was not found in PATH.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    %PY_EXE% -m venv .venv
)

".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    color 0C
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" make_icon.py
".venv\Scripts\python.exe" -m PyInstaller --clean --noconfirm --onefile --windowed --name "VIBESTREAM RELEASE" --icon "vibestream.ico" --paths "." --add-data "vibestream;vibestream" --collect-all "yt_dlp" --hidden-import "vibestream" --hidden-import "vibestream.core" --hidden-import "vibestream.core.storage" --hidden-import "vibestream.core.music_provider" --hidden-import "vibestream.ui" --hidden-import "vibestream.ui.styles" --hidden-import "vibestream.ui.visualizer" --hidden-import "vibestream.ui.mini_player" --hidden-import "vibestream.ui.main_window" --hidden-import "vibestream.ui.icons" --hidden-import "vibestream.ui.star_rating" --hidden-import "vibestream.ui.playing_indicator" --hidden-import "PyQt6.QtMultimedia" --hidden-import "PyQt6.QtNetwork" main.py
if errorlevel 1 (
    color 0C
    echo [ERROR] PyInstaller build failed.
    pause
    exit /b 1
)

color 0A
echo.
echo SUCCESS! Built: %~dp0dist\VIBESTREAM RELEASE.exe
if exist "dist" explorer "dist"
pause
