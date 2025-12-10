import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { StockSearch } from "@/components/StockSearch";
import { StockChart } from "@/components/StockChart";
import { TechnicalAnalysis } from "@/components/TechnicalAnalysis";
import { StockComments } from "@/components/StockComments";
import { CompanyFinancials } from "@/components/CompanyFinancials";
import { BackgroundChart } from "@/components/BackgroundChart";
import { TrendingUp, BarChart3, MessageCircle, Newspaper, History, LineChart, Building2, Sparkles, LogOut, User, Star } from "lucide-react";
import { getTimeSeries, TimeSeriesData } from "@/services/stockService";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";

interface Stock {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
}

const Index = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, signOut } = useAuth();
  const [selectedStock, setSelectedStock] = useState<Stock | null>(null);
  const [timeSeries, setTimeSeries] = useState<TimeSeriesData[]>([]);
  const [tsLoading, setTsLoading] = useState(false);
  const [tsError, setTsError] = useState<string | null>(null);
  const [isHistOpen, setIsHistOpen] = useState(false);
  const [isTechnicalOpen, setIsTechnicalOpen] = useState(false);
  const [isCompanyOpen, setIsCompanyOpen] = useState(false);
  const [isCommentsOpen, setIsCommentsOpen] = useState(false);
  const [levels, setLevels] = useState<any>(null);
  const [selectedTimeframe, setSelectedTimeframe] = useState<'1day' | '1week' | '1month'>('1day');

  const fetchTS = async () => {
    if (!selectedStock?.symbol) return;
    setTsLoading(true);
    setTsError(null);
    try {
      setTimeSeries(await getTimeSeries(selectedStock.symbol, selectedTimeframe, 30));
    } catch {
      setTsError("Tarihsel veri alınamadı");
    } finally {
      setTsLoading(false);
    }
  };

  const filterTimeSeries = () => timeSeries.slice(-{ '1day': 1, '1week': 7, '1month': 30 }[selectedTimeframe]);

  useEffect(() => {
    // Hisse değiştiğinde veriyi sıfırla ve tüm bölümleri kapat
    setTimeSeries([]);
    setTsError(null);
    setLevels(null);
    setIsHistOpen(false);
    setIsTechnicalOpen(false);
    setIsCompanyOpen(false);
    setIsCommentsOpen(false);
  }, [selectedStock?.symbol]);

  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      <BackgroundChart />
      
      {/* Header */}
      <header className="relative z-10 border-b border-border/50 bg-background/80 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
              <CardContent className="py-3 px-4">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 bg-gradient-to-br from-primary to-blue-600 rounded-lg flex items-center justify-center shadow-lg">
                    <TrendingUp className="h-6 w-6 text-primary-foreground" />
                  </div>
                  <div>
                    <h1 className="text-2xl font-bold bg-gradient-to-r from-primary to-green-500 bg-clip-text text-transparent">
                        Aden Borsa
                    </h1>
                    <p className="text-sm text-muted-foreground">
                      Profesyonel Borsa Analiz Platformu
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <div className="flex items-center gap-3">
              <Link to="/">
                <Button 
                  variant={location.pathname === "/" ? "default" : "ghost"}
                  className="gap-2"
                >
                  <BarChart3 className="h-4 w-4" />
                  <span>Hisse Analizi</span>
                </Button>
              </Link>
              <Link to="/favoriler">
                <Button 
                  variant={location.pathname === "/favoriler" ? "default" : "ghost"}
                  className="gap-2"
                >
                  <Star className="h-4 w-4" />
                  <span>Favorilerim</span>
                </Button>
              </Link>
              <Link to="/haberler">
                <Button 
                  variant={location.pathname === "/haberler" ? "default" : "ghost"}
                  className="gap-2"
                >
                  <Newspaper className="h-4 w-4" />
                  <span>Haberler</span>
                </Button>
              </Link>
              
              <div className="flex items-center gap-2 ml-4 pl-4 border-l border-border">
                <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-card/50">
                  <User className="h-4 w-4 text-muted-foreground" />
                  <Link to="/profil" className="text-sm font-medium hover:underline">
                      {user?.username}
                  </Link>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={async () => {
                    await signOut();
                    navigate('/giris');
                  }}
                  title="Çıkış Yap"
                >
                  <LogOut className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative z-10 container mx-auto px-4 py-8">
        {/* Search Section */}
        <div className="mb-8">
          <Card className="border-border/50 bg-card/80 backdrop-blur-sm max-w-3xl mx-auto mb-6">
            <CardContent className="py-6">
              <div className="text-center">
                <h2 className="text-3xl font-bold text-foreground mb-2">
                  Hisse Senedi Analizi
                </h2>
                <p className="text-muted-foreground">
                   Aradığınız hisse senedini seçin ve detaylı teknik analiz, grafik ve uzman yorumlarına ulaşın.
                </p>
              </div>
            </CardContent>
          </Card>
          
          <div className="flex justify-center">
            <StockSearch 
              onStockSelect={setSelectedStock} 
              selectedStock={selectedStock}
            />
          </div>
        </div>

        {/* Analysis Content */}
        {selectedStock ? (
          <div className="space-y-8">
            {/* Chart Section */}
            <div className="grid grid-cols-1 gap-8">
              <div>
                <StockChart stock={selectedStock} />
                
                {/* Action Buttons */}
                <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-3">
                  <Button
                    variant={isHistOpen ? "default" : "outline"}
                    className="h-auto py-4 flex flex-col items-center gap-2 transition-all"
                    onClick={async () => {
                      const newState = !isHistOpen;
                      setIsHistOpen(newState);
                      if (newState && !tsLoading && timeSeries.length === 0 && selectedStock?.symbol) {
                        await fetchTS();
                      }
                    }}
                  >
                    <History className="h-5 w-5" />
                    <span className="text-sm font-medium">Tarihsel Veriler</span>
                  </Button>
                  
                  <Button
                    variant={isTechnicalOpen ? "default" : "outline"}
                    className="h-auto py-4 flex flex-col items-center gap-2 transition-all"
                    onClick={() => setIsTechnicalOpen(!isTechnicalOpen)}
                  >
                    <LineChart className="h-5 w-5" />
                    <span className="text-sm font-medium">Teknik Analiz</span>
                  </Button>
                  
                  <Button
                    variant={isCompanyOpen ? "default" : "outline"}
                    className="h-auto py-4 flex flex-col items-center gap-2 transition-all"
                    onClick={() => setIsCompanyOpen(!isCompanyOpen)}
                  >
                    <Building2 className="h-5 w-5" />
                    <span className="text-sm font-medium">Şirket Bilgileri</span>
                  </Button>
                  
                  <Button
                    variant={isCommentsOpen ? "default" : "outline"}
                    className="h-auto py-4 flex flex-col items-center gap-2 transition-all"
                    onClick={() => setIsCommentsOpen(!isCommentsOpen)}
                  >
                    <Sparkles className="h-5 w-5" />
                    <span className="text-sm font-medium">AI Yorumlar</span>
                  </Button>
                </div>

                {/* Historical Data Section */}
                {isHistOpen && (
                  <div className="mt-6 animate-in slide-in-from-top-4 duration-300">
                    <Card>
                      <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                          <History className="h-5 w-5 text-primary" />
                          Tarihsel Veriler
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="flex gap-2 mb-4">
                           <button className={`${selectedTimeframe === '1day' ? 'bg-blue-500 text-white' : 'bg-gray-200'} px-4 py-2 rounded`} onClick={() => setSelectedTimeframe('1day')}>1 Gün</button>
                           <button className={`${selectedTimeframe === '1week' ? 'bg-blue-500 text-white' : 'bg-gray-200'} px-4 py-2 rounded`} onClick={() => setSelectedTimeframe('1week')}>1 Hafta</button>
                           <button className={`${selectedTimeframe === '1month' ? 'bg-blue-500 text-white' : 'bg-gray-200'} px-4 py-2 rounded`} onClick={() => setSelectedTimeframe('1month')}>1 Ay</button>
                        </div>

                        {tsLoading && (
                          <div className="py-8 text-center text-muted-foreground">Yükleniyor...</div>
                        )}
                        {tsError && (
                          <div className="py-4 text-destructive">{tsError}</div>
                        )}
                        {!tsLoading && !tsError && filterTimeSeries().length > 0 && (
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
                                {filterTimeSeries().map((d, idx) => (
                                  <TableRow key={`${d.datetime}-${idx}`}>
                                    <TableCell>{new Date(d.datetime).toLocaleDateString('tr-TR')}</TableCell>
                                    <TableCell>${parseFloat(d.open).toFixed(2)}</TableCell>
                                    <TableCell>${parseFloat(d.high).toFixed(2)}</TableCell>
                                    <TableCell>${parseFloat(d.low).toFixed(2)}</TableCell>
                                    <TableCell>${parseFloat(d.close).toFixed(2)}</TableCell>
                                    <TableCell>{Number(d.volume).toLocaleString()}</TableCell>
                                  </TableRow>
                                ))}
                              </TableBody>
                            </Table>
                          </div>
                        )}
                        {!tsLoading && !tsError && filterTimeSeries().length === 0 && (
                          <div className="py-6 text-center text-muted-foreground">Veri bulunamadı</div>
                        )}
                      </CardContent>
                    </Card>
                  </div>
                )}

                {/* Technical Analysis Section */}
                {isTechnicalOpen && (
                  <div className="mt-6 animate-in slide-in-from-top-4 duration-300">
                    <TechnicalAnalysis stock={selectedStock} onLevelsChange={setLevels} />
                  </div>
                )}

                {/* Company Financials Section */}
                {isCompanyOpen && (
                  <div className="mt-6 animate-in slide-in-from-top-4 duration-300">
                    <CompanyFinancials stock={selectedStock} />
                  </div>
                )}

                {/* Comments Section */}
                {isCommentsOpen && (
                  <div className="mt-6 animate-in slide-in-from-top-4 duration-300">
                    <StockComments stock={selectedStock} levels={levels} />
                  </div>
                )}
              </div>
            </div>
          </div>
        ) : (
          /* Welcome State */
          <Card className="border-border/50 bg-card/80 backdrop-blur-sm max-w-4xl mx-auto">
            <CardContent className="py-12">
              <div className="text-center">
                <div className="relative">
                  <div className="h-32 w-32 bg-gradient-to-br from-primary to-blue-600 rounded-full mx-auto mb-6 flex items-center justify-center shadow-lg animate-pulse">
                    <TrendingUp className="h-16 w-16 text-primary-foreground" />
                  </div>
                  
                  <h3 className="text-2xl font-semibold text-foreground mb-4">
                    Hisse Analizi Yapmaya Başlayın
                  </h3>
                  <p className="text-muted-foreground max-w-md mx-auto mb-8">
                    Yukarıdaki arama çubuğundan bir hisse senedi seçerek detaylı analiz ve grafiklere ulaşabilirsiniz.
                  </p>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
                <div className="p-6 bg-card/50 rounded-lg border border-border/50 backdrop-blur-sm">
                  <BarChart3 className="h-8 w-8 text-primary mb-3 mx-auto" />
                  <h4 className="font-semibold text-foreground mb-2">Canlı Grafikler</h4>
                  <p className="text-sm text-muted-foreground">
                    Gerçek zamanlı fiyat hareketleri ve teknik göstergeler
                  </p>
                </div>
                
                <div className="p-6 bg-card/50 rounded-lg border border-border/50 backdrop-blur-sm">
                  <TrendingUp className="h-8 w-8 text-success mb-3 mx-auto" />
                  <h4 className="font-semibold text-foreground mb-2">Teknik Analiz</h4>
                  <p className="text-sm text-muted-foreground">
                    Destek, direnç seviyeleri ve teknik indikatörler
                  </p>
                </div>
                
                <div className="p-6 bg-card/50 rounded-lg border border-border/50 backdrop-blur-sm">
                  <MessageCircle className="h-8 w-8 text-warning mb-3 mx-auto" />
                  <h4 className="font-semibold text-foreground mb-2">AI Yorumlar</h4>
                  <p className="text-sm text-muted-foreground">
                    Yapay zeka destekli analiz ve uzman yorumları
                  </p>
                </div>
              </div>
                </div>
              </div>
            </CardContent>
          </Card>
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
};

export default Index;