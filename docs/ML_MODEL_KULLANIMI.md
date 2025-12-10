# 🤖 Gerçek ML Modeli Kullanımı

## ✅ Başarıyla Tamamlandı!

Artık projenizde **gerçek bir Machine Learning modeli** çalışıyor!

---

## 📊 Model Detayları

### **Model Tipi**
- **Random Forest Classifier**
- 100 karar ağacı
- %92 doğruluk oranı

### **Eğitim Verisi**
- 1000 örnek
- 17 özellik
- 3 sınıf: AL, SAT, TUT

### **En Önemli Özellikler**
1. **RSI** (33.8%) - En etkili gösterge
2. **Sentiment Score** (16.3%) - Duygu analizi
3. **MACD Histogram** (10.2%) - Momentum
4. **Bollinger Position** (8.1%) - Volatilite
5. **Volatility** (4.1%) - Risk

---

## 🚀 Nasıl Çalışır?

### **1. Model Eğitimi**
```bash
cd ml-service
python train_ml_model.py
```

**Çıktı:**
```
✅ Model eğitimi tamamlandı!
🎯 Doğruluk: 92.00%

Etiket Dağılımı:
SAT    478
AL     291
TUT    231
```

### **2. ML Servisini Başlat**
```bash
python ml_advanced_app.py
```

**Çıktı:**
```
✅ ML Model: YÜKLÜ (Random Forest)
✅ Tahmin Modu: MACHINE LEARNING
✅ OHLCV Verileri: TwelveData API
✅ Teknik Analiz: RSI, MACD, Bollinger, SMA, EMA
```

### **3. Frontend'de Görüntüle**
- Hisse seçin
- "AI Yorumlar" butonuna tıklayın
- **"🤖 ML Model"** etiketi görünecek

---

## 🔄 ML Model vs Kural Tabanlı

### **ML Model Kullanıldığında**
```json
{
  "method": "ml_model",
  "prediction": "AL",
  "confidence": 0.87,
  "probabilities": {
    "AL": 0.87,
    "TUT": 0.10,
    "SAT": 0.03
  }
}
```
- ✅ 1000 örnekten öğrenilmiş
- ✅ Karmaşık ilişkileri yakalar
- ✅ Olasılık dağılımı verir
- ✅ %92 doğruluk

### **Kural Tabanlı Kullanıldığında**
```json
{
  "method": "rule_based",
  "prediction": "TUT",
  "confidence": 0.55
}
```
- 📊 Elle yazılmış kurallar
- 📊 Basit eşik değerleri
- 📊 Şeffaf mantık

---

## 📈 Model Nasıl Tahmin Yapar?

### **Adım 1: Veri Toplama**
```python
# TwelveData'dan OHLCV verileri
closes = [281.08, 283.00, 280.50, ...]
volumes = [45M, 52M, 48M, ...]
```

### **Adım 2: Teknik Göstergeler**
```python
rsi = 45.23
macd_histogram = -0.85
bb_position = 0.42  # 0=alt, 1=üst
```

### **Adım 3: Özellik Vektörü**
```python
features = [
    rsi, macd, macd_signal, macd_histogram,
    bb_position, sma_20, ema_12, ema_26,
    current_price, price_vs_sma, ema_crossover,
    sentiment_score, news_count,
    volatility, volume_trend,
    price_change_1d, price_change_5d
]
```

### **Adım 4: ML Tahmin**
```python
X_scaled = scaler.transform([features])
prediction = model.predict(X_scaled)  # "AL"
probabilities = model.predict_proba(X_scaled)  # [0.87, 0.10, 0.03]
```

---

## 🎯 Örnek Tahmin Senaryosu

### **Girdi:**
```
Symbol: AAPL
Current Price: $281.08
RSI: 45.23 (Nötr)
MACD: -0.85 (Negatif)
Bollinger Position: 0.42 (Orta)
Sentiment: 0.55 (Pozitif)
Volume Trend: 1.15 (Artış)
```

### **ML Model İşlemi:**
```
1. Özellikleri normalize et
2. Random Forest'a gönder
3. 100 karar ağacının oylaması:
   - 54 ağaç: "TUT"
   - 32 ağaç: "AL"
   - 14 ağaç: "SAT"
```

### **Çıktı:**
```json
{
  "prediction": "TUT",
  "confidence": 0.54,
  "method": "ml_model",
  "probabilities": {
    "AL": 0.32,
    "TUT": 0.54,
    "SAT": 0.14
  }
}
```

---

## 🔧 Model Yeniden Eğitimi

### **Ne Zaman Gerekir?**
- Piyasa koşulları değiştiğinde
- Daha fazla veri toplandığında
- Model performansı düştüğünde

### **Nasıl Yapılır?**
```bash
# 1. Yeni veri topla
python collect_data.py

# 2. Modeli yeniden eğit
python train_ml_model.py

# 3. Servisi yeniden başlat
python ml_advanced_app.py
```

---

## 📊 Model Performansı

### **Eğitim Sonuçları**
```
              precision    recall  f1-score   support
          AL       0.94      0.86      0.90        58
         SAT       0.94      0.99      0.96        96
         TUT       0.85      0.85      0.85        46

    accuracy                           0.92       200
```

### **Özellik Önem Sıralaması**
```
1. RSI                 33.8%
2. Sentiment Score     16.3%
3. MACD Histogram      10.2%
4. BB Position          8.1%
5. Volatility           4.1%
6. MACD                 3.8%
7. MACD Signal          3.6%
8. Price Change 1D      2.7%
9. Volume Trend         2.5%
10. SMA 20              2.2%
```

---

## 🎨 Frontend'de Görünüm

### **ML Model Aktif**
```
🤖 ML Model • 06.12.2025 22:00

AL ÖNERİSİ
%87 Güven

Olasılıklar:
• AL:  87%
• TUT: 10%
• SAT:  3%

Teknik Skor: %65
Duygu Skoru: %55
```

### **Kural Tabanlı (Fallback)**
```
📊 Kural Tabanlı • 06.12.2025 22:00

TUT ÖNERİSİ
%55 Güven

Teknik Skor: %52
Duygu Skoru: %50
```

---

## 💡 Avantajlar

### **ML Model**
✅ Verilerden öğrenir  
✅ Karmaşık kalıpları bulur  
✅ Olasılık dağılımı verir  
✅ %92 doğruluk  
✅ Sürekli iyileştirilebilir  

### **Kural Tabanlı**
✅ Hızlı başlangıç  
✅ Şeffaf mantık  
✅ Eğitim verisi gerektirmez  
✅ Fallback olarak güvenilir  

---

## 🚦 Durum Kontrolü

### **ML Model Yüklü mü?**
```bash
curl http://localhost:5000/api/health
```

**Yanıt:**
```json
{
  "status": "ok",
  "ml_model_loaded": true,
  "mode": "ml_model"
}
```

### **Dosyalar Mevcut mu?**
```
ml-service/
├── data/
│   └── models/
│       ├── stock_predictor.joblib  ✅
│       ├── scaler.joblib           ✅
│       ├── feature_columns.joblib  ✅
│       └── model_info.txt          ✅
```

---

## 🎉 Sonuç

Artık projenizde:
- ✅ **Gerçek ML modeli** çalışıyor
- ✅ **Random Forest** ile %92 doğruluk
- ✅ **17 özellik** kullanılıyor
- ✅ **OHLCV + Teknik Analiz** entegre
- ✅ **Olasılık dağılımı** gösteriliyor
- ✅ **Fallback sistemi** var

**Makine öğrenmesi başarıyla entegre edildi!** 🚀
