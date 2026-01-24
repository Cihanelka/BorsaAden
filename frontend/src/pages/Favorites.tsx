import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { BackgroundChart } from "@/components/BackgroundChart";
import { Star, Trash2, RefreshCw, BarChart3 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getFavorites, removeFavorite } from "@/services/favoriteService";
import { toast } from "sonner";
import { AppHeader } from "@/components/AppHeader";

interface Favorite {
  id: number;
  symbol: string;
  stock_name: string;
  created_at: string;
}

interface StockQuote {
  symbol: string;
  name: string;
  price: number;
  change: number;
  percent_change: number;
}

export default function Favorites() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [favorites, setFavorites] = useState<Favorite[]>([]);
  const [quotes, setQuotes] = useState<Record<string, StockQuote>>({});
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchFavorites = async () => {
    try {
      const data = await getFavorites();
      setFavorites(data);
      if (data.length > 0) fetchQuotes(data);
    } catch (error) {
      console.error('Error fetching favorites:', error);
      toast.error('Favoriler yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  const fetchQuotes = async (favs) => {
    setRefreshing(true);
    const quotesData = await Promise.all(favs.map(async (fav) => {
      try {
        const response = await fetch(`https://api.twelvedata.com/quote?symbol=${fav.symbol}&apikey=9535cc258b9f4f668bdc4059c99180d0`);
        const data = await response.json();
        if (data.status !== 'error') {
          return {
            ...fav,
            price: parseFloat(data.close || 0),
            change: parseFloat(data.change || 0),
            percent_change: parseFloat(data.percent_change || 0),
          };
        }
      } catch (error) {
        console.error(`Error fetching quote for ${fav.symbol}:`, error);
      }
      return null;
    }));

    setQuotes(Object.fromEntries(quotesData.filter(Boolean).map(q => [q.symbol, q])));
    setRefreshing(false);
  };

  useEffect(() => {
    fetchFavorites();
  }, []);

  const handleRemoveFavorite = async (symbol: string) => {
    try {
      await removeFavorite(user!.id.toString(), symbol);
      setFavorites(favorites.filter(f => f.symbol !== symbol));
      toast.success('Favorilerden kaldırıldı');
    } catch (error) {
      console.error('Error removing favorite:', error);
      toast.error('Favori kaldırılamadı');
    }
  };

  const handleStockClick = (symbol: string) => {
    navigate('/', { state: { selectedSymbol: symbol } });
  };

  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      <BackgroundChart />
      
      <AppHeader />

      {/* Main Content */}
      <main className="relative z-10 container mx-auto px-4 py-8">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h2 className="text-3xl font-bold text-foreground mb-2">
              Favori Hisselerim
            </h2>
            <p className="text-muted-foreground">
              Takip ettiğiniz {favorites.length} hisse senedi
            </p>
          </div>
          <Button
            onClick={() => fetchQuotes(favorites)}
            disabled={refreshing || favorites.length === 0}
            variant="outline"
            className="gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
            Fiyatları Yenile
          </Button>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="h-12 w-12 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
          </div>
        ) : favorites.length === 0 ? (
          <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
            <CardContent className="py-20">
              <div className="text-center">
                <Star className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-foreground mb-2">
                  Henüz favori hisse eklemediniz
                </h3>
                <p className="text-muted-foreground mb-6">
                  Hisse analizi sayfasından yıldız butonuna tıklayarak favorilere ekleyebilirsiniz
                </p>
                <Link to="/">
                  <Button>
                    <BarChart3 className="h-4 w-4 mr-2" />
                    Hisse Ara
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {favorites.map((favorite) => {
              const quote = quotes[favorite.symbol];
              return (
                <Card 
                  key={favorite.id} 
                  className="border-border/50 bg-card/50 backdrop-blur-sm hover:bg-card/80 transition-all cursor-pointer group"
                >
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex-1" onClick={() => handleStockClick(favorite.symbol)}>
                        <CardTitle className="text-lg flex items-center gap-2">
                          {favorite.symbol}
                          <Star className="h-4 w-4 fill-warning text-warning" />
                        </CardTitle>
                        <p className="text-sm text-muted-foreground mt-1">
                          {quote?.name || favorite.stock_name}
                        </p>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleRemoveFavorite(favorite.symbol);
                        }}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent onClick={() => handleStockClick(favorite.symbol)}>
                    {quote ? (
                      <div>
                        <div className="text-2xl font-bold font-mono mb-2">
                          ${quote.price.toFixed(2)}
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge 
                            variant={quote.change >= 0 ? "default" : "destructive"}
                            className={quote.change >= 0 ? "bg-success" : ""}
                          >
                            {quote.change >= 0 ? '↑' : '↓'} ${Math.abs(quote.change).toFixed(2)}
                          </Badge>
                          <span className={`text-sm font-medium ${
                            quote.change >= 0 ? 'text-success' : 'text-destructive'
                          }`}>
                            {quote.percent_change >= 0 ? '+' : ''}{quote.percent_change.toFixed(2)}%
                          </span>
                        </div>
                      </div>
                    ) : (
                      <div className="text-sm text-muted-foreground">
                        Fiyat bilgisi yükleniyor...
                      </div>
                    )}
                    <div className="mt-3 pt-3 border-t border-border/30">
                      <p className="text-xs text-muted-foreground">
                        Eklenme: {new Date(favorite.created_at).toLocaleDateString('tr-TR')}
                      </p>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="relative z-10 border-t border-border/50 bg-background/80 backdrop-blur-sm mt-20">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              © 2025 Aden Borsa. Tüm Hakları Saklıdır.
            </p>
            <p className="text-xs text-muted-foreground">
              Bu Platform Yatırım Tavsiyesi Vermez. Kendi Riskinizi Değerlendirin.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
