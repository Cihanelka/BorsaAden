import { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { getStockQuote, getTimeSeries, StockQuote, TimeSeriesData } from '@/services/stockService';
import { StockAnalysis } from '@/components/StockAnalysis';

export default function StocksPage() {
  const [symbol, setSymbol] = useState('AAPL');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [quote, setQuote] = useState<StockQuote | null>(null);
  const [timeSeries, setTimeSeries] = useState<TimeSeriesData[]>([]);
  const [showAnalysis, setShowAnalysis] = useState(false);

  const fetchStockData = async () => {
    if (!symbol) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const [quoteData, seriesData] = await Promise.all([
        getStockQuote(symbol),
        getTimeSeries(symbol)
      ]);
      
      setQuote(quoteData);
      setTimeSeries(seriesData);
    } catch (err) {
      setError('Veri çekilirken bir hata oluştu. Lütfen hisse kodunu kontrol edin.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStockData();
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchStockData();
  };

  // Fiyat verilerini hazırla
  const chartData = useMemo(() => {
    return timeSeries.map(item => ({
      date: new Date(item.datetime).toLocaleDateString('tr-TR'),
      price: parseFloat(item.close),
      volume: parseFloat(item.volume || '0'),
    }));
  }, [timeSeries]);

  // Fiyat ve hacim verilerini hazırla
  const prices = useMemo(() => 
    timeSeries.map(item => parseFloat(item.close)).reverse(), 
    [timeSeries]
  );
  
  const volumes = useMemo(() => 
    timeSeries.map(item => parseFloat(item.volume || '0')).reverse(), 
    [timeSeries]
  );

  return (
    <div className="container mx-auto p-4">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Hisse Senedi Takip</h1>
        {quote && (
          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className="text-2xl font-bold">{quote.symbol}</div>
              <div className="text-sm text-muted-foreground">{quote.name}</div>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold">{quote.price} {quote.currency || 'USD'}</div>
              <div className={`text-sm ${
                quote.change >= 0 ? 'text-green-500' : 'text-red-500'
              }`}>
                {quote.change >= 0 ? '+' : ''}{quote.change} 
                ({quote.percent_change >= 0 ? '+' : ''}{quote.percent_change}%)
              </div>
            </div>
          </div>
        )}
      </div>
      
      <form onSubmit={handleSubmit} className="mb-6 flex gap-2">
        <Input
          type="text"
          value={symbol}
          onChange={(e) => setSymbol(e.target.value.toUpperCase())}
          placeholder="Hisse kodu girin (Örn: AAPL)"
          className="flex-1"
        />
        <Button type="submit" disabled={loading}>
          {loading ? 'Aranıyor...' : 'Ara'}
        </Button>
        <Button 
          type="button" 
          variant="outline"
          onClick={() => setShowAnalysis(!showAnalysis)}
          disabled={timeSeries.length === 0}
        >
          {showAnalysis ? 'Analizi Gizle' : 'Teknik Analiz Göster'}
        </Button>
      </form>

      {error && (
        <div className="p-4 mb-4 text-red-700 bg-red-100 rounded-md">
          {error}
        </div>
      )}

      {quote && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Fiyat</CardTitle>
              <span className="text-muted-foreground">{quote.currency || 'USD'}</span>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{quote.price}</div>
              <p className={`text-xs ${quote.change >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                {quote.change >= 0 ? '+' : ''}{quote.change} ({quote.percent_change >= 0 ? '+' : ''}{quote.percent_change}%)
              </p>
              {timeSeries.length > 0 && (
                <p className="text-xs text-muted-foreground mt-2 pt-2 border-t">
                  Hacim: {(parseInt(timeSeries[timeSeries.length - 1].volume || '0') / 1000000).toFixed(2)}M
                </p>
              )}
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Önceki Kapanış</CardTitle>
              <span className="text-muted-foreground">{quote.currency || 'USD'}</span>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{quote.previous_close}</div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Değişim</CardTitle>
              <span className="text-muted-foreground">24s</span>
            </CardHeader>
            <CardContent>
              <div className={`text-2xl font-bold ${quote.change >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                {quote.change >= 0 ? '+' : ''}{quote.change}
              </div>
              <p className="text-xs text-muted-foreground">
                {quote.percent_change >= 0 ? '+' : ''}{quote.percent_change}%
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Son Güncelleme</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {new Date(quote.timestamp * 1000).toLocaleTimeString('tr-TR')}
              </div>
              <p className="text-xs text-muted-foreground">
                {new Date(quote.timestamp * 1000).toLocaleDateString('tr-TR')}
              </p>
            </CardContent>
          </Card>
        </div>
      )}
      
      {timeSeries.length > 0 && (
        <>
          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Kapanış Fiyatı</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="date"
                      tick={{ fontSize: 12 }}
                    />
                    <YAxis domain={['auto', 'auto']} />
                    <Tooltip 
                      contentStyle={{
                        backgroundColor: 'rgba(0, 0, 0, 0.9)',
                        border: '1px solid #667eea',
                        borderRadius: '8px',
                        padding: '12px',
                      }}
                      labelStyle={{ color: '#fff', fontWeight: 'bold' }}
                      formatter={(value: any) => {
                        return [`$${parseFloat(String(value)).toFixed(2)}`, 'Fiyat'];
                      }}
                      labelFormatter={(label) => `📅 ${label}`}
                    />
                    <Legend />
                    <Line 
                      type="monotone" 
                      dataKey="price" 
                      stroke="#8884d8" 
                      strokeWidth={2}
                      dot={false}
                      name="Kapanış Fiyatı"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          <Card className="mt-6">
            <CardHeader>
              <CardTitle>İşlem Hacmi</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-[250px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="date"
                      tick={{ fontSize: 12 }}
                    />
                    <YAxis />
                    <Tooltip 
                      contentStyle={{
                        backgroundColor: 'rgba(0, 0, 0, 0.9)',
                        border: '1px solid #667eea',
                        borderRadius: '8px',
                        padding: '12px',
                      }}
                      labelStyle={{ color: '#fff', fontWeight: 'bold' }}
                      formatter={(value: any) => {
                        return [(parseInt(String(value)) / 1000000).toFixed(2) + 'M', 'Hacim'];
                      }}
                      labelFormatter={(label) => `📅 ${label}`}
                    />
                    <Legend />
                    <Bar 
                      dataKey="volume" 
                      fill="#667eea" 
                      name="Hacim"
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </>
      )}
      
      {/* Hisse Analiz Bileşeni */}
      {showAnalysis && timeSeries.length > 0 && (
        <StockAnalysis 
          symbol={symbol}
          prices={prices}
          volumes={volumes}
        />
      )}

      {timeSeries.length > 0 && (
        <>
          <h2 className="text-xl font-semibold mb-4">Tarihsel Veriler</h2>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Tarih</TableHead>
                  <TableHead>Açılış</TableHead>
                  <TableHead>Yüksek</TableHead>
                  <TableHead>Düşük</TableHead>
                  <TableHead>Kapanış</TableHead>
                  <TableHead>Hacim</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {timeSeries.map((data, index) => (
                  <TableRow key={index}>
                    <TableCell>{new Date(data.datetime).toLocaleDateString('tr-TR')}</TableCell>
                    <TableCell>${data.open}</TableCell>
                    <TableCell>${data.high}</TableCell>
                    <TableCell>${data.low}</TableCell>
                    <TableCell>${data.close}</TableCell>
                    <TableCell>{parseInt(data.volume).toLocaleString()}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </>
      )}
    </div>
  );
}
