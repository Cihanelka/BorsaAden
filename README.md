# Aden Borsa

![Aden Borsa](https://img.shields.io/badge/Aden-Borsa-blue) ![License](https://img.shields.io/badge/license-MIT-green) ![Status](https://img.shields.io/badge/status-active-brightgreen)

Aden Borsa, hisse senedi yatırımcıları için geliştirilmiş kapsamlı bir **AI destekli analiz platformudur**. 15+ makine öğrenmesi modeli, teknik analiz göstergeleri, haber sentiment analizi ve topluluk yorumlarını tek bir platformda birleştirir.

## 🎯 Özellikler

### AI Tahmin Sistemi
- **15+ ML Modeli**: RandomForest, XGBoost, CatBoost, GradientBoosting, HistGradientBoosting, ExtraTrees, AdaBoost, SVM, LogisticRegression, KNN, DecisionTree, Ridge, Bagging, Voting, Stacking
- **Ensemble Yaklaşımı**: 15 modelin oylarıyla %75+ test doğruluğu
- **Per-Symbol Dinamik Etiketleme**: Her hissenin volatilitesine göre otomatik sınıf ayırımı
- **Gerçek Zamanlı Tahmin**: Seçilen hisse için anlık tahmin ve güven skoru

### Teknik Analiz
- **47 Teknik İndikatör**: RSI, MACD, Bollinger Bands, ATR, Stochastic, OBV, Moving Averages (SMA, EMA), Volume Ratios, Price Momentum, Candlestick Patterns, Trend Strength, 52-week High/Low Proximity
- **Destek ve Direnç Seviyeleri**: Otomatik hesaplanan kritik fiyat seviyeleri
- **Trend Analizi**: Güçlü trend tespiti ve yön belirleme

### Haber Sentiment Analizi
- **Finnhub API Entegrasyonu**: Gerçek zamanlı haber çekimi
- **Duygu Analizi**: Haberlerin pozitif/negatif/nötr sınıflandırması
- **Etki Skoru**: Haberlerin tahmin üzerindeki etkisi

### Sosyal Özellikler
- **Kullanıcı Yorumları**: Hisse başına yorum sistemi
- **Favori Hisseler**: Takip edilen hisseler listesi
- **Kullanıcı Profili**: Kişiselleştirilmiş deneyim

### Görsel Arayüz
- **Canlı Grafikler**: Recharts ile interaktif fiyat grafikleri
- **Tarihsel Veriler Tablosu**: Detaylı OHLCV verisi
- **Türkçe Arayüz**: Tamamen yerelleştirilmiş arayüz
- **Responsive Tasarım**: Masaüstü ve mobil uyumlu

## 🛠️ Teknoloji Yığını

### Frontend
- **React 18** + **TypeScript**
- **TailwindCSS** + **shadcn/ui** bileşenleri
- **Recharts** - Grafik kütüphanesi
- **Lucide React** - İkonlar
- **Sonner** - Toast bildirimleri
- **React Router** - Yönlendirme

### Backend
- **Node.js** + **Express.js**
- **SQLite** - Veritabanı
- **JWT** - Kimlik doğrulama
- **bcrypt** - Şifre hashleme

### ML Servis (Python)
- **Flask** - REST API
- **scikit-learn** - ML algoritmaları
- **XGBoost** - Gradient boosting
- **CatBoost** - Kategorik boosting
- **pandas** - Veri işleme
- **yfinance** - Finansal veri
- **Finnhub API** - Haber verisi

## 📦 Kurulum

### Ön Koşullar
- Node.js 18+
- Python 3.9+
- npm veya yarn
- Git

### Adım 1: Projeyi Klonlayın
```bash
git clone <repository-url>
cd "Aden Borsa"
```

### Adım 2: Python Sanal Ortamı Oluşturun
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# veya
source .venv/bin/activate  # Linux/Mac
```

### Adım 3: Python Bağımlılıklarını Kurun
```bash
cd ml-service
pip install -r requirements.txt
```

### Adım 4: ML Modellerini Eğitin
```bash
python train_models.py
```
Bu işlem birkaç dakika sürebilir. Eğitim tamamlandığında 15 model `data/models/` klasörüne kaydedilir.

### Adım 5: Backend Kurulumu
```bash
cd backend
npm install
```

### Adım 6: Frontend Kurulumu
```bash
cd frontend
npm install
```

### Adım 7: Ortam Değişkenlerini Ayarlayın

**Backend (.env)**
```env
API_PORT=3001
ML_SERVICE_URL=http://localhost:5000
JWT_SECRET=your-secret-key
```

**Frontend (.env)**
```env
VITE_API_URL=http://localhost:3001/api
VITE_FINNHUB_KEY=your-finnhub-api-key
```

**ML Servis (config.py)**
```python
# config.py içinde gerekli ayarları yapın
FINNHUB_API_KEY = 'your-finnhub-api-key'
```

## 🚀 Çalıştırma

### Hızlı Başlatma (Tüm Servisler)
```bash
START_EVERYTHING.bat  # Windows
```
Bu komut ML servisi, backend ve frontend'i otomatik başlatır.

### Manuel Başlatma

**ML Servis (Port 5000)**
```bash
cd ml-service
python app.py
```

**Backend (Port 3001)**
```bash
cd backend
npm start
```

**Frontend (Port 5173)**
```bash
cd frontend
npm run dev
```

### Erişim Noktaları
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:3001/api
- **ML Servis**: http://localhost:5000

## 📁 Proje Yapısı

```
Aden Borsa/
├── backend/              # Node.js Express backend
│   ├── routes/          # API route'ları
│   ├── models/          # Sequelize modelleri
│   ├── middleware/      # JWT middleware
│   └── index.js         # Backend giriş noktası
├── frontend/            # React TypeScript frontend
│   ├── src/
│   │   ├── components/  # React bileşenleri
│   │   ├── pages/       # Sayfa bileşenleri
│   │   ├── services/    # API servisleri
│   │   └── contexts/    # React Context
│   └── package.json
├── ml-service/          # Python ML servisi
│   ├── data/            # Veri klasörü (modeller, cache)
│   ├── app.py           # Flask API
│   ├── model_trainer.py # Model eğitimi
│   ├── feature_engineer.py # Feature engineering
│   ├── data_collector.py    # Veri toplama
│   ├── monthly_predictor.py # Tahmin motoru
│   ├── news_collector.py    # Haber çekme
│   └── sentiment_scorer.py  # Sentiment analizi
└── START_EVERYTHING.bat # Hızlı başlatma scripti
```

## 🔌 API Endpoints

### Backend API (Port 3001)

#### Kimlik Doğrulama
- `POST /api/auth/register` - Kullanıcı kaydı
- `POST /api/auth/login` - Kullanıcı girişi
- `GET /api/auth/me` - Mevcut kullanıcı bilgisi
- `PUT /api/auth/update-profile` - Profil güncelleme

#### ML Servis Proxy
- `POST /api/ml/predict-ensemble` - Ensemble tahmin
- `POST /api/ml/stock-data` - OHLCV verisi
- `POST /api/ml/sentiment-summary` - Haber sentiment
- `GET /api/ml/health` - ML servis sağlık kontrolü

#### Favoriler
- `GET /api/favorites` - Favori hisseler
- `POST /api/favorites` - Favori ekle
- `DELETE /api/favorites/:symbol` - Favori sil

#### Yorumlar
- `GET /api/comments/:symbol` - Hisse yorumları
- `POST /api/comments` - Yorum ekle
- `PUT /api/comments/:id` - Yorum güncelle
- `DELETE /api/comments/:id` - Yorum sil

### ML Servis API (Port 5000)

- `POST /api/predict-monthly` - Aylık tahmin
- `POST /api/predict-ensemble` - Ensemble tahmin (frontend uyumlu)
- `POST /api/predict` - Tahmin (alias)
- `POST /api/stock-data` - OHLCV verisi
- `POST /api/sentiment-summary` - Haber sentiment
- `GET /api/health` - Sağlık kontrolü
- `GET /api/models-status` - Model durumu

## 📊 Model Eğitimi

### Veri Hazırlığı
- **Kaynak**: yfinance API
- **Hisseler**: 27 ABD hissesi (AAPL, MSFT, GOOGL, AMZN, vb.)
- **Zaman Aralığı**: 7 yıl OHLCV verisi
- **Özellikler**: 47 teknik indikatör

### Etiketleme Stratejisi
- **Per-Symbol Percentile**: Her hissenin kendi getiri dağılımına göre
- **Dinamik Eşikler**: Top %33 = RISE, Bottom %33 = FALL, Orta = STABLE
- **Minimum Eşik**: ±%1 (gürültü önleme)
- **Tahmin Ufku**: 30 gün

### Sınıf Dağılımı
- DÜŞME (FALL): ~33%
- SABİT (STABLE): ~33%
- YÜKSELME (RISE): ~33%

### Model Sonuçları
| Model | Test Doğruluğu |
|-------|---------------|
| Bagging | 0.7584 |
| XGBoost | 0.6353 |
| HistGradientBoosting | 0.6240 |
| Stacking | 0.6295 |
| Voting | 0.6196 |
| GradientBoosting | 0.5873 |
| RandomForest | 0.5866 |
| ExtraTrees | 0.5710 |

## 🔧 Yapılandırma

### ML Servis (config.py)
```python
# API Anahtarları
FINNHUB_API_KEY = 'your-key'

# Veri Ayarları
DATA_DIR = 'data'
CSV_DIR = 'data/csv'
MODEL_DIR = 'data/models'

# Eğitim Ayarları
OHLCV_YEARS = 7
CACHE_HOURS = 20

# Teknik Analiz
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
```

### Backend (.env)
```env
API_PORT=3001
ML_SERVICE_URL=http://localhost:5000
JWT_SECRET=your-secret-key
DB_PATH=./aden-borsa.db
```

## ⚠️ Risk Uyarısı

Bu platform **yatırım tavsiyesi değildir**. Tüm tahminler ve analizler sadece bilgilendirme amaçlıdır. Finansal kararlarınızı vermeden önce:

1. Kendi araştırmanızı yapın
2. Risk toleransınızı değerlendirin
3. Profesyonel bir danışmana başvurun

## 🤝 Katkıda Bulunma

Katkılarınızı bekliyoruz! Lütfen şu adımları izleyin:

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add amazing feature'`)
4. Branch'inizi push edin (`git push origin feature/amazing-feature`)
5. Pull Request açın

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Daha fazla bilgi için [LICENSE](LICENSE) dosyasına bakın.

---

**© 2025-2026 Aden Borsa. Tüm Hakları Saklıdır.**
