"""
Created by: AdenBorsa ML Team
Created At: 2026-05-03
Subject: Tek seferlik model egitim betigi.
         3 yillik OHLCV verisi ceker, feature muhendisligi yapar,
         her vade ufku (5/21/63 gun) icin 15 modeli egitir ve kaydeder.
"""

import sys
import os
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))

from data_collector import fetchMultipleSymbols
from feature_engineer import prepareTrainingData
from model_trainer import ModelTrainer, SUPPORTED_HORIZONS, HORIZON_LABELS

# Egitimde kullanilacak semboller
TRAINING_SYMBOLS = [
    # Buyuk teknoloji
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'AMD', 'INTC', 'NFLX',
    # Finans
    'JPM', 'GS', 'BAC', 'V', 'MA', 'PYPL',
    # Tuketici / Saglik / Diger
    'WMT', 'KO', 'PFE', 'DIS', 'ADBE', 'CRM', 'ORCL', 'IBM', 'BABA',
    # ETF
    'SPY', 'QQQ',
]

TRAINING_YEARS = 3  # 3 yillik veri kurali (Prompt baslangici)

def main():
    print('\n' + '=' * 60)
    print('ADEN BORSA - ÇOKLU VADE STRATEJİK MODEL EĞİTİMİ')
    print('=' * 60)

    print(f'\n[1/3] Veri toplaniyor ({len(TRAINING_SYMBOLS)} sembol, {TRAINING_YEARS} yil)...')
    # Veri toplama (3 yil)
    allData = fetchMultipleSymbols(TRAINING_SYMBOLS, years=TRAINING_YEARS)

    if allData.empty:
        print('HATA: Hicbir sembol icin veri alinamadi!')
        sys.exit(1)

    uniqueSymbols = allData['symbol'].nunique()
    print(f'  Toplam: {len(allData):,} satir, {uniqueSymbols} sembol yuklendi.')

    # Her horizon icin egitim
    for idx, horizon in enumerate(SUPPORTED_HORIZONS, 1):
        hLabel = HORIZON_LABELS[horizon]
        print(f'\n{"=" * 60}')
        print(f'[2/3] VADE: {hLabel["label"]} (horizon={horizon} gun)')
        print(f'{"=" * 60}')

        print(f'  Feature muhendisligi ve hedef degisken hazirlaniyor (horizon={horizon})...')
        X, y, featureNames = prepareTrainingData(allData, horizon=horizon)

        if X is None or X.empty:
            print(f'  UYARI: horizon={horizon} icin veri yetersiz, atlaniyor!')
            continue

        print(f'  X sekli: {X.shape}')
        labelCounts = y.value_counts().sort_index()
        print(f'  Etiket dagilimi -> FALL(-1): {labelCounts.get(-1, 0)}, STABLE(0): {labelCounts.get(0, 0)}, RISE(1): {labelCounts.get(1, 0)}')

        print(f'\n  {hLabel["label"]} icin 15 model egitiliyor...')
        trainer = ModelTrainer(horizon=horizon)
        trainer.train(X, y)

        print(f'  Modeller diske kaydediliyor (horizon={horizon})...')
        trainer.save()

        print(f'  [DONE] {hLabel["label"]} egitimi tamamlandi!')

    print('\n' + '=' * 60)
    print('TÜM VADE UFUKLARI İÇİN EĞİTİM BAŞARIYLA TAMAMLANDI!')
    print('  • Kısa Vade (5 gün)  - 1 Haftalık tahmin')
    print('  • Orta Vade (21 gün) - 1 Aylık tahmin')
    print('  • Uzun Vade (63 gün) - 3 Aylık tahmin')
    print('=' * 60 + '\n')

if __name__ == '__main__':
    main()
