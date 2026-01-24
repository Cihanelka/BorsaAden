# Enhanced Stock Prediction Pipeline

## 🎯 Amaç
Production-ready, overfitting ve data leakage riskini minimize eden finansal zaman serisi tahmin sistemi.

## ✨ Özellikler

### 1. **Veri Kaynakları**
- ✅ OHLCV verileri (yfinance)
- ✅ Teknik indikatörler (RSI, MACD, Bollinger Bands, ATR)
- ✅ Destek/Direnç seviyeleri

### 2. **Feature Engineering**
- ✅ Normalizasyon (RobustScaler - outlier'lara karşı dayanıklı)
- ✅ Lag features (t-1, t-3, t-5)
- ✅ Volatilite features (ATR%, Bollinger width)
- ✅ Price returns, log returns, momentum
- ✅ Moving averages ve crossover signals

### 3. **Labeling Strategy**
- ✅ Classification: **UP / DOWN / NEUTRAL**
- ✅ Threshold-based labeling (default 2% price change)
- ✅ No look-ahead bias

### 4. **Data Splitting**
- ✅ **TimeSeriesSplit** - Random split YOK!
- ✅ Walk-forward validation
- ✅ 5-fold time-series cross-validation

### 5. **Model Architecture**
- ✅ Ensemble of tree-based models:
  - XGBoost
  - LightGBM  
  - CatBoost
- ✅ Majority voting for final prediction
- ✅ Probability averaging for confidence

### 6. **Training Features**
- ✅ Class imbalance handling (class weights)
- ✅ Early stopping
- ✅ Feature importance tracking
- ✅ Comprehensive metrics (F1, Precision, Recall)

### 7. **Output Format**
```json
{
  "prediction": "UP",
  "confidence": 0.85,
  "probabilities": {
    "UP": 0.75,
    "DOWN": 0.10,
    "NEUTRAL": 0.15
  },
  "disclaimer": "This is a statistical prediction, NOT investment advice"
}
```

## 🚀 Kullanım

### 1. Gerekli Paketleri Kur
```bash
cd ml-service
pip install -r requirements.txt
```

### 2. Modeli Eğit
```bash
python train_enhanced_model.py
```

Bu script:
- Birden fazla hisse için veri toplar (AAPL, MSFT, GOOGL, TSLA, NVDA)
- Teknik indikatörleri hesaplar
- TimeSeriesSplit ile cross-validation yapar
- 3 farklı model eğitir (XGBoost, LightGBM, CatBoost)
- En iyi performansı seçer
- Modelleri kaydeder

### 3. API ile Tahmin Yap

**Endpoint:** `POST /api/predict-enhanced`

**Request:**
```json
{
  "symbol": "AAPL"
}
```

**Response:**
```json
{
  "success": true,
  "prediction": "UP",
  "prediction_numeric": 2,
  "confidence": 0.8532,
  "probabilities": {
    "DOWN": 0.0823,
    "NEUTRAL": 0.0645,
    "UP": 0.8532
  },
  "disclaimer": "This is a statistical prediction, NOT investment advice"
}
```

### 4. Python ile Doğrudan Kullanım
```python
from enhanced_predictor import EnhancedStockPredictor
from data_collector import DataCollector

# Initialize
predictor = EnhancedStockPredictor()
predictor.load_models()  # Eğitilmiş modeli yükle

# Veri topla
collector = DataCollector()
df = collector.collect_stock_data('AAPL', days=90)

# Tahmin yap
result = predictor.predict(df)
print(result)
```

## 📊 Model Performansı

Eğitim sonrası her model için F1 skorları gösterilir:
```
📊 Model Performance (F1 Scores):
  xgboost        : 0.7234
  lightgbm       : 0.7189
  catboost       : 0.7312
```

## ⚠️ Önemli Notlar

### Data Leakage Önleme
- ✅ Tüm feature'lar sadece geçmiş verileri kullanır
- ✅ Future data asla mevcut örneklere karışmaz
- ✅ Rolling calculations doğru şekilde uygulanır

### Overfitting Önleme
- ✅ TimeSeriesSplit ile gerçekçi validation
- ✅ Early stopping
- ✅ Ensemble voting (3 model)
- ✅ Class weight balancing

### Haber Duygu Analizi
- ⚠️ **Tahmin feature'ı olarak KULLANILMAZ**
- ✅ Sadece post-prediction filtre olarak kullanılabilir
- ✅ İkincil risk göstergesi olarak değerlendirilebilir

## 🔄 Model Güncelleme

Modeli yeni verilerle güncellemek için:
```bash
python train_enhanced_model.py
```

Bu işlem:
- Mevcut modelleri yeniden eğitir
- Yeni performans metrikleri gösterir
- Güncellenmiş modelleri kaydeder

## 📈 Feature Importance

Eğitim sonrası hangi feature'ların en önemli olduğunu görmek için model objesini inceleyin:
```python
# XGBoost için
feature_importance = predictor.models['xgboost'].feature_importances_
for name, importance in zip(predictor.feature_names, feature_importance):
    print(f"{name}: {importance:.4f}")
```

## 🎓 Best Practices

1. **Düzenli Model Güncelleme:** Haftada 1 kez modeli yeniden eğitin
2. **Performans İzleme:** F1 skorlarını kaydedin ve trend takip edin
3. **Feature Engineering:** Yeni feature eklerken data leakage kontrolü yapın
4. **Threshold Tuning:** Farklı threshold değerleriyle (0.01, 0.02, 0.03) test edin
5. **Ensemble Optimization:** Model ağırlıklarını performansa göre ayarlayın

## 📝 Sorumluluk Reddi

**Bu sistem sadece istatistiksel tahmin üretir ve asla yatırım tavsiyesi vermez.**
- Kendi riskinizi değerlendirin
- Profesyonel finansal danışmanlık alın
- Geçmiş performans gelecek sonuçları garanti etmez
