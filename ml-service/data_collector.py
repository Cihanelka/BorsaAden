"""
API'den veri çekme ve CSV'ye kaydetme modülü
"""
import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import os
from config import *

class DataCollector:
    """Haber ve hisse senedi verilerini toplar ve CSV'ye kaydeder"""
    
    def __init__(self):
        self.finnhub_base = 'https://finnhub.io/api/v1'
        self.news_base = 'https://newsapi.org/v2'
        
    def collect_stock_data(self, symbol, days=90):
        """
        Belirli bir hisse için fiyat verilerini çeker
        
        Args:
            symbol: Hisse sembolü (örn: AAPL)
            days: Kaç günlük veri çekileceği
            
        Returns:
            DataFrame: Hisse fiyat verileri
        """
        print(f"📊 {symbol} hisse verileri çekiliyor...")
        
        # Tarih aralığı hesapla
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Unix timestamp'e çevir
        start_ts = int(start_date.timestamp())
        end_ts = int(end_date.timestamp())
        
        # Finnhub'dan veri çek (candle data)
        url = f"{self.finnhub_base}/stock/candle"
        params = {
            'symbol': symbol,
            'resolution': 'D',  # Daily
            'from': start_ts,
            'to': end_ts,
            'token': FINNHUB_API_KEY
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('s') != 'ok':
                print(f"❌ {symbol} için veri alınamadı: {data}")
                return pd.DataFrame()
            
            # DataFrame oluştur
            df = pd.DataFrame({
                'timestamp': data['t'],
                'open': data['o'],
                'high': data['h'],
                'low': data['l'],
                'close': data['c'],
                'volume': data['v'],
                'symbol': symbol
            })
            
            # Timestamp'i datetime'a çevir
            df['date'] = pd.to_datetime(df['timestamp'], unit='s')
            df = df.sort_values('date')
            
            print(f"✅ {symbol}: {len(df)} günlük veri alındı")
            return df
            
        except Exception as e:
            print(f"❌ {symbol} veri çekme hatası: {str(e)}")
            return pd.DataFrame()
    
    def collect_company_news(self, symbol, days=30):
        """
        Belirli bir şirket için haberleri çeker
        
        Args:
            symbol: Hisse sembolü
            days: Kaç günlük haber çekileceği
            
        Returns:
            DataFrame: Haber verileri
        """
        print(f"📰 {symbol} haberleri çekiliyor...")
        
        # Tarih aralığı
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Finnhub'dan şirket haberlerini çek
        url = f"{self.finnhub_base}/company-news"
        params = {
            'symbol': symbol,
            'from': start_date.strftime('%Y-%m-%d'),
            'to': end_date.strftime('%Y-%m-%d'),
            'token': FINNHUB_API_KEY
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            news_data = response.json()
            
            if not news_data:
                print(f"⚠️ {symbol} için haber bulunamadı")
                return pd.DataFrame()
            
            # DataFrame oluştur
            df = pd.DataFrame(news_data)
            df['symbol'] = symbol
            df['collected_at'] = datetime.now()
            
            # Gerekli kolonları seç
            columns = ['datetime', 'headline', 'summary', 'source', 'url', 'symbol', 'collected_at']
            df = df[[col for col in columns if col in df.columns]]
            
            print(f"✅ {symbol}: {len(df)} haber alındı")
            return df
            
        except Exception as e:
            print(f"❌ {symbol} haber çekme hatası: {str(e)}")
            return pd.DataFrame()
    
    def save_to_csv(self, df, filename, append=True):
        """
        DataFrame'i CSV dosyasına kaydeder
        
        Args:
            df: Kaydedilecek DataFrame
            filename: Dosya adı
            append: True ise mevcut dosyaya ekler, False ise üzerine yazar
        """
        if df.empty:
            print(f"⚠️ Kaydedilecek veri yok: {filename}")
            return
        
        filepath = os.path.join(CSV_DIR, filename)
        
        try:
            if append and os.path.exists(filepath):
                # Mevcut dosyayı oku
                existing_df = pd.read_csv(filepath)
                # Yeni verileri ekle ve duplikatları kaldır
                combined_df = pd.concat([existing_df, df], ignore_index=True)
                combined_df = combined_df.drop_duplicates()
                combined_df.to_csv(filepath, index=False)
                print(f"💾 Veri eklendi: {filepath} ({len(df)} yeni satır)")
            else:
                df.to_csv(filepath, index=False)
                print(f"💾 Veri kaydedildi: {filepath} ({len(df)} satır)")
                
        except Exception as e:
            print(f"❌ CSV kaydetme hatası: {str(e)}")
    
    def collect_all_data(self, symbols=None, stock_days=90, news_days=30):
        """
        Tüm hisseler için veri toplar ve kaydeder
        
        Args:
            symbols: Hisse listesi (None ise config'den alır)
            stock_days: Hisse verileri için gün sayısı
            news_days: Haberler için gün sayısı
        """
        if symbols is None:
            symbols = DEFAULT_STOCKS
        
        print(f"\n🚀 Veri toplama başlıyor: {len(symbols)} hisse")
        print(f"📊 Hisse verileri: Son {stock_days} gün")
        print(f"📰 Haberler: Son {news_days} gün\n")
        
        all_stock_data = []
        all_news_data = []
        
        for i, symbol in enumerate(symbols, 1):
            print(f"\n[{i}/{len(symbols)}] {symbol} işleniyor...")
            
            # Hisse verilerini çek
            stock_df = self.collect_stock_data(symbol, stock_days)
            if not stock_df.empty:
                all_stock_data.append(stock_df)
            
            # Rate limiting için bekle
            time.sleep(1)
            
            # Haberleri çek
            news_df = self.collect_company_news(symbol, news_days)
            if not news_df.empty:
                all_news_data.append(news_df)
            
            # Rate limiting için bekle
            time.sleep(1)
        
        # Tüm verileri birleştir ve kaydet
        if all_stock_data:
            combined_stock = pd.concat(all_stock_data, ignore_index=True)
            self.save_to_csv(combined_stock, 'stock_data.csv', append=True)
        
        if all_news_data:
            combined_news = pd.concat(all_news_data, ignore_index=True)
            self.save_to_csv(combined_news, 'news_data.csv', append=True)
        
        print("\n✅ Veri toplama tamamlandı!")
        print(f"📊 Toplam hisse verisi: {len(combined_stock) if all_stock_data else 0} satır")
        print(f"📰 Toplam haber: {len(combined_news) if all_news_data else 0} haber")
        
        return combined_stock if all_stock_data else pd.DataFrame(), \
               combined_news if all_news_data else pd.DataFrame()

if __name__ == '__main__':
    # Test amaçlı çalıştır
    collector = DataCollector()
    
    # Tek bir hisse için test
    test_symbol = 'AAPL'
    stock_df = collector.collect_stock_data(test_symbol, days=30)
    news_df = collector.collect_company_news(test_symbol, days=7)
    
    if not stock_df.empty:
        collector.save_to_csv(stock_df, f'{test_symbol}_stock_test.csv', append=False)
    
    if not news_df.empty:
        collector.save_to_csv(news_df, f'{test_symbol}_news_test.csv', append=False)
