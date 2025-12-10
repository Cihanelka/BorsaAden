"""
Random Forest Modeli Eğitim Scripti
Teknik göstergeler + Haber duygu analizi ile AL/SAT/TUT tahmini
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
from ml_data_collector import MLDataCollector

class RandomForestTrainer:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_columns = None
        self.model_dir = 'data/models'
        os.makedirs(self.model_dir, exist_ok=True)
        
    def prepare_data(self, df):
        """Veriyi eğitim için hazırla"""
        print("\n📊 Veri hazırlama başlıyor...")
        
        # NaN değerleri temizle
        df = df.dropna()
        
        # Hedef değişkeni oluştur (gelecek fiyat değişimi)
        # 5 gün sonraki fiyat değişimine göre AL/SAT/TUT kararı
        df = df.sort_values('datetime')
        df['future_return'] = df.groupby('symbol')['close'].shift(-5) / df['close'] - 1
        
        # Hedef sınıfları oluştur - Daha dengeli eşikler
        # AL: %1.5'den fazla artış
        # SAT: %1.5'den fazla düşüş  
        # TUT: Arasındaki değerler
        df['target'] = 'TUT'
        df.loc[df['future_return'] > 0.015, 'target'] = 'AL'
        df.loc[df['future_return'] < -0.015, 'target'] = 'SAT'
        
        # Gelecek verisi olmayan satırları çıkar
        df = df.dropna(subset=['future_return'])
        
        print(f"✅ Temizlenmiş veri: {len(df)} satır")
        print(f"\n📈 Sınıf dağılımı:")
        print(df['target'].value_counts())
        
        return df
    
    def select_features(self, df):
        """Özellik seçimi yap"""
        # Kullanılacak özellikler - Genişletilmiş liste
        feature_cols = [
            # Teknik göstergeler - Temel
            'rsi', 'macd', 'macd_signal', 'macd_diff',
            'bb_width', 'stoch_k', 'stoch_d', 'atr',
            'volume_ratio', 'price_change_1d', 'price_change_5d', 
            'price_change_10d', 'trend_strength',
            
            # Teknik göstergeler - Gelişmiş
            'obv_change', 'mfi', 'adx', 'cci', 'williams_r', 'roc',
            'sma_cross', 'ema_cross',
            
            # Duygu analizi
            'sentiment_score', 'sentiment_std', 
            'positive_ratio', 'negative_ratio', 'news_count'
        ]
        
        # Mevcut sütunları kontrol et
        available_features = [col for col in feature_cols if col in df.columns]
        
        print(f"\n🎯 Kullanılacak özellikler ({len(available_features)} adet):")
        for feat in available_features:
            print(f"  - {feat}")
        
        self.feature_columns = available_features
        
        X = df[available_features]
        y = df['target']
        
        return X, y
    
    def train_model(self, X, y):
        """Random Forest modelini eğit"""
        print("\n🤖 Model eğitimi başlıyor...")
        
        # Veriyi eğitim ve test setlerine ayır
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"📊 Eğitim seti: {len(X_train)} satır")
        print(f"📊 Test seti: {len(X_test)} satır")
        
        # Özellikleri ölçeklendir
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Random Forest modelini oluştur - Optimize edilmiş parametreler
        self.model = RandomForestClassifier(
            n_estimators=400,            # Ağaç sayısı (200 -> 400)
            max_depth=20,                # Maksimum derinlik (15 -> 20)
            min_samples_split=5,         # Bölünme için minimum örnek (10 -> 5)
            min_samples_leaf=2,          # Yaprak için minimum örnek (5 -> 2)
            max_features='sqrt',         # Her bölünmede kullanılacak özellik sayısı
            min_impurity_decrease=0.0001, # Minimum impurity azalması
            bootstrap=True,              # Bootstrap örnekleme
            oob_score=True,              # Out-of-bag score hesapla
            random_state=42,
            n_jobs=-1,                   # Tüm CPU'ları kullan
            class_weight='balanced',     # Dengesiz sınıflar için
            verbose=1                    # İlerlemeyi göster
        )
        
        # Modeli eğit
        print("\n⏳ Eğitim devam ediyor...")
        self.model.fit(X_train_scaled, y_train)
        
        # Tahmin yap
        y_pred = self.model.predict(X_test_scaled)
        
        # Performans metrikleri
        accuracy = accuracy_score(y_test, y_pred)
        
        print("\n" + "="*60)
        print("📊 MODEL PERFORMANSI")
        print("="*60)
        print(f"\n✅ Test Doğruluğu (Accuracy): {accuracy:.2%}")
        
        # OOB Score
        if hasattr(self.model, 'oob_score_'):
            print(f"✅ OOB Doğruluğu: {self.model.oob_score_:.2%}")
        
        print("\n📈 Sınıf Bazlı Performans:")
        print(classification_report(y_test, y_pred, zero_division=0))
        
        print("\n🔢 Confusion Matrix:")
        print(confusion_matrix(y_test, y_pred))
        
        # Cross-validation
        print("\n🔄 Cross-Validation (5-fold)...")
        cv_scores = cross_val_score(self.model, X_train_scaled, y_train, cv=5)
        print(f"CV Skorları: {cv_scores}")
        print(f"Ortalama CV Skoru: {cv_scores.mean():.2%} (+/- {cv_scores.std() * 2:.2%})")
        
        # Özellik önem dereceleri
        feature_importance = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\n🎯 En Önemli 10 Özellik:")
        print(feature_importance.head(10).to_string(index=False))
        
        return accuracy
    
    def save_model(self):
        """Modeli kaydet"""
        print("\n💾 Model kaydediliyor...")
        
        model_path = os.path.join(self.model_dir, 'random_forest_model.joblib')
        scaler_path = os.path.join(self.model_dir, 'scaler.joblib')
        features_path = os.path.join(self.model_dir, 'feature_columns.joblib')
        info_path = os.path.join(self.model_dir, 'model_info.txt')
        
        joblib.dump(self.model, model_path)
        joblib.dump(self.scaler, scaler_path)
        joblib.dump(self.feature_columns, features_path)
        
        # Model bilgilerini kaydet
        with open(info_path, 'w', encoding='utf-8') as f:
            f.write(f"Model Tipi: Random Forest Classifier\n")
            f.write(f"Eğitim Tarihi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Ağaç Sayısı: {self.model.n_estimators}\n")
            f.write(f"Özellik Sayısı: {len(self.feature_columns)}\n")
            f.write(f"Sınıflar: AL, SAT, TUT\n")
            f.write(f"\nÖzellikler:\n")
            for feat in self.feature_columns:
                f.write(f"  - {feat}\n")
        
        print(f"✅ Model kaydedildi: {model_path}")
        print(f"✅ Scaler kaydedildi: {scaler_path}")
        print(f"✅ Özellikler kaydedildi: {features_path}")
        print(f"✅ Bilgiler kaydedildi: {info_path}")

def main():
    """Ana eğitim fonksiyonu"""
    print("\n" + "="*60)
    print("🚀 RANDOM FOREST MODEL EĞİTİMİ")
    print("="*60)
    
    # Eğitim için hisse sembolleri - Genişletilmiş liste (20 hisse)
    training_symbols = [
        # Teknoloji
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'AMD',
        # Finans
        'JPM', 'BAC', 'WFC', 'GS',
        # Tüketici
        'NFLX', 'DIS', 'NKE', 'SBUX',
        # Sağlık
        'JNJ', 'PFE', 'UNH',
        # Enerji
        'XOM'
    ]
    
    print(f"\n📋 Eğitim için {len(training_symbols)} hisse kullanılacak")
    print(f"Hisseler: {', '.join(training_symbols)}")
    
    # Veri topla - 180 gün (6 ay) tarihsel veri
    collector = MLDataCollector()
    df = collector.create_training_dataset(training_symbols, days=180)
    
    if df is None or len(df) < 10:
        print("\n❌ Yeterli veri toplanamadı! En az 10 satır gerekli.")
        return
    
    # CSV olarak kaydet
    csv_path = 'data/csv/training_data.csv'
    os.makedirs('data/csv', exist_ok=True)
    df.to_csv(csv_path, index=False)
    print(f"\n💾 Ham veri kaydedildi: {csv_path}")
    
    # Modeli eğit
    trainer = RandomForestTrainer()
    
    # Veriyi hazırla
    df_prepared = trainer.prepare_data(df)
    
    if len(df_prepared) < 5:
        print("\n❌ Eğitim için yeterli veri yok! En az 5 satır gerekli.")
        return
    
    # Özellikleri seç
    X, y = trainer.select_features(df_prepared)
    
    # Modeli eğit
    accuracy = trainer.train_model(X, y)
    
    # Modeli kaydet
    trainer.save_model()
    
    print("\n" + "="*60)
    print("✅ EĞİTİM TAMAMLANDI!")
    print("="*60)
    print(f"\n📊 Final Doğruluk: {accuracy:.2%}")
    print("\n💡 Model kullanıma hazır!")
    print("   Şimdi START_EVERYTHING.bat ile uygulamayı başlatabilirsiniz.")

if __name__ == "__main__":
    main()
