# 🤖 Random Forest ML Modeli - Kurulum ve Kullanım

## 📋 Genel Bakış

Bu proje **Random Forest** makine öğrenmesi algoritması kullanarak hisse senedi tahminleri yapar:

### ✨ Özellikler
- ✅ **Teknik Göstergeler**: RSI, MACD, Bollinger Bands, SMA, EMA, Stochastic, ATR
- ✅ **Haber Duygu Analizi**: VADER Sentiment ile İngilizce haber analizi
- ✅ **3 Sınıf Tahmini**: AL, SAT, TUT
- ✅ **Güven Skoru**: Her tahmin için olasılık değerleri
- ✅ **Gerçek Zamanlı Veri**: TwelveData ve NewsAPI entegrasyonu

## 🚀 Hızlı Başlangıç

### Adım 1: Python Paketlerini Yükle

```bash
cd ml-service
pip install -r requirements.txt
```

**Gerekli Paketler:**
- pandas, numpy, scikit-learn (ML)
- ta (Teknik analiz)
- flask, flask-cors (API)
- textblob, vaderSentiment (Duygu analizi)
- requests, joblib, python-dotenv

### Adım 2: Modeli Eğit

**Otomatik (Önerilen):**
```bash
cd ml-service
TRAIN_MODEL.bat
```

**Manuel:**
```bash
cd ml-service
python train_random_forest.py
```

**Eğitim Süreci:**
1. 15 farklı hisse için veri toplar (AAPL, MSFT, GOOGL, vb.)
2. Her hisse için 90 günlük geçmiş veri alır
3. Teknik göstergeleri hesaplar
4. Haber duygu analizini yapar
5. Random Forest modelini eğitir
6. Modeli `data/models/` klasörüne kaydeder

**Süre:** 10-15 dakika (internet hızına bağlı)

### Adım 3: Uygulamayı Başlat

```bash
START_EVERYTHING.bat
```

## 📊 Model Detayları

### Random Forest Parametreleri
```python
n_estimators=200        # 200 karar ağacı
max_depth=15            # Maksimum derinlik
min_samples_split=10    # Bölünme için minimum örnek
min_samples_leaf=5      # Yaprak için minimum örnek
class_weight='balanced' # Dengesiz sınıflar için
```

### Kullanılan Özellikler (Features)

**Teknik Göstergeler (13 adet):**
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- MACD Signal, MACD Diff
- Bollinger Band Width
- Stochastic K, Stochastic D
- ATR (Average True Range)
- Volume Ratio
- Price Change (1d, 5d, 10d)
- Trend Strength

**Duygu Analizi (5 adet):**
- Sentiment Score (Ortalama duygu skoru)
- Sentiment Std (Duygu standart sapması)
- Positive Ratio (Pozitif haber oranı)
- Negative Ratio (Negatif haber oranı)
- News Count (Haber sayısı)

**Toplam: 18 özellik**

### Hedef Değişken (Target)

Model 5 gün sonraki fiyat değişimine göre karar verir:

- **AL**: Fiyat %2'den fazla artacak
- **SAT**: Fiyat %2'den fazla düşecek
- **TUT**: Fiyat -%2 ile +%2 arasında kalacak

## 🔌 API Kullanımı

### 1. Servis Durumu
```bash
GET http://localhost:5000/api/health
```

**Response:**
```json
{
  "status": "ok",
  "service": "ML Stock Analysis Service - Random Forest",
  "model_loaded": true,
  "model_type": "Random Forest Classifier",
  "features": 18
}
```

### 2. Tek Hisse Tahmini
```bash
POST http://localhost:5000/api/predict
Content-Type: application/json

{
  "symbol": "AAPL"
}
```

**Response:**
```json
{
  "success": true,
  "result": {
    "symbol": "AAPL",
    "prediction": "AL",
    "confidence": 0.85,
    "probabilities": {
      "AL": 0.85,
      "SAT": 0.05,
      "TUT": 0.10
    },
    "current_price": 150.25,
    "technical_indicators": {
      "rsi": 65.5,
      "macd": 2.3,
      "trend_strength": 0.15,
      "volume_ratio": 1.2
    },
    "sentiment_analysis": {
      "score": 0.45,
      "positive_ratio": 0.7,
      "negative_ratio": 0.1,
      "news_count": 10
    },
    "recommendation": "AL sinyali güçlü - %85 güven",
    "model_type": "Random Forest",
    "features_used": 18
  }
}
```

### 3. Çoklu Hisse Tahmini
```bash
POST http://localhost:5000/api/predict-batch
Content-Type: application/json

{
  "symbols": ["AAPL", "MSFT", "GOOGL"]
}
```

### 4. Model Bilgileri
```bash
GET http://localhost:5000/api/model-info
```

## 📈 Model Performansı

Eğitim sonrası şu metrikleri göreceksiniz:

- **Accuracy**: Genel doğruluk oranı
- **Precision**: Her sınıf için hassasiyet
- **Recall**: Her sınıf için duyarlılık
- **F1-Score**: Precision ve Recall ortalaması
- **Confusion Matrix**: Karışıklık matrisi
- **Cross-Validation**: 5-fold çapraz doğrulama skoru
- **Feature Importance**: En önemli özellikler

## 🔧 Sorun Giderme

### Model Yüklenmiyor
```bash
# Modeli eğitin
cd ml-service
python train_random_forest.py
```

### API 500 Hatası
```bash
# Paketleri kontrol edin
pip install -r requirements.txt

# .env dosyasını kontrol edin
# ml-service/.env dosyası olmalı
```

### Veri Toplanamıyor
- İnternet bağlantınızı kontrol edin
- API limitlerini kontrol edin (TwelveData: 800 istek/gün)
- Farklı hisseler deneyin

### Düşük Doğruluk
- Daha fazla hisse ile eğitin
- Daha uzun geçmiş veri kullanın (days=180)
- Hiperparametreleri ayarlayın

## 📁 Dosya Yapısı

```
ml-service/
├── app_rf.py                    # Flask API (Random Forest)
├── ml_data_collector.py         # Veri toplama ve feature engineering
├── ml_predictor.py              # Tahmin yapma
├── train_random_forest.py       # Model eğitimi
├── TRAIN_MODEL.bat              # Eğitim başlatma scripti
├── requirements.txt             # Python bağımlılıkları
├── .env                         # API anahtarları
└── data/
    ├── models/
    │   ├── random_forest_model.joblib
    │   ├── scaler.joblib
    │   ├── feature_columns.joblib
    │   └── model_info.txt
    └── csv/
        └── training_data.csv
```

## 🎯 Gelecek Geliştirmeler

- [ ] LSTM/GRU ile zaman serisi tahmini
- [ ] Daha fazla teknik gösterge
- [ ] Türkçe haber duygu analizi
- [ ] Otomatik model yeniden eğitimi
- [ ] Ensemble modeller (XGBoost, LightGBM)
- [ ] Backtesting sistemi

## 📚 Kaynaklar

- **TwelveData API**: https://twelvedata.com/
- **NewsAPI**: https://newsapi.org/
- **Scikit-learn**: https://scikit-learn.org/
- **TA-Lib**: https://github.com/bukosabino/ta

## 💡 İpuçları

1. **İlk eğitim uzun sürer** - Sabırlı olun (10-15 dakika)
2. **API limitleri** - Günde 800 istek limiti var
3. **Güven skoru** - %75+ güven skorları daha güvenilir
4. **Çoklu sinyal** - Birden fazla hisseyi karşılaştırın
5. **Güncel veri** - Modeli haftada bir yeniden eğitin

## ⚠️ Yasal Uyarı

Bu model sadece **eğitim amaçlıdır**. Gerçek yatırım kararları için kullanmayın. Finansal piyasalar öngörülemezdir ve geçmiş performans gelecek sonuçları garanti etmez.
