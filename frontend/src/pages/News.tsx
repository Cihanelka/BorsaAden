import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { BackgroundChart } from "@/components/BackgroundChart";
import { Newspaper, ExternalLink, Calendar, Search } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { getCompanyNews } from "@/services/finnhubService";
import { AppHeader } from "@/components/AppHeader";

interface NewsArticle {
  category: string;
  datetime: number;
  headline: string;
  id: number;
  image: string;
  related: string;
  source: string;
  summary: string;
  url: string;
}

const News = () => {
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [symbol, setSymbol] = useState('AAPL');
  const [searchSymbol, setSearchSymbol] = useState('AAPL');

  const fetchNews = async (stockSymbol: string) => {
    setLoading(true);
    setError(null);
    
    try {
      // Son 30 günün haberlerini çek
      const toDate = new Date();
      const fromDate = new Date();
      fromDate.setDate(fromDate.getDate() - 30);
      
      const from = fromDate.toISOString().split('T')[0];
      const to = toDate.toISOString().split('T')[0];
      
      const newsData = await getCompanyNews(stockSymbol, from, to);
      setArticles(newsData.slice(0, 20)); // İlk 20 haberi göster
    } catch (err) {
      console.error('Haber yükleme hatası:', err);
      setError(err instanceof Error ? err.message : "Haberler yüklenirken bir hata oluştu");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNews(symbol);
  }, [symbol]);

  const handleSearch = () => {
    if (searchSymbol.trim()) {
      setSymbol(searchSymbol.trim().toUpperCase());
    }
  };

  const formatDate = (timestamp: number) => {
    const date = new Date(timestamp * 1000);
    return date.toLocaleDateString('tr-TR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      <BackgroundChart />
      
      <AppHeader />

      {/* Main Content */}
      <main className="relative z-10 container mx-auto px-4 py-8">
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <Newspaper className="h-8 w-8 text-primary" />
            <h2 className="text-3xl font-bold text-foreground">
              Şirket Haberleri
            </h2>
          </div>
          <p className="text-muted-foreground">
            Finnhub'tan güncel şirket haberleri
          </p>
        </div>

        {/* Search Section */}
        <Card className="mb-8 border-border/50 bg-card/50 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Search className="h-5 w-5" />
              Şirket Haberlerini Ara
            </CardTitle>
            <CardDescription>
              Hisse senedi sembolü girerek şirket haberlerini görüntüleyin
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2">
              <Input
                placeholder="Örn: AAPL, MSFT, TSLA"
                value={searchSymbol}
                onChange={(e) => setSearchSymbol(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                className="flex-1"
              />
              <Button onClick={handleSearch} disabled={loading}>
                <Search className="h-4 w-4 mr-2" />
                Ara
              </Button>
            </div>
            <div className="text-xs text-muted-foreground mt-2 flex items-center gap-2">
              <span>Şu anda görüntülenen:</span>
              <span className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold">
                {symbol}
              </span>
            </div>
          </CardContent>
        </Card>

        {loading && (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <div className="h-12 w-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-muted-foreground">Haberler yükleniyor...</p>
            </div>
          </div>
        )}

        {error && (
          <Card className="border-destructive/50 bg-destructive/10">
            <CardHeader>
              <CardTitle className="text-destructive">Hata</CardTitle>
              <CardDescription>{error}</CardDescription>
            </CardHeader>
          </Card>
        )}

        {!loading && !error && articles.length === 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Haber Bulunamadı</CardTitle>
              <CardDescription>Şu anda gösterilecek haber bulunmamaktadır.</CardDescription>
            </CardHeader>
          </Card>
        )}

        {!loading && !error && articles.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {articles.map((article) => (
              <Card 
                key={article.id} 
                className="group hover:shadow-lg transition-all duration-300 overflow-hidden border-border/50 bg-card/50 backdrop-blur-sm hover:border-primary/50"
              >
                {article.image && (
                  <div className="relative h-48 overflow-hidden">
                    <img
                      src={article.image}
                      alt={article.headline}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      onError={(e) => {
                        (e.target as HTMLImageElement).style.display = 'none';
                      }}
                    />
                    <div className="absolute top-3 right-3">
                      <Badge variant="secondary" className="bg-background/80 backdrop-blur-sm">
                        {article.source}
                      </Badge>
                    </div>
                    <div className="absolute top-3 left-3">
                      <Badge variant="outline" className="bg-background/80 backdrop-blur-sm">
                        {article.category}
                      </Badge>
                    </div>
                  </div>
                )}
                
                <CardHeader>
                  <CardTitle className="line-clamp-2 text-lg group-hover:text-primary transition-colors">
                    {article.headline}
                  </CardTitle>
                  <CardDescription className="flex items-center gap-2 text-xs">
                    <Calendar className="h-3 w-3" />
                    {formatDate(article.datetime)}
                  </CardDescription>
                </CardHeader>
                
                <CardContent>
                  <p className="text-sm text-muted-foreground line-clamp-3 mb-4">
                    {article.summary || "Özet mevcut değil."}
                  </p>
                  
                  <div className="flex items-center justify-between">
                    <Badge variant="outline" className="text-xs">
                      {article.related}
                    </Badge>
                    
                    <a
                      href={article.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 text-sm text-primary hover:text-primary/80 transition-colors font-medium"
                    >
                      Haberi Oku
                      <ExternalLink className="h-4 w-4" />
                    </a>
                  </div>
                </CardContent>
              </Card>
            ))}
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
              Haberler Finnhub API tarafından sağlanmaktadır.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default News;
