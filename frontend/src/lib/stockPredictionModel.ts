import * as tf from '@tensorflow/tfjs';
import { TechnicalIndicators, calculateTechnicalIndicators } from './technicalIndicators';

type PredictionResult = {
  direction: 'UP' | 'DOWN' | 'NEUTRAL';
  confidence: number;
  indicators: TechnicalIndicators;
  analysis: string;
};

class StockPredictionModel {
  private model: tf.LayersModel | null = null;
  private isTrained: boolean = false;
  private readonly SEQUENCE_LENGTH = 30; // 30 günlük veri ile tahmin yap
  private readonly FEATURES = 15; // Kullanılacak özellik sayısı

  // Modeli başlat
  public async initialize() {
    if (this.model) return;

    // LSTM tabanlı model oluştur
    this.model = tf.sequential({
      layers: [
        // Giriş katmanı
        tf.layers.lstm({
          units: 64,
          inputShape: [this.SEQUENCE_LENGTH, this.FEATURES],
          returnSequences: true,
          kernelInitializer: 'glorotNormal',
        }),
        tf.layers.dropout({ rate: 0.2 }),
        
        // İkinci LSTM katmanı
        tf.layers.lstm({
          units: 32,
          returnSequences: false,
          kernelInitializer: 'glorotNormal',
        }),
        tf.layers.dropout({ rate: 0.2 }),
        
        // Çıkış katmanı
        tf.layers.dense({
          units: 3, // YUKARI, AŞAĞI, NÖTR
          activation: 'softmax',
          kernelInitializer: 'glorotNormal',
        }),
      ],
    });

    // Modeli derle
    this.model.compile({
      optimizer: tf.train.adam(0.001),
      loss: 'categoricalCrossentropy',
      metrics: ['accuracy'],
    });

    // Örnek verilerle modeli hazırla (gerçek eğitim değil)
    await this.pretrainWithSampleData();
  }

  // Örnek verilerle modeli ön eğitme
  private async pretrainWithSampleData() {
    // Burada gerçek verilerle değiştirilecek
    const sampleData = this.generateSampleData(1000);
    const { inputs, labels } = this.prepareTrainingData(sampleData);

    // Modeli eğit
    await this.model!.fit(inputs, labels, {
      epochs: 10,
      batchSize: 32,
      validationSplit: 0.2,
      verbose: 0,
      callbacks: {
        onEpochEnd: (epoch, logs) => {
          console.log(`Epoch ${epoch + 1}: loss = ${logs?.loss?.toFixed(4)}, accuracy = ${logs?.acc?.toFixed(4)}`);
        },
      },
    });

    this.isTrained = true;
  }

  // Örnek veri oluştur (gerçek uygulamada API'den gelecek)
  private generateSampleData(count: number): number[][][] {
    const data: number[][][] = [];
    
    for (let i = 0; i < count; i++) {
      const sequence: number[][] = [];
      
      for (let j = 0; j < this.SEQUENCE_LENGTH; j++) {
        // Rastgele teknik gösterge değerleri oluştur
        const rsi = 30 + Math.random() * 40; // 30-70 arası
        const macd = -2 + Math.random() * 4; // -2 ile +2 arası
        const volume = Math.random() * 1000000; // 0-1M arası
        const price = 100 + Math.random() * 100; // 100-200 arası
        
        sequence.push([
          rsi,
          macd,
          price * 1.02, // bollingerUpper
          price,        // bollingerMiddle
          price * 0.98, // bollingerLower
          price * 0.97, // support
          price * 1.03, // resistance
          price,        // currentPrice
          volume,
          price * (0.98 + Math.random() * 0.04), // sma20
          price * (0.97 + Math.random() * 0.06), // sma50
          price * (0.95 + Math.random() * 0.1),  // sma200
          price * 0.02, // atr
          25 + Math.random() * 30, // adx (25-55 arası)
          30 + Math.random() * 40, // stochasticK (30-70 arası)
        ]);
      }
      
      data.push(sequence);
    }
    
    return data;
  }

  // Eğitim verilerini hazırla
  private prepareTrainingData(data: number[][][]) {
    const xs: number[][][] = [];
    const ys: number[] = [];

    data.forEach(sequence => {
      // Son gün hariç tüm günleri giriş olarak al
      const x = sequence.slice(0, -1);
      
      // Son günün yönünü çıkış olarak al
      const lastPrice = sequence[sequence.length - 1][7]; // currentPrice
      const prevPrice = sequence[sequence.length - 2][7]; // bir önceki günün fiyatı
      
      // Yönü belirle (0: AŞAĞI, 1: NÖTR, 2: YUKARI)
      let direction = 1; // NÖTR
      const changePercent = ((lastPrice - prevPrice) / prevPrice) * 100;
      
      if (Math.abs(changePercent) > 0.5) { // %0.5'ten fazla değişim
        direction = changePercent > 0 ? 2 : 0;
      }
      
      xs.push(x);
      ys.push(direction);
    });

    return {
      inputs: tf.tensor3d(xs),
      labels: tf.oneHot(tf.tensor1d(ys, 'int32'), 3).toFloat(),
    };
  }

  // Hisse senedi için tahmin yap
  public async predictStock(prices: number[], volumes: number[] = []): Promise<PredictionResult> {
    if (!this.model) {
      await this.initialize();
    }

    // Teknik göstergeleri hesapla
    const indicators = calculateTechnicalIndicators(prices, volumes);
    
    // Model girişi için veriyi hazırla
    const sequence: number[][] = [];
    
    // Son 30 günlük veriyi kullan
    for (let i = Math.max(0, prices.length - this.SEQUENCE_LENGTH); i < prices.length; i++) {
      const priceSlice = prices.slice(Math.max(0, i - 30), i + 1);
      const volumeSlice = volumes.slice(Math.max(0, i - 30), i + 1);
      const currentIndicators = calculateTechnicalIndicators(priceSlice, volumeSlice);
      
      sequence.push([
        currentIndicators.rsi,
        currentIndicators.macd,
        currentIndicators.bollingerUpper,
        currentIndicators.bollingerMiddle,
        currentIndicators.bollingerLower,
        currentIndicators.bollingerLower * 0.99, // support (basitçe alt bantın biraz altı)
        currentIndicators.bollingerUpper * 1.01, // resistance (üst bantın biraz üstü)
        prices[i],
        volumes[i] || 0,
        currentIndicators.sma20,
        currentIndicators.sma50,
        currentIndicators.sma200,
        currentIndicators.atr,
        currentIndicators.adx,
        currentIndicators.stochasticK,
      ]);
    }
    
    // Eksik verileri doldur
    while (sequence.length < this.SEQUENCE_LENGTH) {
      sequence.unshift(sequence[0] || Array(this.FEATURES).fill(0));
    }
    
    // Tahmin yap
    const input = tf.tensor3d([sequence]);
    const prediction = this.model!.predict(input) as tf.Tensor;
    const [upProb, neutralProb, downProb] = Array.from((await prediction.data()));
    
    // Sonucu yorumla
    let direction: 'UP' | 'DOWN' | 'NEUTRAL' = 'NEUTRAL';
    let confidence = neutralProb;
    
    if (upProb > downProb && upProb > neutralProb) {
      direction = 'UP';
      confidence = upProb;
    } else if (downProb > upProb && downProb > neutralProb) {
      direction = 'DOWN';
      confidence = downProb;
    }
    
    // Analiz metni oluştur
    const analysis = this.generateAnalysis(direction, confidence, indicators);
    
    return {
      direction,
      confidence,
      indicators,
      analysis,
    };
  }
  
  // Teknik göstergelere göre analiz metni oluştur
  private generateAnalysis(
    direction: 'UP' | 'DOWN' | 'NEUTRAL',
    confidence: number,
    indicators: TechnicalIndicators
  ): string {
    const { rsi, macd, stochasticK, stochasticD, sma20, sma50, sma200 } = indicators;
    
    const confidenceText = confidence > 0.7 ? 'yüksek güvenilirlikle' : 
                          confidence > 0.5 ? 'orta güvenilirlikle' : 'düşük güvenilirlikle';
    
    let analysis = `Analiz sonucu ${confidenceText} `;
    
    // Genel yön
    if (direction === 'UP') {
      analysis += "yükseliş eğilimi tespit edilmiştir. ";
    } else if (direction === 'DOWN') {
      analysis += "düşüş eğilimi tespit edilmiştir. ";
    } else {
      analysis += "belirgin bir yön tespit edilememiştir. ";
    }
    
    // RSI yorumu
    if (rsi > 70) {
      analysis += "RSI değeri aşırı alım bölgesinde, düzeltme beklenebilir. ";
    } else if (rsi < 30) {
      analysis += "RSI değeri aşırı satım bölgesinde, toparlanma beklenebilir. ";
    }
    
    // MACD yorumu
    if (macd > 0) {
      analysis += "MACD pozitif bölgede, yükseliş sinyali. ";
    } else {
      analysis += "MACD negatif bölgede, düşüş sinyali. ";
    }
    
    // Hareketli ortalamalar
    if (sma20 > sma50 && sma50 > sma200) {
      analysis += "Kısa ve orta vadeli hareketli ortalamalar yukarı yönlü sıralanmış, güçlü yükseliş sinyali. ";
    } else if (sma20 < sma50 && sma50 < sma200) {
      analysis += "Kısa ve orta vadeli hareketli ortalamalar aşağı yönlü sıralanmış, güçlü düşüş sinyali. ";
    }
    
    // Stokastik yorumu
    if (stochasticK > 80) {
      analysis += "Stokastik aşırı alım bölgesinde, dikkatli olunmalı. ";
    } else if (stochasticK < 20) {
      analysis += "Stokastik aşırı satım bölgesinde, alım fırsatı olabilir. ";
    }
    
    // Son öneri
    if (direction === 'UP' && confidence > 0.6) {
      analysis += "Güçlü alım sinyali, pozisyon açılabilir. ";
    } else if (direction === 'DOWN' && confidence > 0.6) {
      analysis += "Güçlü satış sinyali, mevcut pozisyonlar gözden geçirilmeli. ";
    } else {
      analysis += "Piyasa belirsiz, yeni pozisyon açmadan önce ek sinyaller beklenmeli. ";
    }
    
    return analysis;
  }
}

// Singleton örneği oluştur
export const stockPredictionModel = new StockPredictionModel();
