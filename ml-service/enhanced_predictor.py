"""
Production-Ready Financial Time Series Prediction Pipeline
Follows best practices: no data leakage, proper time-series validation, ensemble models
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import classification_report, f1_score, precision_score, recall_score
try:
    import xgboost as xgb
    HAS_XGB = True
except:
    HAS_XGB = False
    print("⚠️ XGBoost not available")

try:
    from lightgbm import LGBMClassifier
    HAS_LGBM = True
except:
    HAS_LGBM = False
    print("⚠️ LightGBM not available")

try:
    from catboost import CatBoostClassifier
    HAS_CATBOOST = True
except:
    HAS_CATBOOST = False
    print("⚠️ CatBoost not available")

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
import joblib
import os
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class EnhancedStockPredictor:
    """
    Production-ready stock price direction predictor
    - Classification: UP/DOWN/NEUTRAL
    - No data leakage
    - Time-series aware validation
    - Ensemble of tree-based models
    - Feature importance tracking
    """
    
    def __init__(self, model_dir='data/models'):
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        
        # Ensemble models
        self.models = {}
        self.scaler = RobustScaler()  # More robust to outliers
        self.feature_names = []
        self.trained = False
        
    def create_technical_features(self, df):
        """
        Create technical indicator features WITHOUT data leakage
        All features use only past data (t and before)
        """
        features = df.copy()
        
        # Price-based features
        if 'close' in features.columns:
            # Returns (safe - no future leak)
            features['return_1d'] = features['close'].pct_change(1)
            features['return_3d'] = features['close'].pct_change(3)
            features['return_5d'] = features['close'].pct_change(5)
            features['log_return'] = np.log(features['close'] / features['close'].shift(1))
            
            # Lag features
            for lag in [1, 3, 5]:
                features[f'close_lag_{lag}'] = features['close'].shift(lag)
                features[f'return_lag_{lag}'] = features['return_1d'].shift(lag)
            
            # Moving averages
            features['sma_5'] = features['close'].rolling(5).mean()
            features['sma_10'] = features['close'].rolling(10).mean()
            features['sma_20'] = features['close'].rolling(20).mean()
            features['ema_12'] = features['close'].ewm(span=12).mean()
            features['ema_26'] = features['close'].ewm(span=26).mean()
            
            # Price position relative to MAs
            features['price_to_sma20'] = (features['close'] - features['sma_20']) / features['sma_20']
            features['sma5_to_sma20'] = (features['sma_5'] - features['sma_20']) / features['sma_20']
            
        # Volatility features
        if 'high' in features.columns and 'low' in features.columns:
            # ATR (Average True Range)
            features['tr'] = features[['high', 'low']].max(axis=1) - features[['high', 'low']].min(axis=1)
            features['atr'] = features['tr'].rolling(14).mean()
            features['atr_pct'] = features['atr'] / features['close']
            
            # Bollinger Bands
            features['bb_middle'] = features['close'].rolling(20).mean()
            bb_std = features['close'].rolling(20).std()
            features['bb_upper'] = features['bb_middle'] + (2 * bb_std)
            features['bb_lower'] = features['bb_middle'] - (2 * bb_std)
            features['bb_width'] = (features['bb_upper'] - features['bb_lower']) / features['bb_middle']
            features['bb_position'] = (features['close'] - features['bb_lower']) / (features['bb_upper'] - features['bb_lower'])
            
        # Momentum indicators
        if 'close' in features.columns:
            # RSI
            delta = features['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            features['rsi'] = 100 - (100 / (1 + rs))
            
            # MACD
            features['macd'] = features['ema_12'] - features['ema_26']
            features['macd_signal'] = features['macd'].ewm(span=9).mean()
            features['macd_hist'] = features['macd'] - features['macd_signal']
            
        # Volume features
        if 'volume' in features.columns:
            features['volume_ma'] = features['volume'].rolling(20).mean()
            features['volume_ratio'] = features['volume'] / features['volume_ma']
            features['volume_lag_1'] = features['volume'].shift(1)
            
        return features
    
    def create_labels(self, df, threshold=0.02):
        """
        Create classification labels: UP/DOWN/NEUTRAL
        Based on FUTURE returns (but used carefully to avoid leakage)
        
        threshold: minimum return to be considered UP or DOWN (default 2%)
        """
        # Future return (this is what we're trying to predict)
        future_return = df['close'].shift(-1) / df['close'] - 1
        
        labels = pd.Series('NEUTRAL', index=df.index)
        labels[future_return > threshold] = 'UP'
        labels[future_return < -threshold] = 'DOWN'
        
        # Convert to numeric
        label_map = {'DOWN': 0, 'NEUTRAL': 1, 'UP': 2}
        numeric_labels = labels.map(label_map)
        
        return numeric_labels, labels
    
    def prepare_train_data(self, df, threshold=0.02):
        """
        Prepare training data with proper feature engineering
        """
        print("📊 Creating features...")
        df_features = self.create_technical_features(df)
        
        print("🎯 Creating labels...")
        numeric_labels, text_labels = self.create_labels(df_features, threshold)
        
        # Select features (exclude raw OHLCV and intermediate calculations)
        feature_cols = [col for col in df_features.columns if col not in 
                       ['open', 'high', 'low', 'close', 'volume', 'Date', 'date', 'symbol',
                        'tr', 'bb_middle', 'bb_upper', 'bb_lower', 'ema_12', 'ema_26']]
        
        X = df_features[feature_cols]
        y = numeric_labels
        
        # Remove rows with NaN (from rolling calculations)
        valid_idx = ~(X.isna().any(axis=1) | y.isna())
        X = X[valid_idx]
        y = y[valid_idx]
        
        self.feature_names = feature_cols
        
        print(f"✅ Features created: {len(feature_cols)} features, {len(X)} samples")
        print(f"📈 Label distribution:\n{pd.Series(y).value_counts()}")
        
        return X, y
    
    def train(self, df, threshold=0.02, n_splits=5):
        """
        Train ensemble of models with time-series cross-validation
        """
        print("\n" + "="*50)
        print("🚀 Starting Enhanced ML Training Pipeline")
        print("="*50)
        
        # Prepare data
        X, y = self.prepare_train_data(df, threshold)
        
        # Time-series split (NO random shuffle!)
        tscv = TimeSeriesSplit(n_splits=n_splits)
        
        # Calculate class weights for imbalance
        class_counts = pd.Series(y).value_counts()
        total = len(y)
        class_weights = {cls: total / (len(class_counts) * count) 
                        for cls, count in class_counts.items()}
        
        print(f"\n⚖️ Class weights: {class_weights}")
        
        # Initialize models
        models_config = {}
        
        if HAS_XGB:
            models_config['xgboost'] = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                objective='multi:softmax',
                num_class=3,
                eval_metric='mlogloss',
                random_state=42
            )
        
        if HAS_LGBM:
            models_config['lightgbm'] = LGBMClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                class_weight=class_weights,
                random_state=42,
                verbose=-1
            )
        
        if HAS_CATBOOST:
            models_config['catboost'] = CatBoostClassifier(
                iterations=100,
                depth=5,
                learning_rate=0.1,
                class_weights=list(class_weights.values()),
                random_seed=42,
                verbose=0
            )
        
        # Fallback to sklearn models if advanced models not available
        if not models_config:
            print("⚠️ Using fallback sklearn models")
            models_config['random_forest'] = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                class_weight=class_weights,
                random_state=42
            )
            models_config['gradient_boost'] = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
        
        # Train each model with time-series CV
        best_scores = {}
        
        for name, model in models_config.items():
            print(f"\n🔧 Training {name}...")
            scores = []
            
            for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
                X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
                y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
                
                # Scale features
                X_train_scaled = self.scaler.fit_transform(X_train)
                X_val_scaled = self.scaler.transform(X_val)
                
                # Train
                model.fit(X_train_scaled, y_train)
                
                # Evaluate
                y_pred = model.predict(X_val_scaled)
                f1 = f1_score(y_val, y_pred, average='weighted')
                scores.append(f1)
                
                print(f"  Fold {fold+1}: F1={f1:.4f}")
            
            avg_score = np.mean(scores)
            best_scores[name] = avg_score
            print(f"✅ {name} average F1: {avg_score:.4f}")
            
            # Final training on all data
            X_scaled = self.scaler.fit_transform(X)
            model.fit(X_scaled, y)
            self.models[name] = model
        
        # Select best model
        best_model_name = max(best_scores, key=best_scores.get)
        print(f"\n🏆 Best model: {best_model_name} (F1={best_scores[best_model_name]:.4f})")
        
        self.trained = True
        self.save_models()
        
        return best_scores
    
    def predict(self, df, return_probabilities=False):
        """
        Make prediction with ensemble voting
        Returns: prediction, probability, confidence
        """
        if not self.trained and not self.models:
            raise ValueError("Model not trained! Call train() first or load_models()")
        
        # Create features
        df_features = self.create_technical_features(df)
        X = df_features[self.feature_names].tail(1)
        
        # Handle NaN
        if X.isna().any().any():
            print("⚠️ Warning: NaN values in features, using last valid values")
            X = X.fillna(method='ffill').fillna(method='bfill')
        
        X_scaled = self.scaler.transform(X)
        
        # Ensemble prediction (voting)
        predictions = []
        probabilities = []
        
        for name, model in self.models.items():
            try:
                pred = model.predict(X_scaled)
                if isinstance(pred, np.ndarray):
                    pred = pred[0]
                predictions.append(int(pred))
                
                if hasattr(model, 'predict_proba'):
                    prob = model.predict_proba(X_scaled)
                    if isinstance(prob, np.ndarray) and len(prob.shape) == 2:
                        prob = prob[0]
                    probabilities.append(prob)
            except Exception as e:
                print(f"⚠️ Error with model {name}: {e}")
                continue
        
        if not predictions:
            raise ValueError("No models could make predictions")
        
        # Majority voting
        predictions_array = np.array(predictions, dtype=int)
        final_prediction = int(np.bincount(predictions_array).argmax())
        
        # Average probabilities
        avg_probabilities = np.mean(probabilities, axis=0) if probabilities else None
        confidence = np.max(avg_probabilities) if avg_probabilities is not None else 0.0
        
        # Convert to text
        label_map = {0: 'DOWN', 1: 'NEUTRAL', 2: 'UP'}
        prediction_text = label_map[final_prediction]
        
        result = {
            'prediction': prediction_text,
            'prediction_numeric': final_prediction,
            'confidence': float(confidence),
            'probabilities': {
                'DOWN': float(avg_probabilities[0]) if avg_probabilities is not None else 0.33,
                'NEUTRAL': float(avg_probabilities[1]) if avg_probabilities is not None else 0.33,
                'UP': float(avg_probabilities[2]) if avg_probabilities is not None else 0.33
            } if avg_probabilities is not None else None,
            'disclaimer': 'Bu istatistiksel bir tahmindir, yatırım tavsiyesi DEĞİLDİR'
        }
        
        return result
    
    def save_models(self):
        """Save all trained models"""
        joblib.dump(self.models, os.path.join(self.model_dir, 'ensemble_models.joblib'))
        joblib.dump(self.scaler, os.path.join(self.model_dir, 'enhanced_scaler.joblib'))
        joblib.dump(self.feature_names, os.path.join(self.model_dir, 'enhanced_features.joblib'))
        print(f"💾 Models saved to {self.model_dir}")
    
    def load_models(self):
        """Load trained models"""
        try:
            self.models = joblib.load(os.path.join(self.model_dir, 'ensemble_models.joblib'))
            self.scaler = joblib.load(os.path.join(self.model_dir, 'enhanced_scaler.joblib'))
            self.feature_names = joblib.load(os.path.join(self.model_dir, 'enhanced_features.joblib'))
            self.trained = True
            print(f"✅ Models loaded from {self.model_dir}")
            return True
        except Exception as e:
            print(f"❌ Error loading models: {e}")
            return False
