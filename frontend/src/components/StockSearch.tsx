import { useState, useEffect } from "react";
import { Search, Loader2, TrendingUp, TrendingDown, Star } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";
import { addFavorite, removeFavorite, isFavorite } from "@/services/favoriteService";
import { toast } from "sonner";

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001/api';

export interface Stock {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  previous_close?: number;
  timestamp?: number;
}

const popularStocks: Stock[] = [
  // Teknoloji
  { symbol: "AAPL", name: "Apple Inc.", price: 0, change: 0, changePercent: 0 },
  { symbol: "MSFT", name: "Microsoft", price: 0, change: 0, changePercent: 0 },
  { symbol: "GOOGL", name: "Alphabet Inc.", price: 0, change: 0, changePercent: 0 },
  { symbol: "AMZN", name: "Amazon.com", price: 0, change: 0, changePercent: 0 },
  { symbol: "META", name: "Meta Platforms", price: 0, change: 0, changePercent: 0 },
  { symbol: "TSLA", name: "Tesla Inc.", price: 0, change: 0, changePercent: 0 },
  { symbol: "NVDA", name: "NVIDIA", price: 0, change: 0, changePercent: 0 },
  { symbol: "AMD", name: "Advanced Micro Devices", price: 0, change: 0, changePercent: 0 },
  // Finans
  { symbol: "JPM", name: "JPMorgan Chase", price: 0, change: 0, changePercent: 0 },
  { symbol: "BAC", name: "Bank of America", price: 0, change: 0, changePercent: 0 },
  { symbol: "WFC", name: "Wells Fargo", price: 0, change: 0, changePercent: 0 },
  { symbol: "GS", name: "Goldman Sachs", price: 0, change: 0, changePercent: 0 },
  // Tüketici
  { symbol: "NFLX", name: "Netflix", price: 0, change: 0, changePercent: 0 },
  { symbol: "DIS", name: "Walt Disney", price: 0, change: 0, changePercent: 0 },
  { symbol: "NKE", name: "Nike", price: 0, change: 0, changePercent: 0 },
  { symbol: "SBUX", name: "Starbucks", price: 0, change: 0, changePercent: 0 },
  // Sağlık
  { symbol: "JNJ", name: "Johnson & Johnson", price: 0, change: 0, changePercent: 0 },
  { symbol: "PFE", name: "Pfizer", price: 0, change: 0, changePercent: 0 },
  { symbol: "UNH", name: "UnitedHealth", price: 0, change: 0, changePercent: 0 },
  // Enerji
  { symbol: "XOM", name: "Exxon Mobil", price: 0, change: 0, changePercent: 0 },
];

interface StockSearchProps {
  onStockSelect: (stock: Stock) => void;
  selectedStock?: Stock | null;
  hideFavoriteActions?: boolean;
  initialSymbol?: string;
}

export const StockSearch = ({ onStockSelect, selectedStock, hideFavoriteActions = false, initialSymbol }: StockSearchProps) => {
  const { user } = useAuth();
  const [searchTerm, setSearchTerm] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [stocks, setStocks] = useState<Stock[]>(popularStocks);
  const [error, setError] = useState<string | null>(null);
  const [isFav, setIsFav] = useState(false);
  const [favLoading, setFavLoading] = useState(false);

  // initialSymbol varsa otomatik yükle
  useEffect(() => {
    if (initialSymbol && !selectedStock) {
      const loadInitialStock = async () => {
        setIsLoading(true);
        try {
          const response = await fetch(`${API_BASE_URL}/ml/stock-data`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol: initialSymbol, days: 5 })
          });
          const result = await response.json();
          
          if (result.success && result.data && result.data.length > 0) {
            const latest = result.data[result.data.length - 1];
            const previous = result.data.length > 1 ? result.data[result.data.length - 2] : latest;
            
            const price = parseFloat(latest.close);
            const prevPrice = parseFloat(previous.close);
            const change = price - prevPrice;
            const changePercent = ((change / prevPrice) * 100);
            
            const stock = {
              symbol: initialSymbol,
              name: initialSymbol,
              price: price,
              change: change,
              changePercent: changePercent,
              previous_close: prevPrice,
            };
            
            onStockSelect(stock);
          }
        } catch (err) {
          console.error('Error loading initial stock:', err);
        } finally {
          setIsLoading(false);
        }
      };
      loadInitialStock();
    }
  }, [initialSymbol]);

  // Popüler hisselerin verilerini çek - yfinance ile
  useEffect(() => {
    const fetchPopularStocks = async () => {
      try {
        const updatedStocks = await Promise.all(popularStocks.map(async (stock) => {
          try {
            const response = await fetch(`${API_BASE_URL}/ml/stock-data`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ symbol: stock.symbol, days: 5 })
            });
            const result = await response.json();
            
            if (result.success && result.data && result.data.length > 0) {
              const latest = result.data[result.data.length - 1];
              const previous = result.data.length > 1 ? result.data[result.data.length - 2] : latest;
              
              const price = parseFloat(latest.close);
              const prevPrice = parseFloat(previous.close);
              const change = price - prevPrice;
              const changePercent = ((change / prevPrice) * 100);
              
              return {
                ...stock,
                price: price,
                change: change,
                changePercent: changePercent,
                previous_close: prevPrice,
              };
            }
          } catch (err) {
            console.error(`Error fetching ${stock.symbol}:`, err);
          }
          return stock;
        }));
        setStocks(updatedStocks);
      } catch (err) {
        console.error('Error fetching stock data:', err);
        setError('Veri yüklenirken bir hata oluştu');
      }
    };

    fetchPopularStocks();
  }, []);

  const filteredStocks = searchTerm
    ? stocks.filter(
        (stock) =>
          stock.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
          stock.name.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : stocks;

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchTerm.trim()) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE_URL}/ml/stock-data`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol: searchTerm.toUpperCase(), days: 5 })
      });
      const result = await response.json();
      
      if (!result.success || !result.data || result.data.length === 0) {
        throw new Error('Hisse senedi bulunamadı');
      }
      
      const latest = result.data[result.data.length - 1];
      const previous = result.data.length > 1 ? result.data[result.data.length - 2] : latest;
      
      const price = parseFloat(latest.close);
      const prevPrice = parseFloat(previous.close);
      const change = price - prevPrice;
      const changePercent = ((change / prevPrice) * 100);
      
      const stock = {
        symbol: searchTerm.toUpperCase(),
        name: searchTerm.toUpperCase(),
        price: price,
        change: change,
        changePercent: changePercent,
        previous_close: prevPrice,
      };
      
      onStockSelect(stock);
      setSearchTerm('');
      setIsOpen(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Bir hata oluştu');
      console.error('Search error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStockSelect = (stock: Stock) => {
    onStockSelect(stock);
    setIsOpen(false);
  };

  // Check if current stock is favorite
  useEffect(() => {
    const checkFavorite = async () => {
      if (hideFavoriteActions) return;
      if (selectedStock && user) {
        try {
          const result = await isFavorite(user.id.toString(), selectedStock.symbol);
          setIsFav(result);
        } catch (err) {
          console.error('Error checking favorite:', err);
        }
      }
    };
    checkFavorite();
  }, [selectedStock, user, hideFavoriteActions]);

  const handleToggleFavorite = async () => {
    if (hideFavoriteActions || !selectedStock || !user) return;
    
    setFavLoading(true);
    try {
      if (isFav) {
        await removeFavorite(user.id.toString(), selectedStock.symbol);
        setIsFav(false);
        toast.success('Favorilerden kaldırıldı');
      } else {
        await addFavorite(user.id.toString(), selectedStock.symbol, selectedStock.name);
        setIsFav(true);
        toast.success('Favorilere eklendi');
      }
    } catch (err) {
      console.error('Error toggling favorite:', err);
      toast.error('Bir hata oluştu');
    } finally {
      setFavLoading(false);
    }
  };

  return (
    <div className="relative w-full max-w-md">
      <form onSubmit={handleSearch} className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          type="text"
          placeholder="Hisse kodu girin (Örn: AAPL, MSFT)"
          className="pl-10 pr-4 py-6 text-base"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          onFocus={() => setIsOpen(true)}
          disabled={isLoading}
        />
        {isLoading && (
          <Loader2 className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 animate-spin text-muted-foreground" />
        )}
      </form>

      {error && (
        <div className="mt-2 text-sm text-destructive">
          {error}
        </div>
      )}
      
      {isOpen && (
        <Card className="absolute z-10 mt-1 w-full shadow-lg border-border/50">
          <div className="max-h-60 overflow-y-auto">
            {filteredStocks.length > 0 ? (
              <>
                <div className="p-2 text-xs text-muted-foreground border-b border-border/50">
                  Popüler Hisseler
                </div>
                {filteredStocks.map((stock) => (
                  <div
                    key={stock.symbol}
                    className={`flex items-center justify-between p-3 hover:bg-muted/50 cursor-pointer transition-colors ${
                      selectedStock?.symbol === stock.symbol ? 'bg-muted/30' : ''
                    }`}
                    onClick={() => handleStockSelect(stock)}
                  >
                    <div className="flex-1">
                      <div className="font-medium">{stock.symbol}</div>
                      <div className="text-sm text-muted-foreground truncate max-w-[180px]">
                        {stock.name}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-medium">${stock.price.toFixed(2)}</div>
                      <div className={`text-xs ${
                        stock.change >= 0 ? 'text-success' : 'text-destructive'
                      }`}>
                        {stock.change >= 0 ? '↑' : '↓'} {Math.abs(stock.change).toFixed(2)} ({stock.changePercent.toFixed(2)}%)
                      </div>
                    </div>
                  </div>
                ))}
              </>
            ) : (
              <div className="p-4 text-center text-muted-foreground">
                Hisse bulunamadı
              </div>
            )}
          </div>
        </Card>
      )}

      {selectedStock && !hideFavoriteActions && (
        <div className="mt-4 p-4 bg-card rounded-lg border border-border shadow-lg">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <h3 className="font-bold text-lg text-foreground">{selectedStock.symbol}</h3>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={handleToggleFavorite}
                  disabled={favLoading}
                >
                  <Star className={`h-4 w-4 ${isFav ? 'fill-warning text-warning' : 'text-muted-foreground'}`} />
                </Button>
              </div>
              <p className="text-sm text-muted-foreground">{selectedStock.name}</p>
            </div>
            <div className="text-right">
              <div className="text-2xl font-mono font-bold">
                ${selectedStock.price.toFixed(2)}
              </div>
              <div className="flex items-center gap-2">
                {selectedStock.change > 0 ? (
                  <>
                    <TrendingUp className="h-4 w-4 text-success" />
                    <span className="text-success font-medium">
                      +${selectedStock.change.toFixed(2)} (+{selectedStock.changePercent.toFixed(2)}%)
                    </span>
                  </>
                ) : (
                  <>
                    <TrendingDown className="h-4 w-4 text-destructive" />
                    <span className="text-destructive font-medium">
                      ${selectedStock.change.toFixed(2)} ({selectedStock.changePercent.toFixed(2)}%)
                    </span>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};