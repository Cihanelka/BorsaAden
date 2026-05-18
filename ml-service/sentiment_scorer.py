"""
Created by: AdenBorsa ML Team
Created At: 2026-04-26
Subject: VADER ile haber basliklarindan sentiment skoru hesaplama.
         Agir transformer modeli gerektirmez, aninda calisir.
"""

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()

# Sentiment sinir degerleri
POSITIVE_THRESHOLD = 0.05
NEGATIVE_THRESHOLD = -0.05


def scoreArticle(text: str) -> float:
    """
    Tek bir metin icin VADER compound skoru dondurur.
    Aralik: -1.0 (cok negatif) ile +1.0 (cok pozitif).
    """
    if not text or not text.strip():
        return 0.0
    return _analyzer.polarity_scores(text)['compound']


def scoreNewsBatch(articles: list) -> dict:
    """
    Haber listesini analiz ederek ozet sentiment istatistiklerini dondurur.

    Parametreler:
        articles: [{'headline': str, 'summary': str, ...}, ...] listesi

    Donus:
        {
            'total': int,
            'positive': int,
            'neutral': int,
            'negative': int,
            'avg_score': float,      # -1.0 ile +1.0 arasi
            'sentiment_label': str,  # 'POZITIF' | 'NOTR' | 'NEGATIF'
            'top_positive': [str],   # En pozitif 3 baslik
            'top_negative': [str],   # En negatif 3 baslik
        }
    """
    if not articles:
        return _emptyResult()

    scored = []
    for article in articles:
        headline = article.get('headline', '')
        summary = article.get('summary', '')
        # Baslik daha onemli oldugu icin agirlikli ortalama al
        headlineScore = scoreArticle(headline)
        summaryScore = scoreArticle(summary) if summary else headlineScore
        combinedScore = 0.7 * headlineScore + 0.3 * summaryScore

        scored.append({
            'headline': headline,
            'score': combinedScore,
        })

    if not scored:
        return _emptyResult()

    scores = [s['score'] for s in scored]
    avgScore = sum(scores) / len(scores)

    positiveCount = sum(1 for s in scores if s > POSITIVE_THRESHOLD)
    negativeCount = sum(1 for s in scores if s < NEGATIVE_THRESHOLD)
    neutralCount = len(scores) - positiveCount - negativeCount

    # Genel etiket
    if avgScore > POSITIVE_THRESHOLD:
        sentimentLabel = 'POZITIF'
    elif avgScore < NEGATIVE_THRESHOLD:
        sentimentLabel = 'NEGATIF'
    else:
        sentimentLabel = 'NOTR'

    # En dikkat cekici haberler
    sortedByScore = sorted(scored, key=lambda x: x['score'], reverse=True)
    topPositive = [s['headline'] for s in sortedByScore[:3] if s['score'] > POSITIVE_THRESHOLD]
    topNegative = [s['headline'] for s in sortedByScore[-3:] if s['score'] < NEGATIVE_THRESHOLD]

    return {
        'total': len(scored),
        'positive': positiveCount,
        'neutral': neutralCount,
        'negative': negativeCount,
        'avg_score': round(avgScore, 4),
        'sentiment_label': sentimentLabel,
        'top_positive': topPositive,
        'top_negative': list(reversed(topNegative)),
    }


def _emptyResult() -> dict:
    return {
        'total': 0,
        'positive': 0,
        'neutral': 0,
        'negative': 0,
        'avg_score': 0.0,
        'sentiment_label': 'NOTR',
        'top_positive': [],
        'top_negative': [],
    }
