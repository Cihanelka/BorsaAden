import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { StockSearch } from "@/components/StockSearch";
import { StockChart } from "@/components/StockChart";
import { TechnicalAnalysis } from "@/components/TechnicalAnalysis";
import { StockComments } from "@/components/StockComments";
import { CompanyFinancials } from "@/components/CompanyFinancials";
import { BackgroundChart } from "@/components/BackgroundChart";
import { TrendingUp, BarChart3, MessageCircle, Newspaper, History, LineChart, Building2, Sparkles, Star, Lock } from "lucide-react";
import { getTimeSeries, TimeSeriesData } from "@/services/stockService";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { AppHeader } from "@/components/AppHeader";

interface Stock {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
}

const Index = () => {
  const { user } = useAuth();
  const location = useLocation();
  const [selectedStock, setSelectedStock] = useState<Stock | null>(null);
  const [timeSeries, setTimeSeries] = useState<TimeSeriesData[]>([]);
  const [tsLoading, setTsLoading] = useState(false);
  const [tsError, setTsError] = useState<string | null>(null);
  const [openSection, setOpenSection] = useState<'hist' | 'tech' | 'company' | 'comments' | null>(null);
  const [levels, setLevels] = useState<any>(null);
  const [selectedTimeframe, setSelectedTimeframe] = useState<'1day' | '1week' | '1month'>('1day');

  const fetchTS = async () => {
    if (!selectedStock?.symbol) return;
    setTsLoading(true);
    setTsError(null);
    try {
      const daysMap = { '1day': 1, '1week': 7, '1month': 30 };
      const days = daysMap[selectedTimeframe];

      // ML servisinden yfinance ile veri çek
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001/api';
      const response = await fetch(`${API_BASE_URL}/ml/stock-data`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol: selectedStock.symbol, days: days })
      });

      const result = await response.json();

      if (result.success && result.data && result.data.length > 0) {
        // yfinance formatını TimeSeriesData formatına çevir
        const formattedData = result.data.map((item: any) => ({
          datetime: item.date || item.Date || '',
          open: item.open?.toString() || '0',
          high: item.high?.toString() || '0',
          low: item.low?.toString() || '0',
          close: item.close?.toString() || '0',
          volume: item.volume?.toString() || '0'
        }));

        // Tarihe göre sırala (eskiden yeniye)
        formattedData.sort((a: TimeSeriesData, b: TimeSeriesData) => {
          return new Date(a.datetime).getTime() - new Date(b.datetime).getTime();
        });

        setTimeSeries(formattedData);
      } else {
        setTsError("Veri bulunamadı");
      }
    } catch (error) {
      console.error('Tarihsel veri hatası:', error);
      setTsError("Tarihsel veri alınamadı");
    } finally {
      setTsLoading(false);
    }
  };

  useEffect(() => {
    // Hisse değiştiğinde veriyi sıfırla ve tüm bölümleri kapat
    setTimeSeries([]);
    setTsError(null);
    setLevels(null);
    setOpenSection(null);
  }, [selectedStock?.symbol]);

  // Zaman dilimi değiştiğinde veriyi yeniden çek
  useEffect(() => {
    if (openSection === 'hist' && selectedStock?.symbol) {
      fetchTS();
    }
  }, [selectedTimeframe]);

  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      <BackgroundChart />

      <AppHeader />

      {/* Main Content */}
      <main className="relative z-10 container mx-auto px-4 py-8">
        {/* Search Section */}
        <div className="mb-8">
          <div className="text-center max-w-3xl mx-auto mb-6 space-y-2">
            <h2 className="text-3xl font-bold text-foreground">
              Hisse Senedi Analizi
            </h2>
            <p className="text-muted-foreground font-semibold">
              Aradığınız Hisse Senedini Seçin Ve Detaylı Teknik Analiz, Grafik Ve AI Yorumuna Ulaşın.
            </p>
          </div>

          <div className="flex justify-center">
            <StockSearch
              onStockSelect={setSelectedStock}
              selectedStock={selectedStock}
              initialSymbol={(location.state as any)?.selectedSymbol}
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
                    variant={openSection === "hist" ? "default" : "outline"}
                    className="h-auto py-4 flex flex-col items-center gap-2 transition-all"
                    onClick={async () => {
                      const next = openSection === "hist" ? null : "hist";
                      setOpenSection(next);
                      if (next === "hist" && !tsLoading && timeSeries.length === 0 && selectedStock?.symbol) {
                        await fetchTS();
                      }
                    }}
                  >
                    <History className="h-5 w-5" />
                    <span className="text-sm font-medium">Tarihsel Veriler</span>
                  </Button>

                  <Button
                    variant={openSection === "tech" ? "default" : "outline"}
                    className="h-auto py-4 flex flex-col items-center gap-2 transition-all"
                    onClick={() => setOpenSection(openSection === "tech" ? null : "tech")}
                  >
                    <LineChart className="h-5 w-5" />
                    <span className="text-sm font-medium">Teknik Analiz</span>
                  </Button>

                  <Button
                    variant={openSection === "company" ? "default" : "outline"}
                    className="h-auto py-4 flex flex-col items-center gap-2 transition-all"
                    onClick={() => setOpenSection(openSection === "company" ? null : "company")}
                  >
                    <Building2 className="h-5 w-5" />
                    <span className="text-sm font-medium">Şirket Bilgileri</span>
                  </Button>

                  <Button
                    variant={openSection === "comments" ? "default" : "outline"}
                    className="h-auto py-4 flex flex-col items-center gap-2 transition-all"
                    onClick={() => setOpenSection(openSection === "comments" ? null : "comments")}
                  >
                    <Sparkles className="h-5 w-5" />
                    <span className="text-sm font-medium">AI Analizi</span>
                  </Button>
                </div>

                {/* Historical Data Section */}
                {openSection === "hist" && (
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
                          <button className={`${selectedTimeframe === '1day' ? 'bg-blue-500 text-white' : 'bg-black-200'} px-4 py-2 rounded`} onClick={() => setSelectedTimeframe('1day')}>1 Gün</button>
                          <button className={`${selectedTimeframe === '1week' ? 'bg-blue-500 text-white' : 'bg-black-200'} px-4 py-2 rounded`} onClick={() => setSelectedTimeframe('1week')}>1 Hafta</button>
                          <button className={`${selectedTimeframe === '1month' ? 'bg-blue-500 text-white' : 'bg-black-200'} px-4 py-2 rounded`} onClick={() => setSelectedTimeframe('1month')}>1 Ay</button>
                        </div>

                        {tsLoading && (
                          <div className="py-8 text-center text-muted-foreground">Yükleniyor...</div>
                        )}
                        {tsError && (
                          <div className="py-4 text-destructive">{tsError}</div>
                        )}
                        {!tsLoading && !tsError && timeSeries.length > 0 && (
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
                                {[...timeSeries].reverse().map((d, idx) => (
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
                        {!tsLoading && !tsError && timeSeries.length === 0 && (
                          <div className="py-6 text-center text-muted-foreground">Veri bulunamadı</div>
                        )}
                      </CardContent>
                    </Card>
                  </div>
                )}

                {/* Technical Analysis */}
                {openSection === "tech" && (
                  <div className="mt-6 animate-in slide-in-from-top-4 duration-300">
                    <TechnicalAnalysis
                      stock={selectedStock}
                      onLevelsChange={setLevels} />
                  </div>
                )}

                {/* Company Financials */}
                {openSection === "company" && (
                  <div className="mt-6 animate-in slide-in-from-top-4 duration-300">
                    <CompanyFinancials stock={selectedStock} />
                  </div>
                )}

                {/* Comments */}
                {openSection === "comments" && (
                  <div className="mt-6 animate-in slide-in-from-top-4 duration-300">
                    {user ? (
                      <StockComments stock={selectedStock} levels={levels} />
                    ) : (
                      <Card>
                        <CardContent className="py-12">
                          <div className="text-center space-y-4">
                            <div className="mx-auto w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center">
                              <Lock className="h-8 w-8 text-primary" />
                            </div>
                            <h3 className="text-xl font-semibold text-foreground">
                              AI Analizi Görüntülemek İçin Giriş Yapın
                            </h3>
                            <p className="text-muted-foreground max-w-md mx-auto">
                              Yapay zeka destekli analiz ve yorumları görüntülemek için lütfen hesabınıza giriş yapın.
                            </p>
                            <div className="flex gap-3 justify-center mt-6">
                              <Link to="/giris">
                                <Button>
                                  Giriş Yap
                                </Button>
                              </Link>
                              <Link to="/kayit">
                                <Button variant="outline">
                                  Kayıt Ol
                                </Button>
                              </Link>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    )}
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
                  <div className="relative mx-auto mb-6 h-40 w-40 max-w-full rounded-full border border-border/70 shadow-xl overflow-hidden">
                    <img
                      src="/1.ico"
                      alt="Aden Borsa Logo"
                      className="h-full w-full object-cover"
                      loading="lazy"
                    />
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
                      <h4 className="font-semibold text-foreground mb-2">AI Analizi</h4>
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