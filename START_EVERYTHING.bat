@echo off
chcp 65001 >nul

set "ROOT=%~dp0"
set "VENV_PYTHON=%ROOT%.venv\Scripts\python.exe"

echo ============================================================
echo   Aden Borsa - Tum Servisleri Baslat
echo ============================================================
echo.

REM .venv kontrolu
if not exist "%VENV_PYTHON%" (
    echo [HATA] .venv bulunamadi: %VENV_PYTHON%
    echo Lutfen once sanal ortami olusturun:
    echo   python -m venv .venv
    echo   .venv\Scripts\activate
    echo   pip install -r ml-service\requirements.txt
    pause
    exit /b 1
)

set "ML_DIR=%ROOT%ml-service"
set "BACKEND_DIR=%ROOT%backend"
set "FRONTEND_DIR=%ROOT%frontend"

echo [1/3] Python ML Servisi baslatiliyor...  (Port: 5000)
start "ML Service" cmd /k ""%ROOT%start_ml.bat""
timeout /t 5 /nobreak >nul

echo [2/3] Express.js Backend baslatiliyor... (Port: 3001)
start "Express Backend" /d "%BACKEND_DIR%" cmd /k "npm start"
timeout /t 3 /nobreak >nul

echo [3/3] React Frontend baslatiliyor...     (Port: 5173)
start "React Frontend" /d "%FRONTEND_DIR%" cmd /k "npm run dev"

echo.
echo ============================================================
echo   Tum servisler baslatildi!
echo ============================================================
echo.
echo   ML Service  : http://localhost:5000
echo   Backend API : http://localhost:3001
echo   Frontend    : http://localhost:5173
echo.
echo   Durdurmak icin her terminal penceresinde Ctrl+C yapin.
echo ============================================================
pause
