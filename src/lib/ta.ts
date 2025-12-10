// src/lib/ta.ts
export type Bar = { datetime:string; open:number; high:number; low:number; close:number; volume:number };

export function toBars(values: any[]): Bar[] {
  return values.map(v => ({
    datetime: v.datetime,
    open: +v.open, high: +v.high, low: +v.low, close: +v.close, volume: +v.volume
  })).sort((a,b)=> new Date(a.datetime).getTime()-new Date(b.datetime).getTime());
}

// Klasik Pivot (önceki gün)
export function pivotLevels(prevHigh:number, prevLow:number, prevClose:number) {
  const P = (prevHigh + prevLow + prevClose) / 3;
  const R1 = 2*P - prevLow;
  const S1 = 2*P - prevHigh;
  const R2 = P + (prevHigh - prevLow);
  const S2 = P - (prevHigh - prevLow);
  const R3 = prevHigh + 2*(P - prevLow);
  const S3 = prevLow - 2*(prevHigh - P);
  return { P, R1, S1, R2, S2, R3, S3 };
}

// Fibonacci Pivot
export function fibonacciPivot(prevHigh:number, prevLow:number, prevClose:number) {
  const P = (prevHigh + prevLow + prevClose) / 3;
  const range = prevHigh - prevLow;
  const R1 = P + 0.382 * range;
  const R2 = P + 0.618 * range;
  const R3 = P + 1.000 * range;
  const S1 = P - 0.382 * range;
  const S2 = P - 0.618 * range;
  const S3 = P - 1.000 * range;
  return { P, R1, S1, R2, S2, R3, S3 };
}

// Camarilla Pivot
export function camarillaPivot(prevHigh:number, prevLow:number, prevClose:number) {
  const range = prevHigh - prevLow;
  const P = (prevHigh + prevLow + prevClose) / 3;
  const R1 = prevClose + range * 1.1 / 12;
  const R2 = prevClose + range * 1.1 / 6;
  const R3 = prevClose + range * 1.1 / 4;
  const S1 = prevClose - range * 1.1 / 12;
  const S2 = prevClose - range * 1.1 / 6;
  const S3 = prevClose - range * 1.1 / 4;
  return { P, R1, S1, R2, S2, R3, S3 };
}

// Woodie's Pivot
export function woodiesPivot(prevHigh:number, prevLow:number, prevClose:number, todayOpen:number) {
  const P = (prevHigh + prevLow + 2*todayOpen) / 4;
  const R1 = 2*P - prevLow;
  const R2 = P + (prevHigh - prevLow);
  const R3 = prevHigh + 2*(P - prevLow);
  const S1 = 2*P - prevHigh;
  const S2 = P - (prevHigh - prevLow);
  const S3 = prevLow - 2*(prevHigh - P);
  return { P, R1, S1, R2, S2, R3, S3 };
}

// DeMark's Pivot
export function demarkPivot(prevHigh:number, prevLow:number, prevClose:number, todayOpen:number) {
  let X: number;
  if (todayOpen < prevClose) {
    X = prevHigh + 2*prevLow + todayOpen;
  } else if (todayOpen > prevClose) {
    X = 2*prevHigh + prevLow + todayOpen;
  } else {
    X = prevHigh + prevLow + 2*todayOpen;
  }
  const P = X / 4;
  const R1 = X / 2 - prevLow;
  const S1 = X / 2 - prevHigh;
  return { P, R1, S1, R2: NaN, S2: NaN, R3: NaN, S3: NaN };
}

// Tüm pivot yöntemlerini hesapla
export function calculateAllPivots(prevHigh:number, prevLow:number, prevClose:number, todayOpen:number) {
  return {
    classic: pivotLevels(prevHigh, prevLow, prevClose),
    fibonacci: fibonacciPivot(prevHigh, prevLow, prevClose),
    camarilla: camarillaPivot(prevHigh, prevLow, prevClose),
    woodies: woodiesPivot(prevHigh, prevLow, prevClose, todayOpen),
    demark: demarkPivot(prevHigh, prevLow, prevClose, todayOpen)
  };
}

// Rolling destek/direnç (w gün)
export function rollingLevels(bars: Bar[], w=20) {
  if (bars.length < w) return { support: NaN, resistance: NaN };
  const last = bars.slice(-w);
  const support = Math.min(...last.map(b=>b.low));
  const resistance = Math.max(...last.map(b=>b.high));
  return { support, resistance };
}

// EMA basit
export function ema(series:number[], span:number) {
  const k = 2/(span+1);
  let e = series[0];
  const out=[e];
  for (let i=1;i<series.length;i++){ e = series[i]*k + e*(1-k); out.push(e); }
  return out;
}

// RSI(14) basit
export function rsi(closes:number[], period=14) {
  if (closes.length <= period) return NaN;
  const gains:number[] = [], losses:number[] = [];
  for (let i=1;i<closes.length;i++){
    const ch = closes[i]-closes[i-1];
    gains.push(Math.max(ch,0)); losses.push(Math.max(-ch,0));
  }
  const avg = (arr:number[],n:number, iEnd:number) =>
    arr.slice(iEnd-n,iEnd).reduce((a,b)=>a+b,0)/n;

  let rs = avg(gains, period, period) / Math.max(avg(losses, period, period), 1e-9);
  let r = 100 - 100/(1+rs);
  for (let i=period+1;i<gains.length;i++){
    const prevAvgGain = (rs * avg(losses,1,i) + gains[i]) // not exact Welles Wilder, good enough
    const prevAvgLoss = (avg(losses,1,i) + losses[i])
  }
  // Minimalist: son kapanışa göre Wilder yaklaşımı:
  let ag = gains.slice(0,period).reduce((a,b)=>a+b,0)/period;
  let al = losses.slice(0,period).reduce((a,b)=>a+b,0)/period;
  for (let i=period;i<gains.length;i++){
    ag = (ag*(period-1)+gains[i])/period;
    al = (al*(period-1)+losses[i])/period;
  }
  rs = ag / Math.max(al,1e-9);
  return 100 - 100/(1+rs);
}

// ATR (Average True Range) - Volatilite ölçümü
export function atr(bars: Bar[], period=14) {
  if (bars.length < period+1) return NaN;
  const trueRanges: number[] = [];
  
  for (let i=1; i<bars.length; i++) {
    const high = bars[i].high;
    const low = bars[i].low;
    const prevClose = bars[i-1].close;
    
    // True Range = max(high-low, |high-prevClose|, |low-prevClose|)
    const tr = Math.max(
      high - low,
      Math.abs(high - prevClose),
      Math.abs(low - prevClose)
    );
    trueRanges.push(tr);
  }
  
  // İlk ATR: basit ortalama
  let atrValue = trueRanges.slice(0, period).reduce((a,b)=>a+b,0) / period;
  
  // Sonraki ATR değerleri: Wilder smoothing
  for (let i=period; i<trueRanges.length; i++) {
    atrValue = (atrValue * (period-1) + trueRanges[i]) / period;
  }
  
  return atrValue;
}

// Tampon bölge hesaplama - Çoklu yöntem
export function calculateBufferZone(
  bars: Bar[], 
  supportLevel: number, 
  resistanceLevel: number,
  currentPrice: number
) {
  const atrValue = atr(bars, 14);
  
  // 1. ATR bazlı tolerans (en güvenilir)
  const atrTolerance = atrValue * 0.5; // ATR'nin yarısı
  
  // 2. Yüzdelik tolerans
  const percentTolerance = currentPrice * 0.015; // %1.5
  
  // 3. Destek/Direnç aralığı bazlı
  const rangeTolerance = Math.abs(resistanceLevel - supportLevel) * 0.1; // %10
  
  // En sağlıklı: ATR ve yüzdelik ortalaması (volatiliteyi ve fiyat seviyesini dengeler)
  const optimalTolerance = Number.isFinite(atrValue) 
    ? (atrTolerance + percentTolerance) / 2 
    : percentTolerance;
  
  return {
    support: {
      lower: supportLevel - optimalTolerance,
      upper: supportLevel + optimalTolerance
    },
    resistance: {
      lower: resistanceLevel - optimalTolerance,
      upper: resistanceLevel + optimalTolerance
    },
    tolerance: optimalTolerance,
    atr: atrValue,
    method: Number.isFinite(atrValue) ? 'ATR + Yüzdelik' : 'Yüzdelik'
  };
}
