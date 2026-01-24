"""
Training script for Enhanced Stock Predictor
Usage: python train_enhanced_model.py
"""
from enhanced_predictor import EnhancedStockPredictor
from data_collector import DataCollector
import pandas as pd

def main():
    print("="*60)
    print("🚀 ENHANCED STOCK PREDICTION MODEL TRAINING")
    print("="*60)
    
    # Initialize
    predictor = EnhancedStockPredictor()
    collector = DataCollector()
    
    # Collect training data for multiple symbols
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
    all_data = []
    
    print(f"\n📥 Collecting data for {len(symbols)} symbols...")
    for symbol in symbols:
        try:
            print(f"  - Fetching {symbol}...")
            df = collector.collect_stock_data(symbol, days=365)  # 1 year of data
            if not df.empty:
                all_data.append(df)
        except Exception as e:
            print(f"  ⚠️ Error with {symbol}: {e}")
    
    # Combine all data
    if not all_data:
        print("❌ No data collected! Exiting.")
        return
    
    combined_df = pd.concat(all_data, ignore_index=True)
    print(f"\n✅ Total samples collected: {len(combined_df)}")
    
    # Train model
    scores = predictor.train(combined_df, threshold=0.015, n_splits=5)
    
    print("\n" + "="*60)
    print("🎉 TRAINING COMPLETE!")
    print("="*60)
    print("\n📊 Model Performance (F1 Scores):")
    for model_name, score in scores.items():
        print(f"  {model_name:15s}: {score:.4f}")
    
    print("\n💡 Model is ready for predictions!")
    print("   Use enhanced_predictor.predict(df) to make predictions")
    
if __name__ == '__main__':
    main()
