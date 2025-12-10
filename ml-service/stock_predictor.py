"""
Duygu analizi + Teknik analiz birleştirilerek AL/SAT/TUT kararı veren model
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import joblib
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from config import *
from sentiment_analyzer import SentimentAnalyzer
from technical_analyzer import TechnicalAnalyzer

class StockPredictor:
    """
    Haber duygu skorları ve teknik analiz verilerini birleştirerek
    hisse senedi için AL/SAT/TUT önerisi üretir
    """
    
    def __init__(self):
        """Model ve analizcileri başlatır"""
        print("🤖 Stock Predictor başlatılıyor...")
        
        self.sentiment_analyzer = SentimentAnalyzer()
        self.technical_analyzer = TechnicalAnalyzer()
        
        # ML Model (varsa yükle, yoksa None)
        self.model = None
        self.scaler = None
        self.load_model()
        
        print("✅ Stock Predictor hazır")
    
    def load_model(self):
        """Eğitilmiş modeli yükler"""
        model_path = os.path.join(MODEL_DIR, 'stock_predictor.joblib')
        scaler_path = os.path.join(MODEL_DIR, 'scaler.joblib')
        
        if os.path.exists(model_path) and os.path.exists(scaler_path):
            try:
                self.model = joblib.load(model_path)
                self.scaler = joblib.load(scaler_path)
                print(f"✅ Model yüklendi: {model_path}")
            except Exception as e:
                print(f"⚠️ Model yükleme hatası: {str(e)}")
                self.model = None
                self.scaler = None
        else:
            print("ℹ️ Eğitilmiş model bulunamadı, rule-based sistem kullanılacak")
    
    def save_model(self):
        """Eğitilmiş modeli kaydeder"""
        if self.model is None or self.scaler is None:
            print("⚠️ Kaydedilecek model yok")
            return
        
        model_path = os.path.join(MODEL_DIR, 'stock_predictor.joblib')
        scaler_path = os.path.join(MODEL_DIR, 'scaler.joblib')
        
        try:
            joblib.dump(self.model, model_path)
            joblib.dump(self.scaler, scaler_path)
            print(f"💾 Model kaydedildi: {model_path}")
        except Exception as e:
            print(f"❌ Model kaydetme hatası: {str(e)}")
    
    def prepare_features(self, technical_data, sentiment_data):
        """
        Teknik ve duygu verilerinden özellik vektörü oluşturur
        
        Args:
            technical_data: Teknik analiz sonuçları (dict)
            sentiment_data: Duygu analizi sonuçları (dict)
            
        Returns:
            dict: Birleştirilmiş özellikler
        """
        features = {}
        
        # Teknik göstergelerden özellikler
        if technical_data and isinstance(technical_data, dict):
            features['technical_score'] = technical_data.get('score', 0.5)
            
            # Teknik sinyallerden skorlar
            signals = technical_data.get('signals', {})
            features['rsi_score'] = signals.get('RSI', {}).get('score', 0.5)
            features['macd_score'] = signals.get('MACD', {}).get('score', 0.5)
            features['bb_score'] = signals.get('BB', {}).get('score', 0.5)
            features['sma_score'] = signals.get('SMA', {}).get('score', 0.5)
            features['stoch_score'] = signals.get('STOCH', {}).get('score', 0.5)
        else:
            features.update({
                'technical_score': 0.5,
                'rsi_score': 0.5,
                'macd_score': 0.5,
                'bb_score': 0.5,
                'sma_score': 0.5,
                'stoch_score': 0.5
            })
        
        # Duygu analizinden özellikler
        if sentiment_data and isinstance(sentiment_data, dict):
            features['sentiment_score'] = sentiment_data.get('normalized_sentiment', 0.0)
            features['news_count'] = sentiment_data.get('news_count', 0)
            features['positive_ratio'] = (
                sentiment_data.get('positive_count', 0) / max(sentiment_data.get('news_count', 1), 1)
            )
            features['negative_ratio'] = (
                sentiment_data.get('negative_count', 0) / max(sentiment_data.get('news_count', 1), 1)
            )
        else:
            features.update({
                'sentiment_score': 0.0,
                'news_count': 0,
                'positive_ratio': 0.0,
                'negative_ratio': 0.0
            })
        
        return features
    
    def rule_based_prediction(self, features):
        """
        Kural tabanlı tahmin (model yoksa kullanılır)
        
        Args:
            features: Özellik vektörü
            
        Returns:
            dict: Tahmin sonucu
        """
        # Ağırlıklar
        TECHNICAL_WEIGHT = 0.6
        SENTIMENT_WEIGHT = 0.4
        
        # Teknik skor
        tech_score = features.get('technical_score', 0.5)
        
        # Duygu skorunu 0-1 aralığına normalize et (-1,+1 -> 0,1)
        sentiment_raw = features.get('sentiment_score', 0.0)
        sentiment_score = (sentiment_raw + 1) / 2  # -1,+1 -> 0,1
        
        # Haber sayısına göre duygu skorunun ağırlığını ayarla
        news_count = features.get('news_count', 0)
        if news_count < 3:
            # Az haber varsa duygu skorunun etkisini azalt
            sentiment_weight_adjusted = SENTIMENT_WEIGHT * (news_count / 3)
            technical_weight_adjusted = 1 - sentiment_weight_adjusted
        else:
            sentiment_weight_adjusted = SENTIMENT_WEIGHT
            technical_weight_adjusted = TECHNICAL_WEIGHT
        
        # Birleşik skor
        combined_score = (
            tech_score * technical_weight_adjusted +
            sentiment_score * sentiment_weight_adjusted
        )
        
        # Karar ver
        if combined_score >= BUY_THRESHOLD:
            prediction = 'AL'
            confidence = combined_score
        elif combined_score <= SELL_THRESHOLD:
            prediction = 'SAT'
            confidence = 1 - combined_score
        else:
            prediction = 'TUT'
            confidence = 1 - abs(combined_score - 0.5) * 2
        
        return {
            'prediction': prediction,
            'confidence': confidence,
            'combined_score': combined_score,
            'technical_score': tech_score,
            'sentiment_score': sentiment_score,
            'news_count': news_count,
            'method': 'rule_based'
        }
    
    def ml_based_prediction(self, features):
        """
        ML model ile tahmin
        
        Args:
            features: Özellik vektörü
            
        Returns:
            dict: Tahmin sonucu
        """
        if self.model is None or self.scaler is None:
            return self.rule_based_prediction(features)
        
        try:
            # Özellikleri sırala ve array'e çevir
            feature_names = [
                'technical_score', 'sentiment_score', 'news_count',
                'rsi_score', 'macd_score', 'bb_score', 'sma_score', 'stoch_score',
                'positive_ratio', 'negative_ratio'
            ]
            
            feature_vector = np.array([[features.get(f, 0.5) for f in feature_names]])
            
            # Normalize et
            feature_vector_scaled = self.scaler.transform(feature_vector)
            
            # Tahmin yap
            prediction = self.model.predict(feature_vector_scaled)[0]
            probabilities = self.model.predict_proba(feature_vector_scaled)[0]
            
            # Sınıf etiketleri: 0=SAT, 1=TUT, 2=AL
            class_names = ['SAT', 'TUT', 'AL']
            prediction_label = class_names[prediction]
            confidence = probabilities[prediction]
            
            return {
                'prediction': prediction_label,
                'confidence': confidence,
                'probabilities': {
                    'AL': probabilities[2],
                    'TUT': probabilities[1],
                    'SAT': probabilities[0]
                },
                'technical_score': features.get('technical_score', 0.5),
                'sentiment_score': features.get('sentiment_score', 0.0),
                'news_count': features.get('news_count', 0),
                'method': 'ml_model'
            }
            
        except Exception as e:
            print(f"⚠️ ML tahmin hatası, rule-based'e geçiliyor: {str(e)}")
            return self.rule_based_prediction(features)
    
    def predict_stock(self, symbol, stock_df=None, news_df=None):
        """
        Belirli bir hisse için AL/SAT/TUT tahmini yapar
        
        Args:
            symbol: Hisse sembolü
            stock_df: Hisse fiyat verileri (DataFrame)
            news_df: Haber verileri (DataFrame)
            
        Returns:
            dict: Tahmin sonucu
        """
        print(f"\n🔮 {symbol} için tahmin yapılıyor...")
        
        # Teknik analiz
        technical_result = None
        if stock_df is not None and not stock_df.empty:
            # Sembole göre filtrele
            symbol_stock = stock_df[stock_df['symbol'] == symbol].copy()
            if not symbol_stock.empty:
                symbol_stock = symbol_stock.sort_values('date')
                analyzed_stock = self.technical_analyzer.calculate_all_indicators(symbol_stock)
                technical_result = self.technical_analyzer.get_technical_signals(analyzed_stock)
        
        # Duygu analizi
        sentiment_result = None
        if news_df is not None and not news_df.empty:
            # Eğer sentiment skorları yoksa hesapla
            if 'sentiment_score' not in news_df.columns:
                news_df = self.sentiment_analyzer.analyze_news_batch(news_df)
            
            sentiment_result = self.sentiment_analyzer.get_aggregated_sentiment(
                news_df, symbol, days=7
            )
        
        # Özellikleri hazırla
        features = self.prepare_features(technical_result, sentiment_result)
        
        # Tahmin yap
        if self.model is not None:
            result = self.ml_based_prediction(features)
        else:
            result = self.rule_based_prediction(features)
        
        # Ek bilgiler ekle
        result['symbol'] = symbol
        result['timestamp'] = datetime.now().isoformat()
        result['technical_details'] = technical_result
        result['sentiment_details'] = sentiment_result
        
        # Sonucu yazdır
        print(f"\n{'='*50}")
        print(f"📊 {symbol} Analiz Sonucu")
        print(f"{'='*50}")
        print(f"🎯 Karar: {result['prediction']}")
        print(f"💯 Güven: {result['confidence']*100:.1f}%")
        print(f"📈 Teknik Skor: {result['technical_score']*100:.1f}%")
        print(f"💭 Duygu Skoru: {result['sentiment_score']:.2f}")
        print(f"📰 Haber Sayısı: {result['news_count']}")
        print(f"🔧 Metod: {result['method']}")
        
        if technical_result and 'latest_price' in technical_result:
            print(f"💵 Güncel Fiyat: ${technical_result['latest_price']:.2f}")
        
        print(f"{'='*50}\n")
        
        return result
    
    def train_model(self, training_data_csv='training_data.csv'):
        """
        ML modelini eğitir
        
        Args:
            training_data_csv: Eğitim verileri CSV dosyası
        """
        training_path = os.path.join(CSV_DIR, training_data_csv)
        
        if not os.path.exists(training_path):
            print(f"❌ Eğitim verisi bulunamadı: {training_path}")
            print("ℹ️ Önce veri toplayıp etiketlemeniz gerekiyor")
            return
        
        print(f"📚 Model eğitimi başlıyor...")
        print(f"📂 Eğitim verisi: {training_data_csv}")
        
        # Veriyi yükle
        df = pd.read_csv(training_path)
        
        if len(df) < MIN_TRAINING_SAMPLES:
            print(f"⚠️ Yetersiz veri: {len(df)} < {MIN_TRAINING_SAMPLES}")
            return
        
        # Özellikler ve etiketler
        feature_columns = [
            'technical_score', 'sentiment_score', 'news_count',
            'rsi_score', 'macd_score', 'bb_score', 'sma_score', 'stoch_score',
            'positive_ratio', 'negative_ratio'
        ]
        
        X = df[feature_columns].values
        y = df['label'].values  # 0=SAT, 1=TUT, 2=AL
        
        # Normalize et
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X)
        
        # Model eğit
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )
        
        self.model.fit(X_scaled, y)
        
        # Doğruluk skoru
        train_score = self.model.score(X_scaled, y)
        print(f"✅ Model eğitildi")
        print(f"📊 Eğitim doğruluğu: {train_score*100:.2f}%")
        
        # Modeli kaydet
        self.save_model()

if __name__ == '__main__':
    # Test
    predictor = StockPredictor()
    
    # Örnek veri ile test
    stock_csv = os.path.join(CSV_DIR, 'stock_data.csv')
    news_csv = os.path.join(CSV_DIR, 'news_data.csv')
    
    if os.path.exists(stock_csv) and os.path.exists(news_csv):
        stock_df = pd.read_csv(stock_csv)
        news_df = pd.read_csv(news_csv)
        
        # İlk hisse için tahmin
        if not stock_df.empty:
            test_symbol = stock_df['symbol'].iloc[0]
            result = predictor.predict_stock(test_symbol, stock_df, news_df)
    else:
        print("⚠️ Test için veri dosyaları bulunamadı")
        print("Önce data_collector.py ile veri toplayın")
