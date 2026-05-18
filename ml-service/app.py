"""
Created by: AdenBorsa ML Team
Created At: 2026-04-26
Subject: ML Stock Analysis Service - Flask REST API.
         15 modelli aylik hisse tahmini servisi.
         Modeller once train_models.py ile egitilmeli, sonra bu servis baslatilmalidir.
"""

import os
import math
import traceback
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from config import FLASK_HOST, FLASK_PORT, DEBUG_MODE
from data_collector import loadOrFetchOhlcv
from model_trainer import ModelTrainer
from monthly_predictor import MonthlyPredictor

app = Flask(__name__)
CORS(app)

# Uygulama baslarken modelleri yukle
_predictor = MonthlyPredictor()

try:
    loaded = _predictor.loadModels()
    if loaded:
        print('Modeller basariyla yuklendi.')
    else:
        print('UYARI: Kayitli model bulunamadi.')
        print('  Once "python train_models.py" calistirin.')
except Exception as _err:
    print(f'Model yukleme hatasi: {_err}')


# ---------------------------------------------------------------------------
# Endpoint'ler
# ---------------------------------------------------------------------------

@app.route('/api/health', methods=['GET'])
def healthCheck():
    """Servis saglik kontrolu."""
    return jsonify({
        'status': 'ok',
        'service': 'ML Monthly Stock Predictor',
        'timestamp': datetime.now().isoformat(),
        'models_loaded': _predictor.isLoaded,
        'model_count': len(_predictor._trainer.models) if _predictor.isLoaded else 0,
        'trained_at': _predictor.trainedAt if _predictor.isLoaded else None,
    })


@app.route('/api/predict-monthly', methods=['POST'])
def predictMonthly():
    """
    Bir hisse icin gelecek ay tahmini yapar ve teknik aciklama uretir.

    Istek govdesi:
        { "symbol": "AAPL" }

    Yanit:
        {
            "success": true,
            "symbol": "AAPL",
            "verdict": "RISE",
            "verdict_tr": "yukselebilir",
            "explanation": "...detayli Turkce teknik aciklama...",
            "model_votes": { "rise": 10, "stable": 3, "fall": 2, "total": 15 },
            "individual_model_votes": { "random_forest": "RISE", ... },
            "model_count": 15,
            "trained_at": "2026-04-26T..."
        }
    """
    try:
        body = request.json or {}
        symbol = body.get('symbol', '').strip().upper()

        if not symbol:
            return jsonify({'success': False, 'error': 'symbol parametresi gerekli'}), 400

        if not _predictor.isLoaded:
            return jsonify({
                'success': False,
                'error': 'Modeller yuklu degil. Once "python train_models.py" calistirin.',
            }), 503

        print(f'[predict-monthly] {symbol} icin veri cekiliyor...')
        df = loadOrFetchOhlcv(symbol, years=3)

        if df.empty:
            return jsonify({'success': False, 'error': f'{symbol} icin OHLCV verisi alinamadi'}), 404

        print(f'[predict-monthly] {symbol}: {len(df)} gunluk veri, tahmin yapiliyor...')
        result = _predictor.predict(symbol, df)

        return jsonify({'success': True, **result})

    except ValueError as ve:
        return jsonify({'success': False, 'error': str(ve)}), 400
    except Exception as err:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(err)}), 500


@app.route('/api/predict-ensemble', methods=['POST'])
@app.route('/api/predict', methods=['POST'])
def predictEnsemble():
    """
    Frontend uyumlu ensemble tahmin endpoint'i.
    predict-monthly sonucunu frontend'in bekledigi formata cevirir.
    """
    try:
        body = request.json or {}
        symbol = body.get('symbol', '').strip().upper()
        horizon = int(body.get('horizon', 5))
        print(f">>> DEBUG: predictEnsemble - Symbol: {symbol}, Horizon: {horizon}")

        # Eger istenen horizon yuklu degilse, diski tekrar tara (yeni egitim bitmis olabilir)
        if horizon not in _predictor.availableHorizons:
            print(f"  [Reload] Horizon {horizon} yuklu degil, modelleri tekrar tariyorum...")
            _predictor.loadModels()

        if not _predictor.isLoaded:
            return jsonify({
                'success': False,
                'error': 'Modeller yuklu degil. Once "python train_models.py" calistirin.',
            }), 503

        print(f'[predict-ensemble] {symbol} (horizon={horizon}) icin veri cekiliyor...')
        df = loadOrFetchOhlcv(symbol, years=3)

        if df.empty:
            return jsonify({'success': False, 'error': f'{symbol} icin OHLCV verisi alinamadi'}), 404

        print(f'[predict-ensemble] {symbol}: {len(df)} gunluk veri, tahmin yapiliyor...')
        result = _predictor.predict(symbol, df, horizon=horizon)

        # Frontend'in bekledigi formata cevir
        verdictMap = {'RISE': 'UP', 'FALL': 'DOWN', 'STABLE': 'NEUTRAL'}
        displayMap = {'RISE': 'YÜKSELEBİLİR', 'FALL': 'DÜŞEBİLİR', 'STABLE': 'SABİT KALABİLİR'}
        predictionMap = {'RISE': 'AL', 'FALL': 'SAT', 'STABLE': 'TUT'}

        verdict = result.get('verdict', 'STABLE')
        modelVotes = result.get('model_votes', {})
        totalVotes = modelVotes.get('total', 1)

        # Soft voting olasılıklarını kullan (varsa), yoksa hard vote oranına fall back
        avgProbs = result.get('avg_probabilities', {})
        probRise = avgProbs.get('rise', 0.0)
        probStable = avgProbs.get('stable', 0.0)
        probFall = avgProbs.get('fall', 0.0)

        # Olasılıklar mevcutsa bunları kullan, yoksa oy oranlarından hesapla
        if probRise + probStable + probFall > 0:
            confidence = max(probRise, probStable, probFall)
        else:
            winningVotes = max(modelVotes.get('rise', 0), modelVotes.get('stable', 0), modelVotes.get('fall', 0))
            confidence = winningVotes / totalVotes if totalVotes > 0 else 0.5
            probRise = modelVotes.get('rise', 0) / totalVotes if totalVotes > 0 else 0
            probStable = modelVotes.get('stable', 0) / totalVotes if totalVotes > 0 else 0
            probFall = modelVotes.get('fall', 0) / totalVotes if totalVotes > 0 else 0

        sentiment = result.get('sentiment', {})

        frontendResult = {
            'success': True,
            'result': {
                'symbol': symbol,
                'prediction': predictionMap.get(verdict, 'TUT'),
                'prediction_display': displayMap.get(verdict, 'SABİT KALABİLİR'),
                'confidence': round(confidence, 4),
                'probabilities': {
                    'AL': round(probRise, 4),
                    'TUT': round(probStable, 4),
                    'SAT': round(probFall, 4),
                },
                'method': 'ensemble',
                'best_model': max(_predictor._trainer.scores, key=_predictor._trainer.scores.get) if _predictor._trainer.scores else 'ensemble',
                'total_models': modelVotes.get('total', 0),
                'recommendation': result.get('explanation', ''),
                'sentiment_analysis': {
                    'score': sentiment.get('avg_score', 0),
                    'positive_ratio': sentiment.get('positive', 0) / max(sentiment.get('total', 1), 1),
                    'negative_ratio': sentiment.get('negative', 0) / max(sentiment.get('total', 1), 1),
                    'news_count': sentiment.get('total', 0),
                } if sentiment.get('total', 0) > 0 else None,
                'technical_score': confidence,
                'sentiment_score': sentiment.get('avg_score', 0),
                'news_count': sentiment.get('total', 0),
                'model_votes': modelVotes,
                'individual_model_votes': result.get('individual_model_votes', {}),
                'trained_at': result.get('trained_at', ''),
                'timestamp': datetime.now().isoformat(),
            },
        }

        return jsonify(frontendResult)

    except ValueError as ve:
        return jsonify({'success': False, 'error': str(ve)}), 400
    except Exception as err:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(err)}), 500


@app.route('/api/stock-data', methods=['POST'])
def stockData():
    """
    Bir hisse icin OHLCV verisini dondurur (frontend grafikleri icin).

    Istek govdesi:
        { "symbol": "AAPL", "years": 1 }
        veya
        { "symbol": "AAPL", "days": 30 }
    """
    try:
        body = request.json or {}
        symbol = body.get('symbol', '').strip().upper()

        # days veya years parametresini kabul et
        days = body.get('days')
        if days:
            years = max(1, math.ceil(int(days) / 365))
        else:
            years = int(body.get('years', 1))

        if not symbol:
            return jsonify({'success': False, 'error': 'symbol parametresi gerekli'}), 400

        df = loadOrFetchOhlcv(symbol, years=years)

        if df.empty:
            return jsonify({'success': False, 'error': f'{symbol} icin veri bulunamadi'}), 404

        # days parametresi varsa son N gunluk veriyi filtrele
        if days:
            df = df.tail(int(days))

        dfCopy = df.copy()
        # Tarihleri YYYY-MM-DD formatinda dondur (JS Date uyumu icin)
        dfCopy['date'] = dfCopy['date'].dt.strftime('%Y-%m-%d')
        records = dfCopy.to_dict('records')

        return jsonify({'success': True, 'symbol': symbol, 'data': records, 'count': len(records)})

    except Exception as err:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(err)}), 500


@app.route('/api/models-status', methods=['GET'])
def modelsStatus():
    """
    Yuklenmis modeller hakkinda durum bilgisi dondurur.
    """
    if not _predictor.isLoaded:
        return jsonify({
            'success': False,
            'models_loaded': False,
            'message': 'Modeller yuklu degil. train_models.py calistirin.',
        })

    return jsonify({
        'success': True,
        'models_loaded': True,
        'model_count': len(_predictor._trainer.models),
        'model_names': list(_predictor._trainer.models.keys()),
        'scores': _predictor._trainer.scores,
        'feature_count': len(_predictor._trainer.featureNames),
        'trained_at': _predictor.trainedAt,
    })


@app.route('/api/sentiment-summary', methods=['POST'])
def sentimentSummary():
    """
    Bir hisse icin haber sentiment ozetini dondurur.

    Istek govdesi:
        { "symbol": "AAPL", "days": 7 }
    """
    try:
        body = request.json or {}
        symbol = body.get('symbol', '').strip().upper()
        days = int(body.get('days', 7))

        if not symbol:
            return jsonify({'success': False, 'error': 'symbol parametresi gerekli'}), 400

        from news_collector import fetchCompanyNews
        from sentiment_scorer import scoreNewsBatch

        articles = fetchCompanyNews(symbol, days=days)

        if not articles:
            return jsonify({
                'success': True,
                'result': {
                    'symbol': symbol,
                    'period_days': days,
                    'total_news': 0,
                    'sentiment_distribution': {'positive': 0, 'negative': 0, 'neutral': 0},
                    'average_score': 0,
                    'recent_headlines': [],
                },
            })

        sentimentResult = scoreNewsBatch(articles)

        headlines = []
        for article in articles[:10]:
            headlines.append({
                'datetime': article.get('datetime', ''),
                'headline': article.get('headline', ''),
                'sentiment': 'POZİTİF' if article.get('sentiment_score', 0) > 0.1 else
                             'NEGATİF' if article.get('sentiment_score', 0) < -0.1 else 'NÖTR',
                'score': article.get('sentiment_score', 0),
            })

        return jsonify({
            'success': True,
            'result': {
                'symbol': symbol,
                'period_days': days,
                'total_news': sentimentResult.get('total', 0),
                'sentiment_distribution': {
                    'positive': sentimentResult.get('positive', 0),
                    'negative': sentimentResult.get('negative', 0),
                    'neutral': sentimentResult.get('neutral', 0),
                },
                'average_score': sentimentResult.get('avg_score', 0),
                'recent_headlines': headlines,
            },
        })

    except Exception as err:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(err)}), 500


# ---------------------------------------------------------------------------
# Baslangic
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    print('\n' + '=' * 60)
    print('ML Monthly Stock Predictor - Servis Baslatiliyor')
    print('=' * 60)
    print(f'Host          : {FLASK_HOST}')
    print(f'Port          : {FLASK_PORT}')
    print(f'Debug         : {DEBUG_MODE}')
    print(f'Modeller      : {"Yuklendi (" + str(len(_predictor._trainer.models)) + " model)" if _predictor.isLoaded else "YUKLENMEDI - train_models.py calistirin"}')
    print('=' * 60 + '\n')

    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=DEBUG_MODE)
