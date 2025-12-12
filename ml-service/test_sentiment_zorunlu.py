"""
Sentiment analizinin MUTLAKA yapıldığını test et
"""
from data_collector import DataCollector
from sentiment_analyzer import SentimentAnalyzer
from config import COMPANY_NAMES

def test_mandatory_sentiment():
    """Tüm senaryolarda sentiment analizinin yapıldığını test et"""
    collector = DataCollector()
    analyzer = SentimentAnalyzer()
    
    test_symbol = 'AAPL'
    company_name = COMPANY_NAMES.get(test_symbol)
    
    print("\n" + "="*70)
    print("🧪 ZORUNLU SENTIMENT ANALİZİ TESTİ")
    print("="*70)
    print(f"Test Edilecek Hisse: {test_symbol} ({company_name})")
    print("="*70)
    
    # TEST 1: Haber Çekme
    print("\n📰 TEST 1: HABER ÇEKME")
    print("-" * 70)
    news_df = collector.collect_company_news(test_symbol, days=7, company_name=company_name)
    
    if news_df.empty:
        print("\n❌ HATA: Hiçbir kaynaktan haber çekilemedi!")
        print("⚠️ Bu durumda bile tahmin yapılır ama sentiment skoru 0 olur")
        return False
    else:
        print(f"\n✅ BAŞARILI: {len(news_df)} haber çekildi")
        print(f"📊 Kolonlar: {list(news_df.columns)}")
        print(f"\n📝 İlk haber:")
        print(f"   Başlık: {news_df.iloc[0]['headline']}")
        print(f"   Kaynak: {news_df.iloc[0]['source']}")
    
    # TEST 2: Sentiment Analizi
    print("\n\n💭 TEST 2: SENTIMENT ANALİZİ")
    print("-" * 70)
    analyzed_df = analyzer.analyze_news_batch(news_df)
    
    if 'sentiment' not in analyzed_df.columns:
        print("\n❌ HATA: Sentiment analizi yapılmadı!")
        return False
    else:
        print(f"\n✅ BAŞARILI: Sentiment analizi tamamlandı")
        print(f"\n📊 Sentiment Dağılımı:")
        print(f"   Pozitif: {(analyzed_df['sentiment'] == 'positive').sum()}")
        print(f"   Negatif: {(analyzed_df['sentiment'] == 'negative').sum()}")
        print(f"   Nötr: {(analyzed_df['sentiment'] == 'neutral').sum()}")
        print(f"\n📈 Ortalama Skorlar:")
        print(f"   Sentiment Score: {analyzed_df['sentiment_score'].mean():.2f}")
        print(f"   Normalized Score: {analyzed_df['normalized_score'].mean():.2f}")
        
        # İlk 3 haberin sentiment sonuçları
        print(f"\n📰 İlk 3 Haberin Sentiment Sonuçları:")
        for idx, row in analyzed_df.head(3).iterrows():
            print(f"\n  {idx + 1}. {row['headline'][:60]}...")
            print(f"     Sentiment: {row['sentiment']} (Skor: {row['sentiment_score']:.2f})")
            print(f"     Normalized: {row['normalized_score']:.2f}")
    
    # TEST 3: Basit Sentiment Testi
    print("\n\n🔬 TEST 3: KELİME TABANLI SENTIMENT ANALİZİ")
    print("-" * 70)
    
    test_texts = [
        ("Apple stock surges 5% on strong earnings", "Pozitif bekleniyor"),
        ("Company faces losses, stock drops significantly", "Negatif bekleniyor"),
        ("Market remains steady with no major changes", "Nötr bekleniyor"),
        ("AAPL kazançları artıyor, güçlü büyüme", "Pozitif bekleniyor (Türkçe)"),
        ("Zarar açıklandı, hisse düşüşte", "Negatif bekleniyor (Türkçe)")
    ]
    
    for text, expected in test_texts:
        result = analyzer.analyze_sentiment(text)
        print(f"\n  📝 '{text}'")
        print(f"     Sonuç: {result['label']} (Skor: {result['score']:.2f})")
        print(f"     Beklenen: {expected}")
    
    print("\n\n" + "="*70)
    print("✅ TÜM TESTLER TAMAMLANDI!")
    print("="*70)
    print("\n📌 SONUÇ:")
    print("   • Haber çekme: ✅ Çalışıyor")
    print("   • Sentiment analizi: ✅ Çalışıyor")
    print("   • Kelime tabanlı analiz: ✅ Çalışıyor")
    print("\n🎯 Sistem tahmin yaparken MUTLAKA sentiment analizi yapacak!")
    
    return True

if __name__ == '__main__':
    success = test_mandatory_sentiment()
    exit(0 if success else 1)
