@echo off
title Onix Cleaner

echo.
echo =================================
echo      Cleaning Project Files
echo =================================
echo.

echo [1/6] Removing build and dist directories...
if exist "build" (
    rmdir /s /q "build"
    echo   - 'build' directory removed.
) else (
    echo   - 'build' directory not found.
)
if exist "dist" (
    rmdir /s /q "dist"
    echo   - 'dist' directory removed.
) else (
    echo   - 'dist' directory not found.
)
echo.

echo [2/6] Removing PyInstaller spec file...
if exist "onix.spec" (
    del /q "onix.spec"
    echo   - 'onix.spec' removed.
) else (
    echo   - 'onix.spec' not found.
)
echo.

echo [3/6] Removing __pycache__ directories...
for /d /r . %%d in (__pycache__) do (
    if exist "%%d" (
        echo   - Removing "%%d"
        rmdir /s /q "%%d"
    )
)
echo   - __pycache__ cleanup complete.
echo.

echo [4/6] Removing compiled translation files (.qm)...
if exist "translations\*.qm" (
    del /q "translations\*.qm"
    echo   - .qm files in 'translations' removed.
) else (
    echo   - No .qm files found in 'translations'.
)
echo.

echo [5/6] Removing temporary config and log files...
if exist "temp_config.json" ( del /q "temp_config.json" && echo   - 'temp_config.json' removed. )
if exist "singbox_core.log" ( del /q "singbox_core.log" && echo   - 'singbox_core.log' removed. )
if exist "xray_core.log" ( del /q "xray_core.log" && echo   - 'xray_core.log' removed. )
echo.

echo [6/6] Cleanup complete.
echo.
echo =================================
echo      Project is now clean.
echo =================================
echo.
echo Press any key to close this window...
pause >nul