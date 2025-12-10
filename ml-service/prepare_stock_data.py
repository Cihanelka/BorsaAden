"""
Farklı CSV dosyalarını birleştirip standart formata çevir
"""
import pandas as pd
import os

def clean_volume(vol_str):
    """Volume değerini temizle (33.12M -> 33120000)"""
    if pd.isna(vol_str) or vol_str == '-':
        return 0
    
    vol_str = str(vol_str).replace(',', '')
    
    if 'M' in vol_str:
        return float(vol_str.replace('M', '')) * 1_000_000
    elif 'K' in vol_str:
        return float(vol_str.replace('K', '')) * 1_000
    elif 'B' in vol_str:
        return float(vol_str.replace('B', '')) * 1_000_000_000
    else:
        try:
            return float(vol_str)
        except:
            return 0

def clean_percentage(pct_str):
    """Yüzde değerini temizle (0.18% -> 0.0018)"""
    if pd.isna(pct_str) or pct_str == '-':
        return 0
    
    try:
        return float(str(pct_str).replace('%', '')) / 100
    except:
        return 0

def process_csv_file(file_path, symbol):
    """Tek bir CSV dosyasını işle"""
    print(f"📊 {symbol} işleniyor...")
    
    try:
        # CSV'yi oku
        df = pd.read_csv(file_path)
        
        # Sütun isimlerini standartlaştır
        df.columns = df.columns.str.strip().str.lower()
        
        # Tarih formatını düzelt
        df['date'] = pd.to_datetime(df['date'], format='%m/%d/%Y')
        
        # Volume temizle
        df['volume'] = df['vol.'].apply(clean_volume)
        
        # Change % temizle
        df['change_pct'] = df['change %'].apply(clean_percentage)
        
        # Standart sütunları seç ve yeniden adlandır
        result = pd.DataFrame({
            'date': df['date'],
            'symbol': symbol,
            'open': df['open'],
            'high': df['high'],
            'low': df['low'],
            'close': df['price'],  # Price = Close
            'volume': df['volume'],
            'change_pct': df['change_pct']
        })
        
        # Tarihe göre sırala (eskiden yeniye)
        result = result.sort_values('date')
        
        print(f"✅ {symbol}: {len(result)} satır")
        return result
        
    except Exception as e:
        print(f"❌ {symbol} hatası: {e}")
        return None

def main():
    """Ana fonksiyon"""
    print("\n" + "="*60)
    print("📦 HİSSE VERİLERİNİ BİRLEŞTİRME")
    print("="*60)
    
    # Dosya yolları ve semboller
    data_dir = '../data'
    
    files = {
        'AAPL': 'Apple Stock Price History (1).csv',
        'MSFT': 'Microsoft Stock Price History.csv',
        'GOOGL': 'Alphabet A Stock Price History.csv',
        'AMZN': 'Amazon.com Stock Price History.csv',
        'META': 'Meta Platforms Stock Price History.csv',
        'TSLA': 'Tesla Stock Price History.csv'
    }
    
    # Tüm verileri birleştir
    all_data = []
    
    for symbol, filename in files.items():
        file_path = os.path.join(data_dir, filename)
        
        if not os.path.exists(file_path):
            print(f"⚠️ Dosya bulunamadı: {filename}")
            continue
        
        df = process_csv_file(file_path, symbol)
        
        if df is not None:
            all_data.append(df)
    
    if not all_data:
        print("\n❌ Hiç veri işlenemedi!")
        return
    
    # Tüm verileri birleştir
    combined_df = pd.concat(all_data, ignore_index=True)
    combined_df = combined_df.sort_values(['symbol', 'date'])
    
    print("\n" + "="*60)
    print("📊 BİRLEŞTİRİLMİŞ VERİ ÖZETİ")
    print("="*60)
    print(f"\nToplam satır: {len(combined_df)}")
    print(f"Tarih aralığı: {combined_df['date'].min()} - {combined_df['date'].max()}")
    print(f"\nHisse başına satır sayısı:")
    print(combined_df['symbol'].value_counts().sort_index())
    
    # Kaydet
    output_dir = 'data/csv'
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'stock_data.csv')
    
    combined_df.to_csv(output_path, index=False)
    
    print(f"\n✅ Veri kaydedildi: {output_path}")
    print("\n💡 Şimdi şu komutu çalıştırın:")
    print("   python train_from_csv.py")

if __name__ == "__main__":
    main()
