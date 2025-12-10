import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { stockPredictionModel } from '@/lib/stockPredictionModel';

type StockAnalysisProps = {
  symbol: string;
  prices: number[];
  volumes?: number[];
};

export function StockAnalysis({ symbol, prices, volumes = [] }: StockAnalysisProps) {
  const [analysis, setAnalysis] = useState<{
    direction: 'UP' | 'DOWN' | 'NEUTRAL';
    confidence: number;
    analysis: string;
    indicators: any;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const analyzeStock = async () => {
      if (prices.length < 30) {
        setError('Analiz için en az 30 günlük veri gereklidir');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);
        
        // Modeli başlat ve tahmin yap
        await stockPredictionModel.initialize();
        const result = await stockPredictionModel.predictStock(prices, volumes);
        
        setAnalysis({
          direction: result.direction,
          confidence: result.confidence,
          analysis: result.analysis,
          indicators: result.indicators,
        });
      } catch (err) {
        console.error('Analiz hatası:', err);
        setError('Hisse analizi sırasında bir hata oluştu. Lütfen tekrar deneyin.');
      } finally {
        setLoading(false);
      }
    };

    analyzeStock();
  }, [prices, volumes]);

  // Yön ikonunu belirle
  const getDirectionIcon = () => {
    if (!analysis) return '➡️';
    
    switch (analysis.direction) {
      case 'UP': return '📈';
      case 'DOWN': return '📉';
      default: return '➡️';
    }
  };

  // Yön rengini belirle
  const getDirectionColor = () => {
    if (!analysis) return 'text-gray-500';
    
    switch (analysis.direction) {
      case 'UP': return 'text-green-500';
      case 'DOWN': return 'text-red-500';
      default: return 'text-yellow-500';
    }
  };

  // Güven yüzdesini hesapla
  const confidencePercent = analysis ? Math.round(analysis.confidence * 100) : 0;

  // Teknik gösterge kartı
  const IndicatorCard = ({ title, value, isGood, isBad }: {
    title: string;
    value: string | number;
    isGood?: boolean;
    isBad?: boolean;
  }) => (
    <div className="flex flex-col items-center p-4 border rounded-lg">
      <span className="text-sm text-muted-foreground">{title}</span>
      <span className={`text-lg font-semibold ${
        isGood ? 'text-green-500' : isBad ? 'text-red-500' : ''
      }`}>
        {value}
      </span>
    </div>
  );

  if (loading) {
    return (
      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Hisse Analizi Yükleniyor...</CardTitle>
        </CardHeader>
        <CardContent className="flex justify-center py-8">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="mt-6 border-red-200 bg-red-50">
        <CardHeader>
          <CardTitle className="text-red-600">Hata</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-red-600">{error}</p>
        </CardContent>
      </Card>
    );
  }

  if (!analysis) {
    return (
      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Analiz Bulunamadı</CardTitle>
        </CardHeader>
        <CardContent>
          <p>Hisse analizi yapılamadı.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6 mt-6">
      {/* Genel Analiz Kartı */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <CardTitle>{symbol} Teknik Analizi</CardTitle>
            <span className={`text-3xl ${getDirectionColor()}`}>
              {getDirectionIcon()}
            </span>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <div className="flex justify-between mb-1">
              <span className="text-sm font-medium">Tahmin Güveni</span>
              <span className="text-sm font-medium">{confidencePercent}%</span>
            </div>
            <Progress value={confidencePercent} className="h-2" />
          </div>
          
          <div className="p-4 bg-muted/50 rounded-lg">
            <h4 className="font-medium mb-2">Yapay Zeka Yorumu:</h4>
            <p className="text-sm">{analysis.analysis}</p>
          </div>
        </CardContent>
      </Card>

      {/* Teknik Göstergeler */}
      <Card>
        <CardHeader>
          <CardTitle>Teknik Göstergeler</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            <IndicatorCard 
              title="RSI (14)" 
              value={analysis.indicators.rsi?.toFixed(2) || 'N/A'}
              isGood={analysis.indicators.rsi < 30}
              isBad={analysis.indicators.rsi > 70}
            />
            <IndicatorCard 
              title="MACD" 
              value={analysis.indicators.macd?.toFixed(4) || 'N/A'}
              isGood={analysis.indicators.macd > 0}
              isBad={analysis.indicators.macd < 0}
            />
            <IndicatorCard 
              title="Stokastik %K" 
              value={analysis.indicators.stochasticK?.toFixed(2) || 'N/A'}
              isGood={analysis.indicators.stochasticK < 20}
              isBad={analysis.indicators.stochasticK > 80}
            />
            <IndicatorCard 
              title="Hacim (Ort.)" 
              value={analysis.indicators.volumeMA ? (analysis.indicators.volumeMA / 1000).toFixed(1) + 'K' : 'N/A'}
            />
            <IndicatorCard 
              title="SMA (20)" 
              value={analysis.indicators.sma20?.toFixed(2) || 'N/A'}
            />
            <IndicatorCard 
              title="SMA (50)" 
              value={analysis.indicators.sma50?.toFixed(2) || 'N/A'}
            />
            <IndicatorCard 
              title="SMA (200)" 
              value={analysis.indicators.sma200?.toFixed(2) || 'N/A'}
            />
            <IndicatorCard 
              title="Bollinger Üst" 
              value={analysis.indicators.bollingerUpper?.toFixed(2) || 'N/A'}
            />
            <IndicatorCard 
              title="Bollinger Alt" 
              value={analysis.indicators.bollingerLower?.toFixed(2) || 'N/A'}
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
