@echo off
cd /d "%~dp0"
title VIBESTREAM RELEASE - Auto GitHub Publisher
color 0B

where git >nul 2>&1
if errorlevel 1 (
    color 0C
    echo [ERROR] Git is not installed. Install Git for Windows first: https://git-scm.com/
    pause
    exit /b 1
)

if not exist ".git" (
    git init
    git branch -M main
)

git add .
git commit -m "Release VIBESTREAM RELEASE" >nul 2>&1

where gh >nul 2>&1
if %errorlevel% equ 0 (
    gh auth status >nul 2>&1
    if %errorlevel% equ 0 (
        echo Creating public GitHub repository vibestream-release...
        gh repo create vibestream-release --public --source=. --remote=origin --push
        if %errorlevel% equ 0 (
            color 0A
            echo.
            echo DONE! Repository published on GitHub:
            gh repo view --json url -q .url
            pause
            exit /b 0
        )
    )
)

echo.
echo Enter your empty GitHub repository URL (example: https://github.com/USERNAME/vibestream-release.git):
set /p "REPO_URL="
if "%REPO_URL%"=="" (
    color 0C
    echo [ERROR] Repository URL was empty.
    pause
    exit /b 1
)

git remote remove origin >nul 2>&1
git remote add origin "%REPO_URL%"
git push -u origin main
if errorlevel 1 (
    color 0C
    echo [ERROR] Push failed. Check your GitHub login or repository URL.
    pause
    exit /b 1
)

color 0A
echo.
echo DONE! Pushed to: %REPO_URL%
pause
