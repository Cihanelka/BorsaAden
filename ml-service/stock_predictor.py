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
        self.feature_columns = None
        self.load_model()
        
        print("✅ Stock Predictor hazır")
    
    def load_model(self):
        """Eğitilmiş modeli yükler"""
        model_path = os.path.join(MODEL_DIR, 'random_forest_model.joblib')
        scaler_path = os.path.join(MODEL_DIR, 'scaler.joblib')
        feature_cols_path = os.path.join(MODEL_DIR, 'feature_columns.joblib')
        
        if os.path.exists(model_path) and os.path.exists(scaler_path):
            try:
                self.model = joblib.load(model_path)
                self.scaler = joblib.load(scaler_path)
                
                # Feature columns'u da yükle
                if os.path.exists(feature_cols_path):
                    self.feature_columns = joblib.load(feature_cols_path)
                    print(f"✅ Model yüklendi: {model_path} ({len(self.feature_columns)} features)")
                else:
                    print(f"✅ Model yüklendi: {model_path}")
            except Exception as e:
                print(f"⚠️ Model yükleme hatası: {str(e)}")
                self.model = None
                self.scaler = None
        else:
            print("⚠️ Eğitilmiş Random Forest modeli bulunamadı. Tahmin yapabilmek için önce modeli eğitmeniz gerekiyor.")
    
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
    
    def ml_based_prediction(self, features):
        """
        ML model ile tahmin (Random Forest)
        
        Args:
            features: Özellik vektörü
            
        Returns:
            dict: Tahmin sonucu
        """
        if self.model is None or self.scaler is None:
            raise Exception("ML modeli yüklü değil. Lütfen önce modeli eğitin veya yükleyin.")
        
        try:
            # Özellikleri sırala ve array'e çevir (model 26 feature bekliyor)
            feature_names = [
                'rsi', 'macd', 'macd_signal', 'macd_diff', 'bb_width',
                'stoch_k', 'stoch_d', 'atr', 'volume_ratio',
                'price_change_1d', 'price_change_5d', 'price_change_10d',
                'trend_strength', 'obv_change', 'mfi', 'adx', 'cci',
                'williams_r', 'roc', 'sma_cross', 'ema_cross',
                'sentiment_score', 'sentiment_std', 'positive_ratio',
                'negative_ratio', 'news_count'
            ]
            
            # Mevcut feature'lardan mapping yap
            feature_mapping = {
                # Teknik göstergeleri 0-100 ölçeğine çek, etkisini artır
                'rsi': features.get('rsi_score', 0.5) * 100,
                'macd': features.get('macd_score', 0.5) * 100,
                'macd_signal': features.get('macd_score', 0.5) * 100,
                'macd_diff': 0.0,
                'bb_width': features.get('bb_score', 0.5) * 100,
                'stoch_k': features.get('stoch_score', 0.5) * 100,
                'stoch_d': features.get('stoch_score', 0.5) * 100,
                'atr': 50.0,
                'volume_ratio': 1.0,
                'price_change_1d': 0.0,
                'price_change_5d': 0.0,
                'price_change_10d': 0.0,
                'trend_strength': features.get('technical_score', 0.5) * 100,
                'obv_change': 0.0,
                'mfi': 50.0,
                'adx': 25.0,
                'cci': 0.0,
                'williams_r': -50.0,
                'roc': 0.0,
                'sma_cross': features.get('sma_score', 0.5) * 100,
                'ema_cross': features.get('sma_score', 0.5) * 100,
                # Sentiment etkisini normalize et (0..1), teknik ağırlık önde
                'sentiment_score': max(0.0, min(1.0, features.get('sentiment_score', 0.0))),
                'sentiment_std': 0.1,
                'positive_ratio': features.get('positive_ratio', 0.0),
                'negative_ratio': features.get('negative_ratio', 0.0),
                'news_count': float(features.get('news_count', 0))
            }
            
            feature_vector = np.array([[feature_mapping.get(f, 0.5) for f in feature_names]])
            
            # Normalize et
            feature_vector_scaled = self.scaler.transform(feature_vector)
            
            # Tahmin yap
            prediction = self.model.predict(feature_vector_scaled)[0]
            probabilities = self.model.predict_proba(feature_vector_scaled)[0]
            
            # Sınıf etiketleri: 0=SAT, 1=TUT, 2=AL
            class_names = ['SAT', 'TUT', 'AL']
            
            # Model string döndürüyorsa label'dan index bul
            if isinstance(prediction, str):
                if prediction in class_names:
                    prediction_idx = class_names.index(prediction)
                else:
                    print(f"⚠️ Bilinmeyen tahmin: {prediction}, varsayılan TUT")
                    prediction_idx = 1
            elif isinstance(prediction, (int, np.integer)):
                prediction_idx = int(prediction)
            else:
                try:
                    prediction_idx = int(prediction)
                except (ValueError, TypeError):
                    print(f"⚠️ Tahmin dönüştürülemedi: {prediction}, varsayılan TUT")
                    prediction_idx = 1
            
            prediction_label = class_names[prediction_idx]
            base_confidence = probabilities[prediction_idx]

            # Güveni artırmak için teknik skoru daha fazla hesaba kat ve taban güveni ez aşırı düşmesin
            base_conf_clamped = max(base_confidence, 0.4)
            tech_score_raw = float(features.get('technical_score', 0.5))
            tech_score_boosted = 0.3 + 0.7 * tech_score_raw  # 0.3-1.0 aralığına çek
            confidence = 0.5 * base_conf_clamped + 0.5 * tech_score_boosted
            
            # Düşük güven uyarısı
            confidence_warning = ""
            if confidence < 0.55:
                confidence_warning = "⚠️ Düşük güven skoru - Haber verisi eksik olabilir"
                print(f"⚠️ Düşük güven: {confidence:.2%} - Haber sayısı: {features.get('news_count', 0)}")
            
            # Duygu skorunu normalize et (-1,+1 -> 0,1) frontend için
            sentiment_raw = features.get('sentiment_score', 0.0)
            sentiment_normalized = (sentiment_raw + 1) / 2  # -1,+1 -> 0,1
            
            return {
                'prediction': prediction_label,
                'confidence': float(confidence),
                'confidence_warning': confidence_warning,
                'probabilities': {
                    'AL': float(probabilities[2]),
                    'TUT': float(probabilities[1]),
                    'SAT': float(probabilities[0])
                },
                'technical_score': float(features.get('technical_score', 0.5)),
                'sentiment_score': float(sentiment_normalized),
                'news_count': int(features.get('news_count', 0)),
                'method': 'ml_model'
            }
            
        except Exception as e:
            print(f"❌ ML tahmin hatası: {str(e)}")
            raise
    
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
        
        # ML Model kontrolü - ZORUNLU
        if self.model is None or self.scaler is None:
            raise Exception("ML modeli yüklü değil! Lütfen önce modeli eğitin: python ml-service/train_random_forest.py")
        
        # Teknik analiz
        technical_result = None
        if stock_df is not None and not stock_df.empty:
            # Sembole göre filtrele
            symbol_stock = stock_df[stock_df['symbol'] == symbol].copy()
            if not symbol_stock.empty:
                # Tarih kolonu adını normalize et
                symbol_stock.columns = [c.lower() for c in symbol_stock.columns]
                if 'date' not in symbol_stock.columns:
                    if symbol_stock.index.name and symbol_stock.index.name.lower() == 'date':
                        symbol_stock = symbol_stock.reset_index().rename(columns={'index': 'date'})
                    else:
                        for candidate in ['datetime', 'time']:
                            if candidate in symbol_stock.columns:
                                symbol_stock = symbol_stock.rename(columns={candidate: 'date'})
                                break
                if 'date' in symbol_stock.columns:
                    symbol_stock = symbol_stock.sort_values('date')
                analyzed_stock = self.technical_analyzer.calculate_all_indicators(symbol_stock)
                technical_result = self.technical_analyzer.get_technical_signals(analyzed_stock)
        
        # Duygu analizi
        sentiment_result = None
        if news_df is not None and not news_df.empty:
            print(f"📰 Toplam haber sayısı: {len(news_df)}")
            print(f"🔍 news_df kolonları: {list(news_df.columns)}")
            
            # Sembole göre filtrele
            symbol_news = news_df[news_df['symbol'] == symbol] if 'symbol' in news_df.columns else news_df
            
            if not symbol_news.empty:
                # Eğer sentiment skorları yoksa hesapla
                if 'sentiment_score' not in symbol_news.columns:
                    print("⚙️ Sentiment analizi yapılıyor...")
                    symbol_news = self.sentiment_analyzer.analyze_news_batch(symbol_news)
                else:
                    print(f"✅ Sentiment skorları mevcut: {symbol_news['sentiment_score'].mean():.3f}")
                
                sentiment_result = self.sentiment_analyzer.get_aggregated_sentiment(
                    symbol_news, symbol, days=7
                )
                print(f"📊 {symbol} için {sentiment_result.get('news_count', 0)} haber analiz edildi")
                print(f"🎭 Sentiment sonuç: {sentiment_result}")
            else:
                print(f"⚠️ CSV'de {symbol} haberi yok")
        else:
            print(f"⚠️ {symbol} için haber verisi bulunamadı!")
        
        # Özellikleri hazırla
        features = self.prepare_features(technical_result, sentiment_result)
        print(f"🔧 Hazırlanan features: {features}")
        
        # Random Forest ile tahmin yap (SADECE ML MODEL)
        result = self.ml_based_prediction(features)
        
        # Ek bilgiler ekle
        result['symbol'] = symbol
        result['timestamp'] = datetime.now().isoformat()
        result['technical_details'] = technical_result
        result['sentiment_details'] = sentiment_result
        
        # Fiyat bilgilerini ekle (frontend için)
        if technical_result and 'latest_price' in technical_result:
            result['price_data'] = {
                'current': technical_result.get('latest_price', 0.0),
                'change': technical_result.get('price_change_1d', 0.0),
                'change_percent': technical_result.get('price_change_1d_percent', 0.0)
            }
        else:
            result['price_data'] = {
                'current': 0.0,
                'change': 0.0,
                'change_percent': 0.0
            }
        
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
