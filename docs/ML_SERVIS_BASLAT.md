# 🚀 ML Servisi Nasıl Başlatılır?

## ⚡ Hızlı Başlangıç (Basit Mod - Önerilen)

En hızlı yol, demo modda çalışan basit servisi başlatmaktır:

### Windows:
```bash
cd ml-service
START_SIMPLE.bat
```

Bu mod:
- ✅ Sadece Flask ve Flask-CORS gerektirir
- ✅ 30 saniyede başlar
- ✅ Demo tahminler döner (gerçek ML değil)
- ✅ Frontend'i test etmek için yeterli

---

## 🤖 Tam ML Servisi (Gerçek Tahminler)

Gerçek makine öğrenmesi tahminleri için:

### 1. Gereksinimleri Yükleyin

```bash
cd ml-service
pip install -r requirements.txt
```

**Not:** Bu işlem 5-10 dakika sürebilir (TensorFlow, PyTorch vb. yüklenir)

### 2. API Anahtarlarını Ayarlayın

`.env` dosyası oluşturun:

```env
FINNHUB_API_KEY=your_api_key_here
NEWS_API_KEY=78e1efb0e1964e8fbbf4158f7b9c65f1
```

Finnhub API anahtarı için: https://finnhub.io/register

### 3. Servisi Başlatın

**Windows:**
```bash
start_ml_service.bat
```

**veya Manuel:**
```bash
python app.py
```

---

## 🔍 Servis Çalışıyor mu Kontrol Et

Tarayıcıda açın:
```
http://localhost:5000/api/health
```

Başarılı yanıt:
```json
{
  "status": "ok",
  "service": "ML Stock Analysis Service",
  "model_loaded": false
}
```

---

## ❌ Sorun Giderme

### "Python yuklu degil" Hatası
- Python 3.8+ yükleyin: https://www.python.org/downloads/
- Kurulumda "Add Python to PATH" seçeneğini işaretleyin

### "Module not found" Hatası
```bash
pip install flask flask-cors
```

### Port 5000 Kullanımda
`config.py` dosyasında `FLASK_PORT` değerini değiştirin:
```python
FLASK_PORT = 5001  # veya başka bir port
```

### TensorFlow/PyTorch Yükleme Hatası
- Basit modu kullanın: `START_SIMPLE.bat`
- veya sadece gerekli paketleri yükleyin:
```bash
pip install flask flask-cors pandas numpy scikit-learn
```

---

## 📊 Hangi Modu Kullanmalıyım?

| Özellik | Basit Mod | Tam ML Servisi |
|---------|-----------|----------------|
| Kurulum Süresi | 30 saniye | 10 dakika |
| Gereksinimler | Flask + CORS | TensorFlow, PyTorch, BERT |
| Tahmin Kalitesi | Demo veri | Gerçek ML tahminleri |
| Duygu Analizi | Demo | Türkçe BERT modeli |
| Kullanım | Test/Geliştirme | Production |

**Öneri:** Önce basit modu deneyin, frontend çalışıyorsa tam servise geçin.

---

## 🔗 Frontend Entegrasyonu

ML servisi çalıştıktan sonra:

1. Express server'ı başlatın:
```bash
cd server
npm start
```

2. Frontend'i başlatın:
```bash
npm run dev
```

3. Bir hisse seçin ve "AI Yorumlar" butonuna tıklayın

---

## 📝 Notlar

- Basit mod gerçek ML tahmini yapmaz, sadece demo veri döner
- Tam servis ilk çalıştırmada BERT modelini indirir (~500MB)
- Finnhub API ücretsiz planda günlük 60 istek limiti var
- Veri toplamak için: `python run_collection.py`
