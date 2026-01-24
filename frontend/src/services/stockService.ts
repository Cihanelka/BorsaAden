const API_KEY = '9535cc258b9f4f668bdc4059c99180d0';
const BASE_URL = 'https://api.twelvedata.com';

export interface StockQuote {
  symbol: string;
  name: string;
  price: number;
  change: number;
  percent_change: number;
  previous_close: number;
  timestamp: number;
  currency?: string;
}

export interface TimeSeriesData {
  datetime: string;
  open: string;
  high: string;
  low: string;
  close: string;
  volume: string;
}

export const getStockQuote = async (symbol: string): Promise<StockQuote> => {
  const response = await fetch(
    `${BASE_URL}/quote?symbol=${symbol}&apikey=${API_KEY}`
  );
  if (!response.ok) {
    throw new Error('Hisse senedi verisi alınamadı');
  }
  return response.json();
};

export const getTimeSeries = async (
  symbol: string,
  interval: string = '1day',
  outputsize: number = 30
): Promise<TimeSeriesData[]> => {
  const response = await fetch(
    `${BASE_URL}/time_series?symbol=${symbol}&interval=${interval}&outputsize=${outputsize}&apikey=${API_KEY}`
  );
  
  if (!response.ok) {
    throw new Error('Tarihsel veri alınamadı');
  }
  
  const data = await response.json();
  const values = data.values || [];
  
  // Tarihe göre eskiden yeniye sırala
  return values.sort((a: TimeSeriesData, b: TimeSeriesData) => {
    return new Date(a.datetime).getTime() - new Date(b.datetime).getTime();
  });
};
