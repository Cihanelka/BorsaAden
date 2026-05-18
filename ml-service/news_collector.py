"""
Created by: AdenBorsa ML Team
Created At: 2026-04-26
Subject: Finnhub API'sinden hisse haberleri cekme modulu.
         Son N gunluk baslik ve ozet verilerini dondurur.
"""

import requests
import os
from datetime import datetime, timedelta
from config import FINNHUB_API_KEY

FINNHUB_BASE_URL = 'https://finnhub.io/api/v1'
MAX_NEWS_DAYS = 30
MAX_ARTICLES = 50


def fetchCompanyNews(symbol: str, days: int = MAX_NEWS_DAYS) -> list:
    """
    Finnhub'dan belirtilen sembol icin son 'days' gunluk haberleri ceker.

    Donus: Her haber icin {'headline': str, 'summary': str, 'datetime': int} listesi.
           Hata durumunda bos liste doner - haber yoksa model calismaya devam eder.
    """
    endDate = datetime.today()
    startDate = endDate - timedelta(days=days)

    params = {
        'symbol': symbol,
        'from': startDate.strftime('%Y-%m-%d'),
        'to': endDate.strftime('%Y-%m-%d'),
        'token': FINNHUB_API_KEY,
    }

    try:
        response = requests.get(
            f'{FINNHUB_BASE_URL}/company-news',
            params=params,
            timeout=10,
        )
        response.raise_for_status()
        articles = response.json()

        if not isinstance(articles, list):
            return []

        # Sadece gerekli alanlari dondur, makul sayida tut
        result = []
        for article in articles[:MAX_ARTICLES]:
            headline = article.get('headline', '').strip()
            summary = article.get('summary', '').strip()
            publishedAt = article.get('datetime', 0)

            if headline:
                result.append({
                    'headline': headline,
                    'summary': summary,
                    'published_at': publishedAt,
                })

        return result

    except requests.exceptions.RequestException as err:
        print(f'  Haber API hatasi ({symbol}): {err}')
        return []
    except Exception as err:
        print(f'  Haber isleme hatasi ({symbol}): {err}')
        return []
