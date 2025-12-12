# 🚀 SENTIMENT ANALİZİ - HIZLI BAŞLANGIÇ

## ✅ ÖNEMLİ: SİSTEM ARTIK MUTLAKA SENTIMENT ANALİZİ YAPIYOR!

Tahmin yaparken sistem **HER ZAMAN** aşağıdakileri yapar:

1. ✅ Haber çekmeyi dener (Google News → Finnhub → yfinance)
2. ✅ Haberlere sentiment analizi uygular
3. ✅ Sonuçları CSV'ye kaydeder
4. ✅ Sentiment + Teknik analiz ile tahmin yapar

---

## 🎯 HIZLI TEST

### 1. Google News RSS Testi
```bash
cd "Aden Borsa/ml-service"
python test_google_news_rss.py
```

### 2. Zorunlu Sentiment Testi
```bash
python test_sentiment_zorunlu.py
```

### 3. Canlı Tahmin Testi
```bash
# ML servisini başlat
python app.py

# Başka bir terminalde:
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d "{\"symbol\": \"AAPL\", \"use_cached_data\": false}"
```

---

## 📊 HABER KAYNAKLARI

### 1. Google News RSS (ÜCRETSİZ) ✅ ÖNCELİK #1
- API key gerektirmez
- Limitsiz
- Hemen çalışır

### 2. Finnhub API (İsteğe Bağlı)
```bash
# .env dosyasına ekle:
FINNHUB_API_KEY=your_key_here
```

### 3. yfinance (Otomatik Fallback)
- Ek ayar gerektirmez

---

## 💡 SENTIMENT SKORLARI

```
Pozitif Haber: +0.5 ile +0.9 arası
Nötr Haber:     0.5
Negatif Haber: -0.9 ile -0.5 arası
```

**Normalized Score:**
- Pozitif → 0.0 ile +1.0
- Negatif → -1.0 ile 0.0

---

## 🔍 LOG ÖRNEKLERI

### Başarılı Haber Çekme:
```
============================================================
📰 AAPL için HABER TOPLAMA BAŞLADI
============================================================

🔍 1. Deneme: Google News RSS...
✅ Google News RSS BAŞARILI: 15 haber

⚙️ SENTIMENT ANALİZİ YAPILIYOR: 15 haber
✅ Sentiment analizi tamamlandı!

💾 Haber sentiment CSV güncellendi: 15 yeni satır
```

### Haber Bulunamadığında:
```
⚠️ UYARI: AAPL için haber bulunamadı, sadece teknik analiz kullanılacak
```

---

## 📝 SENTIMENT SONUÇ ÖRNEĞİ

```json
{
  "success": true,
  "symbol": "AAPL",
  "result": {
    "news_count": 15,
    "positive_count": 10,
    "negative_count": 2,
    "neutral_count": 3,
    "avg_sentiment": 0.68,
    "normalized_sentiment": 0.42,
    "recent_headlines": [
      "Apple stock rises on strong iPhone sales",
      "Tech giant beats earnings expectations"
    ]
  }
}
```

---

## 🎓 DETAYLI DOKÜMANTASYON

Daha fazla bilgi için:
```
SENTIMENT_ANALIZI_DOKUMANTASYON.md
```

---

## ⚡ HIZLI KONTROL LİSTESİ

- [x] Google News RSS çalışıyor
- [x] Sentiment analizi otomatik yapılıyor
- [x] Sonuçlar CSV'ye kaydediliyor
- [x] Tahminlerde sentiment kullanılıyor
- [x] Hata durumunda fallback çalışıyor

---

**Hazır! Artık sistem tam otomatik sentiment analizi yapıyor.** 🚀
