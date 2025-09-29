@echo off
title Onix Builder

echo.
echo =================================
echo      Starting Onix Build
echo =================================
echo.

REM --- Step 1: Check Prerequisites (including sing-box download) ---
echo [1/5] Checking prerequisites...
if not exist "main.py" echo ERROR: 'main.py' not found. & goto :fail

echo [1/5] Ensuring sing-box binary is available...
python download_singbox.py
if %errorlevel% neq 0 (
    echo ERROR: Failed to ensure sing-box binary.
    goto :fail
)
echo sing-box binary check complete.

where pyinstaller >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: 'pyinstaller' command not found.
    echo Please make sure Python and PyInstaller are installed correctly.
    echo You can install it by running: pip install pyinstaller
    goto :fail
)
echo Prerequisites check passed.
echo.


REM --- Step 2: Create version.txt ---
echo [2/5] Creating version.txt...
(echo dev) > version.txt
if not exist "version.txt" echo ERROR: Failed to create version.txt. & goto :fail
echo version.txt created.
echo.

REM --- Step 3: Compile Translations ---
echo [3/5] Compiling translation files (.qm)...
python update_translations.py
if %errorlevel% neq 0 (
    echo ERROR: Failed to compile translations.
    goto :fail
)
echo Translations compiled successfully.
echo.

REM --- Step 4: Download GeoIP database ---
echo [4/5] Checking for GeoIP database...
if exist "geoip.db" (
    echo geoip.db already exists.
) else (
    echo Downloading geoip.db...
    powershell -ExecutionPolicy Bypass -NoProfile -Command "try { [Net.ServicePointManager]::SecurityProtocol = 'Tls12'; Invoke-WebRequest -Uri 'https://github.com/SagerNet/sing-geoip/releases/latest/download/geoip.db' -OutFile 'geoip.db' } catch { Write-Host 'Download failed.'; exit 1 }"
    if not exist "geoip.db" (
        echo ERROR: Automatic download of geoip.db failed.
        echo Please download it manually from:
        echo https://github.com/SagerNet/sing-geoip/releases/latest/download/geoip.db
        echo And place it in this directory.
        goto :fail
    )
    echo geoip.db downloaded.
)
echo.

REM --- Step 5: Build the executable ---
echo [5/5] Building the executable with PyInstaller...
echo This might take a few minutes.
echo.

pyinstaller --noconfirm --onefile --windowed --name onix --add-data "sing-box.exe;." --add-data "version.txt;." --add-data "geoip.db;." --add-data "translations;translations" --icon="assets/icon.ico" main.py

if %errorlevel% neq 0 (
    echo ERROR: PyInstaller build failed.
    goto :fail
)

REM --- Step 6: Cleanup and Final Message ---
echo [6/6] Cleaning up...
del version.txt

echo.
echo =======================================================
echo  Build successful!
echo  The executable 'onix.exe' can be found in the 'dist' folder.
echo =======================================================
goto :end

:fail
echo.
echo =======================================================
echo  Build failed! Please check the output above for errors.
echo =======================================================

:end
echo.
echo Press any key to close this window...
pause >nul
