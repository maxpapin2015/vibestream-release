$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Host "========================================================" -ForegroundColor Green
Write-Host "  VibeStream - Launcher & EXE Builder v5" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
Write-Host ""

function Find-Python {
    foreach ($cmd in @("py", "python", "python3")) {
        $found = Get-Command $cmd -ErrorAction SilentlyContinue
        if ($found) {
            try {
                if ($cmd -eq "py") {
                    & py -3 --version 2>$null | Out-Null
                    if ($LASTEXITCODE -eq 0) { return "py -3" }
                } else {
                    & $cmd --version 2>$null | Out-Null
                    if ($LASTEXITCODE -eq 0) { return $cmd }
                }
            } catch {}
        }
    }
    return $null
}

$pyCmd = Find-Python

if (-not $pyCmd) {
    Write-Host "[!] Python не найден в системе." -ForegroundColor Yellow
    $installAns = Read-Host "Установить Python 3.12 автоматически через winget? (Y/N)"
    if ($installAns -match "^[YyДд]$") {
        winget install --id Python.Python.3.12 -e --source winget --accept-package-agreements --accept-source-agreements
        Write-Host "[!] После установки Python перезапустите START_HERE.bat." -ForegroundColor Yellow
        return
    } else {
        Write-Host "[X] Скачайте Python 3.12 с https://www.python.org/downloads/ и отметьте 'Add Python to PATH'." -ForegroundColor Red
        return
    }
}

Write-Host "[OK] Найден Python: $pyCmd" -ForegroundColor Green

$venvPy = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPy)) {
    Write-Host "[1/3] Создаю виртуальное окружение .venv..." -ForegroundColor Cyan
    if ($pyCmd -eq "py -3") {
        & py -3 -m venv .venv
    } else {
        & $pyCmd -m venv .venv
    }
}

Write-Host "[2/3] Устанавливаю зависимости..." -ForegroundColor Cyan
& $venvPy -m pip install --upgrade pip --quiet
& $venvPy -m pip install -r requirements.txt

Write-Host ""
Write-Host "Выберите действие:" -ForegroundColor Green
Write-Host "  [1] Запустить плеер VibeStream сейчас"
Write-Host "  [2] Собрать автономный файл dist\VibeStream.exe (с модулями vibestream)"
Write-Host "  [3] Собрать VibeStream.exe И сразу запустить его"
$choice = Read-Host "Введите 1, 2 или 3 (по умолчанию 1)"
if ([string]::IsNullOrWhiteSpace($choice)) { $choice = "1" }

if ($choice -eq "2" -or $choice -eq "3") {
    Write-Host "[*] Генерирую иконку vibestream.ico..." -ForegroundColor Cyan
    if (Test-Path "make_icon.py") {
        & $venvPy make_icon.py
    }
    Write-Host "[*] Собираю VibeStream.exe через PyInstaller..." -ForegroundColor Cyan
    $iconArgs = @()
    if (Test-Path "vibestream.ico") {
        $iconArgs = @("--icon", "vibestream.ico")
    }
    & $venvPy -m PyInstaller --clean --noconfirm --onefile --windowed --name "VibeStream" @iconArgs --paths "." --add-data "vibestream;vibestream" --collect-all "yt_dlp" --hidden-import "vibestream" --hidden-import "vibestream.core" --hidden-import "vibestream.core.storage" --hidden-import "vibestream.core.music_provider" --hidden-import "vibestream.ui" --hidden-import "vibestream.ui.styles" --hidden-import "vibestream.ui.visualizer" --hidden-import "vibestream.ui.mini_player" --hidden-import "vibestream.ui.main_window" --hidden-import "PyQt6.QtMultimedia" --hidden-import "PyQt6.QtNetwork" main.py
    $exePath = Join-Path $PSScriptRoot "dist\VibeStream.exe"
    if (Test-Path $exePath) {
        Write-Host "[OK] Собран файл: $exePath" -ForegroundColor Green
        if ($choice -eq "3") {
            Start-Process $exePath
        } else {
            Start-Process (Join-Path $PSScriptRoot "dist")
        }
    } else {
        Write-Host "[X] dist\VibeStream.exe не найден после сборки." -ForegroundColor Red
    }
} else {
    Write-Host "[*] Запускаю VibeStream..." -ForegroundColor Cyan
    & $venvPy main.py
}
