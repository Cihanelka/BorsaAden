"""
Ensemble Borsa Tahmin Sistemi
- 15+ farklı ML modeli (sklearn + XGBoost + LightGBM + CatBoost + LSTM/GRU)
- Sentiment feature engineering (zaman bazlı, maks %2 etki - teknik analiz öncelikli)
- Confidence score tabanlı model seçimi
- Cross-validation ile overfitting önleme
- Modeller diske kaydedilir, yeniden eğitim gerektirmez
- Tahmin: YÜKSELECEK / SABİT KALABİLİR / DÜŞECEK
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import RobustScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import f1_score, accuracy_score, mean_absolute_error
from sklearn.ensemble import (
    RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier,
    AdaBoostClassifier, BaggingClassifier, HistGradientBoostingClassifier
)
from sklearn.linear_model import LogisticRegression, RidgeClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis, QuadraticDiscriminantAnalysis
from sklearn.neural_network import MLPClassifier
import joblib
import os
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

try:
    import os as _os
    _os.environ.setdefault('LIGHTGBM_NO_DASK', '1')
    from lightgbm import LGBMClassifier
    HAS_LGBM = True
except (ImportError, TypeError, Exception):
    HAS_LGBM = False

try:
    from catboost import CatBoostClassifier
    HAS_CATBOOST = True
except ImportError:
    HAS_CATBOOST = False

try:
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, GRU, Dense, Dropout
    from tensorflow.keras.callbacks import EarlyStopping
    import tensorflow as tf
    tf.get_logger().setLevel('ERROR')
    HAS_TF = True
except ImportError:
    HAS_TF = False

# Sentiment ağırlık sabitleri
SENTIMENT_WEIGHT_CAP = 0.02  # Maksimum %2 (teknik analiz öncelikli)
NEWS_TIME_WEIGHTS = {0: 1.0, 1: 0.7, 2: 0.4, 3: 0.2}
SEQUENCE_LENGTH = 10  # LSTM/GRU için


class SentimentFeatureEngineer:
    """Haber verisinden zaman bazlı, sınırlı etkili sentiment feature'lar üretir"""

    @staticmethod
    def compute_time_weighted_sentiment(news_df, symbol, reference_date=None):
        """Son 1-3 günün haberlerini azalan ağırlıkla skorlar"""
        if news_df is None or news_df.empty:
            return SentimentFeatureEngineer._empty_features()

        if 'symbol' in news_df.columns:
            df = news_df[news_df['symbol'] == symbol].copy()
        else:
            df = news_df.copy()

        if df.empty:
            return SentimentFeatureEngineer._empty_features()

        if reference_date is None:
            reference_date = pd.Timestamp.utcnow().tz_localize(None)
        else:
            reference_date = pd.to_datetime(reference_date, errors='coerce')
            if pd.isna(reference_date):
                reference_date = pd.Timestamp.utcnow().tz_localize(None)
            else:
                try:
                    reference_date = reference_date.tz_localize(None)
                except TypeError:
                    reference_date = reference_date.tz_convert(None)

        # datetime parse
        if 'datetime' in df.columns:
            try:
                if np.issubdtype(df['datetime'].dtype, np.number):
                    df['datetime'] = pd.to_datetime(df['datetime'], unit='s', errors='coerce', utc=True)
                else:
                    df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce', utc=True)
                df['datetime'] = df['datetime'].dt.tz_localize(None)
            except Exception:
                df['datetime'] = pd.NaT

        df = df.dropna(subset=['datetime'])
        if df.empty:
            return SentimentFeatureEngineer._empty_features()

        # Son 3 gün filtre
        cutoff = reference_date - timedelta(days=4)
        df = df[df['datetime'] >= cutoff]
        if df.empty:
            return SentimentFeatureEngineer._empty_features()

        # Gün farkı hesapla
        df['days_ago'] = (reference_date - df['datetime']).dt.days.clip(0, 3)
        df['time_weight'] = df['days_ago'].map(NEWS_TIME_WEIGHTS).fillna(0.0)

        # 3 günden eski haberleri çıkar
        df = df[df['time_weight'] > 0]
        if df.empty:
            return SentimentFeatureEngineer._empty_features()

        # Sentiment skoru
        if 'normalized_score' not in df.columns:
            if 'sentiment_score' in df.columns and 'sentiment' in df.columns:
                df['normalized_score'] = df.apply(
                    lambda r: r['sentiment_score'] if r['sentiment'] == 'positive'
                    else -r['sentiment_score'] if r['sentiment'] == 'negative'
                    else 0.0, axis=1
                )
            else:
                df['normalized_score'] = 0.0

        # --- Feature'lar ---
        # Günlük ortalama sentiment
        daily_avg = df['normalized_score'].mean()

        # Ağırlıklı sentiment skoru
        weighted_scores = df['normalized_score'] * df['time_weight']
        weight_sum = df['time_weight'].sum()
        weighted_sentiment = weighted_scores.sum() / weight_sum if weight_sum > 0 else 0.0

        # Pozitif / negatif haber oranı
        total = len(df)
        pos_count = (df['normalized_score'] > 0.1).sum()
        neg_count = (df['normalized_score'] < -0.1).sum()
        pos_ratio = pos_count / total if total > 0 else 0.0
        neg_ratio = neg_count / total if total > 0 else 0.0

        # Sentiment değişim hızı (delta) - bugün vs dün
        today = df[df['days_ago'] == 0]['normalized_score'].mean()
        yesterday = df[df['days_ago'] == 1]['normalized_score'].mean()
        today = today if not np.isnan(today) else 0.0
        yesterday = yesterday if not np.isnan(yesterday) else 0.0
        sentiment_delta = today - yesterday

        # Lag features: t, t-1, t-2
        lag_t0 = df[df['days_ago'] == 0]['normalized_score'].mean()
        lag_t1 = df[df['days_ago'] == 1]['normalized_score'].mean()
        lag_t2 = df[df['days_ago'] == 2]['normalized_score'].mean()

        return {
            'sent_daily_avg': float(np.nan_to_num(daily_avg)),
            'sent_weighted': float(np.nan_to_num(weighted_sentiment)),
            'sent_pos_ratio': float(pos_ratio),
            'sent_neg_ratio': float(neg_ratio),
            'sent_delta': float(np.nan_to_num(sentiment_delta)),
            'sent_lag_t0': float(np.nan_to_num(lag_t0)),
            'sent_lag_t1': float(np.nan_to_num(lag_t1)),
            'sent_lag_t2': float(np.nan_to_num(lag_t2)),
            'sent_news_count': int(total),
        }

    @staticmethod
    def _empty_features():
        return {
            'sent_daily_avg': 0.0,
            'sent_weighted': 0.0,
            'sent_pos_ratio': 0.0,
            'sent_neg_ratio': 0.0,
            'sent_delta': 0.0,
            'sent_lag_t0': 0.0,
            'sent_lag_t1': 0.0,
            'sent_lag_t2': 0.0,
            'sent_news_count': 0,
        }


class EnsembleStockPredictor:
    """
    10 farklı model ile ensemble borsa tahmin sistemi.
    Her model bağımsız eğitilir, en yüksek confidence score'a sahip modelin tahmini sunulur.
    """

    LABEL_MAP = {0: 'DOWN', 1: 'NEUTRAL', 2: 'UP'}
    INV_LABEL_MAP = {'DOWN': 0, 'NEUTRAL': 1, 'UP': 2}
    # Kullanıcıya gösterilecek Türkçe etiketler
    DISPLAY_LABEL_MAP = {0: 'DÜŞEBİLİR', 1: 'SABİT KALABİLİR', 2: 'YÜKSELEBİLİR'}

    def __init__(self, model_dir='data/models/ensemble'):
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)

        self.models = {}
        self.model_scores = {}  # Her modelin CV skoru
        self.scaler = RobustScaler()
        self.feature_names = []
        self.trained = False
        self.sentiment_engineer = SentimentFeatureEngineer()

    # ─── Teknik Feature'lar ───
    def create_technical_features(self, df):
        def _calc(group_df):
            f = group_df.copy()
            if 'date' in f.columns:
                f = f.sort_values('date')
            if 'close' not in f.columns:
                return f

            f['return_1d'] = f['close'].pct_change(1)
            f['return_3d'] = f['close'].pct_change(3)
            f['return_5d'] = f['close'].pct_change(5)
            f['return_10d'] = f['close'].pct_change(10)
            f['return_20d'] = f['close'].pct_change(20)
            f['log_return'] = np.log(f['close'] / f['close'].shift(1))
            f['log_return_3d'] = np.log(f['close'] / f['close'].shift(3))

            for lag in [1, 2, 3, 5, 10]:
                f[f'close_lag_{lag}'] = f['close'].shift(lag)
                f[f'return_lag_{lag}'] = f['return_1d'].shift(lag)

            # Hareketli ortalamalar
            f['sma_5'] = f['close'].rolling(5).mean()
            f['sma_10'] = f['close'].rolling(10).mean()
            f['sma_20'] = f['close'].rolling(20).mean()
            f['sma_50'] = f['close'].rolling(50).mean()
            f['ema_9'] = f['close'].ewm(span=9).mean()
            f['ema_12'] = f['close'].ewm(span=12).mean()
            f['ema_26'] = f['close'].ewm(span=26).mean()
            f['ema_50'] = f['close'].ewm(span=50).mean()

            f['price_to_sma20'] = (f['close'] - f['sma_20']) / f['sma_20']
            f['price_to_sma50'] = (f['close'] - f['sma_50']) / f['sma_50'].replace(0, np.nan)
            f['sma5_to_sma20'] = (f['sma_5'] - f['sma_20']) / f['sma_20']
            f['sma10_to_sma50'] = (f['sma_10'] - f['sma_50']) / f['sma_50'].replace(0, np.nan)
            f['ema9_to_ema26'] = (f['ema_9'] - f['ema_26']) / f['ema_26'].replace(0, np.nan)

            # Golden/Death cross sinyalleri
            f['golden_cross'] = (f['sma_5'] > f['sma_20']).astype(int)
            f['ema_cross'] = (f['ema_12'] > f['ema_26']).astype(int)

            if 'high' in f.columns and 'low' in f.columns:
                high = f['high']
                low = f['low']
                close = f['close']

                # ATR ve True Range
                prev_close = close.shift(1)
                tr1 = high - low
                tr2 = (high - prev_close).abs()
                tr3 = (low - prev_close).abs()
                f['tr'] = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
                f['atr'] = f['tr'].rolling(14).mean()
                f['atr_pct'] = f['atr'] / close

                # Bollinger Bands
                bb_mid = close.rolling(20).mean()
                bb_std = close.rolling(20).std()
                f['bb_width'] = (4 * bb_std) / bb_mid
                f['bb_position'] = (close - (bb_mid - 2 * bb_std)) / (4 * bb_std)
                f['bb_upper_dist'] = ((bb_mid + 2 * bb_std) - close) / close
                f['bb_lower_dist'] = (close - (bb_mid - 2 * bb_std)) / close

                # Stochastic Oscillator %K ve %D
                low14 = low.rolling(14).min()
                high14 = high.rolling(14).max()
                stoch_range = (high14 - low14).replace(0, np.nan)
                f['stoch_k'] = 100 * (close - low14) / stoch_range
                f['stoch_d'] = f['stoch_k'].rolling(3).mean()
                f['stoch_signal'] = (f['stoch_k'] > f['stoch_d']).astype(int)

                # Williams %R
                f['williams_r'] = -100 * (high14 - close) / stoch_range

                # Commodity Channel Index (CCI)
                tp = (high + low + close) / 3
                tp_sma = tp.rolling(20).mean()
                tp_mad = tp.rolling(20).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)
                f['cci'] = (tp - tp_sma) / (0.015 * tp_mad.replace(0, np.nan))

                # Donchian Channel
                f['donchian_high'] = high.rolling(20).max()
                f['donchian_low'] = low.rolling(20).min()
                donchian_range = (f['donchian_high'] - f['donchian_low']).replace(0, np.nan)
                f['donchian_position'] = (close - f['donchian_low']) / donchian_range

                # High/Low ratios
                f['high_low_ratio'] = (high - low) / close
                f['close_to_high'] = (high - close) / (high - low).replace(0, np.nan)

            delta = f['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            f['rsi'] = 100 - (100 / (1 + rs))
            f['rsi_overbought'] = (f['rsi'] > 70).astype(int)
            f['rsi_oversold'] = (f['rsi'] < 30).astype(int)

            # RSI farklı periyotlar
            gain9 = delta.where(delta > 0, 0).rolling(9).mean()
            loss9 = (-delta.where(delta < 0, 0)).rolling(9).mean()
            f['rsi_9'] = 100 - (100 / (1 + gain9 / loss9.replace(0, np.nan)))

            f['macd'] = f['ema_12'] - f['ema_26']
            f['macd_signal'] = f['macd'].ewm(span=9).mean()
            f['macd_hist'] = f['macd'] - f['macd_signal']
            f['macd_cross'] = (f['macd'] > f['macd_signal']).astype(int)

            # Momentum
            f['momentum_5'] = f['close'] / f['close'].shift(5) - 1
            f['momentum_10'] = f['close'] / f['close'].shift(10) - 1
            f['momentum_20'] = f['close'] / f['close'].shift(20) - 1

            # Rate of Change
            f['roc_5'] = f['close'].pct_change(5) * 100
            f['roc_10'] = f['close'].pct_change(10) * 100

            # Volatilite
            f['volatility_10'] = f['return_1d'].rolling(10).std()
            f['volatility_20'] = f['return_1d'].rolling(20).std()

            if 'volume' in f.columns:
                f['volume_ma'] = f['volume'].rolling(20).mean()
                f['volume_ratio'] = f['volume'] / f['volume_ma'].replace(0, np.nan)
                f['volume_ma5'] = f['volume'].rolling(5).mean()
                f['volume_trend'] = f['volume_ma5'] / f['volume_ma'].replace(0, np.nan)

                # OBV (On-Balance Volume)
                obv = [0]
                closes = f['close'].values
                volumes = f['volume'].values
                for i in range(1, len(closes)):
                    if closes[i] > closes[i - 1]:
                        obv.append(obv[-1] + volumes[i])
                    elif closes[i] < closes[i - 1]:
                        obv.append(obv[-1] - volumes[i])
                    else:
                        obv.append(obv[-1])
                f['obv'] = obv
                f['obv_pct'] = pd.Series(obv).pct_change(5).values

                # Price-Volume Trend
                f['pvt'] = (f['return_1d'] * f['volume']).cumsum()

            return f

        base = df.copy()
        if 'symbol' in base.columns:
            parts = [_calc(g) for _, g in base.groupby('symbol', sort=False)]
            return pd.concat(parts, axis=0).sort_index()
        return _calc(base)

    # ─── Label ───
    def create_labels(self, df, threshold=0.02):
        if 'symbol' in df.columns:
            future_close = df.groupby('symbol')['close'].shift(-1)
            future_ret = future_close / df['close'] - 1
        else:
            future_ret = df['close'].shift(-1) / df['close'] - 1
        labels = pd.Series(1, index=df.index)  # NEUTRAL default
        labels[future_ret > threshold] = 2   # UP
        labels[future_ret < -threshold] = 0  # DOWN
        return labels

    # ─── Sentiment Feature'ları DataFrame'e ekle ───
    def add_sentiment_features_to_df(self, df, news_df=None, symbol=None):
        """Her satır için (tarih bazlı) sentiment feature hesaplar"""
        sent_cols = list(SentimentFeatureEngineer._empty_features().keys())
        for c in sent_cols:
            df[c] = 0.0

        if news_df is None or news_df.empty or 'date' not in df.columns:
            return df

        for idx in df.index:
            row_date = df.loc[idx, 'date']
            row_symbol = symbol
            if row_symbol is None and 'symbol' in df.columns:
                row_symbol = df.loc[idx, 'symbol']
            try:
                ref_date = pd.to_datetime(row_date)
            except Exception:
                continue
            feats = SentimentFeatureEngineer.compute_time_weighted_sentiment(
                news_df, row_symbol, reference_date=ref_date
            )
            for k, v in feats.items():
                df.loc[idx, k] = v

        return df

    # ─── Feature seçimi ───
    def _select_feature_cols(self, df):
        exclude = {
            'open', 'high', 'low', 'close', 'volume', 'Date', 'date', 'symbol',
            'tr', 'ema_12', 'ema_26', 'sma_5', 'sma_10', 'sma_20',
            'bb_middle', 'bb_upper', 'bb_lower', 'volume_ma',
        }
        return [c for c in df.columns if c not in exclude and df[c].dtype in ['float64', 'float32', 'int64', 'int32']]

    # ─── Sentiment etkisini %1-5 ile sınırla ───
    def _cap_sentiment_features(self, X, feature_names):
        """Sentiment feature'ların toplam etkisini SENTIMENT_WEIGHT_CAP ile sınırla"""
        sent_cols = [c for c in feature_names if c.startswith('sent_')]
        if not sent_cols:
            return X

        sent_indices = [feature_names.index(c) for c in sent_cols]
        tech_indices = [i for i in range(len(feature_names)) if i not in sent_indices]

        if isinstance(X, pd.DataFrame):
            X_arr = X.values.copy()
        else:
            X_arr = X.copy()

        # Sentiment sütunlarını kap ağırlığı ile ölçekle
        # Toplam varyans oranını sınırla
        tech_std = np.std(X_arr[:, tech_indices], axis=0).mean() if tech_indices else 1.0
        sent_std = np.std(X_arr[:, sent_indices], axis=0).mean() if sent_indices else 1.0

        if sent_std > 0 and tech_std > 0:
            desired_ratio = SENTIMENT_WEIGHT_CAP / (1 - SENTIMENT_WEIGHT_CAP)
            current_ratio = sent_std / tech_std
            if current_ratio > desired_ratio:
                scale_factor = desired_ratio / current_ratio
                X_arr[:, sent_indices] *= scale_factor

        return X_arr

    # ─── Model Tanımları ───
    def _build_models(self, class_weights):
        models = {}

        # --- Ağaç Tabanlı Modeller ---
        models['random_forest'] = RandomForestClassifier(
            n_estimators=500, max_depth=14, min_samples_leaf=2, class_weight=class_weights,
            random_state=42, n_jobs=-1
        )
        models['extra_trees'] = ExtraTreesClassifier(
            n_estimators=500, max_depth=14, min_samples_leaf=2, class_weight=class_weights,
            random_state=42, n_jobs=-1
        )
        models['gradient_boosting'] = GradientBoostingClassifier(
            n_estimators=300, max_depth=5, learning_rate=0.05,
            subsample=0.8, random_state=42
        )
        models['hist_gradient_boosting'] = HistGradientBoostingClassifier(
            max_iter=300, max_depth=8, learning_rate=0.05,
            random_state=42
        )
        models['ada_boost'] = AdaBoostClassifier(
            n_estimators=200, learning_rate=0.1, random_state=42
        )
        models['bagging'] = BaggingClassifier(
            n_estimators=200, max_samples=0.8, max_features=0.8,
            random_state=42, n_jobs=-1
        )

        # --- Doğrusal / İstatistiksel Modeller ---
        models['logistic_regression'] = LogisticRegression(
            max_iter=1000, class_weight=class_weights, C=1.0,
            random_state=42
        )
        models['lda'] = LinearDiscriminantAnalysis()
        models['naive_bayes'] = GaussianNB()

        # --- Kernel / Instance Tabanlı ---
        models['svm'] = SVC(
            kernel='rbf', probability=True, class_weight=class_weights,
            C=1.5, gamma='scale', random_state=42
        )
        models['knn'] = KNeighborsClassifier(
            n_neighbors=7, weights='distance', n_jobs=-1
        )

        # --- Sinir Ağı (sklearn MLP) ---
        models['mlp'] = MLPClassifier(
            hidden_layer_sizes=(128, 64, 32), max_iter=500,
            early_stopping=True, validation_fraction=0.15,
            random_state=42, learning_rate='adaptive'
        )

        if HAS_XGB:
            models['xgboost'] = xgb.XGBClassifier(
                n_estimators=400, max_depth=6, learning_rate=0.04,
                subsample=0.8, colsample_bytree=0.8,
                objective='multi:softmax', num_class=3,
                eval_metric='mlogloss', random_state=42, verbosity=0
            )
        if HAS_LGBM:
            models['lightgbm'] = LGBMClassifier(
                n_estimators=400, max_depth=7, learning_rate=0.04,
                subsample=0.8, colsample_bytree=0.8,
                class_weight=class_weights, random_state=42, verbose=-1
            )
        if HAS_CATBOOST:
            cb_weights = [class_weights.get(i, 1.0) for i in range(3)] if isinstance(class_weights, dict) else None
            models['catboost'] = CatBoostClassifier(
                iterations=400, depth=7, learning_rate=0.04,
                class_weights=cb_weights,
                random_seed=42, verbose=0
            )

        return models

    def _build_lstm_model(self, input_shape, num_classes=3):
        if not HAS_TF:
            return None
        model = Sequential([
            LSTM(64, input_shape=input_shape, return_sequences=True),
            Dropout(0.3),
            LSTM(32),
            Dropout(0.3),
            Dense(num_classes, activation='softmax')
        ])
        model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
        return model

    def _build_gru_model(self, input_shape, num_classes=3):
        if not HAS_TF:
            return None
        model = Sequential([
            GRU(64, input_shape=input_shape, return_sequences=True),
            Dropout(0.3),
            GRU(32),
            Dropout(0.3),
            Dense(num_classes, activation='softmax')
        ])
        model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
        return model

    # ─── LSTM/GRU için sekans verisi oluştur ───
    def _create_sequences(self, X, y, seq_len=SEQUENCE_LENGTH):
        Xs, ys = [], []
        for i in range(seq_len, len(X)):
            Xs.append(X[i - seq_len:i])
            ys.append(y[i])
        return np.array(Xs), np.array(ys)

    # ─── EĞİTİM ───
    def train(self, df, news_df=None, symbol=None, threshold=0.02, n_splits=5):
        print("\n" + "=" * 60)
        print("🚀 Ensemble ML Eğitim Pipeline Başlatılıyor (10 Model)")
        print("=" * 60)

        # Feature engineering
        df_feat = self.create_technical_features(df)
        if news_df is not None:
            print("📰 Sentiment feature'lar ekleniyor (zaman bazlı, %1-5 sınırlı)...")
            df_feat = self.add_sentiment_features_to_df(df_feat, news_df, symbol)

        # Labels
        y_all = self.create_labels(df_feat, threshold)

        # Feature columns
        feature_cols = self._select_feature_cols(df_feat)
        self.feature_names = feature_cols
        X_all = df_feat[feature_cols]

        # NaN temizle
        valid = ~(X_all.isna().any(axis=1) | y_all.isna())
        X_all = X_all[valid].reset_index(drop=True)
        y_all = y_all[valid].reset_index(drop=True)

        print(f"✅ {len(feature_cols)} feature, {len(X_all)} örnek")
        print(f"📊 Label dağılımı: {dict(y_all.value_counts().sort_index())}")

        # Sentiment cap
        X_capped = self._cap_sentiment_features(X_all, feature_cols)

        # Class weights
        counts = y_all.value_counts()
        total = len(y_all)
        class_weights = {int(c): total / (len(counts) * cnt) for c, cnt in counts.items()}
        print(f"⚖️ Class weights: {class_weights}")

        # Time-series CV
        tscv = TimeSeriesSplit(n_splits=n_splits)

        # Scale
        X_scaled = self.scaler.fit_transform(X_capped)

        # ── Sklearn Modelleri Eğit ──
        sklearn_models = self._build_models(class_weights)
        model_results = {}

        for name, model in sklearn_models.items():
            print(f"\n🔧 Eğitiliyor: {name}")
            fold_scores = []

            for fold, (train_idx, val_idx) in enumerate(tscv.split(X_scaled)):
                X_tr, X_val = X_scaled[train_idx], X_scaled[val_idx]
                y_tr, y_val = y_all.iloc[train_idx].values, y_all.iloc[val_idx].values

                model.fit(X_tr, y_tr)
                y_pred = model.predict(X_val)
                score = f1_score(y_val, y_pred, average='weighted')
                fold_scores.append(score)

            avg_f1 = np.mean(fold_scores)
            std_f1 = np.std(fold_scores)
            print(f"  ✅ {name}: F1={avg_f1:.4f} (±{std_f1:.4f})")

            # Final eğitim (tüm veri)
            model.fit(X_scaled, y_all.values)
            self.models[name] = model
            model_results[name] = {
                'f1_mean': avg_f1, 'f1_std': std_f1,
                'type': 'sklearn'
            }

        # ── LSTM Eğit ──
        if HAS_TF and len(X_scaled) > SEQUENCE_LENGTH + 20:
            for dl_name, builder in [('lstm', self._build_lstm_model), ('gru', self._build_gru_model)]:
                print(f"\n🔧 Eğitiliyor: {dl_name}")
                try:
                    X_seq, y_seq = self._create_sequences(X_scaled, y_all.values)
                    if len(X_seq) < 30:
                        print(f"  ⚠️ {dl_name}: Yetersiz sekans verisi, atlanıyor")
                        continue

                    fold_scores = []
                    n_dl_splits = min(3, n_splits)
                    tscv_dl = TimeSeriesSplit(n_splits=n_dl_splits)

                    for fold, (train_idx, val_idx) in enumerate(tscv_dl.split(X_seq)):
                        X_tr, X_val = X_seq[train_idx], X_seq[val_idx]
                        y_tr, y_val = y_seq[train_idx], y_seq[val_idx]

                        dl_model = builder((X_tr.shape[1], X_tr.shape[2]))
                        if dl_model is None:
                            break
                        es = EarlyStopping(patience=5, restore_best_weights=True, verbose=0)
                        dl_model.fit(X_tr, y_tr, epochs=80, batch_size=16,
                                     validation_data=(X_val, y_val),
                                     callbacks=[es], verbose=0)
                        y_pred = np.argmax(dl_model.predict(X_val, verbose=0), axis=1)
                        score = f1_score(y_val, y_pred, average='weighted')
                        fold_scores.append(score)

                    if fold_scores:
                        avg_f1 = np.mean(fold_scores)
                        std_f1 = np.std(fold_scores)
                        print(f"  ✅ {dl_name}: F1={avg_f1:.4f} (±{std_f1:.4f})")

                        # Final eğitim
                        final_model = builder((X_seq.shape[1], X_seq.shape[2]))
                        if final_model:
                            es = EarlyStopping(patience=5, restore_best_weights=True, verbose=0)
                            final_model.fit(X_seq, y_seq, epochs=80, batch_size=16,
                                            callbacks=[es], verbose=0)
                            self.models[dl_name] = final_model
                            model_results[dl_name] = {
                                'f1_mean': avg_f1, 'f1_std': std_f1,
                                'type': 'deep_learning'
                            }
                except Exception as e:
                    print(f"  ❌ {dl_name} hatası: {e}")

        # Sonuçları kaydet
        self.model_scores = model_results
        self.trained = True

        # Özet
        print(f"\n{'=' * 60}")
        print(f"📊 MODEL SONUÇLARI ({len(self.models)} model eğitildi)")
        print(f"{'=' * 60}")
        sorted_models = sorted(model_results.items(), key=lambda x: x[1]['f1_mean'], reverse=True)
        for rank, (name, info) in enumerate(sorted_models, 1):
            marker = "🏆" if rank == 1 else f"  {rank}."
            print(f"  {marker} {name}: F1={info['f1_mean']:.4f} (±{info['f1_std']:.4f})")

        best_name = sorted_models[0][0] if sorted_models else None
        print(f"\n🏆 En iyi model: {best_name}")

        self.save_models()
        return model_results

    # ─── TAHMİN ───
    def predict(self, df, news_df=None, symbol=None):
        if not self.trained and not self.models:
            raise ValueError("Model eğitilmemiş! Önce train() çağırın veya load_models() yapın.")

        # Kolon isimlerini normalize et
        df = df.copy()
        df.columns = [c.lower() for c in df.columns]

        # Feature'lar
        df_feat = self.create_technical_features(df)
        if news_df is not None and symbol:
            df_feat = self.add_sentiment_features_to_df(df_feat, news_df, symbol)

        feature_cols = self.feature_names
        available_cols = [c for c in feature_cols if c in df_feat.columns]
        missing_cols = [c for c in feature_cols if c not in df_feat.columns]
        for mc in missing_cols:
            df_feat[mc] = 0.0

        X_last = df_feat[feature_cols].tail(1)
        if X_last.isna().any().any():
            X_last = X_last.ffill().fillna(0)

        X_capped = self._cap_sentiment_features(X_last, feature_cols)
        X_scaled = self.scaler.transform(X_capped)

        # Her model için tahmin + confidence
        all_predictions = {}

        for name, model in self.models.items():
            try:
                model_info = self.model_scores.get(name, {})
                model_type = model_info.get('type', 'sklearn')

                if model_type == 'deep_learning':
                    # LSTM/GRU: son SEQUENCE_LENGTH satır gerekli
                    X_full = df_feat[feature_cols].tail(SEQUENCE_LENGTH + 1)
                    if X_full.isna().any().any():
                        X_full = X_full.ffill().fillna(0)
                    X_full_capped = self._cap_sentiment_features(X_full, feature_cols)
                    X_full_scaled = self.scaler.transform(X_full_capped)

                    if len(X_full_scaled) >= SEQUENCE_LENGTH:
                        X_seq = X_full_scaled[-SEQUENCE_LENGTH:].reshape(1, SEQUENCE_LENGTH, -1)
                        probs = model.predict(X_seq, verbose=0)[0]
                        pred = int(np.argmax(probs))
                        confidence = float(np.max(probs))
                    else:
                        continue
                else:
                    pred = int(model.predict(X_scaled)[0])
                    if hasattr(model, 'predict_proba'):
                        probs = model.predict_proba(X_scaled)[0]
                        confidence = float(np.max(probs))
                    else:
                        probs = None
                        confidence = model_info.get('f1_mean', 0.5)

                # Backtest F1 skoru ile ağırlıklandır
                backtest_f1 = model_info.get('f1_mean', 0.5)
                combined_confidence = 0.6 * confidence + 0.4 * backtest_f1

                all_predictions[name] = {
                    'prediction': int(pred),
                    'prediction_label': self.LABEL_MAP[pred],
                    'raw_confidence': float(confidence),
                    'backtest_f1': float(backtest_f1),
                    'combined_confidence': float(combined_confidence),
                    'probabilities': {
                        self.LABEL_MAP[i]: float(probs[i]) for i in range(len(probs))
                    } if probs is not None else None,
                }

            except Exception as e:
                print(f"⚠️ {name} tahmin hatası: {e}")
                continue

        if not all_predictions:
            raise ValueError("Hiçbir model tahmin yapamadı!")

        # En yüksek combined_confidence modeli seç
        best_model_name = max(
            all_predictions, key=lambda k: all_predictions[k]['combined_confidence']
        )
        best = all_predictions[best_model_name]

        best_numeric = best['prediction']
        display_label = self.DISPLAY_LABEL_MAP.get(best_numeric, self.LABEL_MAP.get(best_numeric, 'SABİT KALABİLİR'))

        result = {
            'prediction': best['prediction_label'],
            'prediction_display': display_label,
            'prediction_numeric': best_numeric,
            'confidence': best['combined_confidence'],
            'best_model': best_model_name,
            'best_model_backtest_f1': best['backtest_f1'],
            'probabilities': best['probabilities'] or {
                'DOWN': 0.33, 'NEUTRAL': 0.33, 'UP': 0.33
            },
            'all_models': {
                name: {
                    'prediction': info['prediction_label'],
                    'prediction_display': self.DISPLAY_LABEL_MAP.get(info['prediction'], info['prediction_label']),
                    'confidence': round(info['combined_confidence'], 4),
                    'backtest_f1': round(info['backtest_f1'], 4),
                }
                for name, info in sorted(
                    all_predictions.items(),
                    key=lambda x: x[1]['combined_confidence'],
                    reverse=True
                )
            },
            'total_models': len(all_predictions),
            'sentiment_impact': f'{SENTIMENT_WEIGHT_CAP * 100:.1f}%',
            'method': 'ensemble',
            'disclaimer': 'Bu analiz istatistiksel bir tahmindir ve kesin fiyat yönü garanti edilemez. Yatırım tavsiyesi değildir.',
            'timestamp': datetime.now().isoformat(),
        }

        return result

    # ─── Kaydet / Yükle ───
    def save_models(self):
        sklearn_models = {k: v for k, v in self.models.items()
                         if self.model_scores.get(k, {}).get('type') != 'deep_learning'}
        dl_models = {k: v for k, v in self.models.items()
                     if self.model_scores.get(k, {}).get('type') == 'deep_learning'}

        joblib.dump(sklearn_models, os.path.join(self.model_dir, 'ensemble_sklearn.joblib'))
        joblib.dump(self.scaler, os.path.join(self.model_dir, 'ensemble_scaler.joblib'))
        joblib.dump(self.feature_names, os.path.join(self.model_dir, 'ensemble_features.joblib'))
        joblib.dump(self.model_scores, os.path.join(self.model_dir, 'ensemble_scores.joblib'))

        for name, model in dl_models.items():
            try:
                model.save(os.path.join(self.model_dir, f'{name}_model.keras'))
            except Exception as e:
                print(f"⚠️ {name} kaydedilemedi: {e}")

        print(f"💾 {len(self.models)} model kaydedildi: {self.model_dir}")

    def load_models(self):
        try:
            sklearn_path = os.path.join(self.model_dir, 'ensemble_sklearn.joblib')
            if not os.path.exists(sklearn_path):
                return False

            self.models = joblib.load(sklearn_path)
            self.scaler = joblib.load(os.path.join(self.model_dir, 'ensemble_scaler.joblib'))
            self.feature_names = joblib.load(os.path.join(self.model_dir, 'ensemble_features.joblib'))
            self.model_scores = joblib.load(os.path.join(self.model_dir, 'ensemble_scores.joblib'))

            # DL modelleri yükle
            if HAS_TF:
                for dl_name in ['lstm', 'gru']:
                    dl_path = os.path.join(self.model_dir, f'{dl_name}_model.keras')
                    if os.path.exists(dl_path):
                        try:
                            from tensorflow.keras.models import load_model
                            self.models[dl_name] = load_model(dl_path)
                            print(f"  ✅ {dl_name} yüklendi")
                        except Exception as e:
                            print(f"  ⚠️ {dl_name} yüklenemedi: {e}")

            self.trained = True
            print(f"✅ {len(self.models)} model yüklendi: {self.model_dir}")
            return True
        except Exception as e:
            print(f"❌ Model yükleme hatası: {e}")
            return False
