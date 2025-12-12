# ML Model Sorunları ve Çözümleri

## 🔍 Tespit Edilen Sorunlar

### 1. **Haber Sayısı 0 Görünüyor**
**Sebep:** 
- `app.py` yfinance ile haber çekiyor
- Ancak CSV'de o sembol için haber olmayabilir
- yfinance API bazen haber döndürmüyor

**Çözüm:**
- `app.py` artık CSV'de veri yoksa otomatik canlı API'den çekiyor
- Sembole göre filtreleme eklendi

### 2. **Güven Skoru %35-51 Arası**
**Sebep:**
- Model haber verisi olmadan tahmin yapıyor
- Default sentiment değerleri (0.0) kullanılıyor
- Model zayıf özelliklerle tahmin yapıyor

**Çözüm:**
- Minimum güven zorlaması kaldırıldı (gerçek skoru göster)
- Düşük güven uyarısı eklendi
- Haber sayısı loglanıyor

### 3. **İki Farklı Sistem Var**
**Mevcut Durum:**
- `ml_predictor.py` → MLDataCollector → NewsAPI kullanıyor (kullanılmıyor)
- `stock_predictor.py` → DataCollector → yfinance kullanıyor (aktif)

**Aktif Sistem:** `stock_predictor.py` + `data_collector.py` (yfinance)

## ✅ Yapılan Düzeltmeler

1. **app.py**
   - CSV'de veri yoksa otomatik canlı API'den çek
   - Sembole göre filtreleme ekle
   - Debug logları ekle

2. **data_collector.py**
   - Finnhub yerine yfinance kullan (API key gerektirmez)
   - Haber çekme fonksiyonu güncellendi

3. **stock_predictor.py**
   - Minimum güven zorlaması kaldırıldı
   - Gerçek güven skoru gösteriliyor
   - Düşük güven uyarısı eklendi
   - Haber filtreleme iyileştirildi

## 🚀 Güven Skorunu Artırmak İçin

### Kısa Vadeli Çözüm:
```bash
# ML servisi yeniden başlat
cd ml-service
python app.py
```

### Uzun Vadeli Çözüm (Modeli İyileştir):

1. **Daha Fazla Veri Topla:**
```bash
cd ml-service
python data_collector.py
```

2. **Modeli Yeniden Eğit:**
```bash
python train_random_forest.py
```

3. **Haber Kaynaklarını Artır:**
   - NewsAPI (ücretsiz 100 istek/gün)
   - yfinance (sınırsız ama az haber)
   - Finnhub (ücretsiz 60 istek/dakika)

## 📊 Model Performansı

**Mevcut Durum:**
- Haber verisi: yfinance'den (sınırlı)
- Güven skoru: %35-51 (düşük)
- Sebep: Yetersiz haber verisi

**Hedef:**
- Haber verisi: Çoklu kaynak
- Güven skoru: %60+ (yüksek)
- Çözüm: Daha fazla veri + model iyileştirme

## 🔧 Test Etme

```bash
# 1. ML servisi başlat
cd ml-service
python app.py

# 2. Test isteği gönder
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "use_cached_data": false}'
```

Konsol çıktısında şunları göreceksiniz:
- 📰 Kaç haber çekildi
- ⚙️ Sentiment analizi yapılıyor mu
- 📊 Kaç haber analiz edildi
- ⚠️ Düşük güven uyarısı (varsa)
