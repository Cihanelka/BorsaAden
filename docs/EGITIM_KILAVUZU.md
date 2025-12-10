# 🚀 Model Eğitim Kılavuzu

## 📊 Veri Kaynağı

### Yeni Sistem: yfinance (Yahoo Finance)
- ✅ **Ücretsiz** ve **limitsiz**
- ✅ Güvenilir tarihsel veri
- ✅ API key gerektirmez
- ✅ Gerçek zamanlı veri

### Eski Sistem: TwelveData API
- ❌ Günlük 800 istek limiti
- ❌ API key gerekli
- ❌ Yavaş yanıt süresi

## 🎯 Eğitim Parametreleri

### Veri Seti
- **20 hisse**: AAPL, MSFT, GOOGL, AMZN, META, TSLA, NVDA, AMD, JPM, BAC, WFC, GS, NFLX, DIS, NKE, SBUX, JNJ, PFE, UNH, XOM
- **180 gün** tarihsel veri (6 ay)
- **Beklenen toplam satır**: ~3,000-3,600 satır

### Model Parametreleri
- **Algoritma**: Random Forest Classifier
- **Ağaç sayısı**: 400
- **Max derinlik**: 20
- **Min samples split**: 5
- **Min samples leaf**: 2
- **Class weight**: Balanced
- **OOB Score**: Aktif

### Özellikler (26 adet)
**Teknik Göstergeler (18):**
- RSI, MACD, MACD Signal, MACD Diff
- Bollinger Bands Width
- Stochastic K, Stochastic D
- ATR (Average True Range)
- Volume Ratio
- Price Change (1d, 5d, 10d)
- Trend Strength
- OBV Change, MFI, ADX
- CCI, Williams %R, ROC
- SMA Cross, EMA Cross

**Duygu Analizi (5):**
- Sentiment Score
- Sentiment Std
- Positive Ratio
- Negative Ratio
- News Count

## 📝 Eğitim Adımları

### 1. Gerekli Kütüphaneleri Yükle
```bash
cd ml-service
pip install -r requirements.txt
```

### 2. Modeli Eğit
```bash
python train_random_forest.py
```

**Süre**: ~10-15 dakika
- Veri toplama: ~5 dakika
- Model eğitimi: ~5-10 dakika

### 3. Sonuçları Kontrol Et
Eğitim tamamlandığında şunları göreceksiniz:
- ✅ Test Doğruluğu (Accuracy)
- ✅ OOB Doğruluğu
- ✅ Sınıf Bazlı Performans (Precision, Recall, F1-Score)
- ✅ Confusion Matrix
- ✅ Cross-Validation Skorları
- ✅ Özellik Önem Dereceleri

## 📂 Kaydedilen Dosyalar

Eğitim sonrası `data/models/` klasöründe:
- `random_forest_model.joblib` - Eğitilmiş model
- `scaler.joblib` - Veri ölçekleyici
- `feature_columns.joblib` - Özellik listesi
- `model_info.txt` - Model bilgileri

Eğitim verisi `data/csv/` klasöründe:
- `training_data.csv` - Ham eğitim verisi

## 🎯 Beklenen Performans

### Önceki Durum
- Doğruluk: ~%40-45
- Güven: Düşük
- Sınıf dengesizliği var

### Yeni Durum (Beklenen)
- Doğruluk: **%60-75+**
- Güven: Yüksek
- Dengeli sınıf tahminleri
- Daha az overfitting

## ⚠️ Sorun Giderme

### "yfinance bulunamadı" hatası
```bash
pip install yfinance
```

### "Yetersiz veri" hatası
- İnternet bağlantınızı kontrol edin
- Hisse sembollerinin doğru olduğundan emin olun
- Bazı hisseler için veri olmayabilir (normal)

### API limiti hatası
- yfinance kullanıyorsanız limit yok
- Eğer TwelveData kullanıyorsanız, yfinance'e geçin

### Düşük performans
- Daha fazla hisse ekleyin
- Eğitim süresini artırın (days parametresi)
- Hiperparametreleri ayarlayın

## 🔄 Model Güncelleme

Model performansını artırmak için:

1. **Daha fazla veri**: `days=180` → `days=365`
2. **Daha fazla hisse**: Listeye yeni hisseler ekleyin
3. **Hiperparametre tuning**: GridSearchCV kullanın
4. **Ensemble methods**: XGBoost, LightGBM deneyin

## 📊 Performans Metrikleri

### Accuracy (Doğruluk)
- Genel başarı oranı
- Hedef: >%60

### Precision (Kesinlik)
- Pozitif tahminlerin doğruluk oranı
- AL/SAT kararlarında önemli

### Recall (Duyarlılık)
- Gerçek pozitifleri yakalama oranı
- Fırsatları kaçırmamak için önemli

### F1-Score
- Precision ve Recall'un dengesi
- En önemli metrik

### OOB Score
- Out-of-bag doğruluğu
- Overfitting kontrolü için

## 🎓 İpuçları

1. **İlk eğitim**: Küçük veri setiyle test edin (3-5 hisse, 30 gün)
2. **Veri kalitesi**: Eksik verileri kontrol edin
3. **Sınıf dengesi**: Her sınıftan yeterli örnek olmalı
4. **Feature importance**: En önemli özelliklere odaklanın
5. **Cross-validation**: Overfitting'i önleyin

## 📞 Destek

Sorun yaşarsanız:
1. Hata mesajını okuyun
2. Log dosyalarını kontrol edin
3. Veri kalitesini kontrol edin
4. Model parametrelerini gözden geçirin
