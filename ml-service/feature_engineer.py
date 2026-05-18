"""
Created by: AdenBorsa ML Team
Created At: 2026-05-03
Subject: OHLCV verilerinden 80+ teknik gosterge feature'i ureten modul.
         Prompt 1: Ham teknik gostergeler (7 kategori)
         Prompt 2: Zone/sinyal kodlamalari + confluence score
         Prompt 3: 5 gunluk ileri getiri ile 3-sinif hedef degisken
         Prompt 5: Data leakage onleme kurallarina uygun tasarim
"""

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Sabitler
# ---------------------------------------------------------------------------
PREDICTION_HORIZON = 5       # 5 is gunu ileriye bakis
RISE_THRESHOLD = 0.02        # +%2 yukselis esigi
FALL_THRESHOLD = -0.02       # -%2 dusus esigi
SEQUENCE_LENGTH = 20          # LSTM/GRU/CNN icin pencere uzunlugu

LABEL_RISE = 1
LABEL_STABLE = 0
LABEL_FALL = -1


# ===========================================================================
# BOLUM 1: HAM TEKNIK GOSTERGELER (Prompt 1)
# ===========================================================================

# --- 1.1 Trend / Momentum ---

def _computeRSI(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avgGain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avgLoss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avgGain / (avgLoss + 1e-10)
    return 100 - (100 / (1 + rs))


def _computeEMA(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def _computeMACD(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    fastEma = _computeEMA(series, fast)
    slowEma = _computeEMA(series, slow)
    macdLine = fastEma - slowEma
    signalLine = _computeEMA(macdLine, signal)
    histogram = macdLine - signalLine
    return macdLine, signalLine, histogram


def _trendMomentumFeatures(df: pd.DataFrame) -> dict:
    close = df['close']
    feats = {}

    # RSI
    feats['RSI_14'] = _computeRSI(close, 14)

    # MACD
    macdLine, macdSignal, macdHist = _computeMACD(close)
    feats['MACD_line'] = macdLine
    feats['MACD_signal'] = macdSignal
    feats['MACD_hist'] = macdHist
    feats['MACD_hist_dir'] = np.sign(macdHist.diff()).fillna(0).astype(int)

    # EMA'lar
    feats['EMA_20'] = _computeEMA(close, 20)
    feats['EMA_50'] = _computeEMA(close, 50)
    feats['EMA_200'] = _computeEMA(close, 200)

    # Fiyat vs EMA oranlari
    feats['price_vs_EMA20'] = (close - feats['EMA_20']) / (feats['EMA_20'] + 1e-10)
    feats['price_vs_EMA50'] = (close - feats['EMA_50']) / (feats['EMA_50'] + 1e-10)
    feats['EMA20_vs_EMA50'] = (feats['EMA_20'] - feats['EMA_50']) / (feats['EMA_50'] + 1e-10)

    return feats


# --- 1.2 Volatilite ---

def _volatilityFeatures(df: pd.DataFrame) -> dict:
    close = df['close']
    high = df['high']
    low = df['low']
    feats = {}

    # Bollinger Bands
    sma20 = close.rolling(20).mean()
    std20 = close.rolling(20).std()
    feats['BB_upper'] = sma20 + 2 * std20
    feats['BB_mid'] = sma20
    feats['BB_lower'] = sma20 - 2 * std20
    feats['BB_width'] = (feats['BB_upper'] - feats['BB_lower']) / (feats['BB_mid'] + 1e-10)
    feats['BB_position'] = (close - feats['BB_lower']) / (feats['BB_upper'] - feats['BB_lower'] + 1e-10)

    # ATR
    prevClose = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prevClose).abs(),
        (low - prevClose).abs(),
    ], axis=1).max(axis=1)
    feats['ATR_14'] = tr.ewm(alpha=1 / 14, min_periods=14, adjust=False).mean()
    feats['ATR_pct'] = feats['ATR_14'] / (close + 1e-10)

    return feats


# --- 1.3 Support & Resistance ---

def _supportResistanceFeatures(df: pd.DataFrame, atr14: pd.Series) -> dict:
    close = df['close']
    high = df['high']
    low = df['low']
    feats = {}

    feats['support_level'] = low.rolling(20).min()
    feats['resistance_level'] = high.rolling(20).max()
    feats['dist_to_support'] = (close - feats['support_level']) / (close + 1e-10)
    feats['dist_to_resistance'] = (feats['resistance_level'] - close) / (close + 1e-10)

    buffer = atr14 * 0.5
    feats['inside_support_buffer'] = ((close - feats['support_level']).abs() < buffer).astype(int)
    feats['inside_resist_buffer'] = ((feats['resistance_level'] - close).abs() < buffer).astype(int)

    return feats


# --- 1.4 Pivot Points (t-1 verileri kullanilir, leakage onleme) ---

def _pivotPointFeatures(df: pd.DataFrame) -> dict:
    prevHigh = df['high'].shift(1)
    prevLow = df['low'].shift(1)
    prevClose = df['close'].shift(1)
    close = df['close']
    feats = {}

    # Classic Pivot
    feats['pivot_classic'] = (prevHigh + prevLow + prevClose) / 3
    feats['pivot_r1'] = 2 * feats['pivot_classic'] - prevLow
    feats['pivot_s1'] = 2 * feats['pivot_classic'] - prevHigh
    feats['pivot_r2'] = feats['pivot_classic'] + (prevHigh - prevLow)
    feats['pivot_s2'] = feats['pivot_classic'] - (prevHigh - prevLow)

    # Fibonacci Pivot
    hlRange = prevHigh - prevLow
    feats['pivot_fib_r1'] = feats['pivot_classic'] + 0.382 * hlRange
    feats['pivot_fib_s1'] = feats['pivot_classic'] - 0.382 * hlRange

    # Fiyat vs pivot
    feats['price_vs_pivot'] = (close - feats['pivot_classic']) / (feats['pivot_classic'] + 1e-10)
    feats['above_pivot'] = (close > feats['pivot_classic']).astype(int)

    return feats


# --- 1.5 Hacim ---

def _volumeFeatures(df: pd.DataFrame) -> dict:
    close = df['close']
    volume = df['volume']
    feats = {}

    feats['volume_sma20'] = volume.rolling(20).mean()
    feats['volume_ratio'] = volume / (feats['volume_sma20'] + 1e-10)

    direction = np.sign(close.diff()).fillna(0)
    feats['OBV'] = (volume * direction).cumsum()
    obvEma20 = _computeEMA(feats['OBV'], 20)
    feats['OBV_trend'] = np.where(feats['OBV'] > obvEma20, 1, -1)

    return feats


# --- 1.6 Mum Yapisi ---

def _candlestickFeatures(df: pd.DataFrame) -> dict:
    o, h, l, c = df['open'], df['high'], df['low'], df['close']
    feats = {}

    feats['body_size'] = (c - o).abs() / (o + 1e-10)
    feats['upper_wick'] = (h - pd.concat([o, c], axis=1).max(axis=1)) / (o + 1e-10)
    feats['lower_wick'] = (pd.concat([o, c], axis=1).min(axis=1) - l) / (o + 1e-10)
    feats['is_bullish_bar'] = (c > o).astype(int)
    feats['daily_range'] = (h - l) / (o + 1e-10)

    return feats


# --- 1.7 Geckmeli (Lagged) Feature'lar ---

def _addLaggedFeatures(feats: pd.DataFrame) -> pd.DataFrame:
    lagCols = ['close_return', 'RSI_14', 'MACD_hist', 'BB_position', 'volume_ratio']
    for col in lagCols:
        if col in feats.columns:
            for lag in [1, 2, 3]:
                feats[f'{col}_lag{lag}'] = feats[col].shift(lag)
    return feats


# ===========================================================================
# BOLUM 2: ZONE & SIGNAL ENCODING (Prompt 2)
# ===========================================================================

def _rsiZoneEncoding(feats: pd.DataFrame) -> dict:
    rsi = feats['RSI_14']
    zones = {}

    # 4 seviyeli RSI zone
    conditions = [rsi < 30, (rsi >= 30) & (rsi < 50), (rsi >= 50) & (rsi < 70), rsi >= 70]
    choices = [-1, 0, 1, 2]
    zones['RSI_zone'] = np.select(conditions, choices, default=0)

    # RSI 50 gecisi
    prevRsi = rsi.shift(1)
    crossUp = (prevRsi < 50) & (rsi >= 50)
    crossDown = (prevRsi > 50) & (rsi <= 50)
    zones['RSI_cross_50'] = np.where(crossUp, 1, np.where(crossDown, -1, 0))

    # RSI Divergence (son 5 bar)
    close = feats['close']
    priceNewLow = close == close.rolling(5).min()
    rsiNotNewLow = rsi > rsi.rolling(5).min()
    zones['RSI_divergence_bull'] = (priceNewLow & rsiNotNewLow).astype(int)

    priceNewHigh = close == close.rolling(5).max()
    rsiNotNewHigh = rsi < rsi.rolling(5).max()
    zones['RSI_divergence_bear'] = (priceNewHigh & rsiNotNewHigh).astype(int)

    return zones


def _macdZoneEncoding(feats: pd.DataFrame) -> dict:
    macdLine = feats['MACD_line']
    macdSignal = feats['MACD_signal']
    macdHist = feats['MACD_hist']
    atrRef = feats['ATR_14'] * 0.1
    zones = {}

    # Signal cross
    prevLine = macdLine.shift(1)
    prevSig = macdSignal.shift(1)
    crossUp = (prevLine < prevSig) & (macdLine > macdSignal)
    crossDown = (prevLine > prevSig) & (macdLine < macdSignal)
    zones['MACD_signal_cross'] = np.where(crossUp, 1, np.where(crossDown, -1, 0))

    # Zero cross
    prevLineVal = macdLine.shift(1)
    zeroUp = (prevLineVal < 0) & (macdLine >= 0)
    zeroDown = (prevLineVal > 0) & (macdLine <= 0)
    zones['MACD_zero_cross'] = np.where(zeroUp, 1, np.where(zeroDown, -1, 0))

    # MACD zone (5 seviye)
    nearZero = macdLine.abs() < atrRef
    conditions = [
        nearZero,
        (macdLine > 0) & (macdHist > 0),
        (macdLine > 0) & (macdHist <= 0),
        (macdLine < 0) & (macdHist < 0),
        (macdLine < 0) & (macdHist >= 0),
    ]
    choices = [0, 1, 2, -1, -2]
    zones['MACD_zone'] = np.select(conditions, choices, default=0)

    # Histogram acceleration
    h0 = macdHist
    h1 = macdHist.shift(1)
    h2 = macdHist.shift(2)
    accelUp = (h0 > h1) & (h1 > h2)
    accelDown = (h0 < h1) & (h1 < h2)
    zones['MACD_hist_acceleration'] = np.where(accelUp, 1, np.where(accelDown, -1, 0))

    return zones


def _bbZoneEncoding(feats: pd.DataFrame) -> dict:
    close = feats['close']
    bbUpper = feats['BB_upper']
    bbMid = feats['BB_mid']
    bbLower = feats['BB_lower']
    bbWidth = feats['BB_width']
    zones = {}

    # BB zone (4 seviye)
    conditions = [
        close < bbLower,
        (close >= bbLower) & (close < bbMid),
        (close >= bbMid) & (close < bbUpper),
        close >= bbUpper,
    ]
    choices = [-2, -1, 1, 2]
    zones['BB_zone'] = np.select(conditions, choices, default=0)

    # BB squeeze (son 100 bar icerisinde percentile 20 altinda mi)
    bbWidthPct20 = bbWidth.rolling(100, min_periods=20).quantile(0.20)
    zones['BB_squeeze'] = (bbWidth < bbWidthPct20).astype(int)

    # BB breakout
    prevZone = pd.Series(zones['BB_zone']).shift(1)
    currentZone = pd.Series(zones['BB_zone'])
    breakUp = (currentZone == 2) & (prevZone < 2)
    breakDown = (currentZone == -2) & (prevZone > -2)
    zones['BB_breakout'] = np.where(breakUp, 1, np.where(breakDown, -1, 0))

    # Mean reversion signal
    mRevUp = (prevZone <= -2) & (close > bbLower)
    mRevDown = (prevZone >= 2) & (close < bbUpper)
    zones['BB_mean_reversion_signal'] = np.where(mRevUp, 1, np.where(mRevDown, -1, 0))

    return zones


def _srZoneEncoding(feats: pd.DataFrame) -> dict:
    close = feats['close']
    support = feats['support_level']
    resistance = feats['resistance_level']
    atr = feats['ATR_14']
    zones = {}

    # Near support
    inBuffer = close < (support + atr * 0.5)
    nearBelow = (close > (support - atr)) & (close < support)
    zones['near_support'] = np.where(inBuffer, 2, np.where(nearBelow, 1, 0))

    # Near resistance
    inResBuffer = close > (resistance - atr * 0.5)
    nearAbove = (close > resistance) & (close < (resistance + atr))
    zones['near_resistance'] = np.where(inResBuffer, 2, np.where(nearAbove, 1, 0))

    # Support break
    prevClose = close.shift(1)
    prevSupport = support.shift(1)
    zones['support_break'] = ((close < support) & (prevClose >= prevSupport)).astype(int)

    # Resistance break
    zones['resistance_break'] = ((close > resistance) & (prevClose <= prevSupport)).astype(int)

    return zones


def _pivotZoneEncoding(feats: pd.DataFrame, df: pd.DataFrame) -> dict:
    close = feats['close']
    pivot = feats['pivot_classic']
    r1 = feats['pivot_r1']
    r2 = feats['pivot_r2']
    s1 = feats['pivot_s1']
    s2 = feats['pivot_s2']
    zones = {}

    # Pivot zone (7 seviye)
    conditions = [
        close < s2,
        (close >= s2) & (close < s1),
        (close >= s1) & (close < pivot),
        (close >= pivot) & (close <= r1),
        (close > r1) & (close <= r2),
        close > r2,
    ]
    choices = [-3, -2, -1, 1, 2, 3]
    # Pivot civari kontrol (±%0.3)
    nearPivot = ((close - pivot).abs() / (pivot + 1e-10)) < 0.003
    pivotZone = np.select(conditions, choices, default=0)
    zones['pivot_zone'] = np.where(nearPivot, 0, pivotZone)

    # Pivot consensus (Classic, Woodie, DeMark)
    prevH = df['high'].shift(1)
    prevL = df['low'].shift(1)
    prevC = df['close'].shift(1)
    prevO = df['open'].shift(1)

    # Woodie pivot
    woodiePivot = (prevH + prevL + 2 * prevC) / 4

    # DeMark pivot
    demarkX = np.where(prevC > prevO,
                       2 * prevH + prevL + prevC,
                       np.where(prevC < prevO,
                                prevH + 2 * prevL + prevC,
                                prevH + prevL + 2 * prevC))
    demarkPivot = pd.Series(demarkX, index=close.index) / 4

    zones['pivot_bull_count'] = (
        (close > pivot).astype(int) +
        (close > woodiePivot).astype(int) +
        (close > demarkPivot).astype(int)
    )
    zones['pivot_bear_count'] = (
        (close < pivot).astype(int) +
        (close < woodiePivot).astype(int) +
        (close < demarkPivot).astype(int)
    )

    return zones


def _atrRegimeEncoding(feats: pd.DataFrame) -> dict:
    atrPct = feats['ATR_pct']
    zones = {}

    pct25 = atrPct.rolling(60, min_periods=20).quantile(0.25)
    pct75 = atrPct.rolling(60, min_periods=20).quantile(0.75)

    conditions = [atrPct < pct25, atrPct > pct75]
    choices = [0, 2]
    zones['ATR_regime'] = np.select(conditions, choices, default=1)

    return zones


def _confluenceScore(feats: pd.DataFrame) -> dict:
    zones = {}

    bullScore = (
        (feats['RSI_zone'] >= 1).astype(int) +
        feats['MACD_zone'].isin([1, 2]).astype(int) +
        (feats['BB_zone'] >= 1).astype(int) +
        (feats['above_pivot'] == 1).astype(int) +
        (feats['near_support'] == 2).astype(int)
    )
    zones['bull_confluence'] = bullScore

    bearScore = (
        (feats['RSI_zone'] <= 0).astype(int) +
        feats['MACD_zone'].isin([-1, -2]).astype(int) +
        (feats['BB_zone'] <= -1).astype(int) +
        (feats['above_pivot'] == 0).astype(int) +
        (feats['near_resistance'] == 2).astype(int)
    )
    zones['bear_confluence'] = bearScore
    zones['net_confluence'] = bullScore - bearScore

    return zones


# ===========================================================================
# BOLUM 3: ANA FEATURE URETIM FONKSIYONU
# ===========================================================================

def engineerFeatures(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tek bir hisse icin ham OHLCV DataFrame'inden tum teknik feature'lari uretir.
    Giris: date, open, high, low, close, volume sutunlari.
    Cikis: 80+ teknik gosterge feature'i iceren DataFrame.
    """
    df = df.sort_values('date').reset_index(drop=True).copy()

    feats = pd.DataFrame(index=df.index)
    feats['date'] = df['date']
    feats['close'] = df['close']

    # --- Bolum 1: Ham gostergeler ---
    for name, series in _trendMomentumFeatures(df).items():
        feats[name] = series

    for name, series in _volatilityFeatures(df).items():
        feats[name] = series

    for name, series in _supportResistanceFeatures(df, feats['ATR_14']).items():
        feats[name] = series

    for name, series in _pivotPointFeatures(df).items():
        feats[name] = series

    for name, series in _volumeFeatures(df).items():
        feats[name] = series

    for name, series in _candlestickFeatures(df).items():
        feats[name] = series

    # close_return (lagged features icin gerekli)
    feats['close_return'] = df['close'].pct_change()

    # --- Bolum 2: Zone & Signal encoding ---
    for name, series in _rsiZoneEncoding(feats).items():
        feats[name] = series

    for name, series in _macdZoneEncoding(feats).items():
        feats[name] = series

    for name, series in _bbZoneEncoding(feats).items():
        feats[name] = series

    for name, series in _srZoneEncoding(feats).items():
        feats[name] = series

    for name, series in _pivotZoneEncoding(feats, df).items():
        feats[name] = series

    for name, series in _atrRegimeEncoding(feats).items():
        feats[name] = series

    for name, series in _confluenceScore(feats).items():
        feats[name] = series

    # --- Bolum 1.7: Lagged features ---
    feats = _addLaggedFeatures(feats)

    return feats


# ===========================================================================
# BOLUM 4: HEDEF DEGISKEN (Prompt 3 - Option A: 3 sinif)
# ===========================================================================

def computeTarget(close: pd.Series, horizon: int = PREDICTION_HORIZON) -> pd.Series:
    """
    N gunluk ileri getiriye gore 3-sinif etiket hesaplar.
    Esik degerleri horizon'a gore dinamik belirlenir:
      - 5 gun:  +/-%2
      - 21 gun: +/-%5
      - 63 gun: +/-%10
    Son 'horizon' satir NaN olur (etiket hesaplanamaz).
    """
    # Horizon'a gore dinamik esik degerleri
    thresholds = {
        5:  0.02,   # 1 hafta:  %2
        21: 0.05,   # 1 ay:     %5
        63: 0.10,   # 3 ay:     %10
    }
    threshold = thresholds.get(horizon, 0.02 * (horizon / 5))

    futureReturn = close.shift(-horizon) / close - 1
    labels = pd.Series(LABEL_STABLE, index=close.index)
    labels[futureReturn > threshold] = LABEL_RISE
    labels[futureReturn < -threshold] = LABEL_FALL
    labels[futureReturn.isna()] = np.nan
    return labels


# ===========================================================================
# BOLUM 5: EGITIM VE CANLI TAHMIN HAZIRLAMA
# ===========================================================================

# Modellere verilmeyecek sutunlar (meta veri)
_NON_FEATURE_COLS = frozenset(['date', 'close', 'EMA_20', 'EMA_50', 'EMA_200',
                                'BB_upper', 'BB_mid', 'BB_lower',
                                'support_level', 'resistance_level',
                                'pivot_classic', 'pivot_r1', 'pivot_s1',
                                'pivot_r2', 'pivot_s2',
                                'pivot_fib_r1', 'pivot_fib_s1',
                                'volume_sma20', 'OBV', 'ATR_14'])


def getFeatureColumns(feats: pd.DataFrame) -> list:
    """Feature olarak kullanilacak sutun isimlerini dondurur."""
    return [c for c in feats.columns if c not in _NON_FEATURE_COLS]


def prepareTrainingData(df: pd.DataFrame, horizon: int = PREDICTION_HORIZON):
    """
    Egitim icin X ve y hazirlar. Birden fazla sembol destekler.
    NaN satirlar (lookback penceresi nedeniyle) otomatik olarak cikarilir.

    Donus: (X DataFrame, y Series, featureNames list)
    """
    allFeatures = []
    allLabels = []

    symbols = df['symbol'].unique() if 'symbol' in df.columns else ['UNKNOWN']

    for symbol in symbols:
        symbolDf = df[df['symbol'] == symbol].copy() if 'symbol' in df.columns else df.copy()

        if len(symbolDf) < 250:
            print(f"  {symbol}: yetersiz veri ({len(symbolDf)} satir), atlandi")
            continue

        featureDf = engineerFeatures(symbolDf)
        labels = computeTarget(symbolDf['close'].reset_index(drop=True), horizon)

        featureCols = getFeatureColumns(featureDf)
        numericFeatures = featureDf[featureCols].copy()
        numericFeatures['date'] = featureDf['date'] # Siralamak icin gecici ekle
        numericFeatures['target'] = labels

        # NaN satirlari cikar
        validMask = numericFeatures.notna().all(axis=1)
        if validMask.sum() < 50:
            continue

        allFeatures.append(numericFeatures[validMask])
        print(f"  {symbol}: {validMask.sum()} gecerli satir")

    if not allFeatures:
        return None, None, []

    # Tum hisseleri birlestir
    combined = pd.concat(allFeatures, ignore_index=True)
    
    # KRITIK: Tarihe gore sirala (Leakage onlemek ve dogru split icin)
    combined = combined.sort_values('date').reset_index(drop=True)
    
    y = combined['target'].astype(int)
    X = combined.drop(columns=['date', 'target'])
    featureNames = list(X.columns)

    return X, y, featureNames


def prepareLiveFeatures(df: pd.DataFrame):
    """
    Canli tahmin icin feature'lari dondurur.
    Donus: (son satir feature dict, tam feature DataFrame, featureCols listesi)
    """
    featureDf = engineerFeatures(df)
    featureCols = getFeatureColumns(featureDf)
    lastRow = featureDf[featureCols].iloc[-1]
    return lastRow, featureDf, featureCols
