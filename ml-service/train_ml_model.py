"""
Gerçek ML Modeli Eğitim Scripti
Random Forest kullanarak hisse tahmini modeli eğitir
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score
import joblib
import os
from datetime import datetime

# Klasör oluştur
os.makedirs('data/models', exist_ok=True)

def create_training_data():
    """
    Eğitim verisi oluştur
    Gerçek bir projede bu veriler API'den veya veritabanından gelir
    """
    print("📊 Eğitim verisi oluşturuluyor...")
    
    # Simülasyon: 1000 örnek veri
    np.random.seed(42)
    n_samples = 1000
    
    data = {
        # Teknik göstergeler
        'rsi': np.random.uniform(20, 80, n_samples),
        'macd': np.random.uniform(-5, 5, n_samples),
        'macd_signal': np.random.uniform(-5, 5, n_samples),
        'bb_position': np.random.uniform(0, 1, n_samples),  # 0=alt band, 1=üst band
        'sma_20': np.random.uniform(100, 300, n_samples),
        'ema_12': np.random.uniform(100, 300, n_samples),
        'ema_26': np.random.uniform(100, 300, n_samples),
        'current_price': np.random.uniform(100, 300, n_samples),
        
        # Duygu analizi
        'sentiment_score': np.random.uniform(0, 1, n_samples),
        'news_count': np.random.randint(1, 20, n_samples),
        
        # Volatilite ve hacim
        'volatility': np.random.uniform(0.01, 0.1, n_samples),
        'volume_trend': np.random.uniform(0.5, 2.0, n_samples),
        
        # Fiyat değişimleri
        'price_change_1d': np.random.uniform(-5, 5, n_samples),
        'price_change_5d': np.random.uniform(-10, 10, n_samples),
    }
    
    df = pd.DataFrame(data)
    
    # Özellik mühendisliği
    df['macd_histogram'] = df['macd'] - df['macd_signal']
    df['price_vs_sma'] = (df['current_price'] - df['sma_20']) / df['sma_20']
    df['ema_crossover'] = (df['ema_12'] > df['ema_26']).astype(int)
    
    # Hedef değişken oluştur (AL/TUT/SAT)
    # Gerçekçi kurallar kullanarak etiketler oluştur
    conditions = []
    
    # AL koşulları
    al_condition = (
        (df['rsi'] < 35) |  # Aşırı satım
        ((df['macd_histogram'] > 0) & (df['sentiment_score'] > 0.6)) |  # Pozitif MACD + İyi duygu
        ((df['bb_position'] < 0.2) & (df['volume_trend'] > 1.2))  # Alt band + Yüksek hacim
    )
    
    # SAT koşulları
    sat_condition = (
        (df['rsi'] > 65) |  # Aşırı alım
        ((df['macd_histogram'] < 0) & (df['sentiment_score'] < 0.4)) |  # Negatif MACD + Kötü duygu
        ((df['bb_position'] > 0.8) & (df['volatility'] > 0.05))  # Üst band + Yüksek volatilite
    )
    
    # Etiketleri ata
    df['target'] = 'TUT'  # Varsayılan
    df.loc[al_condition, 'target'] = 'AL'
    df.loc[sat_condition, 'target'] = 'SAT'
    
    # Etiket dağılımını göster
    print("\n📈 Etiket Dağılımı:")
    print(df['target'].value_counts())
    print(f"\nToplam örnek: {len(df)}")
    
    return df

def train_model(df):
    """
    Random Forest modelini eğit
    """
    print("\n🤖 Model eğitimi başlıyor...")
    
    # Özellikler ve hedef
    feature_columns = [
        'rsi', 'macd', 'macd_signal', 'macd_histogram',
        'bb_position', 'sma_20', 'ema_12', 'ema_26',
        'current_price', 'price_vs_sma', 'ema_crossover',
        'sentiment_score', 'news_count',
        'volatility', 'volume_trend',
        'price_change_1d', 'price_change_5d'
    ]
    
    X = df[feature_columns]
    y = df['target']
    
    # Eğitim/test ayrımı
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"Eğitim seti: {len(X_train)} örnek")
    print(f"Test seti: {len(X_test)} örnek")
    
    # Normalizasyon
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Random Forest modeli
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    
    print("\n⏳ Model eğitiliyor...")
    model.fit(X_train_scaled, y_train)
    
    # Tahmin ve değerlendirme
    y_pred = model.predict(X_test_scaled)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"\n✅ Model eğitimi tamamlandı!")
    print(f"🎯 Doğruluk: {accuracy:.2%}")
    
    print("\n📊 Detaylı Rapor:")
    print(classification_report(y_test, y_pred))
    
    # Özellik önem sıralaması
    feature_importance = pd.DataFrame({
        'feature': feature_columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\n🔝 En Önemli Özellikler:")
    print(feature_importance.head(10).to_string(index=False))
    
    return model, scaler, feature_columns

def save_model(model, scaler, feature_columns):
    """
    Modeli ve scaler'ı kaydet
    """
    print("\n💾 Model kaydediliyor...")
    
    model_path = 'data/models/stock_predictor.joblib'
    scaler_path = 'data/models/scaler.joblib'
    features_path = 'data/models/feature_columns.joblib'
    
    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)
    joblib.dump(feature_columns, features_path)
    
    print(f"✅ Model kaydedildi: {model_path}")
    print(f"✅ Scaler kaydedildi: {scaler_path}")
    print(f"✅ Özellikler kaydedildi: {features_path}")
    
    # Model bilgilerini kaydet
    info = {
        'trained_at': datetime.now().isoformat(),
        'model_type': 'RandomForestClassifier',
        'n_features': len(feature_columns),
        'feature_columns': feature_columns
    }
    
    info_path = 'data/models/model_info.txt'
    with open(info_path, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("ML MODEL BİLGİLERİ\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Eğitim Tarihi: {info['trained_at']}\n")
        f.write(f"Model Tipi: {info['model_type']}\n")
        f.write(f"Özellik Sayısı: {info['n_features']}\n\n")
        f.write("Özellikler:\n")
        for i, col in enumerate(feature_columns, 1):
            f.write(f"  {i}. {col}\n")
    
    print(f"✅ Model bilgileri kaydedildi: {info_path}")

def main():
    """
    Ana eğitim fonksiyonu
    """
    print("\n" + "=" * 60)
    print("🚀 ML MODEL EĞİTİMİ BAŞLIYOR")
    print("=" * 60 + "\n")
    
    # 1. Veri oluştur
    df = create_training_data()
    
    # 2. Modeli eğit
    model, scaler, feature_columns = train_model(df)
    
    # 3. Modeli kaydet
    save_model(model, scaler, feature_columns)
    
    print("\n" + "=" * 60)
    print("✅ MODEL EĞİTİMİ TAMAMLANDI!")
    print("=" * 60)
    print("\n💡 Artık advanced_app.py ML modelini kullanacak!")
    print("   Servisi yeniden başlatın: python advanced_app.py\n")

if __name__ == '__main__':
    main()
