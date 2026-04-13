@echo off
REM Build Spring Generator – Windows
REM Requires: pip install flask numpy pyinstaller

setlocal
cd /d "%~dp0"

echo Installing / updating dependencies...
pip install -q flask numpy pyinstaller

echo Building executable...
pyinstaller spring_generator.spec --clean

if errorlevel 1 (
    echo Build FAILED.
    exit /b 1
)

echo.
echo Build successful.  Executable: dist\spring_generator.exe
pause
