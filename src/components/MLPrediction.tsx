import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Loader2, TrendingUp, TrendingDown, Minus, Brain, Activity, MessageSquare } from 'lucide-react';
import { toast } from 'sonner';

interface PredictionResult {
  symbol: string;
  prediction: 'AL' | 'SAT' | 'TUT';
  confidence: number;
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
  method?: string;
  timestamp?: string;
  technical_details?: {
    signal: string;
    score: number;
    latest_price: number;
    signals: Record<string, { score: number; reason: string }>;
  };
  sentiment_details?: {
    avg_sentiment: number;
    normalized_sentiment: number;
    positive_count: number;
    negative_count: number;
    neutral_count: number;
    news_count: number;
  };
}

interface MLPredictionProps {
  symbol: string;
  onPredictionReceived?: (result: PredictionResult) => void;
}

export default function MLPrediction({ symbol, onPredictionReceived }: MLPredictionProps) {
  const [loading, setLoading] = useState(false);
  const [prediction, setPrediction] = useState<PredictionResult | null>(null);

  const getPrediction = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:3001/api/ml/predict', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          symbol: symbol,
          use_cached_data: true,
        }),
      });

      const data = await response.json();

      if (data.success) {
        setPrediction(data.result);
        if (onPredictionReceived) {
          onPredictionReceived(data.result);
        }
        toast.success('Tahmin başarıyla alındı!');
      } else {
        toast.error(data.error || 'Tahmin alınamadı');
      }
    } catch (error) {
      console.error('ML prediction error:', error);
      toast.error('ML servisi ile bağlantı kurulamadı');
    } finally {
      setLoading(false);
    }
  };

  const getPredictionColor = (pred: string) => {
    switch (pred) {
      case 'AL':
        return 'bg-green-500 hover:bg-green-600';
      case 'SAT':
        return 'bg-red-500 hover:bg-red-600';
      case 'TUT':
        return 'bg-yellow-500 hover:bg-yellow-600';
      default:
        return 'bg-gray-500';
    }
  };

  const getPredictionIcon = (pred: string) => {
    switch (pred) {
      case 'AL':
        return <TrendingUp className="w-5 h-5" />;
      case 'SAT':
        return <TrendingDown className="w-5 h-5" />;
      case 'TUT':
        return <Minus className="w-5 h-5" />;
      default:
        return null;
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Brain className="w-5 h-5" />
          Random Forest ML Tahmini
        </CardTitle>
        <CardDescription>
          18 özellik (Teknik göstergeler + Haber duygu analizi) ile makine öğrenmesi tahmini
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {!prediction ? (
          <Button
            onClick={getPrediction}
            disabled={loading}
            className="w-full"
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Analiz Ediliyor...
              </>
            ) : (
              <>
                <Brain className="mr-2 h-4 w-4" />
                {symbol} için Tahmin Al
              </>
            )}
          </Button>
        ) : (
          <div className="space-y-4">
            {/* Ana Tahmin */}
            <div className="flex items-center justify-between p-4 rounded-lg bg-muted">
              <div className="flex items-center gap-3">
                {getPredictionIcon(prediction.prediction)}
                <div>
                  <p className="text-sm text-muted-foreground">Öneri</p>
                  <p className="text-2xl font-bold">{prediction.prediction}</p>
                </div>
              </div>
              <Badge className={getPredictionColor(prediction.prediction)}>
                %{(prediction.confidence * 100).toFixed(1)} Güven
              </Badge>
            </div>

            {/* Olasılıklar (Random Forest) */}
            {prediction.probabilities && (
              <div className="p-3 rounded-lg border space-y-2">
                <p className="text-sm font-medium">Tahmin Olasılıkları</p>
                <div className="space-y-1">
                  {Object.entries(prediction.probabilities).map(([cls, prob]) => (
                    <div key={cls} className="flex items-center justify-between">
                      <span className="text-sm">{cls}</span>
                      <div className="flex items-center gap-2">
                        <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div 
                            className={`h-full ${cls === 'AL' ? 'bg-green-500' : cls === 'SAT' ? 'bg-red-500' : 'bg-yellow-500'}`}
                            style={{ width: `${prob * 100}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium w-12 text-right">
                          {(prob * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Skor Detayları */}
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 rounded-lg border">
                <div className="flex items-center gap-2 mb-1">
                  <Activity className="w-4 h-4 text-blue-500" />
                  <p className="text-xs text-muted-foreground">Teknik Analiz</p>
                </div>
                <p className="text-xl font-semibold">
                  {prediction.technical_indicators?.rsi 
                    ? `RSI: ${prediction.technical_indicators.rsi.toFixed(1)}`
                    : prediction.technical_score 
                    ? `%${(prediction.technical_score * 100).toFixed(1)}`
                    : 'N/A'}
                </p>
              </div>

              <div className="p-3 rounded-lg border">
                <div className="flex items-center gap-2 mb-1">
                  <MessageSquare className="w-4 h-4 text-purple-500" />
                  <p className="text-xs text-muted-foreground">Haber Duygusu</p>
                </div>
                <p className="text-xl font-semibold">
                  {prediction.sentiment_analysis?.score !== undefined
                    ? `${prediction.sentiment_analysis.score > 0 ? '+' : ''}${prediction.sentiment_analysis.score.toFixed(2)}`
                    : prediction.sentiment_score !== undefined
                    ? `${prediction.sentiment_score > 0 ? '+' : ''}${prediction.sentiment_score.toFixed(2)}`
                    : 'N/A'}
                </p>
              </div>
            </div>

            {/* Haber İstatistikleri (Random Forest) */}
            {prediction.sentiment_analysis && (
              <div className="p-3 rounded-lg border space-y-2">
                <p className="text-sm font-medium">
                  Haber Analizi ({prediction.sentiment_analysis.news_count} haber)
                </p>
                <div className="flex gap-2 text-xs">
                  <Badge variant="outline" className="bg-green-50">
                    ✅ Pozitif: {(prediction.sentiment_analysis.positive_ratio * 100).toFixed(0)}%
                  </Badge>
                  <Badge variant="outline" className="bg-red-50">
                    ❌ Negatif: {(prediction.sentiment_analysis.negative_ratio * 100).toFixed(0)}%
                  </Badge>
                </div>
              </div>
            )}

            {/* Haber İstatistikleri (Eski Format) */}
            {!prediction.sentiment_analysis && prediction.sentiment_details && (
              <div className="p-3 rounded-lg border space-y-2">
                <p className="text-sm font-medium">Haber Analizi ({prediction.news_count} haber)</p>
                <div className="flex gap-2 text-xs">
                  <Badge variant="outline" className="bg-green-50">
                    ✅ {prediction.sentiment_details.positive_count} Pozitif
                  </Badge>
                  <Badge variant="outline" className="bg-red-50">
                    ❌ {prediction.sentiment_details.negative_count} Negatif
                  </Badge>
                  <Badge variant="outline" className="bg-gray-50">
                    ⚖️ {prediction.sentiment_details.neutral_count} Nötr
                  </Badge>
                </div>
              </div>
            )}

            {/* Teknik Göstergeler (Random Forest) */}
            {prediction.technical_indicators && (
              <div className="p-3 rounded-lg border space-y-2">
                <p className="text-sm font-medium">Teknik Göstergeler</p>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">RSI:</span>
                    <span className="font-medium">{prediction.technical_indicators.rsi.toFixed(1)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">MACD:</span>
                    <span className="font-medium">{prediction.technical_indicators.macd.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Trend:</span>
                    <span className="font-medium">{(prediction.technical_indicators.trend_strength * 100).toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Volume:</span>
                    <span className="font-medium">{prediction.technical_indicators.volume_ratio.toFixed(2)}x</span>
                  </div>
                </div>
                {prediction.current_price && (
                  <p className="text-sm pt-2 border-t">
                    Güncel Fiyat: <span className="font-bold">${prediction.current_price.toFixed(2)}</span>
                  </p>
                )}
              </div>
            )}

            {/* Teknik Göstergeler (Eski Format) */}
            {!prediction.technical_indicators && prediction.technical_details && (
              <div className="p-3 rounded-lg border space-y-2">
                <p className="text-sm font-medium">Teknik Göstergeler</p>
                <div className="space-y-1">
                  {Object.entries(prediction.technical_details.signals).map(([indicator, info]) => (
                    <div key={indicator} className="flex justify-between text-xs">
                      <span className="text-muted-foreground">{indicator}:</span>
                      <span className="font-medium">
                        %{(info.score * 100).toFixed(0)}
                      </span>
                    </div>
                  ))}
                </div>
                {prediction.technical_details.latest_price && (
                  <p className="text-sm pt-2 border-t">
                    Güncel Fiyat: <span className="font-bold">${prediction.technical_details.latest_price.toFixed(2)}</span>
                  </p>
                )}
              </div>
            )}

            {/* Tavsiye ve Model Bilgisi */}
            {prediction.recommendation && (
              <div className="p-3 rounded-lg bg-blue-50 border border-blue-200">
                <p className="text-sm font-medium text-blue-900">
                  💡 {prediction.recommendation}
                </p>
              </div>
            )}

            {/* Metod Bilgisi */}
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>
                {prediction.model_type 
                  ? `Model: ${prediction.model_type}${prediction.features_used ? ` (${prediction.features_used} özellik)` : ''}`
                  : prediction.method === 'ml_model' 
                  ? 'ML Model' 
                  : 'Kural Tabanlı'}
              </span>
              <span>
                {prediction.timestamp && new Date(prediction.timestamp).toLocaleTimeString('tr-TR')}
              </span>
            </div>

            {/* Yeniden Analiz Butonu */}
            <Button
              onClick={getPrediction}
              variant="outline"
              disabled={loading}
              className="w-full"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Yeniden Analiz Ediliyor...
                </>
              ) : (
                'Yeniden Analiz Et'
              )}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
