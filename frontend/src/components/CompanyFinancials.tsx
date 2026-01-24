import { useEffect, useState, useCallback } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Building2, Globe, TrendingUp, Calendar, DollarSign, Users } from "lucide-react";
import { getCompanyProfile, getFinancialReports, CompanyProfile, FinancialsResponse } from "@/services/finnhubService";

interface Stock {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
}

interface CompanyFinancialsProps {
  stock: Stock;
}

export const CompanyFinancials = ({ stock }: CompanyFinancialsProps) => {
  const [profile, setProfile] = useState<CompanyProfile | null>(null);
  const [financials, setFinancials] = useState<FinancialsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const [profileData, financialsData] = await Promise.all([
          getCompanyProfile(stock.symbol),
          getFinancialReports(stock.symbol)
        ]);
        
        setProfile(profileData);
        setFinancials(financialsData);
      } catch (err) {
        console.error('Error fetching company data:', err);
        setError('Şirket bilgileri yüklenirken bir hata oluştu');
      } finally {
        setLoading(false);
      }
    };

    if (stock.symbol) {
      fetchData();
    }
  }, [stock.symbol]);

  const formatCurrency = useCallback((value: number) => {
    if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
    if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
    if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
    return `$${value.toLocaleString()}`;
  }, []);

  const formatNumber = useCallback((value: number) => {
    if (value >= 1e9) return `${(value / 1e9).toFixed(2)}B`;
    if (value >= 1e6) return `${(value / 1e6).toFixed(2)}M`;
    return value.toLocaleString();
  }, []);

  const translateFinancialTerm = (label: string): string => {
    const translations: { [key: string]: string } = {
      // Gelir Tablosu (Income Statement)
      'Net sales': 'Net satışlar',
      'Cost of sales': 'Satışların maliyeti',
      'Gross margin': 'Brüt kar',
      'Gross profit': 'Brüt kar',
      'Research and development': 'Araştırma ve geliştirme',
      'Selling, general and administrative': 'Satış, genel ve idari giderler',
      'Operating expenses': 'Faaliyet giderleri',
      'Operating income': 'Faaliyet geliri',
      'Net income': 'Net gelir',
      'Revenue': 'Gelir',
      'Total revenue': 'Toplam gelir',
      'Interest expense': 'Faiz gideri',
      'Income before tax': 'Vergi öncesi gelir',
      'Income tax expense': 'Gelir vergisi gideri',
      'Net income from continuing operations': 'Sürdürülen faaliyetlerden net gelir',
      'Earnings per share': 'Hisse başına kazanç',
      'Diluted earnings per share': 'Seyreltilmiş hisse başına kazanç',
      
      // Bilanço (Balance Sheet)
      'Cash and cash equivalents': 'Nakit ve nakit benzerleri',
      'Marketable securities': 'Menkul kıymetler',
      'Accounts receivable, net': 'Ticari alacaklar, net',
      'Vendor non-trade receivables': 'Satıcı ticari olmayan alacaklar',
      'Inventories': 'Stoklar',
      'Total current assets': 'Toplam dönen varlıklar',
      'Property, plant and equipment, net': 'Maddi duran varlıklar, net',
      'Total assets': 'Toplam varlıklar',
      'Accounts payable': 'Ticari borçlar',
      'Current liabilities': 'Kısa vadeli yükümlülükler',
      'Total current liabilities': 'Toplam kısa vadeli yükümlülükler',
      'Long-term debt': 'Uzun vadeli borçlar',
      'Total liabilities': 'Toplam yükümlülükler',
      'Common stock': 'Adi hisse senedi',
      'Retained earnings': 'Geçmiş yıl karları',
      'Total equity': 'Toplam özkaynak',
      'Total liabilities and equity': 'Toplam yükümlülükler ve özkaynak',
      'Shareholders\' equity': 'Hissedar özkaynak',
      'Total shareholders\' equity': 'Toplam hissedar özkaynak',
      
      // Nakit Akışı (Cash Flow)
      'Operating cash flow': 'Faaliyetlerden nakit akışı',
      'Investing cash flow': 'Yatırım faaliyetlerinden nakit akışı',
      'Financing cash flow': 'Finansman faaliyetlerinden nakit akışı',
      'Free cash flow': 'Serbest nakit akışı',
      'Capital expenditures': 'Sermaye harcamaları',
    };
    
    return translations[label] || label;
  };

  if (loading) {
    return (
      <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5 text-primary" />
            Şirket Bilgileri
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <div className="h-8 w-8 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error || !profile) {
    return (
      <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5 text-primary" />
            Şirket Bilgileri
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">{error || 'Şirket bilgileri bulunamadı'}</p>
        </CardContent>
      </Card>
    );
  }

  const latestFinancial = financials?.data?.[0];

  return (
    <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            {profile.logo && (
              <img 
                src={profile.logo} 
                alt={profile.name} 
                className="h-12 w-12 rounded-lg object-contain bg-white p-1"
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = 'none';
                }}
              />
            )}
            <div>
              <CardTitle className="flex items-center gap-2">
                <Building2 className="h-5 w-5 text-primary" />
                {profile.name}
              </CardTitle>
              <div className="flex items-center gap-2 mt-1 text-sm text-muted-foreground">
                <Badge variant="outline">{profile.ticker}</Badge>
                <span>{profile.exchange}</span>
              </div>
            </div>
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        <Tabs defaultValue="overview" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="overview">Genel Bakış</TabsTrigger>
            <TabsTrigger value="financials">Finansal Veriler</TabsTrigger>
          </TabsList>
          
          <TabsContent value="overview" className="space-y-4 mt-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-start gap-3 p-3 rounded-lg bg-background/50">
                <DollarSign className="h-5 w-5 text-success mt-0.5" />
                <div>
                  <p className="text-xs text-muted-foreground">Piyasa Değeri</p>
                  <p className="text-lg font-semibold">{formatCurrency(profile.marketCapitalization * 1e6)}</p>
                </div>
              </div>
              
              <div className="flex items-start gap-3 p-3 rounded-lg bg-background/50">
                <Users className="h-5 w-5 text-primary mt-0.5" />
                <div>
                  <p className="text-xs text-muted-foreground">Hisse Sayısı</p>
                  <p className="text-lg font-semibold">{formatNumber(profile.shareOutstanding)}</p>
                </div>
              </div>
              
              <div className="flex items-start gap-3 p-3 rounded-lg bg-background/50">
                <Calendar className="h-5 w-5 text-warning mt-0.5" />
                <div>
                  <p className="text-xs text-muted-foreground">Halka Arz Tarihi</p>
                  <p className="text-lg font-semibold">{profile.ipo || 'N/A'}</p>
                </div>
              </div>
              
              <div className="flex items-start gap-3 p-3 rounded-lg bg-background/50">
                <TrendingUp className="h-5 w-5 text-chart-secondary mt-0.5" />
                <div>
                  <p className="text-xs text-muted-foreground">Sektör</p>
                  <p className="text-lg font-semibold">{profile.finnhubIndustry || 'N/A'}</p>
                </div>
              </div>
            </div>
            
            <div className="space-y-2 pt-2">
              <div className="flex items-center gap-2 text-sm">
                <Globe className="h-4 w-4 text-muted-foreground" />
                <span className="text-muted-foreground">Ülke:</span>
                <span className="font-medium">{profile.country}</span>
              </div>
              
              <div className="flex items-center gap-2 text-sm">
                <DollarSign className="h-4 w-4 text-muted-foreground" />
                <span className="text-muted-foreground">Para Birimi:</span>
                <span className="font-medium">{profile.currency}</span>
              </div>
              
              {profile.weburl && (
                <div className="flex items-center gap-2 text-sm">
                  <Globe className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">Website:</span>
                  <a 
                    href={profile.weburl} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="font-medium text-primary hover:underline"
                  >
                    {profile.weburl}
                  </a>
                </div>
              )}
            </div>
          </TabsContent>
          
          <TabsContent value="financials" className="space-y-4 mt-4">
            {latestFinancial ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between pb-2 border-b">
                  <div>
                    <p className="text-sm font-medium">Raporlama Dönemi</p>
                    <p className="text-xs text-muted-foreground">
                      {latestFinancial.year} Q{latestFinancial.quarter}
                    </p>
                  </div>
                  <Badge variant="secondary">{latestFinancial.form}</Badge>
                </div>
                
                <div className="space-y-2">
                  <p className="text-xs text-muted-foreground">Başlangıç: {new Date(latestFinancial.startDate).toLocaleDateString('tr-TR')}</p>
                  <p className="text-xs text-muted-foreground">Bitiş: {new Date(latestFinancial.endDate).toLocaleDateString('tr-TR')}</p>
                  <p className="text-xs text-muted-foreground">Dosyalama: {new Date(latestFinancial.filedDate).toLocaleDateString('tr-TR')}</p>
                </div>
                
                {latestFinancial.report.ic && latestFinancial.report.ic.length > 0 && (
                  <div className="space-y-2">
                    <h4 className="text-sm font-semibold">Gelir Tablosu (Öne Çıkanlar)</h4>
                    <div className="space-y-1">
                      {latestFinancial.report.ic.slice(0, 5).map((item, idx) => (
                        <div key={idx} className="flex justify-between text-sm py-1 border-b border-border/30">
                          <span className="text-muted-foreground text-xs">{translateFinancialTerm(item.label)}</span>
                          <span className="font-medium">{formatCurrency(item.value)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {latestFinancial.report.bs && latestFinancial.report.bs.length > 0 && (
                  <div className="space-y-2">
                    <h4 className="text-sm font-semibold">Bilanço (Öne Çıkanlar)</h4>
                    <div className="space-y-1">
                      {latestFinancial.report.bs.slice(0, 5).map((item, idx) => (
                        <div key={idx} className="flex justify-between text-sm py-1 border-b border-border/30">
                          <span className="text-muted-foreground text-xs">{translateFinancialTerm(item.label)}</span>
                          <span className="font-medium">{formatCurrency(item.value)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground text-center py-8">
                Finansal veriler bulunamadı
              </p>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};
