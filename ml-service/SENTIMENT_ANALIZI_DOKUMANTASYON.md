# 📊 SENTIMENT ANALİZİ SİSTEMİ - KAPSAMLI DOKÜMANTASYON

## 🎯 Genel Bakış

Bu sistem, hisse senedi tahminlerinde **MUTLAKA** sentiment analizi yapacak şekilde tasarlanmıştır. 
Hiçbir durumda sentiment analizi atlanmaz - en az bir haber kaynağından mutlaka haber çekilir.

---

## 🔄 HABER KAYNAĞI ÖNCELİK SIRASI

Sistem aşağıdaki sırayla haber kaynaklarını dener:

### 1. Google News RSS (ÜCRETSİZ, LİMİTSİZ) ✅
- **URL Format:** `https://news.google.com/rss/search?q={company}+stock`
- **Avantajları:**
  - Ücretsiz
  - API key gerektirmez
  - Limitsiz kullanım
  - Başlık + kısa özet
- **Dezavantajları:**
  - Tam metin yok (sadece description)

### 2. Finnhub API (Backend)
- **Kullanım:** `FINNHUB_API_KEY` varsa
- **Avantajları:**
  - Zengin içerik (headline, summary, source, url)
  - Profesyonel veri kaynağı
- **Dezavantajları:**
  - API key gerekli
  - Limiti var

### 3. yfinance (Fallback)
- **Kullanım:** Diğer kaynaklar başarısız olursa
- **Avantajları:**
  - Ücretsiz
  - API key gerektirmez
- **Dezavantajları:**
  - Sınırlı haber
  - Bazen haber yok

---

## 🧠 SENTIMENT ANALİZİ YÖNTEMLERİ

### 1. Geliştirilmiş Kelime Tabanlı Analiz (Aktif)

**Özellikler:**
- 60+ İngilizce finansal kelime
- 20+ Türkçe finansal kelime
- Dinamik skor hesaplama

**Pozitif Kelimeler:**
```
İngilizce: gain, profit, rise, surge, growth, strong, bull, beat, upgrade...
Türkçe: kazanç, kâr, yükseliş, artış, büyüme, güçlü, pozitif, başarı...
```

**Negatif Kelimeler:**
```
İngilizce: loss, fall, drop, decline, weak, bear, miss, risk, downgrade...
Türkçe: kayıp, zarar, düşüş, azalış, zayıf, negatif, risk, endişe...
```

**Skor Hesaplama:**
- Pozitif/Negatif kelime sayısı
- Oran bazlı skor: 0.5-0.9 arası
- Neutral: Eşit dağılım

### 2. BERT Modeli (Devre Dışı)
- Şu an kapalı (performans nedeniyle)
- İsterse aktif edilebilir

---

## 📝 PREDICT İŞLEYİŞİ

### Cached Mod (use_cached_data: true)

```
1. Sentiment CSV'sini kontrol et
   ├─ Var ve içinde veri var → Kullan
   └─ Yok veya boş → Adım 2

2. Ham Haber CSV'sini kontrol et
   ├─ Var ve içinde veri var → Sentiment analizi yap + Kaydet
   └─ Yok veya boş → Adım 3

3. CANLI HABER ÇEK (MUTLAKA!)
   ├─ Google News RSS dene
   ├─ Başarısız ise Finnhub dene
   ├─ Başarısız ise yfinance dene
   └─ Haber bulunursa → Sentiment analizi yap + Kaydet

4. Tahmin yap (sentiment + teknik analiz)
```

### Canlı Mod (use_cached_data: false)

```
1. Hisse verisi çek (yfinance)

2. CANLI HABER ÇEK
   ├─ Google News RSS dene
   ├─ Başarısız ise Finnhub dene
   └─ Başarısız ise yfinance dene

3. MUTLAKA Sentiment analizi yap

4. Sonuçları CSV'ye kaydet

5. Tahmin yap (sentiment + teknik analiz)
```

---

## 💾 VERİ KAYDETME

### news_with_sentiment.csv Formatı

```csv
datetime,headline,summary,source,url,symbol,collected_at,combined_text,sentiment,sentiment_score,normalized_score
```

**Kolonlar:**
- `datetime`: Unix timestamp (epoch)
- `headline`: Haber başlığı
- `summary`: Kısa özet
- `source`: Kaynak (Google News, Finnhub, yfinance)
- `url`: Haber linki
- `symbol`: Hisse sembolü (AAPL, MSFT...)
- `collected_at`: Toplama tarihi
- `sentiment`: positive/negative/neutral
- `sentiment_score`: 0.0-1.0 arası güven skoru
- `normalized_score`: -1 ile +1 arası normalize skor

---

## 🔧 YAPILANDIRMA

### config.py

**Şirket İsimleri Mapping:**
```python
COMPANY_NAMES = {
    'AAPL': 'Apple',
    'MSFT': 'Microsoft',
    'GOOGL': 'Google Alphabet',
    'AMZN': 'Amazon',
    # ... 20 şirket
}
```

**API Keys:**
```python
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY', '')
```

---

## 📊 SENTIMENT-SUMMARY ENDPOINT

**URL:** `POST /api/sentiment-summary`

**Body:**
```json
{
  "symbol": "AAPL",
  "days": 7
}
```

**Response:**
```json
{
  "success": true,
  "symbol": "AAPL",
  "result": {
    "news_count": 25,
    "positive_count": 15,
    "negative_count": 5,
    "neutral_count": 5,
    "avg_sentiment": 0.65,
    "normalized_sentiment": 0.42,
    "recent_headlines": [...]
  }
}
```

---

## 🚀 KULLANIM

### Manuel Test

```bash
cd "Aden Borsa/ml-service"
python test_google_news_rss.py
```

### API Üzerinden

```bash
# Tahmin yap (otomatik sentiment analizi yapılır)
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL"}'

# Sentiment özeti al
curl -X POST http://localhost:5000/api/sentiment-summary \
  -H "Content-Type: application/json" \
  -d '{"symbol": "AAPL", "days": 7}'
```

---

## ⚡ PERFORMANS VE LOGLARTüm işlemler detaylı loglanır:

```
============================================================
📰 AAPL için HABER TOPLAMA BAŞLADI
============================================================

🔍 1. Deneme: Google News RSS...
✅ Google News RSS BAŞARILI: 15 haber

⚙️ SENTIMENT ANALİZİ YAPILIYOR: 15 haber
  İşlenen: 0/15
  İşlenen: 10/15
✅ Sentiment analizi tamamlandı!

💾 Haber sentiment CSV güncellendi: 15 yeni satır
```

---

## 🛡️ HATA YÖNETİMİ

### Haber Bulunamadığında

```python
# Sistem UYARI verir ama DEVAM EDER
print(f"⚠️ UYARI: {symbol} için haber bulunamadı, sadece teknik analiz kullanılacak")

# Tahmin yine yapılır, sadece sentiment skoru 0 olur
```

### Sentiment Analizi Hatası

```python
# Basit kelime tabanlı analize geçer
try:
    result = self.sentiment_pipeline(text)
except Exception:
    result = self._simple_sentiment(text)  # Fallback
```

---

## 📈 GELECEKTEKİ GELİŞTİRMELER

1. ✅ Google News RSS entegrasyonu
2. ✅ Çoklu kaynak desteği
3. ✅ Geliştirilmiş kelime sözlüğü
4. 🔄 BERT modelini opsiyonel aktif etme
5. 🔄 Frontend'den gelen haberleri kullanma
6. 🔄 Real-time sentiment tracking

---

## 🔐 GÜVENLİK

- API keyleri `.env` dosyasında saklanır
- Hassas veriler Git'e commit edilmez
- Rate limiting ile API limit aşımı önlenir

---

## 📞 DESTEK

Hata durumunda:
1. Logları kontrol et
2. `test_google_news_rss.py` çalıştır
3. API key'leri kontrol et
4. Manuel haber çekmeyi test et

---

**Son Güncelleme:** 11 Aralık 2025
**Versiyon:** 2.0 - Zorunlu Sentiment Analizi
