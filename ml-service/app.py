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
from enhanced_predictor import EnhancedStockPredictor
from ensemble_predictor import EnsembleStockPredictor

app = Flask(__name__)
CORS(app)  # CORS'u etkinleştir

# Global instance'lar
collector = DataCollector()
predictor = StockPredictor()
enhanced_predictor = EnhancedStockPredictor()
ensemble_predictor = EnsembleStockPredictor()

# Try to load enhanced model
try:
    enhanced_predictor.load_models()
except:
    print("⚠️ Enhanced model not loaded - train it first with train_enhanced_model.py")

# Try to load ensemble model
try:
    ensemble_predictor.load_models()
except:
    print("⚠️ Ensemble model not loaded - train it first with train_ensemble.py")

def save_sentiment_csv(df):
    """
    Haber sentiment sonuçlarını merkezi CSV'de saklar
    """
    if df is None or df.empty:
        return
    
    sentiment_csv = os.path.join(CSV_DIR, 'news_with_sentiment.csv')
    
    try:
        if os.path.exists(sentiment_csv):
            existing_df = pd.read_csv(sentiment_csv)
            combined_df = pd.concat([existing_df, df], ignore_index=True)
            # Yinelenenleri sembol + tarih + başlık bazında kaldır
            duplicate_cols = [col for col in ['symbol', 'datetime', 'headline'] if col in combined_df.columns]
            if duplicate_cols:
                combined_df = combined_df.drop_duplicates(subset=duplicate_cols, keep='last')
            combined_df.to_csv(sentiment_csv, index=False)
            print(f"💾 Haber sentiment CSV güncellendi: {len(df)} yeni satır")
        else:
            df.to_csv(sentiment_csv, index=False)
            print(f"💾 Haber sentiment CSV oluşturuldu: {sentiment_csv} ({len(df)} satır)")
    except Exception as e:
        print(f"⚠️ Haber sentiment CSV kaydedilemedi: {e}")

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
        
        # Model kontrolü
        if predictor.model is None or predictor.scaler is None:
            return jsonify({
                'success': False,
                'error': 'ML modeli yüklü değil. Lütfen önce modeli eğitin: python ml-service/train_random_forest.py'
            }), 503
        
        use_cached = data.get('use_cached_data', True)
        
        print(f"🔍 use_cached_data parametresi: {use_cached} (tip: {type(use_cached)})")
        
        stock_df = None
        news_df = None
        
        if use_cached:
            # CSV'den verileri oku
            stock_csv = os.path.join(CSV_DIR, 'stock_data.csv')
            news_csv = os.path.join(CSV_DIR, 'news_with_sentiment.csv')
            
            # Hisse verilerini yükle
            if os.path.exists(stock_csv):
                stock_df = pd.read_csv(stock_csv)
                # Sembole göre filtrele
                stock_df = stock_df[stock_df['symbol'] == symbol]
                if stock_df.empty:
                    print(f"⚠️ CSV'de {symbol} hisse verisi yok, canlı çekiliyor...")
                    stock_df = collector.collect_stock_data(symbol, days=90)
            else:
                print(f"⚠️ CSV bulunamadı, canlı veri çekiliyor...")
                stock_df = collector.collect_stock_data(symbol, days=90)
            
            # Haber verilerini yükle - MUTLAKA HABER BULUNMALI!
            news_df = None
            
            # 1. Önce sentiment analizli CSV'yi kontrol et
            if os.path.exists(news_csv):
                temp_df = pd.read_csv(news_csv)
                temp_df = temp_df[temp_df['symbol'] == symbol]
                if not temp_df.empty:
                    news_df = temp_df
                    print(f"✅ CSV'den {len(news_df)} haber yüklendi (sentiment var)")
            
            # 2. Sentiment analizli haber yoksa, ham haber CSV'sini kontrol et
            if news_df is None or news_df.empty:
                if os.path.exists(os.path.join(CSV_DIR, 'news_data.csv')):
                    temp_df = pd.read_csv(os.path.join(CSV_DIR, 'news_data.csv'))
                    temp_df = temp_df[temp_df['symbol'] == symbol]
                    if not temp_df.empty:
                        print(f"⚙️ CSV'den {len(temp_df)} haber bulundu, sentiment analizi yapılıyor...")
                        news_df = predictor.sentiment_analyzer.analyze_news_batch(temp_df)
                        save_sentiment_csv(news_df)
            
            # 3. Hala haber yoksa MUTLAKA canlı çek!
            if news_df is None or news_df.empty:
                print(f"\n{'='*60}")
                print(f"⚠️ CSV'de {symbol} haberi yok - CANLI ÇEKİLECEK!")
                print(f"{'='*60}")
                company_name = COMPANY_NAMES.get(symbol)
                news_df = collector.collect_company_news(symbol, days=30, company_name=company_name)
                
                # Haber bulunduysa sentiment analizi YAP!
                if not news_df.empty:
                    print(f"\n⚙️ SENTIMENT ANALİZİ YAPILIYOR: {len(news_df)} haber")
                    news_df = predictor.sentiment_analyzer.analyze_news_batch(news_df)
                    save_sentiment_csv(news_df)
                    print(f"✅ Sentiment analizi tamamlandı!\n")
                else:
                    print(f"\n⚠️ UYARI: {symbol} için haber bulunamadı, sadece teknik analiz kullanılacak\n")
            
            result = predictor.predict_stock(symbol, stock_df, news_df)
        else:
            # Canlı veri çek ve tahmin yap
            print(f"\n{'='*60}")
            print(f"🔴 CANLI VERİ MODU - {symbol}")
            print(f"{'='*60}\n")
            
            stock_df = collector.collect_stock_data(symbol, days=90)
            company_name = COMPANY_NAMES.get(symbol)
            news_df = collector.collect_company_news(symbol, days=30, company_name=company_name)
            
            # MUTLAKA sentiment analizi yap!
            if not news_df.empty:
                print(f"\n⚙️ SENTIMENT ANALİZİ YAPILIYOR: {len(news_df)} haber")
                news_df = predictor.sentiment_analyzer.analyze_news_batch(news_df)
                save_sentiment_csv(news_df)
                print(f"✅ Sentiment analizi tamamlandı!\n")
            else:
                print(f"\n⚠️ UYARI: {symbol} için haber bulunamadı, sadece teknik analiz kullanılacak\n")
            
            result = predictor.predict_stock(symbol, stock_df, news_df)
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        print(f"❌ Predict hatası ({symbol}): {str(e)}")
        import traceback
        traceback.print_exc()
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
        
        print(f"\n📊 SENTIMENT SUMMARY İSTEĞİ: {symbol} ({days} gün)")
        
        if not symbol:
            return jsonify({
                'success': False,
                'error': 'symbol parametresi gerekli'
            }), 400
        
        # CSV'den haber verilerini oku
        news_csv = os.path.join(CSV_DIR, 'news_with_sentiment.csv')
        
        if not os.path.exists(news_csv):
            print(f"⚠️ CSV bulunamadı: {news_csv}")
            print("ℹ️ Önce /api/predict endpoint'ini çağırın, otomatik haber çekecek")
            # Boş sonuç döndür, hata verme
            return jsonify({
                'success': True,
                'symbol': symbol,
                'result': {
                    'news_count': 0,
                    'positive_count': 0,
                    'negative_count': 0,
                    'neutral_count': 0,
                    'avg_sentiment': 0.0,
                    'normalized_sentiment': 0.0,
                    'recent_headlines': []
                }
            })
        
        try:
            news_df = pd.read_csv(news_csv)
            print(f"✅ CSV okundu: {len(news_df)} satır")
            
            # Symbol'e göre filtrele ve say
            symbol_news = news_df[news_df['symbol'] == symbol] if 'symbol' in news_df.columns else pd.DataFrame()
            print(f"📰 {symbol} için: {len(symbol_news)} haber")
            
            sentiment_result = predictor.sentiment_analyzer.get_aggregated_sentiment(
                news_df, symbol, days
            )
            print(f"✅ Sentiment hesaplandı: {sentiment_result.get('news_count', 0)} haber")
            
        except Exception as e:
            print(f"⚠️ İşlem hatası: {e}")
            import traceback
            traceback.print_exc()
            sentiment_result = {
                'symbol': symbol,
                'avg_sentiment': 0.0,
                'normalized_sentiment': 0.0,
                'news_count': 0,
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0,
                'recent_headlines': []
            }
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'result': sentiment_result
        })
        
    except Exception as e:
        print(f"❌ Sentiment summary hatası: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stock-data', methods=['POST'])
def stock_data():
    """
    Hisse senedi fiyat verilerini çeker (yfinance ile)
    
    Body:
    {
        "symbol": "AAPL",
        "days": 30
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
        
        # Hisse verilerini çek
        stock_df = collector.collect_stock_data(symbol, days=days)
        
        if stock_df.empty:
            return jsonify({
                'success': False,
                'error': f'{symbol} için veri bulunamadı'
            }), 404
        
        # DataFrame'i JSON'a çevir - date formatını düzelt
        stock_df_copy = stock_df.reset_index()
        
        # Date sütununu ISO format string'e çevir
        if 'Date' in stock_df_copy.columns:
            stock_df_copy['Date'] = stock_df_copy['Date'].dt.strftime('%Y-%m-%d')
        elif stock_df_copy.index.name == 'Date':
            stock_df_copy.index = stock_df_copy.index.strftime('%Y-%m-%d')
        
        stock_data = stock_df_copy.to_dict('records')
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'data': stock_data
        })
        
    except Exception as e:
        print(f"❌ Stock data hatası: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/predict-enhanced', methods=['POST'])
def predict_enhanced():
    """
    Enhanced prediction endpoint using production-ready ML pipeline
    
    Body:
    {
        "symbol": "AAPL"
    }
    
    Returns:
    {
        "success": true,
        "prediction": "UP" | "DOWN" | "NEUTRAL",
        "confidence": 0.85,
        "probabilities": {
            "UP": 0.75,
            "DOWN": 0.10,
            "NEUTRAL": 0.15
        },
        "disclaimer": "This is a statistical prediction, NOT investment advice"
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
        
        # Model kontrolü
        if not enhanced_predictor.trained:
            return jsonify({
                'success': False,
                'error': 'Enhanced model henüz eğitilmedi. Lütfen train_enhanced_model.py çalıştırın'
            }), 503
        
        # Veri çek (minimum 60 gün gerekli - rolling calculations için)
        print(f"📊 Fetching data for {symbol}...")
        stock_df = collector.collect_stock_data(symbol, days=90)
        
        if stock_df.empty:
            return jsonify({
                'success': False,
                'error': f'{symbol} için veri bulunamadı'
            }), 404
        
        # Tahmin yap
        result = enhanced_predictor.predict(stock_df)
        
        return jsonify({
            'success': True,
            **result
        })
        
    except Exception as e:
        print(f"❌ Enhanced predict hatası: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/predict-ensemble', methods=['POST'])
def predict_ensemble():
    """
    Ensemble prediction: 10 model, en yüksek confidence score ile tahmin
    
    Body:
    {
        "symbol": "AAPL"
    }
    """
    try:
        data = request.json
        symbol = data.get('symbol')

        if not symbol:
            return jsonify({'success': False, 'error': 'symbol parametresi gerekli'}), 400

        if not ensemble_predictor.trained:
            loaded = ensemble_predictor.load_models()
            if not loaded:
                return jsonify({
                    'success': False,
                    'error': 'Ensemble model henüz eğitilmedi. Lütfen train_ensemble.py çalıştırın'
                }), 503

        # Hisse verisi çek
        stock_df = collector.collect_stock_data(symbol, days=120)
        if stock_df.empty:
            return jsonify({'success': False, 'error': f'{symbol} için veri bulunamadı'}), 404

        # Haber verisi
        news_df = None
        news_csv = os.path.join(CSV_DIR, 'news_with_sentiment.csv')
        if os.path.exists(news_csv):
            temp_df = pd.read_csv(news_csv)
            if 'symbol' in temp_df.columns:
                temp_df = temp_df[temp_df['symbol'] == symbol]
            if not temp_df.empty:
                news_df = temp_df

        if news_df is None or news_df.empty:
            company_name = COMPANY_NAMES.get(symbol)
            raw_news = collector.collect_company_news(symbol, days=3, company_name=company_name)
            if not raw_news.empty:
                analyzer = SentimentAnalyzer()
                news_df = analyzer.analyze_news_batch(raw_news)
                save_sentiment_csv(news_df)

        result = ensemble_predictor.predict(stock_df, news_df=news_df, symbol=symbol)

        return jsonify({'success': True, **result})

    except Exception as e:
        print(f"❌ Ensemble predict hatası: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 ML Stock Analysis Service Başlatılıyor")
    print("="*60)
    print(f"📡 Host: {FLASK_HOST}")
    print(f"🔌 Port: {FLASK_PORT}")
    print(f"🔧 Debug: {DEBUG_MODE}")
    print(f"📁 Data Dir: {DATA_DIR}")
    print(f"🤖 Model Loaded: {predictor.model is not None}")
    print(f"🚀 Enhanced Model Loaded: {enhanced_predictor.trained}")
    print(f"🎯 Ensemble Model Loaded: {ensemble_predictor.trained} ({len(ensemble_predictor.models)} models)")
    print("="*60 + "\n")
    
    app.run(
        host=FLASK_HOST,
        port=FLASK_PORT,
        debug=DEBUG_MODE
    )
