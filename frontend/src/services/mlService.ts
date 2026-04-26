/**
 * Created by: Aden Borsa Team
 * Created At: 2025
 * Subject: ML servis entegrasyonu - Python backend üzerinden tahmin, teknik analiz ve sentiment
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001/api';
const API_URL = `${API_BASE_URL}/ml`;

export interface ModelResult {
  prediction: string;
  confidence: number;
  backtest_f1: number;
}

export interface MLPrediction {
  symbol: string;
  prediction: 'AL' | 'SAT' | 'TUT' | 'UP' | 'DOWN' | 'NEUTRAL';
  confidence: number;
  // Enhanced prediction format
  prediction_numeric?: number;
  probabilities?: {
    AL?: number;
    SAT?: number;
    TUT?: number;
    UP?: number;
    DOWN?: number;
    NEUTRAL?: number;
  };
  disclaimer?: string;
  // Random Forest yeni format
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
  method?: 'ml_model' | 'enhanced' | 'ensemble';
  timestamp?: string;
  price_data?: {
    current: number;
    change: number;
    change_percent: number;
  };
  signals?: string[];
  volatility?: number;
  volume_trend?: number;
  // Ensemble alanları
  best_model?: string;
  best_model_backtest_f1?: number;
  all_models?: Record<string, ModelResult>;
  total_models?: number;
  sentiment_impact?: string;
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

    const data = await response.json();
    if (!response.ok) {
      return { success: false, error: data.error || `HTTP error! status: ${response.status}` };
    }

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
/**
 * Enhanced ML tahmin al (Production-ready model)
 */
export async function getEnhancedPrediction(symbol: string): Promise<MLResponse> {
  try {
    const response = await fetch(`${API_URL}/predict-enhanced`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ symbol }),
    });

    const data = await response.json();
    if (!response.ok) {
      return { success: false, error: data.error || `HTTP error! status: ${response.status}` };
    }
    
    // Convert enhanced format to MLPrediction format
    if (data.success) {
      const enhanced = data as any;
      return {
        success: true,
        result: {
          symbol: symbol,
          prediction: enhanced.prediction as 'UP' | 'DOWN' | 'NEUTRAL',
          confidence: enhanced.confidence || 0,
          probabilities: enhanced.probabilities,
          prediction_numeric: enhanced.prediction_numeric,
          disclaimer: enhanced.disclaimer,
          method: 'enhanced',
          timestamp: new Date().toISOString()
        }
      };
    }
    
    return data;
  } catch (error) {
    console.error('Enhanced prediction error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Enhanced tahmin alınamadı',
    };
  }
}

/**
 * Toplu tahmin al
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
 * Ensemble ML tahmin al (10 model, en yüksek confidence)
 */
export async function getEnsemblePrediction(symbol: string): Promise<MLResponse> {
  try {
    const response = await fetch(`${API_URL}/predict-ensemble`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ symbol }),
    });

    const data = await response.json();
    if (!response.ok) {
      return { success: false, error: data.error || `HTTP error! status: ${response.status}` };
    }

    if (data.success) {
      return {
        success: true,
        result: {
          symbol,
          prediction: data.prediction as 'UP' | 'DOWN' | 'NEUTRAL',
          confidence: data.confidence || 0,
          probabilities: data.probabilities,
          prediction_numeric: data.prediction_numeric,
          disclaimer: data.disclaimer,
          method: 'ensemble',
          timestamp: data.timestamp || new Date().toISOString(),
          best_model: data.best_model,
          best_model_backtest_f1: data.best_model_backtest_f1,
          all_models: data.all_models,
          total_models: data.total_models,
          sentiment_impact: data.sentiment_impact,
        },
      };
    }

    return data;
  } catch (error) {
    console.error('Ensemble prediction error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Ensemble tahmin alınamadı',
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
