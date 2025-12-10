import { useState, useEffect, useMemo, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { MessageSquare, TrendingUp, TrendingDown, Clock, User, Send, Trash2, Edit2, Sparkles, AlertTriangle } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { getComments, addComment, deleteComment, updateComment } from "@/services/commentService";
import { toast } from "sonner";
import { getMLPrediction, getSentimentSummary, type MLPrediction, type SentimentSummary } from "@/services/mlService";

interface Comment {
  id: string;
  user_id: string;
  symbol: string;
  content: string;
  created_at: string;
  user?: {
    full_name?: string;
    email?: string;
    profession?: string;
  };
}

interface StockCommentsProps {
  stock: {
    symbol: string;
    name: string;
    price: number;
    change: number;
    changePercent: number;
  };
  levels?: any; // Teknik analiz verileri
}

const fetchComments = async (symbol) => {
  try {
    return await getComments(symbol);
  } catch (err) {
    console.error('Error fetching comments:', err);
    return [];
  }
};


export const StockComments = ({ stock, levels }: StockCommentsProps) => {
  const { user } = useAuth();
  const [mlPrediction, setMlPrediction] = useState<MLPrediction | null>(null);
  const [sentimentData, setSentimentData] = useState<SentimentSummary['result'] | null>(null);
  const [mlLoading, setMlLoading] = useState(true);
  const [mlError, setMlError] = useState<string | null>(null);
  
  useEffect(() => {
    const loadMLData = async () => {
      setMlLoading(true);
      setMlError(null);
      
      try {
        // ML tahminini al
        const predictionResponse = await getMLPrediction(stock.symbol, true);
        if (predictionResponse.success && predictionResponse.result) {
          setMlPrediction(predictionResponse.result);
        } else {
          setMlError(predictionResponse.error || 'Tahmin alınamadı');
        }
        
        // Duygu analizi özetini al
        const sentimentResponse = await getSentimentSummary(stock.symbol, 7);
        if (sentimentResponse.success && sentimentResponse.result) {
          setSentimentData(sentimentResponse.result);
        }
      } catch (error) {
        console.error('ML data loading error:', error);
        setMlError('ML servisi yanıt vermiyor');
      } finally {
        setMlLoading(false);
      }
    };
    
    loadMLData();
  }, [stock.symbol]);
  
  const [userComments, setUserComments] = useState<Comment[]>([]);
  const [newComment, setNewComment] = useState("");
  const [loading, setLoading] = useState(false);
  const [editingId, setEditingId] = useState<string | number | null>(null);
  const [editContent, setEditContent] = useState("");

  // Fetch user comments
  useEffect(() => {
    fetchComments(stock.symbol.toString()).then(setUserComments);
  }, [stock.symbol]);

  const handleAddComment = async () => {
    if (!newComment.trim() || !user) return;
    
    setLoading(true);
    try {
      const comment = await addComment(user.id.toString(), stock.symbol.toString(), newComment);
      setUserComments([comment, ...userComments]);
      setNewComment("");
      toast.success('Yorum eklendi');
    } catch (err) {
      console.error('Error adding comment:', err);
      toast.error('Yorum eklenirken hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteComment = async (commentId: string) => {
    try {
      await deleteComment(commentId);
      setUserComments(userComments.filter(c => c.id !== commentId));
      toast.success('Yorum silindi');
    } catch (err) {
      console.error('Error deleting comment:', err);
      toast.error('Yorum silinirken hata oluştu');
    }
  };

  const handleUpdateComment = async (commentId: string) => {
    if (!editContent.trim()) return;
    
    try {
      const updated = await updateComment(commentId, editContent);
      setUserComments(userComments.map(c => c.id === commentId ? updated : c));
      setEditingId(null);
      setEditContent("");
      toast.success('Yorum güncellendi');
    } catch (err) {
      console.error('Error updating comment:', err);
      toast.error('Yorum güncellenirken hata oluştu');
    }
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case "ÇOK POZİTİF":
      case "POZİTİF":
        return "success";
      case "ÇOK NEGATİF":
      case "NEGATİF":
        return "error";
      default:
        return "warning";
    }
  };

  const getRecommendationColor = (recommendation: string) => {
    switch (recommendation) {
      case "AL":
        return "success";
      case "SAT":
        return "destructive";
      case "TUT":
        return "warning";
      default:
        return "secondary";
    }
  };

  const getPredictionIcon = (prediction: string) => {
    switch (prediction) {
      case "AL":
        return <TrendingUp className="h-4 w-4 text-success" />;
      case "SAT":
        return <TrendingDown className="h-4 w-4 text-destructive" />;
      default:
        return <Sparkles className="h-4 w-4 text-warning" />;
    }
  };

  const generateAnalysisText = () => {
    if (!mlPrediction) return "";
    
    const { prediction } = mlPrediction;
    
    // Basitleştirilmiş yorum metni
    const text = `Yaptığım analizler ve incelemeler doğrultusunda ${stock.symbol} hissesi için "${prediction}" önerisinde bulunabilirim. Tüm teknik detaylar aşağıda verilmiştir. Yatırım tavsiyesi değildir, kendi analizlerinizi yapın.`;
    
    return text;
  };

  return (
    <Card className="bg-card border-border shadow-card">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-primary" />
          ML Tahmin & AI Analiz - {stock.symbol}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* ML Prediction Section */}
        {mlLoading ? (
          <div className="p-6 bg-gradient-to-r from-primary/10 to-primary/5 rounded-lg border border-primary/20">
            <div className="flex items-center justify-center gap-2">
              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary"></div>
              <p className="text-sm text-muted-foreground">ML tahmini yükleniyor...</p>
            </div>
          </div>
        ) : mlError ? (
          <div className="p-4 bg-destructive/10 rounded-lg border border-destructive/20">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-destructive" />
              <div>
                <p className="font-semibold text-destructive">ML Servisi Hatası</p>
                <p className="text-sm text-muted-foreground mt-1">{mlError}</p>
                <p className="text-xs text-muted-foreground mt-2">
                  ML servisinin çalıştığından emin olun: <code className="bg-muted px-1 py-0.5 rounded">python ml-service/app.py</code>
                </p>
              </div>
            </div>
          </div>
        ) : mlPrediction ? (
          <div className={`p-4 rounded-lg border-2 ${
            mlPrediction.prediction === 'AL' ? 'bg-success/10 border-success/30' :
            mlPrediction.prediction === 'SAT' ? 'bg-destructive/10 border-destructive/30' :
            'bg-warning/10 border-warning/30'
          }`}>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className={`h-10 w-10 rounded-full flex items-center justify-center ${
                  mlPrediction.prediction === 'AL' ? 'bg-success' :
                  mlPrediction.prediction === 'SAT' ? 'bg-destructive' :
                  'bg-warning'
                }`}>
                  {getPredictionIcon(mlPrediction.prediction)}
                </div>
                <div>
                  <p className="font-bold text-lg text-foreground">{mlPrediction.prediction} ÖNERİSİ</p>
                  <p className="text-xs text-muted-foreground">
                    {mlPrediction.method === 'ml_model' ? '🤖 ML Model' : 
                     mlPrediction.method === 'technical_analysis' ? '📈 Teknik Analiz + OHLCV' : 
                     '📊 Kural Tabanlı'} • 
                    {new Date().toLocaleString('tr-TR')}
                  </p>
                </div>
              </div>
              <div className={`text-lg px-4 py-2 rounded-md font-semibold ${
                mlPrediction.prediction === 'AL' ? 'bg-green-500 text-white' :
                mlPrediction.prediction === 'SAT' ? 'bg-red-500 text-white' :
                'bg-yellow-500 text-white'
              }`}>
                %{(mlPrediction.confidence * 100).toFixed(0)} Güven
              </div>
            </div>
            
            <p className="text-sm text-foreground leading-relaxed mb-4">
              {generateAnalysisText()}
            </p>
            
            {/* Fiyat Bilgileri */}
            {mlPrediction.price_data && (
              <div className="mb-4 p-3 bg-background/50 rounded-lg">
                <p className="text-xs text-muted-foreground mb-2">Güncel Fiyat Bilgileri</p>
                <div className="flex items-center gap-4">
                  <div>
                    <p className="text-2xl font-bold text-foreground">${mlPrediction.price_data.current.toFixed(2)}</p>
                  </div>
                  <div className={`flex items-center gap-1 ${mlPrediction.price_data.change >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                    {mlPrediction.price_data.change >= 0 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                    <span className="font-semibold">{mlPrediction.price_data.change.toFixed(2)} ({mlPrediction.price_data.change_percent.toFixed(2)}%)</span>
                  </div>
                </div>
              </div>
            )}
            
            <div className="grid grid-cols-3 gap-3 mb-4">
              <div className="p-3 bg-background/50 rounded-lg">
                <p className="text-xs text-muted-foreground mb-1">Teknik Skor</p>
                <p className="text-lg font-bold text-foreground">%{(mlPrediction.technical_score * 100).toFixed(0)}</p>
              </div>
              <div className="p-3 bg-background/50 rounded-lg">
                <p className="text-xs text-muted-foreground mb-1">Duygu Skoru</p>
                <p className="text-lg font-bold text-foreground">%{(mlPrediction.sentiment_score * 100).toFixed(0)}</p>
              </div>
              <div className="p-3 bg-background/50 rounded-lg">
                <p className="text-xs text-muted-foreground mb-1">Analiz Edilen Haber</p>
                <p className="text-lg font-bold text-foreground">{mlPrediction.news_count}</p>
              </div>
            </div>
            
            {/* Teknik Göstergeler */}
            {mlPrediction.technical_indicators && (
              <div className="mb-4 p-3 bg-background/50 rounded-lg">
                <p className="text-xs font-semibold text-muted-foreground mb-3">Teknik Göstergeler</p>
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div>
                    <span className="text-muted-foreground">RSI:</span>
                    <span className={`ml-2 font-semibold ${
                      mlPrediction.technical_indicators.rsi < 30 ? 'text-green-500' :
                      mlPrediction.technical_indicators.rsi > 70 ? 'text-red-500' :
                      'text-yellow-500'
                    }`}>
                      {mlPrediction.technical_indicators.rsi.toFixed(2)}
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">MACD:</span>
                    <span className={`ml-2 font-semibold ${mlPrediction.technical_indicators.macd > 0 ? 'text-green-500' : 'text-red-500'}`}>
                      {mlPrediction.technical_indicators.macd.toFixed(2)}
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Trend:</span>
                    <span className="ml-2 font-semibold text-foreground">
                      {(mlPrediction.technical_indicators.trend_strength * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Volume:</span>
                    <span className="ml-2 font-semibold text-foreground">
                      {mlPrediction.technical_indicators.volume_ratio.toFixed(2)}x
                    </span>
                  </div>
                </div>
              </div>
            )}
            
            {/* Teknik Sinyaller */}
            {mlPrediction.signals && mlPrediction.signals.length > 0 && (
              <div className="mb-4 p-3 bg-background/50 rounded-lg">
                <p className="text-xs font-semibold text-muted-foreground mb-2">Teknik Sinyaller</p>
                <div className="space-y-1">
                  {mlPrediction.signals.map((signal, idx) => (
                    <div key={idx} className="text-xs text-foreground flex items-start gap-2">
                      <span className="text-muted-foreground">•</span>
                      <span>{signal}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {sentimentData && sentimentData.recent_headlines && sentimentData.recent_headlines.length > 0 && (
              <div className="mt-4 pt-4 border-t border-border/50">
                <p className="text-xs font-semibold text-muted-foreground mb-2">Son Haberler:</p>
                <div className="space-y-2 max-h-40 overflow-y-auto">
                  {sentimentData.recent_headlines.slice(0, 3).map((headline, idx) => (
                    <div key={idx} className="text-xs p-2 bg-background/50 rounded">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant="outline" className="text-xs">
                          {headline.sentiment}
                        </Badge>
                        <span className="text-muted-foreground">
                          {new Date(headline.datetime).toLocaleDateString('tr-TR')}
                        </span>
                      </div>
                      <p className="text-foreground line-clamp-2">{headline.headline}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : null}

        <div>
          <h3 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
            <MessageSquare className="h-4 w-4" />
            Kullanıcı Yorumları ({userComments.length})
          </h3>
          
          {/* Add Comment Form */}
          <div className="mb-4 p-4 bg-muted/20 rounded-lg border border-muted/30">
            <Textarea
              placeholder="Yorumunuzu yazın..."
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              className="mb-2"
              rows={3}
            />
            <Button
              onClick={handleAddComment}
              disabled={loading || !newComment.trim()}
              className="w-full sm:w-auto"
            >
              <Send className="h-4 w-4 mr-2" />
              Yorum Ekle
            </Button>
          </div>

          {/* Comments List */}
          <div className="space-y-3">
            {userComments.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                Henüz yorum yapılmamış. İlk yorumu siz yapın!
              </div>
            ) : (
              userComments.map((comment) => (
                <div key={comment.id} className="p-4 bg-muted/20 rounded-lg border border-muted/30">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <User className="h-4 w-4 text-muted-foreground" />
                        <span className="font-medium text-foreground text-sm">
                          {comment.user?.full_name || comment.user?.email || 'Anonim'}
                        </span>
                        {comment.user?.profession && (
                          <Badge variant="outline" className="ml-2 text-xs">
                            {comment.user.profession}
                          </Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-1 mt-1">
                        <Clock className="h-3 w-3 text-muted-foreground" />
                        <span className="text-xs text-muted-foreground">
                          {new Date(comment.created_at).toLocaleString('tr-TR')}
                        </span>
                      </div>
                    </div>
                    {user?.id.toString() === comment.user_id && (
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={() => {
                            setEditingId(comment.id);
                            setEditContent(comment.content);
                          }}
                        >
                          <Edit2 className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-destructive"
                          onClick={() => handleDeleteComment(comment.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    )}
                  </div>
                  
                  {editingId === comment.id ? (
                    <div className="space-y-2">
                      <Textarea
                        value={editContent}
                        onChange={(e) => setEditContent(e.target.value)}
                        rows={3}
                      />
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          onClick={() => handleUpdateComment(comment.id)}
                        >
                          Kaydet
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setEditingId(null);
                            setEditContent("");
                          }}
                        >
                          İptal
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <p className="text-sm text-foreground leading-relaxed">
                      {comment.content}
                    </p>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Risk Uyarısı */}
        <div className="p-4 bg-emerald-500/20 rounded-lg border-2 border-emerald-500/40">
          <p className="text-sm text-foreground font-medium leading-relaxed">
            <strong className="text-emerald-700 dark:text-emerald-400">⚠️ Risk Uyarısı:</strong> Bu yorumlar yatırım tavsiyesi değildir. 
            Yatırım kararlarınızı vermeden önce kendi araştırmanızı yapın ve risk toleransınızı değerlendirin.
          </p>
        </div>
      </CardContent>
    </Card>
  );
};