"""
Google News RSS entegrasyonunu test et
"""
from data_collector import DataCollector
from config import COMPANY_NAMES

def test_google_news_rss():
    """Google News RSS'den haber çekmeyi test et"""
    collector = DataCollector()
    
    # Birkaç hisse için test
    test_symbols = ['AAPL', 'MSFT', 'TSLA']
    
    print("=" * 60)
    print("🧪 GOOGLE NEWS RSS TESTİ")
    print("=" * 60)
    
    for symbol in test_symbols:
        print(f"\n{'=' * 60}")
        print(f"📊 {symbol} için test...")
        print('=' * 60)
        
        # Şirket ismini al
        company_name = COMPANY_NAMES.get(symbol)
        print(f"🏢 Şirket: {company_name}")
        
        # Google News RSS'den haber çek
        news_df = collector.collect_news_from_google_rss(symbol, company_name, days=7)
        
        if not news_df.empty:
            print(f"\n✅ BAŞARILI: {len(news_df)} haber bulundu")
            print("\n📰 İlk 3 haber:")
            for idx, row in news_df.head(3).iterrows():
                print(f"\n  {idx + 1}. {row['headline']}")
                print(f"     Kaynak: {row['source']}")
                print(f"     URL: {row['url'][:80]}...")
        else:
            print(f"\n❌ BAŞARISIZ: Haber bulunamadı")
        
        print("\n" + "-" * 60)
    
    print("\n" + "=" * 60)
    print("✅ TEST TAMAMLANDI")
    print("=" * 60)

if __name__ == '__main__':
    test_google_news_rss()
