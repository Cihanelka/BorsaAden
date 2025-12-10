"""
Flask API servisi - ML modeli için REST endpoint'leri
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import os
from datetime import datetime
from config import *
from data_collector import DataCollector
from sentiment_analyzer import SentimentAnalyzer
from technical_analyzer import TechnicalAnalyzer
from stock_predictor import StockPredictor

app = Flask(__name__)
CORS(app)  # CORS'u etkinleştir

# Global instance'lar
collector = DataCollector()
predictor = StockPredictor()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Servis sağlık kontrolü"""
    return jsonify({
        'status': 'ok',
        'service': 'ML Stock Analysis Service',
        'timestamp': datetime.now().isoformat(),
        'model_loaded': predictor.model is not None
    })

@app.route('/api/collect-data', methods=['POST'])
def collect_data():
    """
    Belirli hisseler için veri toplar ve CSV'ye kaydeder
    
    Body:
    {
        "symbols": ["AAPL", "MSFT"],
        "stock_days": 90,
        "news_days": 30
    }
    """
    try:
        data = request.json
        symbols = data.get('symbols', DEFAULT_STOCKS)
        stock_days = data.get('stock_days', 90)
        news_days = data.get('news_days', 30)
        
        # Veri topla
        stock_df, news_df = collector.collect_all_data(symbols, stock_days, news_days)
        
        return jsonify({
            'success': True,
            'message': 'Veri toplama tamamlandı',
            'stock_rows': len(stock_df),
            'news_count': len(news_df),
            'symbols': symbols
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/analyze-sentiment', methods=['POST'])
def analyze_sentiment():
    """
    Haberlerin duygu analizini yapar
    
    Body:
    {
        "news_csv": "news_data.csv",
        "output_csv": "news_with_sentiment.csv"
    }
    """
    try:
        data = request.json
        news_csv = data.get('news_csv', 'news_data.csv')
        output_csv = data.get('output_csv', 'news_with_sentiment.csv')
        
        analyzed_df = predictor.sentiment_analyzer.analyze_and_save(news_csv, output_csv)
        
        if analyzed_df is None:
            return jsonify({
                'success': False,
                'error': 'Haber dosyası bulunamadı'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Duygu analizi tamamlandı',
            'analyzed_count': len(analyzed_df),
            'output_file': output_csv
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/predict', methods=['POST'])
def predict():
    """
    Belirli bir hisse için AL/SAT/TUT tahmini yapar
    
    Body:
    {
        "symbol": "AAPL",
        "use_cached_data": true  // CSV'deki verileri kullan
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
        
        use_cached = data.get('use_cached_data', True)
        
        if use_cached:
            # CSV'den verileri oku
            stock_csv = os.path.join(CSV_DIR, 'stock_data.csv')
            news_csv = os.path.join(CSV_DIR, 'news_with_sentiment.csv')
            
            stock_df = None
            news_df = None
            
            if os.path.exists(stock_csv):
                stock_df = pd.read_csv(stock_csv)
            
            if os.path.exists(news_csv):
                news_df = pd.read_csv(news_csv)
            elif os.path.exists(os.path.join(CSV_DIR, 'news_data.csv')):
                # Sentiment analizi yapılmamışsa şimdi yap
                news_df = pd.read_csv(os.path.join(CSV_DIR, 'news_data.csv'))
                news_df = predictor.sentiment_analyzer.analyze_news_batch(news_df)
            
            result = predictor.predict_stock(symbol, stock_df, news_df)
        else:
            # Canlı veri çek ve tahmin yap
            stock_df = collector.collect_stock_data(symbol, days=90)
            news_df = collector.collect_company_news(symbol, days=30)
            
            if not news_df.empty:
                news_df = predictor.sentiment_analyzer.analyze_news_batch(news_df)
            
            result = predictor.predict_stock(symbol, stock_df, news_df)
        
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
    Birden fazla hisse için tahmin yapar
    
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
        
        # CSV'den verileri oku
        stock_csv = os.path.join(CSV_DIR, 'stock_data.csv')
        news_csv = os.path.join(CSV_DIR, 'news_with_sentiment.csv')
        
        stock_df = None
        news_df = None
        
        if os.path.exists(stock_csv):
            stock_df = pd.read_csv(stock_csv)
        
        if os.path.exists(news_csv):
            news_df = pd.read_csv(news_csv)
        
        # Her hisse için tahmin yap
        results = []
        for symbol in symbols:
            try:
                result = predictor.predict_stock(symbol, stock_df, news_df)
                results.append(result)
            except Exception as e:
                print(f"❌ {symbol} tahmin hatası: {str(e)}")
                results.append({
                    'symbol': symbol,
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'results': results,
            'count': len(results)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/train-model', methods=['POST'])
def train_model():
    """
    ML modelini eğitir
    
    Body:
    {
        "training_data_csv": "training_data.csv"
    }
    """
    try:
        data = request.json
        training_csv = data.get('training_data_csv', 'training_data.csv')
        
        predictor.train_model(training_csv)
        
        return jsonify({
            'success': True,
            'message': 'Model eğitimi tamamlandı',
            'model_loaded': predictor.model is not None
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/technical-analysis', methods=['POST'])
def technical_analysis():
    """
    Sadece teknik analiz yapar
    
    Body:
    {
        "symbol": "AAPL"
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
        
        # CSV'den veri oku
        stock_csv = os.path.join(CSV_DIR, 'stock_data.csv')
        
        if not os.path.exists(stock_csv):
            return jsonify({
                'success': False,
                'error': 'Hisse verisi bulunamadı'
            }), 404
        
        stock_df = pd.read_csv(stock_csv)
        symbol_stock = stock_df[stock_df['symbol'] == symbol].copy()
        
        if symbol_stock.empty:
            return jsonify({
                'success': False,
                'error': f'{symbol} için veri bulunamadı'
            }), 404
        
        symbol_stock = symbol_stock.sort_values('date')
        analyzed_stock = predictor.technical_analyzer.calculate_all_indicators(symbol_stock)
        signals = predictor.technical_analyzer.get_technical_signals(analyzed_stock)
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'technical_analysis': signals
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/sentiment-summary', methods=['POST'])
def sentiment_summary():
    """
    Bir hisse için duygu analizi özeti
    
    Body:
    {
        "symbol": "AAPL",
        "days": 7
    }
    """
    try:
        data = request.json
        symbol = data.get('symbol')
        days = data.get('days', 7)
        
        if not symbol:
            return jsonify({
                'success': False,
                'error': 'symbol parametresi gerekli'
            }), 400
        
        # CSV'den haber verilerini oku
        news_csv = os.path.join(CSV_DIR, 'news_with_sentiment.csv')
        
        if not os.path.exists(news_csv):
            return jsonify({
                'success': False,
                'error': 'Duygu analizi verisi bulunamadı'
            }), 404
        
        news_df = pd.read_csv(news_csv)
        sentiment_result = predictor.sentiment_analyzer.get_aggregated_sentiment(
            news_df, symbol, days
        )
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'sentiment_summary': sentiment_result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 ML Stock Analysis Service Başlatılıyor")
    print("="*60)
    print(f"📡 Host: {FLASK_HOST}")
    print(f"🔌 Port: {FLASK_PORT}")
    print(f"🔧 Debug: {DEBUG_MODE}")
    print(f"📁 Data Dir: {DATA_DIR}")
    print(f"🤖 Model Loaded: {predictor.model is not None}")
    print("="*60 + "\n")
    
    app.run(
        host=FLASK_HOST,
        port=FLASK_PORT,
        debug=DEBUG_MODE
    )
