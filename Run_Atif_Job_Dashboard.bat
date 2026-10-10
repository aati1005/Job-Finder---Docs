@echo off
setlocal
cd /d "%~dp0"
echo ==========================================
echo Atif Job Dashboard
 echo Folder: %CD%
echo ==========================================
where python >nul 2>nul
if errorlevel 1 (
  echo Python is not installed or not in PATH.
  echo Install Python 3.11+ from https://www.python.org/downloads/ and tick Add Python to PATH.
  pause
  exit /b 1
)
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo Package installation failed. Check your internet connection and Python version.
  pause
  exit /b 1
)
python -m streamlit run app.py
if errorlevel 1 pause
endlocal
