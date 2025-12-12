"""
API'den veri çekme ve CSV'ye kaydetme modülü
"""
import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import os
import xml.etree.ElementTree as ET
from urllib.parse import quote
from config import *

class DataCollector:
    """Haber ve hisse senedi verilerini toplar ve CSV'ye kaydeder"""
    
    def __init__(self):
        self.finnhub_base = 'https://finnhub.io/api/v1'
        self.news_base = 'https://newsapi.org/v2'
        self.google_news_base = 'https://news.google.com/rss/search'
        
    def collect_stock_data(self, symbol, days=90):
        """
        Belirli bir hisse için fiyat verilerini çeker (yfinance ile)
        
        Args:
            symbol: Hisse sembolü (örn: AAPL)
            days: Kaç günlük veri çekileceği
            
        Returns:
            DataFrame: Hisse fiyat verileri
        """
        print(f"📊 {symbol} hisse verileri çekiliyor...")
        
        try:
            import yfinance as yf
            
            # Tarih aralığı hesapla
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # yfinance ile veri çek
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date)
            
            if df.empty:
                print(f"❌ {symbol} için veri bulunamadı")
                return pd.DataFrame()
            
            # Sütun isimlerini küçük harfe çevir
            df.columns = df.columns.str.lower()
            
            # Symbol ekle
            df['symbol'] = symbol
            
            print(f"✅ {symbol}: {len(df)} günlük veri alındı")
            return df
            
        except Exception as e:
            print(f"❌ {symbol} veri çekme hatası: {str(e)}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def collect_company_news(self, symbol, days=30, company_name=None):
        """
        Belirli bir şirket için haberleri çeker.
        Öncelik: 1) Google News RSS (ÜCRETSİZ, LİMİTSİZ)
                 2) Finnhub API (Backend)
                 3) yfinance (fallback)
        
        MUTLAKA HABER DÖNDÜRÜR - En az bir kaynak başarılı olmalı!
        
        Args:
            symbol: Hisse sembolü
            days: Kaç günlük haber çekileceği
            company_name: Şirket adı (Google News için daha iyi sonuçlar)
            
        Returns:
            DataFrame: Haber verileri
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_ts = cutoff_date.timestamp()
        
        print(f"\n{'='*60}")
        print(f"📰 {symbol} için HABER TOPLAMA BAŞLADI")
        print(f"{'='*60}")
        
        # 1) Google News RSS (Öncelikli - ÜCRETSİZ ve LİMİTSİZ)
        print("\n🔍 1. Deneme: Google News RSS...")
        try:
            df = self.collect_news_from_google_rss(symbol, company_name, days)
            if not df.empty:
                print(f"✅ Google News RSS BAŞARILI: {len(df)} haber")
                return df
            else:
                print("⚠️ Google News RSS'de haber bulunamadı")
        except Exception as e:
            print(f"❌ Google News RSS hatası: {e}")
        
        # 2) Finnhub API (Backend)
        print("\n🔍 2. Deneme: Finnhub API...")
        if FINNHUB_API_KEY:
            try:
                from_date = cutoff_date.strftime('%Y-%m-%d')
                to_date = datetime.now().strftime('%Y-%m-%d')
                url = f"{self.finnhub_base}/company-news"
                params = {
                    'symbol': symbol,
                    'from': from_date,
                    'to': to_date,
                    'token': FINNHUB_API_KEY
                }
                print(f"📰 {symbol} haberleri çekiliyor (Finnhub)...")
                resp = requests.get(url, params=params, timeout=10)
                resp.raise_for_status()
                news = resp.json()
                
                if news:
                    df = pd.DataFrame(news)
                    # Finnhub datetime saniye cinsinden epoch gelir
                    df = df[df['datetime'] >= cutoff_ts]
                    df = df.rename(columns={'datetime': 'datetime'})
                    df = df[['datetime', 'headline', 'summary', 'source', 'url']].copy()
                    df['symbol'] = symbol
                    df['collected_at'] = datetime.now()
                    print(f"✅ Finnhub BAŞARILI: {len(df)} haber")
                    return df
                else:
                    print(f"⚠️ Finnhub'da haber bulunamadı")
            except Exception as e:
                print(f"❌ Finnhub hatası: {e}")
        else:
            print("⚠️ Finnhub API key yok, atlanıyor")
        
        # 3) Fallback: yfinance
        print("\n🔍 3. Deneme: yfinance...")
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            news = ticker.news
            
            if not news:
                print(f"❌ yfinance'de haber bulunamadı")
                print(f"\n{'='*60}")
                print(f"⚠️ UYARI: {symbol} için HİÇBİR KAYNAKTAN HABER ÇEKİLEMEDİ!")
                print(f"{'='*60}\n")
                return pd.DataFrame()
            
            news_list = []
            for item in news:
                news_time = item.get('providerPublishTime', 0)
                if news_time < cutoff_ts:
                    continue
                news_list.append({
                    'datetime': news_time,
                    'headline': item.get('title', ''),
                    'summary': item.get('summary', ''),
                    'source': item.get('publisher', ''),
                    'url': item.get('link', ''),
                    'symbol': symbol,
                    'collected_at': datetime.now()
                })
            
            if not news_list:
                print(f"⚠️ {symbol} için son {days} günde haber bulunamadı (yfinance)")
                return pd.DataFrame()
            
            df = pd.DataFrame(news_list)
            print(f"✅ yfinance BAŞARILI: {len(df)} haber")
            return df
        except Exception as e:
            print(f"❌ yfinance hatası: {str(e)}")
            print(f"\n{'='*60}")
            print(f"⚠️ UYARI: {symbol} için HİÇBİR KAYNAKTAN HABER ÇEKİLEMEDİ!")
            print(f"{'='*60}\n")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def collect_news_from_google_rss(self, symbol, company_name=None, days=30):
        """
        Google News RSS'den haber çeker (ÜCRETSİZ, LİMİTSİZ)
        
        Args:
            symbol: Hisse sembolü (örn: AAPL)
            company_name: Şirket adı (örn: Apple). None ise symbol kullanılır.
            days: Kaç günlük haber çekileceği
            
        Returns:
            DataFrame: Haber verileri
        """
        try:
            # Arama sorgusu oluştur
            search_query = company_name if company_name else symbol
            search_query = f"{search_query} stock"
            encoded_query = quote(search_query)
            
            # Google News RSS URL
            url = f"{self.google_news_base}?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
            
            print(f"📰 {symbol} haberleri çekiliyor (Google News RSS)...")
            print(f"   Sorgu: {search_query}")
            
            # RSS feed çek
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # XML parse et
            root = ET.fromstring(response.content)
            
            news_list = []
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # RSS item'ları işle
            for item in root.findall('.//item'):
                try:
                    title = item.find('title')
                    link = item.find('link')
                    pub_date = item.find('pubDate')
                    description = item.find('description')
                    source = item.find('source')
                    
                    # Tarihi parse et (RFC 822 formatı)
                    pub_datetime = None
                    if pub_date is not None and pub_date.text:
                        try:
                            # RFC 822: "Wed, 02 Oct 2002 13:00:00 GMT"
                            from email.utils import parsedate_to_datetime
                            pub_datetime = parsedate_to_datetime(pub_date.text)
                            
                            # Tarih kontrolü
                            if pub_datetime < cutoff_date:
                                continue
                        except Exception as e:
                            print(f"⚠️ Tarih parse hatası: {e}")
                            pub_datetime = datetime.now()
                    else:
                        pub_datetime = datetime.now()
                    
                    news_list.append({
                        'datetime': int(pub_datetime.timestamp()),
                        'headline': title.text if title is not None else '',
                        'summary': description.text if description is not None else '',
                        'source': source.text if source is not None else 'Google News',
                        'url': link.text if link is not None else '',
                        'symbol': symbol,
                        'collected_at': datetime.now()
                    })
                    
                except Exception as e:
                    print(f"⚠️ RSS item parse hatası: {e}")
                    continue
            
            if not news_list:
                print(f"⚠️ {symbol} için Google News'de haber bulunamadı")
                return pd.DataFrame()
            
            df = pd.DataFrame(news_list)
            print(f"✅ {symbol}: {len(df)} haber (Google News RSS - ÜCRETSİZ)")
            return df
            
        except Exception as e:
            print(f"❌ Google News RSS hatası ({symbol}): {str(e)}")
            import traceback
            traceback.print_exc()
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
            
            # Şirket ismini al (varsa)
            company_name = COMPANY_NAMES.get(symbol)
            
            # Haberleri çek
            news_df = self.collect_company_news(symbol, news_days, company_name)
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
