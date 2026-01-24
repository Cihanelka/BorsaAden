"""
Enhanced Model Test Script
Tests the enhanced predictor directly without API
"""
from enhanced_predictor import EnhancedStockPredictor
from data_collector import DataCollector

def main():
    print("="*60)
    print("🧪 TESTING ENHANCED STOCK PREDICTOR")
    print("="*60)
    
    # Initialize
    predictor = EnhancedStockPredictor()
    
    # Load model
    if not predictor.load_models():
        print("❌ Model could not be loaded!")
        return
    
    print("\n✅ Model loaded successfully!")
    
    # Test with AAPL
    symbol = 'AAPL'
    print(f"\n📊 Testing prediction for {symbol}...")
    
    # Collect data
    collector = DataCollector()
    df = collector.collect_stock_data(symbol, days=90)
    
    if df.empty:
        print(f"❌ No data for {symbol}")
        return
    
    print(f"✅ Data collected: {len(df)} rows")
    
    # Make prediction
    print(f"\n🔮 Making prediction...")
    result = predictor.predict(df)
    
    print("\n" + "="*60)
    print("📈 PREDICTION RESULT")
    print("="*60)
    print(f"Symbol: {symbol}")
    print(f"Prediction: {result['prediction']}")
    print(f"Confidence: {result['confidence']:.2%}")
    
    if result.get('probabilities'):
        print(f"\nProbabilities:")
        for label, prob in result['probabilities'].items():
            print(f"  {label:10s}: {prob:.2%}")
    
    print(f"\n⚠️  {result['disclaimer']}")
    print("="*60)

if __name__ == '__main__':
    main()
