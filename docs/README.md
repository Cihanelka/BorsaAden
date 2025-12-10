# 📊 ML Stock Analysis Service

Haber duygu analizi ve teknik analiz kullanarak hisse senetleri için AL/SAT/TUT önerileri üreten makine öğrenmesi servisi.

## 🎯 Özellikler

- **Veri Toplama**: Finnhub API'den hisse fiyatları ve şirket haberlerini çeker
- **Duygu Analizi**: Türkçe BERT modeli ile haberlerin duygu analizini yapar
- **Teknik Analiz**: RSI, MACD, Bollinger Bands, SMA, EMA, Stochastic ve daha fazlası
- **Tahmin Modeli**: Duygu + teknik analiz ile AL/SAT/TUT önerisi
- **REST API**: Flask tabanlı API servisi

## 📋 Gereksinimler

```bash
pip install -r requirements.txt
```

### 🔑 API Anahtarları

`.env` dosyası oluşturun:

```env
FINNHUB_API_KEY=your_finnhub_api_key_here
NEWS_API_KEY=your_news_api_key_here
```

## 🚀 Kullanım

### 1. Veri Toplama

```python
python data_collector.py
```

Bu komut:
- Belirtilen hisseler için son 90 günlük fiyat verilerini çeker
- Son 30 günlük şirket haberlerini çeker
- Verileri `data/csv/` klasörüne kaydeder

### 2. Duygu Analizi

```python
python sentiment_analyzer.py
```

Bu komut:
- Toplanan haberlerin duygu analizini yapar
- Her habere pozitif/negatif/nötr etiketi ve skor atar
- Sonuçları `news_with_sentiment.csv` dosyasına kaydeder

### 3. Tahmin Yapma

```python
python stock_predictor.py
```

Veya Flask API'yi başlatın:

```bash
python app.py
```

## 🔌 API Endpoints

### Health Check
```http
GET /api/health
```

### Veri Toplama
```http
POST /api/collect-data
Content-Type: application/json

{
  "symbols": ["AAPL", "MSFT", "GOOGL"],
  "stock_days": 90,
  "news_days": 30
}
```

### Tahmin Yap
```http
POST /api/predict
Content-Type: application/json

{
  "symbol": "AAPL",
  "use_cached_data": true
}
```

**Yanıt:**
```json
{
  "success": true,
  "result": {
    "symbol": "AAPL",
    "prediction": "AL",
    "confidence": 0.78,
    "technical_score": 0.72,
    "sentiment_score": 0.45,
    "news_count": 15,
    "method": "rule_based"
  }
}
```

### Toplu Tahmin
```http
POST /api/predict-batch
Content-Type: application/json

{
  "symbols": ["AAPL", "MSFT", "GOOGL", "AMZN"]
}
```

### Teknik Analiz
```http
POST /api/technical-analysis
Content-Type: application/json

{
  "symbol": "AAPL"
}
```

### Duygu Analizi Özeti
```http
POST /api/sentiment-summary
Content-Type: application/json

{
  "symbol": "AAPL",
  "days": 7
}
```

## 📊 Veri Yapısı

### Hisse Verileri (stock_data.csv)
```csv
timestamp,open,high,low,close,volume,symbol,date
1701388800,189.92,191.08,189.23,190.33,52242815,AAPL,2023-12-01
```

### Haber Verileri (news_data.csv)
```csv
datetime,headline,summary,source,url,symbol,collected_at
1701388800,"Apple Launches New iPhone","...",Reuters,https://...,AAPL,2023-12-01
```

### Duygu Analizi Sonuçları (news_with_sentiment.csv)
```csv
...,sentiment,sentiment_score,normalized_score
...,positive,0.92,0.92
...,negative,0.85,-0.85
...,neutral,0.55,0.0
```

## 🧠 Model Eğitimi

Model eğitmek için etiketlenmiş veri gerekir. `training_data.csv` formatı:

```csv
technical_score,sentiment_score,news_count,rsi_score,...,label
0.72,0.45,15,0.65,...,2
0.35,-0.32,8,0.28,...,0
0.52,0.05,3,0.48,...,1
```

Etiketler:
- `0` = SAT
- `1` = TUT
- `2` = AL

Eğitim:
```python
from stock_predictor import StockPredictor

predictor = StockPredictor()
predictor.train_model('training_data.csv')
```

## 🎯 Karar Mantığı

### Kural Tabanlı (Model Yoksa)
- Teknik analiz skoru: %60 ağırlık
- Duygu analizi skoru: %40 ağırlık
- Birleşik skor >= 0.65 → **AL**
- Birleşik skor <= 0.35 → **SAT**
- Aradaki değerler → **TUT**

### ML Tabanlı (Model Varsa)
- Random Forest classifier
- 10 özellik kullanır
- Olasılık bazlı tahmin

## 📁 Klasör Yapısı

```
ml-service/
├── app.py                    # Flask API servisi
├── config.py                 # Yapılandırma
├── data_collector.py         # Veri toplama
├── sentiment_analyzer.py     # Duygu analizi
├── technical_analyzer.py     # Teknik analiz
├── stock_predictor.py        # Ana tahmin modeli
├── requirements.txt          # Python bağımlılıkları
├── README.md                 # Bu dosya
└── data/
    ├── csv/                  # CSV veri dosyaları
    └── models/               # Eğitilmiş modeller
```

## 🔧 Yapılandırma

`config.py` dosyasında ayarlanabilir parametreler:

- `DEFAULT_STOCKS`: Varsayılan hisse listesi
- `NEWS_LOOKBACK_DAYS`: Haber toplama gün sayısı
- `SENTIMENT_MODEL`: Duygu analizi modeli
- `TECHNICAL_INDICATORS`: Hesaplanacak teknik göstergeler
- `BUY_THRESHOLD`: AL eşiği (0.65)
- `SELL_THRESHOLD`: SAT eşiği (0.35)

## 🤝 Express.js Entegrasyonu

Express.js backend'den Python ML servisini çağırmak için:

```javascript
const response = await fetch('http://localhost:5000/api/predict', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ 
    symbol: 'AAPL',
    use_cached_data: true 
  })
});

const data = await response.json();
console.log(data.result.prediction); // AL, SAT veya TUT
```

## 📝 Notlar

1. İlk çalıştırmada BERT modeli indirilecek (~500MB)
2. GPU varsa otomatik kullanılır, yoksa CPU ile çalışır
3. API rate limiting nedeniyle büyük veri toplamada bekleme süreleri var
4. Model yoksa kural tabanlı sistem kullanılır

## 🐛 Hata Ayıklama

Logları kontrol edin:
```bash
python app.py
```

CSV dosyalarını kontrol edin:
```bash
ls -lh data/csv/
```

## 📄 Lisans

MIT License
