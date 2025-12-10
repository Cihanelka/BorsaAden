"""
Random Forest Modeli ile Tahmin Yapma
"""
import joblib
import pandas as pd
import numpy as np
import os
from ml_data_collector import MLDataCollector

class MLPredictor:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_columns = None
        self.collector = MLDataCollector()
        self.model_dir = 'data/models'
        
        # Modeli yükle
        self.load_model()
    
    def load_model(self):
        """Eğitilmiş modeli yükle"""
        model_path = os.path.join(self.model_dir, 'random_forest_model.joblib')
        scaler_path = os.path.join(self.model_dir, 'scaler.joblib')
        features_path = os.path.join(self.model_dir, 'feature_columns.joblib')
        
        if not os.path.exists(model_path):
            print("⚠️ Model bulunamadı! Önce train_random_forest.py çalıştırın.")
            return False
        
        try:
            self.model = joblib.load(model_path)
            self.scaler = joblib.load(scaler_path)
            self.feature_columns = joblib.load(features_path)
            print("✅ Random Forest modeli yüklendi")
            return True
        except Exception as e:
            print(f"❌ Model yükleme hatası: {e}")
            return False
    
    def predict(self, symbol):
        """Bir hisse için tahmin yap"""
        if self.model is None:
            return {
                'success': False,
                'error': 'Model Yüklenemedi.'
            }
        
        try:
            print(f"\n🔮 {symbol} için tahmin yapılıyor...")
            
            # Özellikleri topla
            features = self.collector.create_features(symbol, days=90)
            
            if features is None:
                return {
                    'success': False,
                    'error': f'{symbol} için veri alınamadı'
                }
            
            # DataFrame'e çevir
            features_df = pd.DataFrame([features])
            
            # Sadece model özelliklerini al
            X = features_df[self.feature_columns]
            
            # Eksik değerleri doldur
            X = X.fillna(0)
            
            # Ölçeklendir
            X_scaled = self.scaler.transform(X)
            
            # Tahmin yap
            prediction = self.model.predict(X_scaled)[0]
            probabilities = self.model.predict_proba(X_scaled)[0]
            
            # Sınıf isimleri
            classes = self.model.classes_
            
            # Olasılıkları sözlüğe çevir
            proba_dict = {cls: float(prob) for cls, prob in zip(classes, probabilities)}
            
            # En yüksek olasılık
            confidence = float(max(probabilities))
            
            # Sonucu hazırla
            result = {
                'success': True,
                'symbol': symbol,
                'prediction': prediction,
                'confidence': confidence,
                'probabilities': proba_dict,
                'current_price': float(features['close']),
                'technical_indicators': {
                    'rsi': float(features.get('rsi', 0)),
                    'macd': float(features.get('macd', 0)),
                    'trend_strength': float(features.get('trend_strength', 0)),
                    'volume_ratio': float(features.get('volume_ratio', 0))
                },
                'sentiment_analysis': {
                    'score': float(features.get('sentiment_score', 0)),
                    'positive_ratio': float(features.get('positive_ratio', 0)),
                    'negative_ratio': float(features.get('negative_ratio', 0)),
                    'news_count': int(features.get('news_count', 0))
                },
                'recommendation': self._get_recommendation(prediction, confidence),
                'model_type': 'Random Forest',
                'features_used': len(self.feature_columns)
            }
            
            print(f"✅ Tahmin: {prediction} (Güven: {confidence:.2%})")
            
            return result
            
        except Exception as e:
            print(f"❌ Tahmin hatası: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_recommendation(self, prediction, confidence):
        """Tavsiye metni oluştur - basitleştirilmiş versiyon"""
        if confidence < 0.6:
            return f"{prediction} sinyali zayıf - Dikkatli olun"
        elif confidence < 0.75:
            return f"{prediction} sinyali orta güçte - Dikkatli takip edin"
        else:
            return f"{prediction} sinyali güçlü - %{int(confidence * 100)} güven"
        return prediction
    
    def predict_batch(self, symbols):
        """Birden fazla hisse için tahmin yap"""
        results = []
        
        for symbol in symbols:
            result = self.predict(symbol)
            results.append(result)
        
        return results

if __name__ == "__main__":
    # Test
    predictor = MLPredictor()
    
    if predictor.model is not None:
        # Test tahmini
        result = predictor.predict('AAPL')
        
        if result['success']:
            print("\n" + "="*60)
            print("📊 TAHMİN SONUCU")
            print("="*60)
            print(f"\nSembol: {result['symbol']}")
            print(f"Tahmin: {result['prediction']}")
            print(f"Güven: {result['confidence']:.2%}")
            print(f"Tavsiye: {result['recommendation']}")
            print(f"\nOlasılıklar:")
            for cls, prob in result['probabilities'].items():
                print(f"  {cls}: {prob:.2%}")
        else:
            print(f"\n❌ Hata: {result['error']}")
