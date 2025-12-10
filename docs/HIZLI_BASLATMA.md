# 🚀 Aden Borsa - Hızlı Başlatma Kılavuzu

## ✅ Gereksinimler

### 1. Python (ML Servisi için)
```bash
python --version  # 3.8+ gerekli
```

### 2. Node.js (Backend ve Frontend için)
```bash
node --version  # 16+ gerekli
npm --version
```

## 📦 İlk Kurulum (Sadece Bir Kez)

### 1. Python Paketlerini Yükle
```bash
pip install flask flask-cors
```

### 2. Backend Paketlerini Yükle
```bash
cd server
npm install
cd ..
```

### 3. Frontend Paketlerini Yükle
```bash
npm install
```

## 🎯 Uygulamayı Başlat

### Otomatik Başlatma (Önerilen)
`START_EVERYTHING.bat` dosyasına **çift tıklayın**

veya

```bash
.\START_EVERYTHING.bat
```

### Manuel Başlatma
```bash
# Terminal 1 - ML Servisi
cd ml-service
python app_simple.py

# Terminal 2 - Backend
cd server
npm start

# Terminal 3 - Frontend
npm run dev
```

## 🌐 Erişim Adresleri

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:3001
- **ML Service:** http://localhost:5000

## ⚠️ Önemli Notlar

### ML Servisi Hakkında
- Şu an **DEMO modunda** çalışıyor
- Gerçek ML tahmini yapmaz, rastgele demo verileri üretir
- Tam ML özelliklerini kullanmak için:
  ```bash
  cd ml-service
  pip install -r requirements.txt
  python app.py
  ```

### Sorun Giderme

#### ML Servisi 500 Hatası
```bash
# Flask ve Flask-CORS'u yükleyin
pip install flask flask-cors
```

#### Backend Başlamıyor
```bash
cd server
npm install
npm start
```

#### Frontend Başlamıyor
```bash
npm install
npm run dev
```

## 🛑 Uygulamayı Durdurma

Her terminal penceresinde **Ctrl+C** tuşlarına basın.

## 📝 Giriş Bilgileri

Uygulama ilk açıldığında kayıt olmanız gerekecek. Kayıt olduktan sonra aynı bilgilerle giriş yapabilirsiniz.

## 🎨 Özellikler

- ✅ Hisse senedi arama ve analiz
- ✅ Teknik analiz göstergeleri
- ✅ ML tahmin sistemi (Demo)
- ✅ Kullanıcı yorumları
- ✅ Favoriler sistemi
- ✅ Finansal haberler
- ✅ Kullanıcı profili

## 💡 İpuçları

1. İlk kullanımda tüm paketlerin yüklenmesi 5-10 dakika sürebilir
2. ML servisi demo modunda çalışıyor, gerçek tahminler için `requirements.txt` yükleyin
3. Her servis ayrı terminal penceresinde çalışır
4. Hata alırsanız terminal çıktılarını kontrol edin
