@echo off
echo Building Iceberg Launcher executable...

REM Check if PyInstaller is installed
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

REM Clean previous builds
echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Build executable
echo Building executable...
pyinstaller IcebergLauncher.spec

REM Check if build was successful
if exist "dist\IcebergLauncher.exe" (
    echo ✅ Build successful!
    echo Executable created at: dist\IcebergLauncher.exe
    for %%I in ("dist\IcebergLauncher.exe") do echo Size: %%~zI bytes
) else (
    echo ❌ Build failed!
    pause
    exit /b 1
)

echo 🎉 Iceberg Launcher build complete!
echo Run with: dist\IcebergLauncher.exe
pause
