// Teknik göstergeleri hesaplamak için yardımcı fonksiyonlar

export interface TechnicalIndicators {
  rsi: number;
  macd: number;
  signal: number;
  histogram: number;
  bollingerUpper: number;
  bollingerMiddle: number;
  bollingerLower: number;
  atr: number;
  adx: number;
  stochasticK: number;
  stochasticD: number;
  sma20: number;
  sma50: number;
  sma200: number;
  volumeMA: number;
  rsiStrength: number;
}

export function calculateTechnicalIndicators(prices: number[], volumes: number[] = []): TechnicalIndicators {
  // Basit Hareketli Ortalama (SMA)
  const sma = (period: number, offset: number = 0): number => {
    const slice = prices.slice(-period - offset, offset || undefined);
    return slice.reduce((sum, price) => sum + price, 0) / slice.length;
  };

  // Üssel Hareketli Ortalama (EMA)
  const ema = (period: number, offset: number = 0): number => {
    const k = 2 / (period + 1);
    let ema = sma(period, offset + period - 1);
    
    for (let i = offset + period - 2; i >= offset; i--) {
      ema = prices[i] * k + ema * (1 - k);
    }
    
    return ema;
  };

  // RSI (Göreceli Güç Endeksi)
  const calculateRSI = (period: number = 14): number => {
    if (prices.length < period + 1) return 50; // Yeterli veri yoksa nötr değer
    
    let gains = 0;
    let losses = 0;
    
    // İlk periyottaki ortalama kazanç ve kayıplar
    for (let i = 1; i <= period; i++) {
      const diff = prices[i] - prices[i - 1];
      if (diff >= 0) {
        gains += diff;
      } else {
        losses -= diff;
      }
    }
    
    let avgGain = gains / period;
    let avgLoss = losses / period || 1; // Sıfıra bölünmeyi önle
    
    // Sonraki değerler için üssel ortalama
    for (let i = period + 1; i < prices.length; i++) {
      const diff = prices[i] - prices[i - 1];
      if (diff >= 0) {
        avgGain = (avgGain * (period - 1) + diff) / period;
        avgLoss = (avgLoss * (period - 1)) / period;
      } else {
        avgGain = (avgGain * (period - 1)) / period;
        avgLoss = (avgLoss * (period - 1) - diff) / period;
      }
    }
    
    const rs = avgGain / (avgLoss || 1); // Sıfıra bölünmeyi önle
    return 100 - (100 / (1 + rs));
  };

  // MACD (Hareketli Ortalama Yakınsama/Iraksama)
  const calculateMACD = () => {
    const ema12 = ema(12);
    const ema26 = ema(26);
    const macdLine = ema12 - ema26;
    
    // Sinyal hattı (MACD'nin 9 günlük EMA'sı)
    // Basitçe hesaplamak için son 9 MACD değerini kullanıyoruz
    const macdValues = [];
    for (let i = 0; i < 9; i++) {
      macdValues.push(ema(12, i) - ema(26, i));
    }
    const signalLine = macdValues.reduce((sum, val) => sum + val, 0) / macdValues.length;
    
    return {
      macd: macdLine,
      signal: signalLine,
      histogram: macdLine - signalLine
    };
  };

  // Bollinger Bantları
  const calculateBollingerBands = (period: number = 20, stdDev: number = 2) => {
    const middle = sma(period);
    let sum = 0;
    
    // Standart sapma hesapla
    for (let i = 1; i <= period; i++) {
      sum += Math.pow(prices[prices.length - i] - middle, 2);
    }
    const std = Math.sqrt(sum / period);
    
    return {
      middle,
      upper: middle + std * stdDev,
      lower: middle - std * stdDev
    };
  };

  // Stokastik Osilatör
  const calculateStochastic = (period: number = 14, smoothK: number = 3, smoothD: number = 3) => {
    const currentClose = prices[prices.length - 1];
    let lowestLow = Infinity;
    let highestHigh = -Infinity;
    
    // Belirtilen periyottaki en düşük ve en yüksek değerleri bul
    for (let i = 1; i <= period; i++) {
      const idx = prices.length - i;
      if (idx < 0) break;
      
      const high = prices[idx]; // Gerçekte high değeri kullanılmalı
      const low = prices[idx];  // Gerçekte low değeri kullanılmalı
      
      if (high > highestHigh) highestHigh = high;
      if (low < lowestLow) lowestLow = low;
    }
    
    const k = ((currentClose - lowestLow) / (highestHigh - lowestLow)) * 100;
    
    // Basitçe K ve D değerlerini aynı yapıyoruz
    // Gerçek uygulamada farklı hesaplamalar yapılabilir
    return {
      k: k || 50, // NaN kontrolü
      d: k || 50  // NaN kontrolü
    };
  };

  // Hacim Ortalaması
  const calculateVolumeMA = (period: number = 20): number => {
    if (volumes.length === 0) return 0;
    const slice = volumes.slice(-period);
    return slice.reduce((sum, vol) => sum + vol, 0) / slice.length;
  };

  // RSI Güç Göstergesi
  const calculateRSIStrength = (rsiValue: number): number => {
    // RSI değerini 0-1 aralığına normalize et
    if (rsiValue >= 70) return 1;    // Aşırı alım
    if (rsiValue <= 30) return 0;    // Aşırı satım
    return (rsiValue - 30) / 40;     // 30-70 arası lineer dönüşüm
  };

  // Tüm göstergeleri hesapla
  const rsi = calculateRSI();
  const macd = calculateMACD();
  const bollinger = calculateBollingerBands();
  const stochastic = calculateStochastic();
  
  return {
    rsi,
    macd: macd.macd,
    signal: macd.signal,
    histogram: macd.histogram,
    bollingerUpper: bollinger.upper,
    bollingerMiddle: bollinger.middle,
    bollingerLower: bollinger.lower,
    atr: 0, // ATR hesaplaması eklenebilir
    adx: 0, // ADX hesaplaması eklenebilir
    stochasticK: stochastic.k,
    stochasticD: stochastic.d,
    sma20: sma(20),
    sma50: sma(50),
    sma200: sma(200),
    volumeMA: calculateVolumeMA(),
    rsiStrength: calculateRSIStrength(rsi)
  };
}
