// src/components/TechnicalAnalysis.tsx
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { TrendingUp, TrendingDown, Minus, Target, Shield, AlertTriangle, Info } from "lucide-react";
import { useEffect, useState } from "react";
import { toBars, pivotLevels, rollingLevels, ema, rsi, calculateBufferZone, calculateAllPivots } from "@/lib/ta";

interface TechnicalAnalysisProps {
  stock: { symbol: string; name: string; price: number; change: number; changePercent: number };
  onLevelsChange?: (levels: Levels | null) => void;
}

type PivotData = {
  P: number; R1: number; S1: number; R2: number; S2: number; R3: number; S3: number;
};

type Levels = {
  support1:number; support2:number; resistance1:number; resistance2:number;
  bufferZone:{
    support: {lower:number; upper:number};
    resistance: {lower:number; upper:number};
    tolerance: number;
    atr: number;
    method: string;
  };
  pivots: {
    classic: PivotData;
    fibonacci: PivotData;
    camarilla: PivotData;
    woodies: PivotData;
    demark: PivotData;
  };
  rsi:number; macd:number;
  bollinger:{upper:number; middle:number; lower:number};
};

export const TechnicalAnalysis = ({ stock, onLevelsChange }: TechnicalAnalysisProps) => {
  const [levels, setLevels] = useState<Levels | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // Currency conversion function (1 USD ≈ 34 TRY)
  const convertToUSD = (tlValue: number): number => {
    const conversionRate = 34;
    return tlValue / conversionRate;
  };

  const formatCurrency = (value: number): string => {
    if (value >= 1e9) return `$${value.toFixed(2)}`;
    if (value >= 1e6) return `$${value.toFixed(2)}`;
    if (value >= 1e3) return `$${value.toFixed(2)}`;
    return `$${value.toFixed(4)}`;
  };

  const fetchData = async (stock: any, setLoading: (loading: boolean) => void, setErr: (err: string | null) => void, setLevels: (levels: Levels | null) => void, getAlive: () => boolean) => {
    try {
      setLoading(true);
      setErr(null);
      const url = new URL("https://api.twelvedata.com/time_series");
      url.search = new URLSearchParams({
        symbol: stock.symbol,
        exchange: "",
        interval: "1day",
        outputsize: "60",
        apikey: '9535cc258b9f4f668bdc4059c99180d0'
      }).toString();
      const res = await fetch(`${url}`);
      const json = await res.json();
      if (!json?.values) throw new Error(json?.message || "veri yok");
      const bars = toBars(json.values);
      if (bars.length < 21) throw new Error("yetersiz veri");

      const closes = bars.map(b=>b.close);
      const highs  = bars.map(b=>b.high);
      const lows   = bars.map(b=>b.low);
      const last   = bars[bars.length-1];
      const prev   = bars[bars.length-2];

      // Pivot (önceki gün)
      const piv = pivotLevels(prev.high, prev.low, prev.close);

      // Rolling destek/direnç
      const roll = rollingLevels(bars, 20);

      // Bollinger(20, 2)
      const window = 20;
      const last20 = closes.slice(-window);
      const mu = last20.reduce((a,b)=>a+b,0)/window;
      const sd = Math.sqrt(last20.reduce((a,b)=>a+(b-mu)**2,0)/window);
      const bbUpper = mu + 2*sd, bbLower = mu - 2*sd;

      // EMA ve MACD yaklaşımı
      const ema12 = ema(closes,12), ema26 = ema(closes,26);
      const macd  = ema12[ema12.length-1] - ema26[ema26.length-1];

      // RSI(14)
      const rsi14 = rsi(closes, 14);

      // Destek/Direnç seviyeleri
      const support1 = Math.min(piv.S1, roll.support);
      const resistance1 = Math.max(piv.R1, roll.resistance);
      
      // Tampon bölge: ATR + Yüzdelik bazlı (en sağlıklı yöntem)
      const bufferZone = calculateBufferZone(bars, support1, resistance1, last.close);
      
      // Tüm pivot yöntemlerini hesapla
      const allPivots = calculateAllPivots(prev.high, prev.low, prev.close, last.open);
      
      const out: Levels = {
        support1,
        support2: Math.min(piv.S2, roll.support),
        resistance1,
        resistance2: Math.max(piv.R2, roll.resistance),
        bufferZone,
        pivots: allPivots,
        rsi: Number.isFinite(rsi14) ? Math.round(rsi14) : 50,
        macd,
        bollinger: { upper: bbUpper, middle: mu, lower: bbLower }
      };
      if (getAlive()) setLevels(out);
      if (onLevelsChange) onLevelsChange(out);
    } catch (e:any) {
      setErr(e.message || "hata");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let alive = true;
    fetchData(stock, setLoading, setErr, setLevels, () => alive);
    return () => { alive = false; };
  }, [stock]);

  const getRSIStatus = (r:number) => r>70 ? {status:"Aşırı Alım", icon:TrendingDown}
                           : r<30 ? {status:"Aşırı Satım", icon:TrendingUp}
                                  : {status:"Nötr", icon:Minus};
  const getMACDStatus = (m:number) => m>0? {status:"Pozitif", icon:TrendingUp}
                                   : m<0? {status:"Negatif", icon:TrendingDown}
                                         : {status:"Nötr", icon:Minus};
  if (loading) return <Card><CardHeader><CardTitle>Teknik Analiz - {stock.symbol}</CardTitle></CardHeader><CardContent>Yükleniyor…</CardContent></Card>;
  if (err) return <Card><CardHeader><CardTitle>Teknik Analiz - {stock.symbol}</CardTitle></CardHeader><CardContent>Hata: {err}</CardContent></Card>;
  if (!levels) return null;

  const rsiStat = getRSIStatus(levels.rsi);
  const macdStat = getMACDStatus(levels.macd);
  const RSIIcon = rsiStat.icon; const MACDIcon = macdStat.icon;

  return (
    <TooltipProvider>
      <Card className="bg-card border-border shadow-lg">
        <CardHeader className="border-b border-border/50">
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5 text-primary" />
            Teknik Analiz - {stock.symbol}
            <Tooltip>
              <TooltipTrigger asChild>
                <Info className="h-4 w-4 text-muted-foreground cursor-help ml-1" />
              </TooltipTrigger>
              <TooltipContent className="max-w-xs">
                <p className="text-xs">
                  <strong>Teknik Analiz Hesaplamaları:</strong><br/>
                  • <strong>Destek/Direnç:</strong> Pivot seviyeleri ve 20 günlük rolling min/max<br/>
                  • <strong>RSI(14):</strong> Relative Strength Index - Aşırı alım/satım göstergesi<br/>
                  • <strong>MACD:</strong> EMA(12) - EMA(26) farkı - Momentum göstergesi<br/>
                  • <strong>Bollinger:</strong> 20 günlük SMA ± 2 standart sapma
                </p>
              </TooltipContent>
            </Tooltip>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6 pt-6">
        {/* Ana İndikatörler Grid */}
        <div className="grid md:grid-cols-3 gap-4">
          {/* RSI */}
          <div className="p-4 bg-muted/30 rounded-lg border border-border/50">
            <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
              <RSIIcon className="h-4 w-4" />
              RSI(14)
            </h3>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Badge variant="outline">{rsiStat.status}</Badge>
                <span className="font-mono text-lg font-bold">{levels.rsi}</span>
              </div>
              <Progress value={Math.max(0, Math.min(100, levels.rsi))} className="h-2" />
            </div>
          </div>
          
          {/* MACD */}
          <div className="p-4 bg-muted/30 rounded-lg border border-border/50">
            <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
              <MACDIcon className="h-4 w-4" />
              MACD(12-26)
            </h3>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Badge variant="outline">{macdStat.status}</Badge>
                <span className="font-mono text-lg font-bold">{levels.macd.toFixed(3)}</span>
              </div>
            </div>
          </div>
          
          {/* Bollinger */}
          <div className="p-4 bg-muted/30 rounded-lg border border-border/50">
            <h3 className="text-sm font-semibold mb-3">Bollinger(20,2)</h3>
            <div className="space-y-1.5 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Üst:</span>
                <span className="font-mono font-medium">{formatCurrency(levels.bollinger.upper)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Orta:</span>
                <span className="font-mono font-medium">{formatCurrency(levels.bollinger.middle)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Alt:</span>
                <span className="font-mono font-medium">{formatCurrency(levels.bollinger.lower)}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Destek/Direnç Seviyeleri */}
        <div className="p-4 bg-primary/5 rounded-lg border border-primary/20">
          <h3 className="text-sm font-semibold mb-4 flex items-center gap-2">
            <Shield className="h-5 w-5 text-primary" />
            Destek & Direnç Seviyeleri
          </h3>
          <div className="grid md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <div className="flex justify-between items-center p-2 bg-background/50 rounded">
                <span className="text-sm font-medium text-success">Destek 1</span>
                <span className="font-mono text-sm font-bold">{formatCurrency(levels.support1)}</span>
              </div>
              <div className="flex justify-between items-center p-2 bg-background/50 rounded">
                <span className="text-sm font-medium text-success">Destek 2</span>
                <span className="font-mono text-sm font-bold">{formatCurrency(levels.support2)}</span>
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between items-center p-2 bg-background/50 rounded">
                <span className="text-sm font-medium text-destructive">Direnç 1</span>
                <span className="font-mono text-sm font-bold">{formatCurrency(levels.resistance1)}</span>
              </div>
              <div className="flex justify-between items-center p-2 bg-background/50 rounded">
                <span className="text-sm font-medium text-destructive">Direnç 2</span>
                <span className="font-mono text-sm font-bold">{formatCurrency(levels.resistance2)}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Tampon Bölgeler */}
        <div className="p-4 bg-muted/20 rounded-lg border border-border/50">
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle className="h-5 w-5 text-warning" />
            <h3 className="text-sm font-semibold">Tampon Bölgeler</h3>
            <Tooltip>
              <TooltipTrigger asChild>
                <Info className="h-4 w-4 text-muted-foreground cursor-help" />
              </TooltipTrigger>
              <TooltipContent className="max-w-sm">
                <p className="text-xs">
                  <strong>Tampon Bölge:</strong> Destek/Direnç seviyeleri etrafında güvenli alım-satım bölgeleri.<br/><br/>
                  <strong>Tolerans:</strong> (ATR + Yüzdelik) / 2 - Hem volatiliteyi hem de fiyat seviyesini dengeler.
                </p>
              </TooltipContent>
            </Tooltip>
            <Badge variant="outline" className="text-xs ml-auto">{levels.bufferZone.method}</Badge>
          </div>
          <div className="grid md:grid-cols-2 gap-3">
            <div className="p-3 bg-success/10 rounded border border-success/20">
              <div className="text-xs text-muted-foreground mb-1">Destek Tamponu</div>
              <div className="font-mono text-sm font-semibold">
                {formatCurrency(levels.bufferZone.support.lower)} - {formatCurrency(levels.bufferZone.support.upper)}
              </div>
            </div>
            <div className="p-3 bg-destructive/10 rounded border border-destructive/20">
              <div className="text-xs text-muted-foreground mb-1">Direnç Tamponu</div>
              <div className="font-mono text-sm font-semibold">
                {formatCurrency(levels.bufferZone.resistance.lower)} - {formatCurrency(levels.bufferZone.resistance.upper)}
              </div>
            </div>
            <div className="p-3 bg-background/50 rounded">
              <div className="text-xs text-muted-foreground mb-1">Tolerans</div>
              <div className="font-mono text-sm font-semibold">±{formatCurrency(levels.bufferZone.tolerance)}</div>
            </div>
            {Number.isFinite(levels.bufferZone.atr) && (
              <div className="p-3 bg-background/50 rounded">
                <div className="text-xs text-muted-foreground mb-1">ATR(14)</div>
                <div className="font-mono text-sm font-semibold">{formatCurrency(levels.bufferZone.atr)}</div>
              </div>
            )}
          </div>
        </div>

        {/* Pivot Points Tablosu */}
        <div className="p-4 bg-card rounded-lg border border-border">
          <div className="flex items-center gap-2 mb-4">
            <Target className="h-5 w-5 text-primary" />
            <h3 className="text-sm font-semibold">Pivot Points</h3>
            <Tooltip>
              <TooltipTrigger asChild>
                <Info className="h-4 w-4 text-muted-foreground cursor-help" />
              </TooltipTrigger>
              <TooltipContent className="max-w-sm">
                <p className="text-xs">
                  <strong>Pivot Points:</strong> Önceki günün fiyat hareketlerine göre hesaplanan destek ve direnç seviyeleri.
                </p>
              </TooltipContent>
            </Tooltip>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-2 px-2 font-semibold text-xs">Yöntem</th>
                  <th className="text-right py-2 px-2 font-semibold text-xs">S3</th>
                  <th className="text-right py-2 px-2 font-semibold text-xs">S2</th>
                  <th className="text-right py-2 px-2 font-semibold text-xs">S1</th>
                  <th className="text-center py-2 px-2 font-semibold text-xs bg-primary/10">P</th>
                  <th className="text-right py-2 px-2 font-semibold text-xs">R1</th>
                  <th className="text-right py-2 px-2 font-semibold text-xs">R2</th>
                  <th className="text-right py-2 px-2 font-semibold text-xs">R3</th>
                </tr>
              </thead>
              <tbody className="text-xs">
                <tr className="border-b border-border/30 hover:bg-muted/20">
                  <td className="py-2 px-2 font-medium">Classic</td>
                  <td className="text-right py-2 px-2 font-mono">{formatCurrency(levels.pivots.classic.S3)}</td>
                  <td className="text-right py-2 px-2 font-mono">{formatCurrency(levels.pivots.classic.S2)}</td>
                  <td className="text-right py-2 px-2 font-mono">{formatCurrency(levels.pivots.classic.S1)}</td>
                  <td className="text-center py-2 px-2 font-mono font-bold bg-primary/10">{formatCurrency(levels.pivots.classic.P)}</td>
                  <td className="text-right py-2 px-2 font-mono">{formatCurrency(levels.pivots.classic.R1)}</td>
                  <td className="text-right py-2 px-2 font-mono">{formatCurrency(levels.pivots.classic.R2)}</td>
                  <td className="text-right py-2 px-2 font-mono">{formatCurrency(levels.pivots.classic.R3)}</td>
                </tr>
                <tr className="border-b border-border/30 hover:bg-muted/20">
                  <td className="py-2 px-2 font-medium">Fibonacci</td>
                  <td className="text-right py-2 px-2 font-mono">{formatCurrency(levels.pivots.fibonacci.S3)}</td>
                  <td className="text-right py-2 px-2 font-mono">{formatCurrency(levels.pivots.fibonacci.S2)}</td>
                  <td className="text-right py-2 px-2 font-mono">{formatCurrency(levels.pivots.fibonacci.S1)}</td>
                  <td className="text-center py-2 px-2 font-mono font-bold bg-primary/10">{formatCurrency(levels.pivots.fibonacci.P)}</td>
                  <td className="text-right py-2 px-2 font-mono">{formatCurrency(levels.pivots.fibonacci.R1)}</td>
                  <td className="text-right py-2 px-2 font-mono">{formatCurrency(levels.pivots.fibonacci.R2)}</td>
                  <td className="text-right py-2 px-2 font-mono">{formatCurrency(levels.pivots.fibonacci.R3)}</td>
                </tr>
                <tr className="border-b border-border/30 hover:bg-muted/20">
                  <td className="py-2 px-2 font-medium">Camarilla</td>
                  <td className="text-right py-2 px-2 font-mono">{formatCurrency(levels.pivots.camarilla.S3)}</td>
                  <td className="text-right py-2 px-2 font-mono">{formatCurrency(levels.pivots.camarilla.S2)}</td>
                  <td className="text-right py-2 px-2 font-mono">{formatCurrency(levels.pivots.camarilla.S1)}</td>
                  <td className="text-center py-2 px-2 font-mono font-bold bg-primary/10">{formatCurrency(levels.pivots.camarilla.P)}</td>
                  <td className="text-right py-2 px-2 font-mono">{formatCurrency(levels.pivots.camarilla.R1)}</td>
                  <td className="text-right py-2 px-2 font-mono">{formatCurrency(levels.pivots.camarilla.R2)}</td>
                  <td className="text-right py-2 px-2 font-mono">{formatCurrency(levels.pivots.camarilla.R3)}</td>
                </tr>
                <tr className="border-b border-border/30 hover:bg-muted/20">
                  <td className="py-2 px-2 font-medium">Woodie's</td>
                  <td className="text-right py-2 px-2 font-mono">{formatCurrency(levels.pivots.woodies.S3)}</td>
                  <td className="text-right py-2 px-2 font-mono">{formatCurrency(levels.pivots.woodies.S2)}</td>
                  <td className="text-right py-2 px-2 font-mono">{formatCurrency(levels.pivots.woodies.S1)}</td>
                  <td className="text-center py-2 px-2 font-mono font-bold bg-primary/10">{formatCurrency(levels.pivots.woodies.P)}</td>
                  <td className="text-right py-2 px-2 font-mono">{formatCurrency(levels.pivots.woodies.R1)}</td>
                  <td className="text-right py-2 px-2 font-mono">{formatCurrency(levels.pivots.woodies.R2)}</td>
                  <td className="text-right py-2 px-2 font-mono">{formatCurrency(levels.pivots.woodies.R3)}</td>
                </tr>
                <tr className="hover:bg-muted/20">
                  <td className="py-2 px-2 font-medium">DeMark's</td>
                  <td className="text-right py-2 px-2 text-muted-foreground">-</td>
                  <td className="text-right py-2 px-2 text-muted-foreground">-</td>
                  <td className="text-right py-2 px-2 font-mono">{formatCurrency(levels.pivots.demark.S1)}</td>
                  <td className="text-center py-2 px-2 font-mono font-bold bg-primary/10">{formatCurrency(levels.pivots.demark.P)}</td>
                  <td className="text-right py-2 px-2 font-mono">{formatCurrency(levels.pivots.demark.R1)}</td>
                  <td className="text-right py-2 px-2 text-muted-foreground">-</td>
                  <td className="text-right py-2 px-2 text-muted-foreground">-</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </CardContent>
    </Card>
    </TooltipProvider>
  );
};
