@echo off
setlocal
chcp 65001 >nul

cd /d "%~dp0"

echo ==========================================
echo  Project Tracker Desktop - EXE build
echo ==========================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python is not found in PATH.
    echo Install Python and enable "Add python.exe to PATH", then run this file again.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo [1/6] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 goto :error
) else (
    echo [1/6] Virtual environment already exists.
)

echo [2/6] Activating virtual environment...
call ".venv\Scripts\activate.bat"
if errorlevel 1 goto :error

echo [3/6] Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 goto :error

echo [4/6] Installing application dependencies...
pip install -r requirements.txt
if errorlevel 1 goto :error

echo [5/6] Installing PyInstaller...
pip install pyinstaller
if errorlevel 1 goto :error

echo [6/6] Building one-file Windows executable...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist ProjectTracker.spec del /q ProjectTracker.spec

pyinstaller ^
  --noconfirm ^
  --clean ^
  --windowed ^
  --onefile ^
  --name ProjectTracker ^
  --collect-all customtkinter ^
  main.py

if errorlevel 1 goto :error

echo.
echo ==========================================
echo  DONE
echo  EXE: dist\ProjectTracker.exe
echo ==========================================
echo.
echo The database will be created on first launch next to the EXE:
echo dist\data\project_tracker.db
echo.
pause
exit /b 0

:error
echo.
echo ==========================================
echo  BUILD FAILED
echo ==========================================
echo Check the error text above. If PyInstaller complains about the Python version,
echo try building from a stable Python 3.12/3.13 virtual environment.
echo.
pause
exit /b 1
