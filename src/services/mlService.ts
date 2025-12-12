/**
 * ML (Machine Learning) servis entegrasyonu
 * Python ML servisinden hisse tahminleri alır
 */

const API_URL = 'http://localhost:3001/api/ml';

export interface MLPrediction {
  symbol: string;
  prediction: 'AL' | 'SAT' | 'TUT';
  confidence: number;
  // Random Forest yeni format
  probabilities?: {
    AL: number;
    SAT: number;
    TUT: number;
  };
  current_price?: number;
  technical_indicators?: {
    rsi: number;
    macd: number;
    trend_strength: number;
    volume_ratio: number;
  };
  sentiment_analysis?: {
    score: number;
    positive_ratio: number;
    negative_ratio: number;
    news_count: number;
  };
  recommendation?: string;
  model_type?: string;
  features_used?: number;
  // Eski format desteği
  technical_score?: number;
  sentiment_score?: number;
  news_count?: number;
  method?: 'ml_model';
  timestamp?: string;
  price_data?: {
    current: number;
    change: number;
    change_percent: number;
  };
  signals?: string[];
  volatility?: number;
  volume_trend?: number;
}

export interface MLResponse {
  success: boolean;
  result?: MLPrediction;
  error?: string;
}

export interface TechnicalAnalysisResult {
  success: boolean;
  result?: {
    symbol: string;
    indicators: {
      rsi: number;
      macd: { macd: number; signal: number; histogram: number };
      bollinger: { upper: number; middle: number; lower: number };
      sma_20: number;
      sma_50: number;
      ema_12: number;
      ema_26: number;
      stochastic: { k: number; d: number };
      atr: number;
      obv: number;
    };
    signals: {
      rsi_signal: string;
      macd_signal: string;
      bb_signal: string;
      trend_signal: string;
      overall_signal: string;
    };
    score: number;
  };
  error?: string;
}

export interface SentimentSummary {
  success: boolean;
  result?: {
    symbol: string;
    period_days: number;
    total_news: number;
    sentiment_distribution: {
      positive: number;
      negative: number;
      neutral: number;
    };
    average_score: number;
    recent_headlines: Array<{
      datetime: string;
      headline: string;
      sentiment: string;
      score: number;
    }>;
  };
  error?: string;
}

/**
 * Hisse senedi için ML tabanlı tahmin al
 */
export async function getMLPrediction(symbol: string, useCachedData: boolean = true): Promise<MLResponse> {
  try {
    const response = await fetch(`${API_URL}/predict`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ symbol, use_cached_data: useCachedData }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('ML prediction error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Tahmin alınamadı',
    };
  }
}

/**
 * Teknik analiz sonuçlarını al
 */
export async function getTechnicalAnalysis(symbol: string): Promise<TechnicalAnalysisResult> {
  try {
    const response = await fetch(`${API_URL}/technical-analysis`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ symbol }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Technical analysis error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Teknik analiz alınamadı',
    };
  }
}

/**
 * Duygu analizi özetini al
 */
export async function getSentimentSummary(symbol: string, days: number = 7): Promise<SentimentSummary> {
  try {
    const response = await fetch(`${API_URL}/sentiment-summary`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ symbol, days }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Sentiment summary error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Duygu analizi alınamadı',
    };
  }
}

/**
 * Toplu tahmin al (birden fazla hisse için)
 */
export async function getBatchPredictions(symbols: string[]): Promise<{
  success: boolean;
  results?: MLPrediction[];
  error?: string;
}> {
  try {
    const response = await fetch(`${API_URL}/predict-batch`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ symbols }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Batch predictions error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Toplu tahmin alınamadı',
    };
  }
}

/**
 * ML servisi sağlık kontrolü
 */
export async function checkMLServiceHealth(): Promise<{
  status: string;
  message?: string;
  error?: string;
}> {
  try {
    const response = await fetch(`${API_URL}/health`);
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('ML service health check error:', error);
    return {
      status: 'error',
      error: error instanceof Error ? error.message : 'ML servisi yanıt vermiyor',
    };
  }
}
