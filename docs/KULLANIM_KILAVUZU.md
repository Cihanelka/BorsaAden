# 📖 Aden Borsa ML Sistemi Kullanım Kılavuzu

Bu kılavuz, ML tabanlı hisse senedi analiz sistemini kurmak ve kullanmak için adım adım talimatlar içerir.

## 🎯 Sistem Özeti

Sistem 3 ana bileşenden oluşur:

1. **Python ML Servisi** (`ml-service/`): Duygu analizi ve tahmin modeli
2. **Express.js Backend** (`server/`): API gateway
3. **React Frontend** (`src/`): Kullanıcı arayüzü

## 🚀 Hızlı Başlangıç

### Adım 1: Python ML Servisini Kurun

```bash
# ml-service klasörüne gidin
cd ml-service

# Python paketlerini yükleyin
pip install -r requirements.txt

# Kurulum scriptini çalıştırın
python setup.py
```

### Adım 2: API Anahtarlarını Ayarlayın

`.env` dosyasını düzenleyin:

```env
FINNHUB_API_KEY=your_actual_api_key_here
```

**API Anahtarı Alma:**
1. https://finnhub.io/ adresine gidin
2. Ücretsiz hesap oluşturun
3. API anahtarınızı kopyalayın
4. `.env` dosyasına yapıştırın

### Adım 3: Veri Toplayın

İlk kez veri toplamak için:

```bash
python run_collection.py
```

Bu script:
- ✅ 20 popüler hisse için veri toplar
- ✅ Son 90 günlük fiyat verilerini çeker
- ✅ Son 30 günlük haberleri çeker
- ✅ Duygu analizini otomatik yapar
- ✅ Sonuçları CSV'ye kaydeder

**Süre:** ~5-10 dakika (API rate limiting nedeniyle)

### Adım 4: ML Servisini Başlatın

```bash
python app.py
```

Servis `http://localhost:5000` adresinde çalışacak.

### Adım 5: Express.js Backend'i Başlatın

Yeni bir terminal açın:

```bash
cd server
npm install
npm start
```

Backend `http://localhost:3001` adresinde çalışacak.

### Adım 6: React Frontend'i Başlatın

Yeni bir terminal daha açın:

```bash
cd ..
npm install
npm run dev
```

Frontend `http://localhost:5173` adresinde açılacak.

## 🎮 Kullanım Senaryoları

### 1. Web Arayüzünden Tahmin Alma

1. Bir hisse seçin (örn: AAPL)
2. "AI Tahmin Sistemi" kartını bulun
3. "Tahmin Al" butonuna tıklayın
4. Sonuçları görün:
   - 🎯 AL/SAT/TUT önerisi
   - 💯 Güven skoru
   - 📊 Teknik analiz detayları
   - 💭 Haber duygu analizi

### 2. API ile Doğrudan Kullanım

#### Tek Hisse İçin Tahmin

```bash
curl -X POST http://localhost:3001/api/ml/predict \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "use_cached_data": true}'
```

#### Birden Fazla Hisse

```bash
curl -X POST http://localhost:3001/api/ml/predict-batch \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL", "MSFT", "GOOGL"]}'
```

#### Sadece Teknik Analiz

```bash
curl -X POST http://localhost:3001/api/ml/technical-analysis \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL"}'
```

#### Sadece Duygu Analizi

```bash
curl -X POST http://localhost:3001/api/ml/sentiment-summary \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "days": 7}'
```

### 3. Yeni Veri Toplama

Sistemdeki verileri güncellemek için:

```bash
# ml-service klasöründe
python run_collection.py
```

Veya API üzerinden:

```bash
curl -X POST http://localhost:3001/api/ml/collect-data \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["AAPL", "TSLA"],
    "stock_days": 90,
    "news_days": 30
  }'
```

## 📊 Veri Dosyaları

Tüm veriler `ml-service/data/csv/` klasöründe saklanır:

- **stock_data.csv**: Hisse fiyat verileri (OHLCV)
- **news_data.csv**: Ham haber verileri
- **news_with_sentiment.csv**: Duygu analizi eklenmiş haberler

## 🧠 Model Eğitimi (İleri Seviye)

Kendi modelinizi eğitmek için:

### 1. Eğitim Verisi Hazırlayın

`training_data.csv` formatı:

```csv
technical_score,sentiment_score,news_count,rsi_score,macd_score,bb_score,sma_score,stoch_score,positive_ratio,negative_ratio,label
0.72,0.45,15,0.65,0.70,0.68,0.75,0.72,0.60,0.20,2
0.35,-0.32,8,0.28,0.35,0.40,0.30,0.25,0.25,0.62,0
```

**Etiketler:**
- `0` = SAT
- `1` = TUT
- `2` = AL

### 2. Modeli Eğitin

```python
from stock_predictor import StockPredictor

predictor = StockPredictor()
predictor.train_model('training_data.csv')
```

Veya API ile:

```bash
curl -X POST http://localhost:3001/api/ml/train-model \
  -H "Content-Type: application/json" \
  -d '{"training_data_csv": "training_data.csv"}'
```

## 🔧 Sorun Giderme

### ML Servisi Başlamıyor

**Hata:** `ModuleNotFoundError`

```bash
# Tüm paketleri yeniden yükleyin
pip install -r requirements.txt --upgrade
```

**Hata:** `FINNHUB_API_KEY not found`

```bash
# .env dosyasını kontrol edin
cat .env

# Yoksa oluşturun
cp .env.example .env
# Ardından düzenleyin
```

### Veri Toplanamıyor

**Hata:** `API rate limit exceeded`

- ⏱️ Birkaç dakika bekleyin
- 🔑 API anahtarınızın geçerli olduğundan emin olun
- 📊 Daha az hisse ile deneyin

**Hata:** `No data collected`

```bash
# API anahtarını test edin
curl "https://finnhub.io/api/v1/quote?symbol=AAPL&token=YOUR_KEY"
```

### Model Yavaş Çalışıyor

BERT modeli ilk çalıştırmada indirilir (~500MB):

```bash
# İndirme durumunu kontrol edin
du -sh ~/.cache/huggingface/
```

GPU varsa otomatik kullanılır, yoksa CPU ile çalışır (daha yavaş).

### Express.js ML Servisine Bağlanamıyor

```bash
# ML servisinin çalıştığını kontrol edin
curl http://localhost:5000/api/health

# Port kullanımda mı?
netstat -an | grep 5000
```

## 📈 Sistem Performansı

### Veri Toplama Süreleri

- 1 hisse: ~5 saniye
- 10 hisse: ~1 dakika
- 20 hisse: ~3 dakika

### Tahmin Süreleri

- Cached verilerle: ~0.5 saniye
- Canlı veri çekerek: ~5 saniye
- Batch tahmin (10 hisse): ~5 saniye

### Duygu Analizi

- 100 haber: ~1 dakika (CPU)
- 100 haber: ~10 saniye (GPU)

## 🎯 En İyi Uygulamalar

1. **Düzenli Veri Güncellemesi**
   - Günde 1 kez veri toplayın
   - Piyasa kapanışından sonra ideal

2. **Cache Kullanımı**
   - İlk tahmin: canlı veri çekin
   - Sonraki tahmınler: cached veri kullanın

3. **API Rate Limiting**
   - Çok sık istekten kaçının
   - Batch endpoint'leri kullanın

4. **Model Güncelleme**
   - Aylık model yeniden eğitimi
   - Yeni verilerle sürekli iyileştirme

## 📝 İpuçları

- 🔍 İlk kullanımda 5-10 hisse ile başlayın
- 📊 Verileri CSV'den inceleyerek sistem mantığını anlayın
- 🧪 Farklı hisseler için sonuçları karşılaştırın
- 📈 Gerçek işlemler için sonuçları referans olarak kullanın (finansal tavsiye değildir!)

## 🆘 Destek

Sorunlarınız için:

1. `ml-service/README.md` dosyasına bakın
2. Log dosyalarını kontrol edin
3. API endpoint'lerini test edin
4. Python ve Node.js sürümlerini kontrol edin

**Gerekli Sürümler:**
- Python: 3.9+
- Node.js: 18+
- npm: 9+

## 📄 Lisans

MIT License - Akademik ve ticari kullanım için uygundur.

---

**⚠️ Önemli Not:** Bu sistem finansal tavsiye vermez. Sadece analiz ve eğitim amaçlıdır. Gerçek yatırım kararlarınızı profesyonel danışmanlarla alın.
