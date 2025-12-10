@echo off
chcp 65001 >nul
echo ============================================================
echo 🤖 Random Forest Model Eğitimi
echo ============================================================
echo.
echo Bu işlem 10-15 dakika sürebilir...
echo.
echo 📋 Yapılacaklar:
echo   1. 15 farklı hisse için veri toplama
echo   2. Teknik göstergeleri hesaplama
echo   3. Haber duygu analizi yapma
echo   4. Random Forest modelini eğitme
echo   5. Modeli kaydetme
echo.
echo ⚠️  İnternet bağlantısı gereklidir!
echo.
pause

cd /d "%~dp0"

echo.
echo ============================================================
echo 📦 Paketler kontrol ediliyor...
echo ============================================================
echo.

REM Gerekli paketleri yükle
pip install pandas numpy scikit-learn ta flask flask-cors requests textblob vaderSentiment joblib python-dotenv

echo.
echo ============================================================
echo 🚀 Model eğitimi başlıyor...
echo ============================================================
echo.

python train_random_forest.py

echo.
echo ============================================================
if errorlevel 1 (
    echo ❌ Eğitim başarısız oldu!
    echo.
    echo Olası nedenler:
    echo   - İnternet bağlantısı yok
    echo   - API limiti aşıldı
    echo   - Python paketleri eksik
) else (
    echo ✅ Eğitim tamamlandı!
    echo.
    echo 💡 Şimdi START_EVERYTHING.bat ile uygulamayı başlatabilirsiniz.
)
echo ============================================================
echo.
pause
