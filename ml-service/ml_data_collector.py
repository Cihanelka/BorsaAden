"""
Random Forest Modeli için Veri Toplama ve Feature Engineering
"""
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import ta
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import os
import yfinance as yf

class MLDataCollector:
    def __init__(self):
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        
    def get_stock_data(self, symbol, days=90):
        """Hisse senedi verilerini al - yfinance kullanarak (ücretsiz, limitsiz)"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days + 30)  # Biraz fazla al, teknik göstergeler için
            
            # yfinance ile veri çek
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date, interval='1d')
            
            if df.empty:
                print(f"⚠️ {symbol} için veri alınamadı")
                return None
            
            # Sütun isimlerini küçük harfe çevir ve datetime ekle
            df = df.reset_index()
            df.columns = [col.lower() for col in df.columns]
            df.rename(columns={'date': 'datetime'}, inplace=True)
            
            # Gereksiz sütunları çıkar
            df = df[['datetime', 'open', 'high', 'low', 'close', 'volume']]
            df = df.sort_values('datetime')
            
            print(f"✅ {symbol}: {len(df)} günlük veri alındı")
            
            return df
            
        except Exception as e:
            print(f"❌ Hisse verisi alma hatası ({symbol}): {e}")
            return None
    
    def calculate_technical_indicators(self, df):
        """Teknik göstergeleri hesapla"""
        if df is None or len(df) < 20:
            return None
        
        try:
            # RSI
            df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
            
            # MACD
            macd = ta.trend.MACD(df['close'])
            df['macd'] = macd.macd()
            df['macd_signal'] = macd.macd_signal()
            df['macd_diff'] = macd.macd_diff()
            
            # Bollinger Bands
            bollinger = ta.volatility.BollingerBands(df['close'])
            df['bb_high'] = bollinger.bollinger_hband()
            df['bb_mid'] = bollinger.bollinger_mavg()
            df['bb_low'] = bollinger.bollinger_lband()
            df['bb_width'] = (df['bb_high'] - df['bb_low']) / df['bb_mid']
            
            # Moving Averages
            df['sma_20'] = ta.trend.SMAIndicator(df['close'], window=20).sma_indicator()
            df['sma_50'] = ta.trend.SMAIndicator(df['close'], window=50).sma_indicator()
            df['ema_12'] = ta.trend.EMAIndicator(df['close'], window=12).ema_indicator()
            df['ema_26'] = ta.trend.EMAIndicator(df['close'], window=26).ema_indicator()
            
            # Stochastic
            stoch = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close'])
            df['stoch_k'] = stoch.stoch()
            df['stoch_d'] = stoch.stoch_signal()
            
            # ATR (Average True Range)
            df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close']).average_true_range()
            
            # Volume indicators
            df['volume_sma'] = df['volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_sma']
            
            # Price momentum
            df['price_change_1d'] = df['close'].pct_change(1)
            df['price_change_5d'] = df['close'].pct_change(5)
            df['price_change_10d'] = df['close'].pct_change(10)
            
            # Trend strength
            df['trend_strength'] = (df['close'] - df['sma_50']) / df['sma_50']
            
            # On-Balance Volume (OBV)
            df['obv'] = ta.volume.OnBalanceVolumeIndicator(df['close'], df['volume']).on_balance_volume()
            df['obv_change'] = df['obv'].pct_change(5)
            
            # Money Flow Index (MFI)
            df['mfi'] = ta.volume.MFIIndicator(df['high'], df['low'], df['close'], df['volume']).money_flow_index()
            
            # Average Directional Index (ADX) - Trend gücü
            df['adx'] = ta.trend.ADXIndicator(df['high'], df['low'], df['close']).adx()
            
            # Commodity Channel Index (CCI)
            df['cci'] = ta.trend.CCIIndicator(df['high'], df['low'], df['close']).cci()
            
            # Williams %R
            df['williams_r'] = ta.momentum.WilliamsRIndicator(df['high'], df['low'], df['close']).williams_r()
            
            # Rate of Change (ROC)
            df['roc'] = ta.momentum.ROCIndicator(df['close'], window=12).roc()
            
            # Hareketli ortalama kesişimleri
            df['sma_cross'] = np.where(df['sma_20'] > df['sma_50'], 1, -1)
            df['ema_cross'] = np.where(df['ema_12'] > df['ema_26'], 1, -1)
            
            return df
            
        except Exception as e:
            print(f"❌ Teknik gösterge hesaplama hatası: {e}")
            return None
    
    def get_news_sentiment(self, symbol, days=7):
        """Haber duygu analizi yap - önce CSV'den oku, yoksa canlı çek"""
        # Önce CSV'den sentiment verilerini kontrol et
        csv_sentiment = self._get_sentiment_from_csv(symbol, days)
        if csv_sentiment is not None:
            print(f"✅ {symbol} sentiment CSV'den okundu: {csv_sentiment['news_count']} haber")
            return csv_sentiment
        
        print(f"📰 {symbol} için canlı haber çekiliyor...")
        try:
            # NewsAPI kullanarak haberleri al
            news_api_key = '78e1efb0e1964e8fbbf4158f7b9c65f1'
            
            # Şirket ismini sembolden çıkar (basitleştirilmiş)
            company_map = {
                'AAPL': 'Apple',
                'MSFT': 'Microsoft',
                'GOOGL': 'Google',
                'AMZN': 'Amazon',
                'TSLA': 'Tesla',
                'META': 'Meta Facebook',
                'NVDA': 'Nvidia',
            }
            
            query = company_map.get(symbol, symbol)
            
            url = 'https://newsapi.org/v2/everything'
            params = {
                'q': query,
                'apiKey': news_api_key,
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': 20,
                'from': (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get('status') != 'ok' or not data.get('articles'):
                return self._get_default_sentiment()
            
            # Her haber için duygu analizi yap
            sentiments = []
            for article in data['articles'][:10]:  # İlk 10 haber
                title = article.get('title', '')
                description = article.get('description', '')
                text = f"{title} {description}"
                
                if text:
                    sentiment = self.sentiment_analyzer.polarity_scores(text)
                    sentiments.append(sentiment['compound'])
            
            if not sentiments:
                return self._get_default_sentiment()
            
            # Ortalama duygu skoru
            avg_sentiment = np.mean(sentiments)
            sentiment_std = np.std(sentiments)
            positive_ratio = len([s for s in sentiments if s > 0.05]) / len(sentiments)
            negative_ratio = len([s for s in sentiments if s < -0.05]) / len(sentiments)
            
            return {
                'sentiment_score': avg_sentiment,
                'sentiment_std': sentiment_std,
                'positive_ratio': positive_ratio,
                'negative_ratio': negative_ratio,
                'news_count': len(sentiments)
            }
            
        except Exception as e:
            print(f"⚠️ Haber analizi hatası ({symbol}): {e}")
            return self._get_default_sentiment()
    
    def _get_sentiment_from_csv(self, symbol, days=7):
        """CSV'den sentiment verilerini oku"""
        try:
            csv_path = 'data/csv/news_with_sentiment.csv'
            if not os.path.exists(csv_path):
                return None
            
            df = pd.read_csv(csv_path)
            
            # Sembole göre filtrele
            symbol_news = df[df['symbol'] == symbol] if 'symbol' in df.columns else df
            
            if symbol_news.empty or 'sentiment_score' not in symbol_news.columns:
                return None
            
            # Son N günlük haberleri al
            if 'published_date' in symbol_news.columns:
                symbol_news['published_date'] = pd.to_datetime(symbol_news['published_date'], errors='coerce')
                cutoff_date = datetime.now() - timedelta(days=days)
                symbol_news = symbol_news[symbol_news['published_date'] >= cutoff_date]
            
            if symbol_news.empty:
                return None
            
            # Sentiment istatistiklerini hesapla
            sentiments = symbol_news['sentiment_score'].dropna()
            
            if len(sentiments) == 0:
                return None
            
            avg_sentiment = sentiments.mean()
            sentiment_std = sentiments.std() if len(sentiments) > 1 else 0.0
            positive_ratio = len(sentiments[sentiments > 0.05]) / len(sentiments)
            negative_ratio = len(sentiments[sentiments < -0.05]) / len(sentiments)
            
            return {
                'sentiment_score': avg_sentiment,
                'sentiment_std': sentiment_std,
                'positive_ratio': positive_ratio,
                'negative_ratio': negative_ratio,
                'news_count': len(sentiments)
            }
            
        except Exception as e:
            print(f"⚠️ CSV sentiment okuma hatası ({symbol}): {e}")
            return None
    
    def _get_default_sentiment(self):
        """Varsayılan duygu değerleri"""
        return {
            'sentiment_score': 0.0,
            'sentiment_std': 0.0,
            'positive_ratio': 0.5,
            'negative_ratio': 0.5,
            'news_count': 0
        }
    
    def create_features(self, symbol, days=90):
        """Bir hisse için tüm özellikleri oluştur"""
        print(f"📊 {symbol} için veri toplama başlıyor...")
        
        # Hisse verilerini al
        stock_df = self.get_stock_data(symbol, days)
        if stock_df is None:
            return None
        
        # Teknik göstergeleri hesapla
        stock_df = self.calculate_technical_indicators(stock_df)
        if stock_df is None:
            return None
        
        # Haber duygu analizini al
        sentiment = self.get_news_sentiment(symbol, days=7)
        
        # Son satır için özellikleri birleştir
        latest = stock_df.iloc[-1].copy()
        
        # Sentiment özelliklerini ekle
        for key, value in sentiment.items():
            latest[key] = value
        
        latest['symbol'] = symbol
        
        return latest
    
    def create_training_dataset(self, symbols, days=90):
        """Birden fazla hisse için eğitim veri seti oluştur - TÜM tarihsel veriyi kullan"""
        print(f"\n🔄 {len(symbols)} hisse için veri toplama başlıyor...\n")
        
        all_data = []
        
        for i, symbol in enumerate(symbols, 1):
            try:
                print(f"\n[{i}/{len(symbols)}] {symbol} işleniyor...")
                
                # Hisse verilerini al
                stock_df = self.get_stock_data(symbol, days)
                if stock_df is None or len(stock_df) < 50:
                    print(f"⚠️ {symbol} - Yetersiz veri, atlandı")
                    continue
                
                # Teknik göstergeleri hesapla
                stock_df = self.calculate_technical_indicators(stock_df)
                if stock_df is None:
                    print(f"⚠️ {symbol} - Teknik gösterge hatası, atlandı")
                    continue
                
                # Haber duygu analizini al (tüm veri için aynı sentiment kullan)
                sentiment = self.get_news_sentiment(symbol, days=7)
                
                # Her satır için sentiment ekle
                for key, value in sentiment.items():
                    stock_df[key] = value
                
                stock_df['symbol'] = symbol
                
                # NaN değerleri temizle (ilk 50 satır teknik göstergeler için)
                stock_df = stock_df.dropna()
                
                all_data.append(stock_df)
                print(f"✅ {symbol}: {len(stock_df)} satır eklendi")
                
            except Exception as e:
                print(f"❌ {symbol} hatası: {e}")
                continue
        
        if not all_data:
            print("\n❌ Hiç veri toplanamadı!")
            return None
        
        # Tüm verileri birleştir
        df = pd.concat(all_data, ignore_index=True)
        print(f"\n✅ Toplam {len(df)} satır veri toplandı ({len(symbols)} hisse)")
        print(f"📊 Ortalama {len(df) // len(symbols)} satır/hisse")
        
        return df

if __name__ == "__main__":
    # Test
    collector = MLDataCollector()
    
    test_symbols = ['AAPL', 'MSFT', 'GOOGL']
    df = collector.create_training_dataset(test_symbols, days=90)
    
    if df is not None:
        print(f"\n📊 Veri Seti Özeti:")
        print(f"Satır sayısı: {len(df)}")
        print(f"Sütun sayısı: {len(df.columns)}")
        print(f"\nİlk 5 satır:")
        print(df.head())
