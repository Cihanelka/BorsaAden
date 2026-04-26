"""
Ensemble model eğitim script'i
15+ farklı ML modeli eğitir ve kaydeder.
Kaydedilmiş model varsa yeniden eğitmez (--force ile zorla eğitilir).
"""
import pandas as pd
import sys
import os
from config import DEFAULT_STOCKS, COMPANY_NAMES
from ensemble_predictor import EnsembleStockPredictor
from data_collector import DataCollector
from sentiment_analyzer import SentimentAnalyzer

def load_or_collect_data(symbols=None, stock_days=365, news_days=30):
    """Verileri her zaman API'den topla (CSV cache kullanma)"""
    symbols = symbols or DEFAULT_STOCKS[:5]
    collector = DataCollector()

    # Hisse verisi (doğrudan API)
    print(f"📡 Hisse verisi API'den toplanıyor ({len(symbols)} hisse, {stock_days} gün)...")
    stock_frames = []
    for sym in symbols:
        df = collector.collect_stock_data(sym, days=stock_days)
        if not df.empty:
            df['symbol'] = sym
            stock_frames.append(df)
    stock_df = pd.concat(stock_frames, ignore_index=True) if stock_frames else pd.DataFrame()

    # Haber verisi + sentiment (doğrudan API)
    print(f"📰 Haber verisi API'den toplanıyor ve sentiment analizi yapılıyor ({len(symbols)} hisse, {news_days} gün)...")
    analyzer = SentimentAnalyzer()
    news_frames = []
    for sym in symbols:
        company_name = COMPANY_NAMES.get(sym)
        ndf = collector.collect_company_news(sym, days=news_days, company_name=company_name)
        if not ndf.empty:
            ndf = analyzer.analyze_news_batch(ndf)
            news_frames.append(ndf)
    news_df = pd.concat(news_frames, ignore_index=True) if news_frames else pd.DataFrame()

    return stock_df, news_df


def check_saved_model_exists(model_dir='data/models/ensemble'):
    """Kaydedilmiş model dosyalarının varlığını kontrol eder"""
    required_files = [
        os.path.join(model_dir, 'ensemble_sklearn.joblib'),
        os.path.join(model_dir, 'ensemble_scaler.joblib'),
        os.path.join(model_dir, 'ensemble_features.joblib'),
        os.path.join(model_dir, 'ensemble_scores.joblib'),
    ]
    return all(os.path.exists(f) for f in required_files)


def train_ensemble(symbols=None, threshold=0.02, n_splits=5):
    """Tüm hisseler için ensemble model eğit"""
    stock_df, news_df = load_or_collect_data(symbols)

    if stock_df.empty:
        print("❌ Hisse verisi bulunamadı! Önce veri toplayın.")
        return

    predictor = EnsembleStockPredictor()

    # Tüm hisseler için birleşik veri ile eğit
    available_symbols = stock_df['symbol'].unique().tolist() if 'symbol' in stock_df.columns else []
    print(f"\n📊 Mevcut hisseler: {available_symbols}")

    # Tüm hisse verilerini birleştir (daha fazla eğitim verisi)
    all_frames = []
    for sym in available_symbols:
        sym_df = stock_df[stock_df['symbol'] == sym].copy()
        sym_df.columns = [c.lower() for c in sym_df.columns]
        if 'date' in sym_df.columns:
            sym_df = sym_df.sort_values('date')
        if len(sym_df) >= 60:
            all_frames.append(sym_df)
            print(f"  ✅ {sym}: {len(sym_df)} satır")
        else:
            print(f"  ⚠️ {sym}: {len(sym_df)} satır (< 60, atlanıyor)")

    if not all_frames:
        print("❌ Yeterli veri olan hisse bulunamadı!")
        return

    # Tüm yeterli hisseleri birleştirerek eğit (daha profesyonel/genelleştirilebilir)
    combined_df = pd.concat(all_frames, ignore_index=True)
    if 'date' in combined_df.columns:
        combined_df['date'] = pd.to_datetime(combined_df['date'], errors='coerce')
        combined_df = combined_df.sort_values(['symbol', 'date']).reset_index(drop=True)

    print(f"\n🎯 Eğitim verisi: {len(all_frames)} hisse, toplam {len(combined_df)} satır")

    results = predictor.train(
        combined_df,
        news_df=news_df if not news_df.empty else None,
        symbol=None,
        threshold=threshold,
        n_splits=n_splits
    )

    print("\n" + "=" * 60)
    print("✅ ENSEMBLE EĞİTİM TAMAMLANDI")
    print("=" * 60)
    print(f"Toplam model: {len(results)}")
    print(f"Model dizini: {predictor.model_dir}")

    return results


if __name__ == '__main__':
    force_retrain = '--force' in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    symbols = args if args else None

    if not force_retrain and check_saved_model_exists():
        print("\n" + "=" * 60)
        print("✅ Kaydedilmiş model bulundu, yeniden eğitme atlanıyor.")
        print("   Yeniden eğitmek için: python train_ensemble.py --force")
        print("=" * 60)
        predictor = EnsembleStockPredictor()
        predictor.load_models()
        print(f"✅ {len(predictor.models)} model yüklendi.")
    else:
        if force_retrain:
            print("⚠️  --force flag'i ile yeniden eğitim zorlandı.")
        train_ensemble(symbols)
