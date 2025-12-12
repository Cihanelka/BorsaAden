@echo off
chcp 65001 >nul
echo ============================================================
echo 🚀 Aden Borsa - Tüm Servisleri Başlat
echo ============================================================
echo.

echo [1/3] 🤖 Python ML Servisi başlatılıyor...
echo Port: 5000
echo Mode: Random Forest (Eğitilmiş Model)
start "ML Service" cmd /k "cd ml-service && python app.py"
timeout /t 3 /nobreak >nul

echo.
echo [2/3] 🔧 Express.js Backend başlatılıyor...
echo Port: 3001
start "Express Backend" cmd /k "cd server && npm start"
timeout /t 3 /nobreak >nul

echo.
echo [3/3] ⚛️ React Frontend başlatılıyor...
echo Port: 5173
start "React Frontend" cmd /k "npm run dev"

echo.
echo ============================================================
echo ✅ Tüm servisler başlatıldı!
echo ============================================================
echo.
echo 📡 ML Service:      http://localhost:5000
echo 🔧 Backend API:     http://localhost:3001
echo ⚛️ Frontend:        http://localhost:5173
echo.
echo ⚠️ Servisler ayrı terminal pencerelerinde çalışıyor.
echo 💡 Durdurmak için her terminal penceresinde Ctrl+C yapın.
echo.
echo ============================================================
pause
