"""
ML Servisi Yapılandırma Dosyası
"""
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# API Anahtarları
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY', '')
NEWS_API_KEY = os.getenv('NEWS_API_KEY', '78e1efb0e1964e8fbbf4158f7b9c65f1')

# Veri Klasörleri
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
CSV_DIR = os.path.join(DATA_DIR, 'csv')
MODEL_DIR = os.path.join(DATA_DIR, 'models')

# Veri Toplama Ayarları
DEFAULT_STOCKS = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META',
    'TSLA', 'NVDA', 'AMD', 'INTC', 'NFLX'
]

# Haber Toplama Ayarları
NEWS_LOOKBACK_DAYS = 30
NEWS_MAX_ARTICLES = 100

# Model Ayarları
SENTIMENT_MODEL = 'savasy/bert-base-turkish-sentiment-cased'
MIN_TRAINING_SAMPLES = 50
BATCH_SIZE = 16

# Teknik Analiz Ayarları
TECHNICAL_INDICATORS = [
    'RSI',      # Relative Strength Index
    'MACD',     # Moving Average Convergence Divergence
    'BB',       # Bollinger Bands
    'SMA',      # Simple Moving Average
    'EMA',      # Exponential Moving Average
    'STOCH',    # Stochastic Oscillator
    'ATR',      # Average True Range
    'OBV',      # On-Balance Volume
]

# Karar Eşikleri
BUY_THRESHOLD = 0.65    # %65 üzeri güven için AL
SELL_THRESHOLD = 0.35   # %35 altı güven için SAT
# Aradaki değerler TUT

# Flask Server
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5000
DEBUG_MODE = True

# Klasörleri oluştur
os.makedirs(CSV_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)
