"""
Created by: AdenBorsa ML Team
Created At: 2026-04-26
Subject: yfinance ile 3 yillik OHLCV veri toplama modulu.
         Veriler CSV'ye cache'lenir - her gun bir kez API cagrisi yapilir.
"""

import os
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from config import CSV_DIR

OHLCV_YEARS = 3
CACHE_HOURS = 20  # Bu sureden eski cache yenilenir


def fetchOhlcv(symbol: str, years: int = OHLCV_YEARS) -> pd.DataFrame:
    """
    yfinance ile belirtilen sembol icin OHLCV verisi ceker.
    'years' yil geri gider, gunluk (1d) interval kullanir.
    """
    endDate = datetime.today()
    startDate = endDate - timedelta(days=years * 365 + 10)  # biraz fazla al, kesilmesin

    ticker = yf.Ticker(symbol)
    rawDf = ticker.history(
        start=startDate.strftime('%Y-%m-%d'),
        end=endDate.strftime('%Y-%m-%d'),
        interval='1d',
        auto_adjust=True,
        actions=False,
    )

    if rawDf is None or rawDf.empty:
        return pd.DataFrame()

    rawDf = rawDf.reset_index()
    rawDf.columns = [c.lower() for c in rawDf.columns]

    keepCols = ['date', 'open', 'high', 'low', 'close', 'volume']
    existingCols = [c for c in keepCols if c in rawDf.columns]
    df = rawDf[existingCols].copy()

    df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None)
    df['symbol'] = symbol
    df = df.sort_values('date').reset_index(drop=True)

    return df


def loadOrFetchOhlcv(symbol: str, years: int = OHLCV_YEARS) -> pd.DataFrame:
    """
    Once CSV cache'e bakar. Cache yoksa veya CACHE_HOURS'dan eskiyse API'den ceker.
    """
    os.makedirs(CSV_DIR, exist_ok=True)
    csvPath = os.path.join(CSV_DIR, f'ohlcv_{symbol}.csv')

    if os.path.exists(csvPath):
        ageHours = (datetime.now() - datetime.fromtimestamp(os.path.getmtime(csvPath))).total_seconds() / 3600
        if ageHours < CACHE_HOURS:
            df = pd.read_csv(csvPath, parse_dates=['date'])
            print(f"  {symbol}: cache'den yuklendi ({len(df)} gun)")
            return df

    print(f"  {symbol}: API'den cekiliyor ({years} yil)...", flush=True)
    df = fetchOhlcv(symbol, years)

    if not df.empty:
        df.to_csv(csvPath, index=False)
        print(f"  {symbol}: {len(df)} gunluk veri kaydedildi")
    else:
        print(f"  {symbol}: veri alinamadi!")

    return df


def fetchMultipleSymbols(symbols: list, years: int = OHLCV_YEARS) -> pd.DataFrame:
    """
    Birden fazla sembol icin OHLCV verisi ceker ve birlestirerek dondurur.
    """
    frames = []
    for symbol in symbols:
        try:
            df = loadOrFetchOhlcv(symbol, years)
            if not df.empty:
                frames.append(df)
        except Exception as e:
            print(f"  {symbol} hatasi: {e}")

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True)
