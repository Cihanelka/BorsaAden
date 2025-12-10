"""
Basitleştirilmiş ML Servisi - Hızlı Test İçin
Sadece Flask ve Flask-CORS gerektirir
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import random

app = Flask(__name__)
CORS(app)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Servis sağlık kontrolü"""
    return jsonify({
        'status': 'ok',
        'service': 'ML Stock Analysis Service (Simple Mode)',
        'timestamp': datetime.now().isoformat(),
        'model_loaded': False,
        'mode': 'demo'
    })

@app.route('/api/predict', methods=['POST'])
def predict():
    """
    Demo tahmin - Gerçek ML modeli olmadan çalışır
    """
    try:
        data = request.json
        symbol = data.get('symbol')
        
        if not symbol:
            return jsonify({
                'success': False,
                'error': 'symbol parametresi gerekli'
            }), 400
        
        # Demo tahmin oluştur
        predictions = ['AL', 'SAT', 'TUT']
        prediction = random.choice(predictions)
        confidence = round(random.uniform(0.6, 0.95), 2)
        
        result = {
            'symbol': symbol,
            'prediction': prediction,
            'confidence': confidence,
            'current_price': round(random.uniform(100, 500), 2),
            'technical_analysis': {
                'rsi': round(random.uniform(30, 70), 2),
                'macd': 'BULLISH' if random.random() > 0.5 else 'BEARISH',
                'trend': 'YUKARI' if random.random() > 0.5 else 'ASAGI'
            },
            'sentiment': {
                'score': round(random.uniform(-1, 1), 2),
                'label': random.choice(['Pozitif', 'Negatif', 'Nötr'])
            },
            'recommendation': f'{prediction} tavsiyesi - %{int(confidence * 100)} güven',
            'timestamp': datetime.now().isoformat(),
            'mode': 'DEMO - Gerçek ML modeli değil'
        }
        
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
    Birden fazla hisse için demo tahmin
    """
    try:
        data = request.json
        symbols = data.get('symbols', [])
        
        if not symbols:
            return jsonify({
                'success': False,
                'error': 'symbols parametresi gerekli'
            }), 400
        
        results = []
        for symbol in symbols:
            predictions = ['AL', 'SAT', 'TUT']
            prediction = random.choice(predictions)
            confidence = round(random.uniform(0.6, 0.95), 2)
            
            results.append({
                'symbol': symbol,
                'prediction': prediction,
                'confidence': confidence,
                'current_price': round(random.uniform(100, 500), 2)
            })
        
        return jsonify({
            'success': True,
            'results': results,
            'count': len(results),
            'mode': 'DEMO'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 ML Stock Analysis Service (DEMO MODE)")
    print("="*60)
    print("📡 Host: 0.0.0.0")
    print("🔌 Port: 5000")
    print("⚠️  DEMO MODE - Gerçek ML tahmini yapmaz!")
    print("="*60 + "\n")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
