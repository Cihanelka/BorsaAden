"""
Türkçe haber duygu analizi modülü
"""
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from config import *

# Transformers'ı lazy import yap (TensorFlow hatalarını önlemek için)
try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
    import torch
    TRANSFORMERS_AVAILABLE = True
except Exception as e:
    print(f"⚠️ Transformers yüklenemedi: {str(e)}")
    print("ℹ️ Basit sentiment analizi kullanılacak")
    TRANSFORMERS_AVAILABLE = False

class SentimentAnalyzer:
    """Haberlerin duygu analizini yapar ve skorlar"""
    
    def __init__(self):
        """Duygu analizi modelini yükler"""
        print("🤖 Basit sentiment analizi kullanılacak (BERT devre dışı)")
        
        # BERT modelini devre dışı bırak, sadece basit analiz kullan
        self.sentiment_pipeline = None
        self.model = None
        self.tokenizer = None
        
        # BERT yüklemeyi atla
        print("✅ Basit kelime tabanlı sentiment analizi hazır")
    
    def clean_text(self, text):
        """
        Metin temizleme
        
        Args:
            text: Ham metin
            
        Returns:
            str: Temizlenmiş metin
        """
        if pd.isna(text) or not isinstance(text, str):
            return ""
        
        # Fazla boşlukları temizle
        text = ' '.join(text.split())
        return text.strip()
    
    def analyze_sentiment(self, text):
        """
        Tek bir metin için duygu analizi yapar
        
        Args:
            text: Analiz edilecek metin
            
        Returns:
            dict: {'label': 'positive/negative/neutral', 'score': 0.0-1.0}
        """
        text = self.clean_text(text)
        
        if not text:
            return {'label': 'neutral', 'score': 0.5}
        
        # Eğer model yüklü değilse basit analiz kullan
        if self.sentiment_pipeline is None:
            return self._simple_sentiment(text)
        
        try:
            # Metni maksimum token uzunluğuna göre kes
            result = self.sentiment_pipeline(text, truncation=True, max_length=512)[0]
            return result
            
        except Exception as e:
            print(f"⚠️ Sentiment analiz hatası: {str(e)}")
            return self._simple_sentiment(text)
    
    def _simple_sentiment(self, text):
        """
        Geliştirilmiş kelime tabanlı sentiment analizi
        İngilizce ve Türkçe finansal kelimeler
        """
        # Pozitif kelimeler (İngilizce + Türkçe)
        positive_words = [
            # İngilizce
            'gain', 'gains', 'profit', 'profits', 'rise', 'rises', 'rose', 'up', 'surge', 'surges',
            'growth', 'grow', 'increase', 'increases', 'high', 'higher', 'beat', 'beats',
            'strong', 'strength', 'positive', 'bull', 'bullish', 'rally', 'rallies',
            'success', 'successful', 'advance', 'advances', 'boost', 'boosts', 'upgraded',
            'outperform', 'outperforms', 'exceed', 'exceeds', 'soar', 'soars',
            # Türkçe
            'kazanç', 'kâr', 'yükseliş', 'artış', 'büyüme', 'güçlü', 'pozitif', 
            'başarı', 'başarılı', 'iyi', 'güzel', 'harika', 'mükemmel', 'rekor'
        ]
        
        # Negatif kelimeler (İngilizce + Türkçe)
        negative_words = [
            # İngilizce
            'loss', 'losses', 'lose', 'lost', 'fall', 'falls', 'fell', 'drop', 'drops', 'dropped',
            'decline', 'declines', 'decrease', 'decreases', 'low', 'lower', 'weak', 'weakness',
            'negative', 'bear', 'bearish', 'miss', 'misses', 'missed', 'risk', 'risks',
            'concern', 'concerns', 'worry', 'worries', 'downgrade', 'downgrades', 'plunge',
            'tumble', 'tumbles', 'underperform', 'underperforms', 'slump', 'slumps',
            # Türkçe
            'kayıp', 'zarar', 'düşüş', 'azalış', 'zayıf', 'negatif', 'risk',
            'endişe', 'kötü', 'düşük', 'gerileme', 'çöküş'
        ]
        
        text_lower = text.lower()
        
        # Kelimeleri say
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        # Skor hesapla
        total = pos_count + neg_count
        if total == 0:
            return {'label': 'neutral', 'score': 0.5}
        
        pos_ratio = pos_count / total
        
        if pos_ratio > 0.6:
            return {'label': 'positive', 'score': min(0.5 + pos_ratio * 0.3, 0.9)}
        elif pos_ratio < 0.4:
            return {'label': 'negative', 'score': min(0.5 + (1 - pos_ratio) * 0.3, 0.9)}
        else:
            return {'label': 'neutral', 'score': 0.5}
    
    def analyze_news_batch(self, news_df):
        """
        Toplu haber verilerinin duygu analizini yapar
        
        Args:
            news_df: Haber verileri içeren DataFrame
            
        Returns:
            DataFrame: Duygu skorları eklenmiş DataFrame
        """
        if news_df.empty:
            print("⚠️ Analiz edilecek haber yok")
            return news_df
        
        print(f"📊 {len(news_df)} haber analiz ediliyor...")
        
        # Başlık ve özet birleştir
        if 'headline' in news_df.columns and 'summary' in news_df.columns:
            news_df['combined_text'] = news_df['headline'].fillna('') + ' ' + news_df['summary'].fillna('')
        elif 'headline' in news_df.columns:
            news_df['combined_text'] = news_df['headline'].fillna('')
        elif 'summary' in news_df.columns:
            news_df['combined_text'] = news_df['summary'].fillna('')
        else:
            print("❌ Haber metni bulunamadı (headline veya summary)")
            return news_df
        
        # Duygu analizi yap
        sentiments = []
        scores = []
        
        for idx, text in enumerate(news_df['combined_text']):
            if idx % 10 == 0:
                print(f"  İşlenen: {idx}/{len(news_df)}")
            
            result = self.analyze_sentiment(text)
            sentiments.append(result['label'])
            scores.append(result['score'])
        
        # Sonuçları ekle
        news_df['sentiment'] = sentiments
        news_df['sentiment_score'] = scores
        
        # Normalize edilmiş skor (-1 ile +1 arası)
        news_df['normalized_score'] = news_df.apply(
            lambda row: row['sentiment_score'] if row['sentiment'] == 'positive' 
            else -row['sentiment_score'] if row['sentiment'] == 'negative'
            else 0.0,
            axis=1
        )
        
        print("✅ Duygu analizi tamamlandı")
        return news_df
    
    def _default_summary(self, symbol):
        """Varsayılan duygu özeti"""
        return {
            'symbol': symbol,
            'avg_sentiment': 0.0,
            'normalized_sentiment': 0.0,
            'news_count': 0,
            'positive_count': 0,
            'negative_count': 0,
            'neutral_count': 0,
            'latest_date': None
        }
    
    def get_aggregated_sentiment(self, news_df, symbol, days=7):
        """
        Belirli bir hisse için belirli gün aralığındaki ortalama duygu skorunu hesaplar
        
        Args:
            news_df: Haber verileri
            symbol: Hisse sembolü
            days: Son kaç günlük haberler
            
        Returns:
            dict: Toplam duygu bilgileri
        """
        required_columns = {'sentiment_score', 'normalized_score'}
        if news_df is None or news_df.empty or not required_columns.issubset(set(news_df.columns)):
            return self._default_summary(symbol)
        
        # Sembole göre filtrele
        if 'symbol' in news_df.columns:
            symbol_news = news_df[news_df['symbol'] == symbol].copy()
        else:
            print("⚠️ 'symbol' kolonu bulunamadı, tüm haberler kullanılacak")
            symbol_news = news_df.copy()
            symbol_news['symbol'] = symbol
        
        if symbol_news.empty:
            return self._default_summary(symbol)
        
        # Son N günlük haberleri al
        if 'datetime' in symbol_news.columns:
            cutoff_date = datetime.now() - timedelta(days=days)
            try:
                if np.issubdtype(symbol_news['datetime'].dtype, np.number):
                    symbol_news['datetime'] = pd.to_datetime(symbol_news['datetime'], unit='s', errors='coerce')
                else:
                    symbol_news['datetime'] = pd.to_datetime(symbol_news['datetime'], errors='coerce')
                symbol_news = symbol_news[symbol_news['datetime'] >= cutoff_date]
            except Exception as e:
                print(f"⚠️ datetime dönüştürme hatası: {e}")
                symbol_news['datetime'] = pd.NaT
        else:
            symbol_news['datetime'] = pd.NaT
        
        if symbol_news.empty:
            return self._default_summary(symbol)
        
        # İstatistikler
        avg_sentiment = np.nan_to_num(symbol_news['sentiment_score'].mean(), nan=0.0)
        normalized_sentiment = np.nan_to_num(symbol_news['normalized_score'].mean(), nan=0.0)
        sentiment_col = 'sentiment' if 'sentiment' in symbol_news.columns else None
        
        positive_count = int((symbol_news[sentiment_col] == 'positive').sum()) if sentiment_col else 0
        negative_count = int((symbol_news[sentiment_col] == 'negative').sum()) if sentiment_col else 0
        neutral_count = int((symbol_news[sentiment_col] == 'neutral').sum()) if sentiment_col else 0
        
        result = {
            'symbol': symbol,
            'avg_sentiment': float(avg_sentiment),
            'normalized_sentiment': float(normalized_sentiment),
            'news_count': int(len(symbol_news)),
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': neutral_count,
            'latest_date': symbol_news['datetime'].max() if symbol_news['datetime'].notna().any() else None
        }
        
        return result
    
    def analyze_and_save(self, news_csv='news_data.csv', output_csv='news_with_sentiment.csv'):
        """
        CSV'deki haberleri analiz edip yeni CSV'ye kaydeder
        
        Args:
            news_csv: Giriş CSV dosyası
            output_csv: Çıkış CSV dosyası
        """
        input_path = os.path.join(CSV_DIR, news_csv)
        output_path = os.path.join(CSV_DIR, output_csv)
        
        if not os.path.exists(input_path):
            print(f"❌ Dosya bulunamadı: {input_path}")
            return None
        
        print(f"📂 Dosya okunuyor: {news_csv}")
        news_df = pd.read_csv(input_path)
        
        # Analiz yap
        analyzed_df = self.analyze_news_batch(news_df)
        
        # Kaydet
        analyzed_df.to_csv(output_path, index=False)
        print(f"💾 Sonuçlar kaydedildi: {output_csv}")
        
        return analyzed_df

if __name__ == '__main__':
    # Test amaçlı çalıştır
    analyzer = SentimentAnalyzer()
    
    # Test metinleri
    test_texts = [
        "Apple hisseleri yeni iPhone lansmanı sonrası %5 yükseldi",
        "Şirket zarara geçti, yönetim değişikliği bekleniyor",
        "Piyasalar yatay seyrini sürdürüyor"
    ]
    
    print("\n🧪 Test metinleri:")
    for text in test_texts:
        result = analyzer.analyze_sentiment(text)
        print(f"\n📝 Metin: {text}")
        print(f"💭 Duygu: {result['label']} (Skor: {result['score']:.2f})")
