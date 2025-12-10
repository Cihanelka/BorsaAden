"""
CSV dosyasından Random Forest Modeli Eğitimi
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import joblib
import os
from datetime import datetime

class CSVModelTrainer:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_columns = None
        self.model_dir = 'data/models'
        os.makedirs(self.model_dir, exist_ok=True)
    
    def load_csv(self, csv_path):
        """CSV dosyasını yükle"""
        print(f"\n📂 CSV dosyası yükleniyor: {csv_path}")
        
        try:
            df = pd.read_csv(csv_path)
            print(f"✅ {len(df)} satır, {len(df.columns)} sütun yüklendi")
            print(f"\n📋 Sütunlar: {', '.join(df.columns.tolist())}")
            return df
        except Exception as e:
            print(f"❌ CSV yükleme hatası: {e}")
            return None
    
    def prepare_data(self, df):
        """Veriyi eğitim için hazırla"""
        print("\n📊 Veri hazırlama başlıyor...")
        
        # Tarih sütununu datetime'a çevir
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
        elif 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'])
            df = df.sort_values('datetime')
        
        # Hedef değişkeni oluştur (gelecek fiyat değişimi)
        # 5 gün sonraki fiyat değişimine göre AL/SAT/TUT kararı
        if 'symbol' in df.columns:
            df['future_return'] = df.groupby('symbol')['close'].shift(-5) / df['close'] - 1
        else:
            df['future_return'] = df['close'].shift(-5) / df['close'] - 1
        
        # Hedef sınıfları oluştur
        df['target'] = 'TUT'
        df.loc[df['future_return'] > 0.02, 'target'] = 'AL'
        df.loc[df['future_return'] < -0.02, 'target'] = 'SAT'
        
        # Gelecek verisi olmayan satırları çıkar
        df = df.dropna(subset=['future_return'])
        
        # NaN değerleri temizle
        df = df.fillna(0)
        
        print(f"✅ Temizlenmiş veri: {len(df)} satır")
        print(f"\n📈 Sınıf dağılımı:")
        print(df['target'].value_counts())
        
        return df
    
    def select_features(self, df):
        """Özellikleri seç"""
        print("\n🎯 Özellik seçimi yapılıyor...")
        
        # Temel özellikler
        base_features = ['open', 'high', 'low', 'close', 'volume']
        
        # Teknik göstergeler (varsa)
        technical_features = [
            'rsi', 'macd', 'macd_signal', 'macd_diff',
            'bb_width', 'stoch_k', 'stoch_d', 'atr',
            'sma_20', 'ema_20', 'volume_ratio',
            'price_change_1d', 'price_change_5d', 'price_change_10d',
            'trend_strength'
        ]
        
        # Duygu analizi özellikleri (varsa)
        sentiment_features = [
            'sentiment_score', 'sentiment_std',
            'positive_ratio', 'negative_ratio', 'news_count'
        ]
        
        # Mevcut sütunları kontrol et
        available_features = []
        for feat in base_features + technical_features + sentiment_features:
            if feat in df.columns:
                available_features.append(feat)
        
        print(f"✅ {len(available_features)} özellik seçildi")
        print(f"Özellikler: {', '.join(available_features)}")
        
        self.feature_columns = available_features
        
        X = df[available_features]
        y = df['target']
        
        return X, y
    
    def train_model(self, X, y):
        """Random Forest modelini eğit"""
        print("\n🤖 Model eğitimi başlıyor...")
        
        # Veriyi böl
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"📊 Eğitim seti: {len(X_train)} satır")
        print(f"📊 Test seti: {len(X_test)} satır")
        
        # Özellikleri ölçeklendir
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Random Forest modeli
        self.model = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=42,
            class_weight='balanced',
            n_jobs=-1
        )
        
        # Eğit
        print("\n⏳ Eğitim devam ediyor...")
        self.model.fit(X_train_scaled, y_train)
        
        # Tahmin yap
        y_pred = self.model.predict(X_test_scaled)
        
        # Değerlendir
        accuracy = accuracy_score(y_test, y_pred)
        
        print("\n" + "="*60)
        print("📊 MODEL PERFORMANSI")
        print("="*60)
        print(f"\n✅ Doğruluk (Accuracy): {accuracy:.4f} ({accuracy*100:.2f}%)")
        
        print("\n📋 Sınıflandırma Raporu:")
        print(classification_report(y_test, y_pred))
        
        print("\n🔢 Karışıklık Matrisi:")
        print(confusion_matrix(y_test, y_pred))
        
        # Çapraz doğrulama
        print("\n🔄 Çapraz doğrulama yapılıyor...")
        cv_scores = cross_val_score(self.model, X_train_scaled, y_train, cv=5)
        print(f"✅ CV Skorları: {cv_scores}")
        print(f"✅ Ortalama CV Skoru: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
        
        # Özellik önemleri
        print("\n⭐ En Önemli 10 Özellik:")
        feature_importance = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        for idx, row in feature_importance.head(10).iterrows():
            print(f"  {row['feature']}: {row['importance']:.4f}")
        
        return accuracy
    
    def save_model(self):
        """Modeli kaydet"""
        print("\n💾 Model kaydediliyor...")
        
        model_path = os.path.join(self.model_dir, 'random_forest_model.joblib')
        scaler_path = os.path.join(self.model_dir, 'scaler.joblib')
        features_path = os.path.join(self.model_dir, 'feature_columns.joblib')
        info_path = os.path.join(self.model_dir, 'model_info.txt')
        
        # Kaydet
        joblib.dump(self.model, model_path)
        joblib.dump(self.scaler, scaler_path)
        joblib.dump(self.feature_columns, features_path)
        
        # Model bilgilerini kaydet
        with open(info_path, 'w', encoding='utf-8') as f:
            f.write(f"Random Forest Model Bilgileri\n")
            f.write(f"="*50 + "\n\n")
            f.write(f"Eğitim Tarihi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Model Tipi: Random Forest Classifier\n")
            f.write(f"Ağaç Sayısı: {self.model.n_estimators}\n")
            f.write(f"Maksimum Derinlik: {self.model.max_depth}\n")
            f.write(f"Özellik Sayısı: {len(self.feature_columns)}\n")
            f.write(f"Sınıflar: {', '.join(self.model.classes_)}\n\n")
            f.write(f"Özellikler:\n")
            for feat in self.feature_columns:
                f.write(f"  - {feat}\n")
        
        print(f"✅ Model kaydedildi: {model_path}")
        print(f"✅ Scaler kaydedildi: {scaler_path}")
        print(f"✅ Özellikler kaydedildi: {features_path}")
        print(f"✅ Bilgiler kaydedildi: {info_path}")

def main():
    """Ana eğitim fonksiyonu"""
    print("\n" + "="*60)
    print("🚀 CSV'DEN RANDOM FOREST MODEL EĞİTİMİ")
    print("="*60)
    
    # CSV dosya yolu
    csv_path = 'data/csv/stock_data.csv'
    
    # Eğitici oluştur
    trainer = CSVModelTrainer()
    
    # CSV'yi yükle
    df = trainer.load_csv(csv_path)
    
    if df is None:
        print("\n❌ CSV dosyası yüklenemedi!")
        return
    
    # Veriyi hazırla
    df_prepared = trainer.prepare_data(df)
    
    if len(df_prepared) < 10:
        print("\n❌ Eğitim için yeterli veri yok! En az 10 satır gerekli.")
        print(f"Mevcut: {len(df_prepared)} satır")
        return
    
    # Özellikleri seç
    X, y = trainer.select_features(df_prepared)
    
    # Modeli eğit
    accuracy = trainer.train_model(X, y)
    
    # Modeli kaydet
    trainer.save_model()
    
    print("\n" + "="*60)
    print("✅ EĞİTİM TAMAMLANDI!")
    print(f"📊 Final Doğruluk: {accuracy*100:.2f}%")
    print("="*60)
    print("\n💡 Şimdi START_EVERYTHING.bat ile uygulamayı başlatabilirsiniz!")

if __name__ == "__main__":
    main()
