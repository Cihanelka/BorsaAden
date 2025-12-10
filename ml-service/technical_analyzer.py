"""
Teknik analiz göstergeleri hesaplama modülü
"""
import pandas as pd
import numpy as np
import pandas_ta as ta
from config import *

class TechnicalAnalyzer:
    """Hisse fiyat verilerinden teknik göstergeleri hesaplar"""
    
    def __init__(self):
        """Teknik analiz modülünü başlatır"""
        print("📊 Teknik analiz modülü hazır")
    
    def calculate_rsi(self, df, period=14):
        """
        RSI (Relative Strength Index) hesaplar
        
        Args:
            df: OHLCV DataFrame
            period: RSI periyodu
            
        Returns:
            Series: RSI değerleri
        """
        rsi = ta.rsi(df['close'], length=period)
        return rsi
    
    def calculate_macd(self, df, fast=12, slow=26, signal=9):
        """
        MACD (Moving Average Convergence Divergence) hesaplar
        
        Args:
            df: OHLCV DataFrame
            
        Returns:
            DataFrame: MACD, MACD Signal, MACD Histogram
        """
        macd = ta.macd(df['close'], fast=fast, slow=slow, signal=signal)
        return macd
    
    def calculate_bollinger_bands(self, df, period=20, std=2):
        """
        Bollinger Bands hesaplar
        
        Args:
            df: OHLCV DataFrame
            period: MA periyodu
            std: Standart sapma çarpanı
            
        Returns:
            DataFrame: Upper, Middle, Lower bands
        """
        bb = ta.bbands(df['close'], length=period, std=std)
        return bb
    
    def calculate_sma(self, df, periods=[20, 50, 200]):
        """
        SMA (Simple Moving Average) hesaplar
        
        Args:
            df: OHLCV DataFrame
            periods: SMA periyotları listesi
            
        Returns:
            DataFrame: Her periyot için SMA
        """
        result = pd.DataFrame()
        for period in periods:
            result[f'SMA_{period}'] = ta.sma(df['close'], length=period)
        return result
    
    def calculate_ema(self, df, periods=[12, 26]):
        """
        EMA (Exponential Moving Average) hesaplar
        
        Args:
            df: OHLCV DataFrame
            periods: EMA periyotları listesi
            
        Returns:
            DataFrame: Her periyot için EMA
        """
        result = pd.DataFrame()
        for period in periods:
            result[f'EMA_{period}'] = ta.ema(df['close'], length=period)
        return result
    
    def calculate_stochastic(self, df, k=14, d=3, smooth_k=3):
        """
        Stochastic Oscillator hesaplar
        
        Args:
            df: OHLCV DataFrame
            
        Returns:
            DataFrame: %K ve %D değerleri
        """
        stoch = ta.stoch(df['high'], df['low'], df['close'], k=k, d=d, smooth_k=smooth_k)
        return stoch
    
    def calculate_atr(self, df, period=14):
        """
        ATR (Average True Range) hesaplar
        
        Args:
            df: OHLCV DataFrame
            period: ATR periyodu
            
        Returns:
            Series: ATR değerleri
        """
        atr = ta.atr(df['high'], df['low'], df['close'], length=period)
        return atr
    
    def calculate_obv(self, df):
        """
        OBV (On-Balance Volume) hesaplar
        
        Args:
            df: OHLCV DataFrame
            
        Returns:
            Series: OBV değerleri
        """
        obv = ta.obv(df['close'], df['volume'])
        return obv
    
    def calculate_all_indicators(self, df):
        """
        Tüm teknik göstergeleri hesaplar ve DataFrame'e ekler
        
        Args:
            df: OHLCV DataFrame
            
        Returns:
            DataFrame: Tüm göstergeler eklenmiş DataFrame
        """
        if df.empty:
            print("⚠️ Boş DataFrame, göstergeler hesaplanamıyor")
            return df
        
        print(f"🔧 {len(df)} satır için teknik göstergeler hesaplanıyor...")
        
        result_df = df.copy()
        
        try:
            # RSI
            result_df['RSI'] = self.calculate_rsi(df)
            
            # MACD
            macd_df = self.calculate_macd(df)
            result_df = pd.concat([result_df, macd_df], axis=1)
            
            # Bollinger Bands
            bb_df = self.calculate_bollinger_bands(df)
            result_df = pd.concat([result_df, bb_df], axis=1)
            
            # SMA
            sma_df = self.calculate_sma(df)
            result_df = pd.concat([result_df, sma_df], axis=1)
            
            # EMA
            ema_df = self.calculate_ema(df)
            result_df = pd.concat([result_df, ema_df], axis=1)
            
            # Stochastic
            stoch_df = self.calculate_stochastic(df)
            result_df = pd.concat([result_df, stoch_df], axis=1)
            
            # ATR
            result_df['ATR'] = self.calculate_atr(df)
            
            # OBV
            result_df['OBV'] = self.calculate_obv(df)
            
            # Fiyat değişim yüzdesi
            result_df['price_change_pct'] = result_df['close'].pct_change() * 100
            
            # Volatilite (20 günlük)
            result_df['volatility'] = result_df['close'].rolling(window=20).std()
            
            print("✅ Teknik göstergeler hesaplandı")
            
        except Exception as e:
            print(f"❌ Gösterge hesaplama hatası: {str(e)}")
        
        return result_df
    
    def get_technical_signals(self, df):
        """
        Teknik göstergelere dayalı alım/satım sinyalleri üretir
        
        Args:
            df: Teknik göstergeler içeren DataFrame
            
        Returns:
            dict: Sinyal skorları ve açıklamalar
        """
        if df.empty or len(df) < 2:
            return {'score': 0.5, 'signal': 'TUT', 'signals': {}}
        
        # Son satırı al
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        signals = {}
        signal_score = 0
        signal_count = 0
        
        # RSI Sinyali (30 altı oversold, 70 üstü overbought)
        if pd.notna(latest.get('RSI')):
            rsi = latest['RSI']
            if rsi < 30:
                signals['RSI'] = {'score': 0.8, 'reason': f'RSI çok düşük ({rsi:.1f}), oversold'}
                signal_score += 0.8
            elif rsi > 70:
                signals['RSI'] = {'score': 0.2, 'reason': f'RSI çok yüksek ({rsi:.1f}), overbought'}
                signal_score += 0.2
            else:
                signals['RSI'] = {'score': 0.5, 'reason': f'RSI nötr ({rsi:.1f})'}
                signal_score += 0.5
            signal_count += 1
        
        # MACD Sinyali
        if pd.notna(latest.get('MACD_12_26_9')) and pd.notna(latest.get('MACDs_12_26_9')):
            macd = latest['MACD_12_26_9']
            signal_line = latest['MACDs_12_26_9']
            prev_macd = prev.get('MACD_12_26_9', macd)
            prev_signal = prev.get('MACDs_12_26_9', signal_line)
            
            # Çaprazlama kontrolü
            if prev_macd <= prev_signal and macd > signal_line:
                signals['MACD'] = {'score': 0.75, 'reason': 'MACD yukarı kesti (bullish)'}
                signal_score += 0.75
            elif prev_macd >= prev_signal and macd < signal_line:
                signals['MACD'] = {'score': 0.25, 'reason': 'MACD aşağı kesti (bearish)'}
                signal_score += 0.25
            else:
                signals['MACD'] = {'score': 0.5, 'reason': 'MACD nötr'}
                signal_score += 0.5
            signal_count += 1
        
        # Bollinger Bands Sinyali
        if pd.notna(latest.get('BBL_20_2.0')) and pd.notna(latest.get('BBU_20_2.0')):
            close = latest['close']
            bb_lower = latest['BBL_20_2.0']
            bb_upper = latest['BBU_20_2.0']
            
            if close <= bb_lower:
                signals['BB'] = {'score': 0.7, 'reason': 'Fiyat alt banda değdi'}
                signal_score += 0.7
            elif close >= bb_upper:
                signals['BB'] = {'score': 0.3, 'reason': 'Fiyat üst banda değdi'}
                signal_score += 0.3
            else:
                signals['BB'] = {'score': 0.5, 'reason': 'Fiyat bantlar içinde'}
                signal_score += 0.5
            signal_count += 1
        
        # SMA Trendi
        if pd.notna(latest.get('SMA_20')) and pd.notna(latest.get('SMA_50')):
            close = latest['close']
            sma20 = latest['SMA_20']
            sma50 = latest['SMA_50']
            
            if close > sma20 > sma50:
                signals['SMA'] = {'score': 0.7, 'reason': 'Fiyat MA\'ların üstünde (uptrend)'}
                signal_score += 0.7
            elif close < sma20 < sma50:
                signals['SMA'] = {'score': 0.3, 'reason': 'Fiyat MA\'ların altında (downtrend)'}
                signal_score += 0.3
            else:
                signals['SMA'] = {'score': 0.5, 'reason': 'Fiyat MA\'larda karışık'}
                signal_score += 0.5
            signal_count += 1
        
        # Stochastic Sinyali
        if pd.notna(latest.get('STOCHk_14_3_3')):
            stoch_k = latest['STOCHk_14_3_3']
            if stoch_k < 20:
                signals['STOCH'] = {'score': 0.7, 'reason': f'Stochastic oversold ({stoch_k:.1f})'}
                signal_score += 0.7
            elif stoch_k > 80:
                signals['STOCH'] = {'score': 0.3, 'reason': f'Stochastic overbought ({stoch_k:.1f})'}
                signal_score += 0.3
            else:
                signals['STOCH'] = {'score': 0.5, 'reason': f'Stochastic nötr ({stoch_k:.1f})'}
                signal_score += 0.5
            signal_count += 1
        
        # Ortalama skor hesapla
        avg_score = signal_score / signal_count if signal_count > 0 else 0.5
        
        # Karar ver
        if avg_score >= BUY_THRESHOLD:
            signal = 'AL'
        elif avg_score <= SELL_THRESHOLD:
            signal = 'SAT'
        else:
            signal = 'TUT'
        
        return {
            'score': avg_score,
            'signal': signal,
            'signals': signals,
            'latest_price': latest['close'] if 'close' in latest else None,
            'date': latest.get('date', None)
        }

if __name__ == '__main__':
    # Test amaçlı çalıştır
    import os
    
    analyzer = TechnicalAnalyzer()
    
    # Test verisi oluştur (örnek)
    test_csv = os.path.join(CSV_DIR, 'stock_data.csv')
    if os.path.exists(test_csv):
        print(f"📂 Test dosyası okunuyor: {test_csv}")
        df = pd.read_csv(test_csv)
        
        # İlk hisse için test
        if not df.empty and 'symbol' in df.columns:
            test_symbol = df['symbol'].iloc[0]
            symbol_df = df[df['symbol'] == test_symbol].copy()
            symbol_df = symbol_df.sort_values('date')
            
            print(f"\n🧪 {test_symbol} için teknik analiz:")
            analyzed_df = analyzer.calculate_all_indicators(symbol_df)
            signals = analyzer.get_technical_signals(analyzed_df)
            
            print(f"\n📊 Teknik Sinyal: {signals['signal']}")
            print(f"💯 Skor: {signals['score']:.2f}")
            print(f"📈 Güncel Fiyat: ${signals['latest_price']:.2f}")
            print(f"\n🔍 Detaylı Sinyaller:")
            for indicator, info in signals['signals'].items():
                print(f"  {indicator}: {info['reason']} (Skor: {info['score']:.2f})")
