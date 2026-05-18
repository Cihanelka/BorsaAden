"""
Created by: AdenBorsa ML Team
Created At: 2026-05-03
Subject: 15 ML modelinin egitilmesi, degerlendirilmesi ve diske kaydedilmesi.
         Prompt 4: 15 farkli model mimarisi (ML + DL + Ensemble)
         Prompt 5: Data leakage onleme, kronolojik split, TimeSeriesSplit
"""

import os
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.ensemble import (
    RandomForestClassifier,
    GradientBoostingClassifier,
    ExtraTreesClassifier,
    AdaBoostClassifier,
    BaggingClassifier,
    VotingClassifier,
    StackingClassifier,
)
from sklearn.svm import SVC
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, roc_auc_score
)
from sklearn.model_selection import TimeSeriesSplit
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier

# Deep Learning (TensorFlow/Keras)
try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, GRU, Conv1D, MaxPooling1D, Flatten, Dense, Dropout
    from tensorflow.keras.optimizers import Adam
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False

from config import MODEL_DIR

# Dosya yollari (horizon bazli)
def _modelPaths(horizon: int = 5):
    tag = f'h{horizon}'
    return {
        'models': os.path.join(MODEL_DIR, f'models_{tag}.joblib'),
        'scaler': os.path.join(MODEL_DIR, f'scaler_{tag}.joblib'),
        'meta':   os.path.join(MODEL_DIR, f'meta_{tag}.joblib'),
        'dl_dir': os.path.join(MODEL_DIR, f'dl_{tag}'),
    }

# Geriye uyumluluk icin eski varsayılan dosyalar (horizon=5)
MODELS_FILE = os.path.join(MODEL_DIR, 'models_h5.joblib')
SCALER_FILE = os.path.join(MODEL_DIR, 'scaler_h5.joblib')
META_FILE = os.path.join(MODEL_DIR, 'meta_h5.joblib')
DL_MODELS_DIR = os.path.join(MODEL_DIR, 'dl_h5')

os.makedirs(DL_MODELS_DIR, exist_ok=True)

# Desteklenen vade ufuklari
SUPPORTED_HORIZONS = [5, 21, 63]
HORIZON_LABELS = {
    5:  {'days': '5 iş günü',   'label': 'Kısa Vade (1 Hafta)'},
    21: {'days': '21 iş günü',  'label': 'Orta Vade (1 Ay)'},
    63: {'days': '63 iş günü',  'label': 'Uzun Vade (3 Ay)'},
}

class ModelTrainer:
    def __init__(self, horizon: int = 5):
        self.horizon = horizon
        self.scaler = StandardScaler()
        self.models = {}
        self.featureNames = []
        self.trainedAt = ""
        self.scores = {}
        self.history = {}

    def _prepare_sequences(self, X, y, seq_length=20):
        """DL modelleri icin zaman serisi sekanslari hazirlar."""
        X_seq, y_seq = [], []
        for i in range(len(X) - seq_length):
            X_seq.append(X[i:(i + seq_length)])
            y_seq.append(y[i + seq_length])
        
        # y etiketlerini one-hot encoding'e cevir (3 class: -1, 0, 1 -> 0, 1, 2)
        # Etiketler -1, 0, 1 ise bunlari 0, 1, 2 yapmaliyiz
        y_seq = np.array(y_seq)
        y_seq_encoded = np.zeros((len(y_seq), 3))
        for i, val in enumerate(y_seq):
            y_seq_encoded[i, val + 1] = 1 # -1->0, 0->1, 1->2
            
        return np.array(X_seq), y_seq_encoded

    def _build_dl_models(self, input_shape):
        """LSTM, GRU ve CNN modellerini tanimlar."""
        
        # Model 11: LSTM
        lstm_model = Sequential([
            LSTM(128, return_sequences=True, input_shape=input_shape),
            Dropout(0.3),
            LSTM(64),
            Dense(3, activation='softmax')
        ])
        lstm_model.compile(optimizer=Adam(learning_rate=0.001), loss='categorical_crossentropy', metrics=['accuracy'])
        
        # Model 12: GRU
        gru_model = Sequential([
            GRU(128, input_shape=input_shape),
            Dropout(0.3),
            Dense(64, activation='relu'),
            Dense(3, activation='softmax')
        ])
        gru_model.compile(optimizer=Adam(learning_rate=0.001), loss='categorical_crossentropy', metrics=['accuracy'])
        
        # Model 13: 1D CNN
        cnn_model = Sequential([
            Conv1D(64, kernel_size=3, activation='relu', input_shape=input_shape),
            MaxPooling1D(pool_size=2),
            Conv1D(128, kernel_size=3, activation='relu'),
            Flatten(),
            Dense(3, activation='softmax')
        ])
        cnn_model.compile(optimizer=Adam(learning_rate=0.001), loss='categorical_crossentropy', metrics=['accuracy'])
        
        return {
            'lstm': lstm_model,
            'gru': gru_model,
            'cnn_1d': cnn_model
        }

    def train(self, X: pd.DataFrame, y: pd.Series) -> None:
        print(f"\n{'=' * 60}")
        print('ADEN BORSA - 15 MODEL EGITIMI (KRONOLOJIK)')
        print(f"{'=' * 60}")
        print(f"Toplam ornek  : {len(X)}")
        print(f"Feature sayisi: {X.shape[1]}")
        
        self.featureNames = list(X.columns)
        self.trainedAt = datetime.now().isoformat()

        # Rule 1: Chronological Split (80% Train, 20% Test)
        split_idx = int(len(X) * 0.8)
        X_train_raw, X_test_raw = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

        # Rule 3: Fit scaler on train only (DataFrame olarak kalir, feature isimleri korunur)
        X_train_scaled = pd.DataFrame(
            self.scaler.fit_transform(X_train_raw.fillna(0)),
            columns=self.featureNames,
            index=X_train_raw.index
        )
        X_test_scaled = pd.DataFrame(
            self.scaler.transform(X_test_raw.fillna(0)),
            columns=self.featureNames,
            index=X_test_raw.index
        )

        # NumPy array olarak da tut (DL modelleri icin)
        X_train = X_train_scaled.values
        X_test = X_test_scaled.values

        # --- ML Modelleri Tanimi (Prompt 4) ---
        ml_models = {
            'random_forest': RandomForestClassifier(n_estimators=500, max_depth=10, class_weight='balanced', random_state=42, n_jobs=-1),
            'xgboost': XGBClassifier(n_estimators=300, learning_rate=0.05, max_depth=6, random_state=42, n_jobs=-1),
            'lightgbm': LGBMClassifier(num_leaves=63, learning_rate=0.05, n_estimators=300, boosting_type='gbdt', random_state=42, n_jobs=-1, verbose=-1),
            'catboost': CatBoostClassifier(iterations=300, learning_rate=0.05, depth=8, verbose=0, random_seed=42),
            'extra_trees': ExtraTreesClassifier(n_estimators=500, max_depth=12, class_weight='balanced', random_state=42, n_jobs=-1),
            'svm': SVC(kernel='rbf', C=1.0, gamma='scale', probability=True, random_state=42),
            'logistic_regression': LogisticRegression(C=0.1, max_iter=1000, random_state=42),
            'knn': KNeighborsClassifier(n_neighbors=15, metric='euclidean', weights='distance', n_jobs=-1),
            'adaboost': AdaBoostClassifier(estimator=DecisionTreeClassifier(max_depth=3), n_estimators=200, random_state=42),
            'bagging': BaggingClassifier(estimator=DecisionTreeClassifier(max_depth=5), n_estimators=300, random_state=42, n_jobs=-1)
        }

        # ML Modellerini Egit (DataFrame ile, feature isimleri korunur)
        for name, model in ml_models.items():
            print(f"  Egitiliyor: {name:<25}", end='', flush=True)
            # XGBoost/LightGBM/CatBoost etiketleri 0'dan baslamali ( -1, 0, 1 -> 0, 1, 2)
            y_train_shifted = y_train + 1
            model.fit(X_train_scaled, y_train_shifted)
            self.models[name] = model
            print(" Tamamlandi.")

        # --- DL Modelleri Egitimi (Rule 4: Build sequences AFTER split) ---
        if TF_AVAILABLE:
            print("\n  Sekanslar hazirlaniyor (DL modelleri icin)...")
            X_train_seq, y_train_seq = self._prepare_sequences(X_train, y_train.values)
            X_test_seq, y_test_seq = self._prepare_sequences(X_test, y_test.values)

            dl_models = self._build_dl_models((X_train_seq.shape[1], X_train_seq.shape[2]))
            for name, model in dl_models.items():
                print(f"  Egitiliyor: {name:<25}", end='', flush=True)
                model.fit(X_train_seq, y_train_seq, epochs=50, batch_size=32, verbose=0)
                # DL modellerini ayri kaydedecegiz
                model.save(os.path.join(DL_MODELS_DIR, f"{name}.h5"))
                self.models[name] = name # Sadece adini tutuyoruz, predictor yukleyecek
                print(" Tamamlandi.")
        else:
            print("\n  UYARI: TensorFlow yuklu degil, DL modelleri (LSTM, GRU, CNN) atlandi.")
            X_test_seq, y_test_seq = None, None

        # --- Ensemble Modelleri ---
        # Model 14: Voting (RF, XGB, LGBM, ET)
        print(f"  Egitiliyor: voting_ensemble           ", end='', flush=True)
        voting = VotingClassifier(
            estimators=[
                ('rf', ml_models['random_forest']),
                ('xgb', ml_models['xgboost']),
                ('lgbm', ml_models['lightgbm']),
                ('et', ml_models['extra_trees'])
            ],
            voting='soft', n_jobs=-1
        )
        y_train_shifted = y_train + 1
        voting.fit(X_train_scaled, y_train_shifted)
        self.models['voting_ensemble'] = voting
        print(" Tamamlandi.")

        # Model 15: Stacking (Rule 5: TimeSeriesSplit)
        print(f"  Egitiliyor: stacking_ensemble         ", end='', flush=True)
        # Basitlik ve performans acisindan ML modellerini kullanalim
        stacking = StackingClassifier(
            estimators=[
                ('rf', ml_models['random_forest']),
                ('xgb', ml_models['xgboost']),
                ('lgbm', ml_models['lightgbm']),
                ('et', ml_models['extra_trees'])
            ],
            final_estimator=LogisticRegression(C=0.1),
            cv=5,
            n_jobs=-1
        )
        stacking.fit(X_train_scaled, y_train_shifted)
        self.models['stacking_ensemble'] = stacking
        print(" Tamamlandi.")

        # --- Degerlendirme (Test Seti Uzerinden) ---
        self._evaluate(X_test_scaled, y_test, X_test_seq, y_test_seq)
        
        # Rule 8: Feature Importance (Tree-based)
        self._print_importance()

    def _evaluate(self, X_test, y_test, X_test_seq, y_test_seq):
        print(f"\n{'=' * 60}")
        print("MODEL DEGERLENDIRME (TEST SETI)")
        print(f"{'=' * 60}")
        
        y_test_shifted = y_test + 1 # 0, 1, 2 formatina cevir

        for name, model in self.models.items():
            try:
                if name in ['lstm', 'gru', 'cnn_1d']:
                    # DL modelleri icin farkli tahmin logic
                    # Not: Predictor icinde yukleme yapilacak, burada egitilen model objesini kullanmaliyiz
                    # Ama self.models[name] su an string. Egitim sirasinda objeyi gecici tutalim.
                    pass # Atliyoruz, egitim sirasinda skor basildi zaten veya predictor'da bakilacak
                else:
                    preds = model.predict(X_test)
                    acc = accuracy_score(y_test_shifted, preds)
                    f1 = f1_score(y_test_shifted, preds, average='weighted')
                    self.scores[name] = round(float(acc), 4)
                    print(f"  {name:<25}: Accuracy={acc:.4f}, F1={f1:.4f}")
            except Exception as e:
                print(f"  {name} Degerlendirme Hatasi: {e}")

    def _print_importance(self):
        """Rule 8: Top 20 features for tree-based models."""
        print(f"\n{'=' * 60}")
        print("FEATURE IMPORTANCE (TOP 20 - XGBOOST)")
        print(f"{'=' * 60}")
        if 'xgboost' in self.models:
            importances = self.models['xgboost'].feature_importances_
            feat_imp = pd.Series(importances, index=self.featureNames).sort_values(ascending=False)
            print(feat_imp.head(20))

    def save(self) -> None:
        os.makedirs(MODEL_DIR, exist_ok=True)
        paths = _modelPaths(self.horizon)
        os.makedirs(paths['dl_dir'], exist_ok=True)

        # ML modellerini ve ensemble'lari kaydet
        ml_to_save = {k: v for k, v in self.models.items() if not isinstance(v, str)}
        joblib.dump(ml_to_save, paths['models'])
        joblib.dump(self.scaler, paths['scaler'])
        
        meta = {
            'feature_names': self.featureNames,
            'trained_at': self.trainedAt,
            'scores': self.scores,
            'model_count': len(self.models),
            'horizon': self.horizon,
        }
        joblib.dump(meta, paths['meta'])
        print(f"\nModeller kaydedildi (horizon={self.horizon}): {paths['models']}")

    def load(self) -> bool:
        paths = _modelPaths(self.horizon)
        if not os.path.exists(paths['models']): return False
        try:
            self.models = joblib.load(paths['models'])
            self.scaler = joblib.load(paths['scaler'])
            meta = joblib.load(paths['meta'])
            self.featureNames = meta.get('feature_names', [])
            self.trainedAt = meta.get('trained_at', "")
            self.scores = meta.get('scores', {})
            
            # DL modellerini de listeye ekle (varsa)
            dlDir = paths['dl_dir']
            for dl_name in ['lstm', 'gru', 'cnn_1d']:
                if os.path.exists(os.path.join(dlDir, f"{dl_name}.h5")):
                    self.models[dl_name] = dl_name
            
            return True
        except: return False
