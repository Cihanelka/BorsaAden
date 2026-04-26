/**
 * Created by: Aden Borsa Team
 * Created At: 2025
 * Subject: Python ML servisine proxy görevi yapan route'lar (tahmin, analiz, sentiment)
 */
import express from 'express';
import fetch from 'node-fetch';

const router = express.Router();

// Python ML servisinin adresi
const ML_SERVICE_URL = process.env.ML_SERVICE_URL || 'http://localhost:5000';

/**
 * ML servisi sağlık kontrolü
 */
router.get('/health', async (req, res) => {
  try {
    const response = await fetch(`${ML_SERVICE_URL}/api/health`);
    const data = await response.json();
    res.json(data);
  } catch (error) {
    console.error('ML service health check error:', error);
    res.status(503).json({ 
      status: 'error', 
      message: 'ML servisi yanıt vermiyor',
      error: error.message 
    });
  }
});

/**
 * Veri toplama endpoint'i
 * POST /api/ml/collect-data
 * Body: { symbols: ["AAPL", "MSFT"], stock_days: 90, news_days: 30 }
 */
router.post('/collect-data', async (req, res) => {
  try {
    const { symbols, stock_days = 90, news_days = 30 } = req.body;

    if (!symbols || !Array.isArray(symbols) || symbols.length === 0) {
      return res.status(400).json({
        success: false,
        error: 'symbols parametresi gerekli (array)'
      });
    }

    const response = await fetch(`${ML_SERVICE_URL}/api/collect-data`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ symbols, stock_days, news_days })
    });

    const data = await response.json();
    res.json(data);
  } catch (error) {
    console.error('ML collect-data error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * Duygu analizi endpoint'i
 * POST /api/ml/analyze-sentiment
 * Body: { news_csv: "news_data.csv", output_csv: "news_with_sentiment.csv" }
 */
router.post('/analyze-sentiment', async (req, res) => {
  try {
    const { news_csv, output_csv } = req.body;

    const response = await fetch(`${ML_SERVICE_URL}/api/analyze-sentiment`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ news_csv, output_csv })
    });

    const data = await response.json();
    res.json(data);
  } catch (error) {
    console.error('ML analyze-sentiment error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * Hisse tahmini endpoint'i
 * POST /api/ml/predict
 * Body: { symbol: "AAPL", use_cached_data: true }
 */
router.post('/predict', async (req, res) => {
  try {
    const { symbol, use_cached_data = true } = req.body;

    if (!symbol) {
      return res.status(400).json({
        success: false,
        error: 'symbol parametresi gerekli'
      });
    }

    const response = await fetch(`${ML_SERVICE_URL}/api/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ symbol, use_cached_data })
    });

    const data = await response.json();
    res.json(data);
  } catch (error) {
    console.error('ML predict error:', error);
    const isServiceDown = error.code === 'ECONNREFUSED' || error.code === 'ENOTFOUND';
    res.status(isServiceDown ? 503 : 500).json({
      success: false,
      error: isServiceDown ? 'ML servisi çalışmıyor. Lütfen başlatın: python ml-service/app.py' : error.message
    });
  }
});

/**
 * Toplu hisse tahmini
 * POST /api/ml/predict-batch
 * Body: { symbols: ["AAPL", "MSFT", "GOOGL"] }
 */
router.post('/predict-batch', async (req, res) => {
  try {
    const { symbols } = req.body;

    if (!symbols || !Array.isArray(symbols) || symbols.length === 0) {
      return res.status(400).json({
        success: false,
        error: 'symbols parametresi gerekli (array)'
      });
    }

    const response = await fetch(`${ML_SERVICE_URL}/api/predict-batch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ symbols })
    });

    const data = await response.json();
    res.json(data);
  } catch (error) {
    console.error('ML predict-batch error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * Hisse senedi tarihsel verilerini al (yfinance ile)
 * POST /api/ml/stock-data
 * Body: { symbol: "AAPL", days: 30 }
 */
router.post('/stock-data', async (req, res) => {
  try {
    const { symbol, days = 30 } = req.body;

    if (!symbol) {
      return res.status(400).json({
        success: false,
        error: 'symbol parametresi gerekli'
      });
    }

    const response = await fetch(`${ML_SERVICE_URL}/api/stock-data`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ symbol, days })
    });

    const data = await response.json();
    res.json(data);
  } catch (error) {
    console.error('ML stock-data error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * Teknik analiz endpoint'i
 * POST /api/ml/technical-analysis
 * Body: { symbol: "AAPL" }
 */
router.post('/technical-analysis', async (req, res) => {
  try {
    const { symbol } = req.body;

    if (!symbol) {
      return res.status(400).json({
        success: false,
        error: 'symbol parametresi gerekli'
      });
    }

    const response = await fetch(`${ML_SERVICE_URL}/api/technical-analysis`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ symbol })
    });

    const data = await response.json();
    res.json(data);
  } catch (error) {
    console.error('ML technical-analysis error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * Duygu analizi özeti
 * POST /api/ml/sentiment-summary
 * Body: { symbol: "AAPL", days: 7 }
 */
router.post('/sentiment-summary', async (req, res) => {
  try {
    const { symbol, days = 7 } = req.body;

    if (!symbol) {
      return res.status(400).json({
        success: false,
        error: 'symbol parametresi gerekli'
      });
    }

    const response = await fetch(`${ML_SERVICE_URL}/api/sentiment-summary`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ symbol, days })
    });

    const data = await response.json();
    res.json(data);
  } catch (error) {
    console.error('ML sentiment-summary error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * Enhanced ML tahmin (Production-ready ensemble model)
 * POST /api/ml/predict-enhanced
 * Body: { symbol: "AAPL" }
 */
router.post('/predict-enhanced', async (req, res) => {
  try {
    const { symbol } = req.body;

    if (!symbol) {
      return res.status(400).json({
        success: false,
        error: 'symbol parametresi gerekli'
      });
    }

    const response = await fetch(`${ML_SERVICE_URL}/api/predict-enhanced`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ symbol })
    });

    const data = await response.json();
    res.json(data);
  } catch (error) {
    console.error('ML predict-enhanced error:', error);
    const isServiceDown = error.code === 'ECONNREFUSED' || error.code === 'ENOTFOUND';
    res.status(isServiceDown ? 503 : 500).json({
      success: false,
      error: isServiceDown ? 'ML servisi çalışmıyor. Lütfen başlatın: python ml-service/app.py' : error.message
    });
  }
});

/**
 * Ensemble ML tahmin (10 model, en yüksek confidence)
 * POST /api/ml/predict-ensemble
 * Body: { symbol: "AAPL" }
 */
router.post('/predict-ensemble', async (req, res) => {
  try {
    const { symbol } = req.body;

    if (!symbol) {
      return res.status(400).json({
        success: false,
        error: 'symbol parametresi gerekli'
      });
    }

    const response = await fetch(`${ML_SERVICE_URL}/api/predict-ensemble`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ symbol })
    });

    const data = await response.json();
    res.json(data);
  } catch (error) {
    console.error('ML predict-ensemble error:', error);
    const isServiceDown = error.code === 'ECONNREFUSED' || error.code === 'ENOTFOUND';
    res.status(isServiceDown ? 503 : 500).json({
      success: false,
      error: isServiceDown ? 'ML servisi çalışmıyor. Lütfen başlatın: python ml-service/app.py' : error.message
    });
  }
});

/**
 * Model eğitimi
 * POST /api/ml/train-model
 * Body: { training_data_csv: "training_data.csv" }
 */
router.post('/train-model', async (req, res) => {
  try {
    const { training_data_csv } = req.body;

    const response = await fetch(`${ML_SERVICE_URL}/api/train-model`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ training_data_csv })
    });

    const data = await response.json();
    res.json(data);
  } catch (error) {
    console.error('ML train-model error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

export default router;
