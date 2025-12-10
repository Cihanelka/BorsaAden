# ⚡ Hızlı Başlangıç

## 🎯 5 Dakikada Başlayın

### 1️⃣ İlk Kurulum (Sadece Bir Kez)

```bash
# Python bağımlılıklarını yükleyin
cd ml-service
pip install -r requirements.txt
python setup.py

# .env dosyasını düzenleyin ve API anahtarınızı ekleyin
# FINNHUB_API_KEY=your_key_here

# Node.js bağımlılıklarını yükleyin
cd ..
npm install

cd server
npm install

cd ..
```

### 2️⃣ Veri Toplayın (İlk Kez)

```bash
cd ml-service
python run_collection.py
```

Bu adım ~5-10 dakika sürer. İstediğiniz hisseleri seçip onaylayın.

### 3️⃣ Servisleri Başlatın

**Windows:**
```bash
START_EVERYTHING.bat
```

**Linux/Mac:**
```bash
# Terminal 1 - ML Service
cd ml-service && python app.py

# Terminal 2 - Backend
cd server && npm start

# Terminal 3 - Frontend
npm run dev
```

### 4️⃣ Tarayıcıda Açın

http://localhost:5173

## 🎮 Temel Kullanım

1. **Hisse Seçin**: Arama çubuğundan (örn: AAPL)
2. **AI Tahmin**: "AI Tahmin Sistemi" kartından tahmin alın
3. **Sonuçları İnceleyin**: AL/SAT/TUT önerisi ve detaylı analiz

## 📡 API Testleri

### Health Check
```bash
curl http://localhost:5000/api/health
curl http://localhost:3001/api/health
```

### Tahmin Al
```bash
curl -X POST http://localhost:3001/api/ml/predict \
  -H "Content-Type: application/json" \
  -d '{"symbol":"AAPL","use_cached_data":true}'
```

## 🔧 Sorun Giderme

### Port Çakışması
```bash
# Kullanımdaki portları kontrol et
netstat -ano | findstr :5000
netstat -ano | findstr :3001
netstat -ano | findstr :5173
```

### ML Servisi Başlamıyor
```bash
# Python sürümünü kontrol et (3.9+ gerekli)
python --version

# Paketleri yeniden yükle
pip install -r requirements.txt --upgrade
```

### Veri Yok
```bash
# Önce veri toplayın
cd ml-service
python run_collection.py
```

## 📚 Detaylı Dokümantasyon

- **Tam Kılavuz**: [KULLANIM_KILAVUZU.md](KULLANIM_KILAVUZU.md)
- **ML Servisi**: [ml-service/README.md](ml-service/README.md)
- **API Referansı**: KULLANIM_KILAVUZU.md içinde

## 🆘 Yardım

Sorun yaşıyorsanız:
1. Servislerin hepsinin çalıştığından emin olun
2. .env dosyasında API anahtarının olduğunu kontrol edin
3. Log çıktılarını inceleyin
4. KULLANIM_KILAVUZU.md'deki sorun giderme bölümüne bakın

---

**🎉 Başarılar!** Sorularınız için dokümantasyona göz atın.
