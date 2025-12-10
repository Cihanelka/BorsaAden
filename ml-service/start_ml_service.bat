@echo off
echo ========================================
echo ML Service Baslatiyor...
echo ========================================
echo.

cd /d "%~dp0"

REM Python yuklu mu kontrol et
python --version >nul 2>&1
if errorlevel 1 (
    echo HATA: Python yuklu degil!
    echo Python 3.8+ yuklemeniz gerekiyor.
    pause
    exit /b 1
)

REM Virtual environment var mi kontrol et
if not exist "venv" (
    echo Virtual environment olusturuluyor...
    python -m venv venv
    if errorlevel 1 (
        echo HATA: Virtual environment olusturulamadi!
        pause
        exit /b 1
    )
)

REM Virtual environment'i aktif et
echo Virtual environment aktif ediliyor...
call venv\Scripts\activate.bat

REM Gerekli paketler yuklu mu kontrol et
echo Gerekli paketler kontrol ediliyor...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo Paketler yukleniyor... (Bu islem biraz zaman alabilir)
    pip install -r requirements.txt
    if errorlevel 1 (
        echo HATA: Paketler yuklenemedi!
        pause
        exit /b 1
    )
)

REM .env dosyasi var mi kontrol et
if not exist ".env" (
    echo .env dosyasi olusturuluyor...
    copy .env.example .env
    echo UYARI: .env dosyasina API anahtarlarinizi eklemeyi unutmayin!
    echo.
)

REM Data klasorlerini olustur
if not exist "data\csv" mkdir data\csv
if not exist "data\models" mkdir data\models

echo.
echo ========================================
echo ML Service Baslatiliyor...
echo Port: 5000
echo ========================================
echo.

python app.py

pause
