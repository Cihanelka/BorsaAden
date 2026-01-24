import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from "recharts";
import { useEffect, useState } from "react";

export interface StockData {
  datetime: string;
  open: string;
  high: string;
  low: string;
  close: string;
  volume: string;
}

interface StockChartProps {
  stock: {
    symbol: string;
    name: string;
    price: number;
    change: number;
    changePercent: number;
    previous_close?: number;
  };
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString);
  return date.toLocaleDateString('tr-TR', { month: 'short', day: 'numeric' });
};

export const StockChart = ({ stock }: StockChartProps) => {
  const [chartData, setChartData] = useState<StockData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const isPositive = stock.change >= 0;

  useEffect(() => {
    const fetchChartData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        // yfinance endpoint'i kullan
        const response = await fetch(
          'http://localhost:3001/api/ml/stock-data',
          {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol: stock.symbol, days: 30 })
          }
        );
        
        const result = await response.json();
        
        if (!result.success || !result.data) {
          throw new Error(result.error || 'Grafik verileri alınamadı');
        }
        
        // Veriyi formatla - Date field'ını datetime'a map et
        const formattedData = result.data.map((item: any) => ({
          datetime: item.Date || item.date || item.datetime,
          open: item.open,
          high: item.high,
          low: item.low,
          close: item.close,
          volume: item.volume
        }));
        
        setChartData(formattedData);
      } catch (err) {
        console.error('Grafik verisi yüklenirken hata:', err);
        setError('Grafik verileri yüklenemedi. Lütfen daha sonra tekrar deneyin.');
      } finally {
        setIsLoading(false);
      }
    };

    if (stock?.symbol) {
      fetchChartData();
    }
  }, [stock.symbol]);

  const formatTooltip = (value: any, name: string) => {
    if (name === "close" || name === 'price') {
      return [`$${parseFloat(value).toFixed(2)}`, "Fiyat"];
    }
    if (name === "volume") {
      return [parseInt(value).toLocaleString(), "Hacim"];
    }
    return [value, name];
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Grafik Yükleniyor...</CardTitle>
        </CardHeader>
        <CardContent className="h-80 flex items-center justify-center">
          <div className="animate-pulse text-muted-foreground">
            Veriler yükleniyor...
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Hata</CardTitle>
        </CardHeader>
        <CardContent className="h-80 flex items-center justify-center">
          <div className="text-destructive">{error}</div>
        </CardContent>
      </Card>
    );
  }
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">
          {stock.name} ({stock.symbol})
        </CardTitle>
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">
            ${stock.price.toFixed(2)}
          </span>
          <span className={`text-xs px-2 py-1 rounded ${isPositive ? 'bg-success/10 text-success' : 'bg-destructive/10 text-destructive'}`}>
            {isPositive ? '↑' : '↓'} {Math.abs(stock.change).toFixed(2)} ({stock.changePercent.toFixed(2)}%)
          </span>
        </div>
      </CardHeader>
      <CardContent className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                <stop
                  offset="5%"
                  stopColor={isPositive ? "#10B981" : "#EF4444"}
                  stopOpacity={0.8}
                />
                <stop
                  offset="95%"
                  stopColor={isPositive ? "#10B981" : "#EF4444"}
                  stopOpacity={0.1}
                />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
            <XAxis
              dataKey="datetime"
              tick={{ fontSize: 12, fill: '#666' }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => formatDate(value)}
              minTickGap={30}
            />
            <YAxis
              domain={['auto', 'auto']}
              tick={{ fontSize: 12, fill: '#666' }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => `$${value}`}
              width={60}
            />
            <Tooltip
              formatter={(value: any, name: string) => {
                if (name === "close" || name === 'price') {
                  return [`$${parseFloat(String(value)).toFixed(2)}`, "Fiyat"];
                }
                if (name === "volume") {
                  const vol = parseInt(String(value));
                  if (vol >= 1000000) {
                    return [(vol / 1000000).toFixed(2) + 'M', "Hacim"];
                  }
                  return [vol.toLocaleString(), "Hacim"];
                }
                return [String(value), name];
              }}
              labelFormatter={(label) => `📅 ${formatDate(label)}`}
              contentStyle={{
                backgroundColor: 'rgba(0, 0, 0, 0.9)',
                border: '1px solid #667eea',
                borderRadius: '0.5rem',
                boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
                color: '#fff'
              }}
            />
            <Area
              type="monotone"
              dataKey="close"
              stroke={isPositive ? "#10B981" : "#EF4444"}
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorPrice)"
              dot={false}
              activeDot={{
                r: 4,
                strokeWidth: 2,
                fill: 'white',
                stroke: isPositive ? "#10B981" : "#EF4444"
              }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};