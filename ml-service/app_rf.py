"""
Flask API servisi - Random Forest ML Modeli
Teknik Göstergeler + Haber Duygu Analizi ile AL/SAT/TUT Tahmini
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os
import pandas as pd
from ml_predictor import MLPredictor

app = Flask(__name__)
CORS(app)

# ML Predictor instance
predictor = MLPredictor()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Servis sağlık kontrolü"""
    model_loaded = predictor.model is not None
    
    return jsonify({
        'status': 'ok',
        'service': 'ML Stock Analysis Service - Random Forest',
        'timestamp': datetime.now().isoformat(),
        'model_loaded': model_loaded,
        'model_type': 'Random Forest Classifier' if model_loaded else 'Not Loaded',
        'features': len(predictor.feature_columns) if predictor.feature_columns else 0
    })

@app.route('/api/sentiment-summary', methods=['POST'])
def sentiment_summary():
    """
    CSV'den sentiment özeti döner.
    Body: {"symbol": "AAPL", "days": 7}
    """
    try:
        data = request.json or {}
        symbol = data.get('symbol')
        days = data.get('days', 7)

        if not symbol:
            return jsonify({'success': False, 'error': 'symbol parametresi gerekli'}), 400

        csv_path = os.path.join('data', 'csv', 'news_with_sentiment.csv')
        if not os.path.exists(csv_path):
            return jsonify({'success': True, 'symbol': symbol, 'result': _empty_sentiment()} )

        df = pd.read_csv(csv_path)
        if df.empty or 'sentiment_score' not in df.columns:
            return jsonify({'success': True, 'symbol': symbol, 'result': _empty_sentiment()})

        if 'symbol' in df.columns:
            df = df[df['symbol'] == symbol]

        # Son N gün filtresi
        if 'published_date' in df.columns:
            df['published_date'] = pd.to_datetime(df['published_date'], errors='coerce')
            cutoff = datetime.now() - pd.Timedelta(days=days)
            df = df[df['published_date'] >= cutoff]

        if df.empty:
            return jsonify({'success': True, 'symbol': symbol, 'result': _empty_sentiment()})

        sentiments = df['sentiment_score'].dropna()
        news_count = len(sentiments)
        positive_count = int((sentiments > 0.05).sum())
        negative_count = int((sentiments < -0.05).sum())
        neutral_count = news_count - positive_count - negative_count
        avg_sentiment = float(sentiments.mean())
        normalized = (avg_sentiment + 1) / 2
        recent_headlines = df['title'].dropna().tail(5).tolist() if 'title' in df.columns else []

        return jsonify({
            'success': True,
            'symbol': symbol,
            'result': {
                'news_count': news_count,
                'positive_count': positive_count,
                'negative_count': negative_count,
                'neutral_count': neutral_count,
                'avg_sentiment': avg_sentiment,
                'normalized_sentiment': normalized,
                'recent_headlines': recent_headlines
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def _empty_sentiment():
    return {
        'news_count': 0,
        'positive_count': 0,
        'negative_count': 0,
        'neutral_count': 0,
        'avg_sentiment': 0.0,
        'normalized_sentiment': 0.0,
        'recent_headlines': []
    }

@app.route('/api/predict', methods=['POST'])
def predict():
    """
    Tek bir hisse için Random Forest tahmini
    
    Body:
    {
        "symbol": "AAPL"
    }
    
    Response:
    {
        "success": true,
        "result": {
            "symbol": "AAPL",
            "prediction": "AL",
            "confidence": 0.85,
            "probabilities": {
                "AL": 0.85,
                "SAT": 0.05,
                "TUT": 0.10
            },
            "current_price": 150.25,
            "technical_indicators": {...},
            "sentiment_analysis": {...},
            "recommendation": "AL sinyali güçlü - %85 güven"
        }
    }
    """
    try:
        data = request.json
        symbol = data.get('symbol')
        
        if not symbol:
            return jsonify({
                'success': False,
                'error': 'symbol parametresi gerekli'
            }), 400
        
        # Tahmin yap
        result = predictor.predict(symbol)
        
        if not result['success']:
            return jsonify(result), 500
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/predict-batch', methods=['POST'])
def predict_batch():
    """
    Birden fazla hisse için tahmin
    
    Body:
    {
        "symbols": ["AAPL", "MSFT", "GOOGL"]
    }
    """
    try:
        data = request.json
        symbols = data.get('symbols', [])
        
        if not symbols:
            return jsonify({
                'success': False,
                'error': 'symbols parametresi gerekli'
            }), 400
        
        # Batch tahmin
        results = predictor.predict_batch(symbols)
        
        # Başarılı tahminleri say
        successful = sum(1 for r in results if r.get('success', False))
        
        return jsonify({
            'success': True,
            'results': results,
            'total': len(results),
            'successful': successful,
            'failed': len(results) - successful
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stock-data', methods=['POST'])
def get_stock_data():
    """
    Hisse senedi tarihsel verilerini al (yfinance ile)
    
    Body:
    {
        "symbol": "AAPL",
        "days": 30  // Opsiyonel, varsayılan 30
    }
    
    Response:
    {
        "success": true,
        "symbol": "AAPL",
        "data": [
            {
                "datetime": "2024-01-01",
                "open": 150.0,
                "high": 152.0,
                "low": 149.0,
                "close": 151.0,
                "volume": 1000000
            },
            ...
        ]
    }
    """
    try:
        data = request.json
        symbol = data.get('symbol')
        days = data.get('days', 30)
        
        if not symbol:
            return jsonify({
                'success': False,
                'error': 'symbol parametresi gerekli'
            }), 400
        
        # yfinance ile veri çek
        from ml_data_collector import MLDataCollector
        collector = MLDataCollector()
        df = collector.get_stock_data(symbol, days=days)
        
        if df is None or df.empty:
            return jsonify({
                'success': False,
                'error': f'{symbol} için veri alınamadı'
            }), 404
        
        # DataFrame'i JSON'a çevir
        df['datetime'] = df['datetime'].astype(str)
        stock_data = df.to_dict('records')
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'data': stock_data,
            'count': len(stock_data)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/model-info', methods=['GET'])
def model_info():
    """Model hakkında bilgi"""
    if predictor.model is None:
        return jsonify({
            'success': False,
            'error': 'Model yüklenmedi. Önce train_random_forest.py çalıştırın.'
        }), 404
    
    try:
        info_path = os.path.join(predictor.model_dir, 'model_info.txt')
        
        info = {
            'model_type': 'Random Forest Classifier',
            'model_loaded': True,
            'n_estimators': predictor.model.n_estimators,
            'max_depth': predictor.model.max_depth,
            'n_features': len(predictor.feature_columns),
            'features': predictor.feature_columns,
            'classes': predictor.model.classes_.tolist()
        }
        
        # Model info dosyasını oku
        if os.path.exists(info_path):
            with open(info_path, 'r', encoding='utf-8') as f:
                info['training_info'] = f.read()
        
        return jsonify({
            'success': True,
            'info': info
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/retrain', methods=['POST'])
def retrain_model():
    """
    Modeli yeniden eğit (Opsiyonel - uzun sürebilir)
    
    Body:
    {
        "symbols": ["AAPL", "MSFT", ...],  // Opsiyonel
        "days": 90  // Opsiyonel
    }
    """
    return jsonify({
        'success': False,
        'error': 'Model eğitimi için train_random_forest.py scriptini kullanın',
        'command': 'python ml-service/train_random_forest.py'
    }), 501

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 ML STOCK ANALYSIS SERVICE - RANDOM FOREST")
    print("="*70)
    print(f"📡 Host: 0.0.0.0")
    print(f"🔌 Port: 5000")
    print(f"🤖 Model: Random Forest Classifier")
    
    if predictor.model is not None:
        print(f"✅ Model Durumu: Yüklendi")
        print(f"🎯 Özellik Sayısı: {len(predictor.feature_columns)}")
        print(f"📊 Sınıflar: {', '.join(predictor.model.classes_)}")
    else:
        print(f"⚠️  Model Durumu: YÜKLENMEDİ")
        print(f"💡 Model eğitmek için: python train_random_forest.py")
    
    print("="*70)
    print("\n📋 Endpoints:")
    print("  GET  /api/health          - Servis durumu")
    print("  POST /api/predict         - Tek hisse tahmini")
    print("  POST /api/predict-batch   - Çoklu hisse tahmini")
    print("  GET  /api/model-info      - Model bilgileri")
    print("="*70 + "\n")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
