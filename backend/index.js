import express from 'express';
import cors from 'cors';
import fetch from 'node-fetch';
import { initDatabase } from './database.js';
import authRoutes from './routes/auth.js';
import favoritesRoutes from './routes/favorites.js';
import commentsRoutes from './routes/comments.js';
import mlRoutes from './routes/ml.js';

const app = express();
const PORT = process.env.API_PORT || 3001;
const HOST = process.env.API_HOST || '0.0.0.0';

// Initialize database
initDatabase();

// Middleware
app.use(cors());
app.use(express.json());

// Routes
app.use('/api/auth', authRoutes);
app.use('/api/favorites', favoritesRoutes);
app.use('/api/comments', commentsRoutes);
app.use('/api/ml', mlRoutes);

// News API proxy (existing)
const NEWS_API_KEY = '78e1efb0e1964e8fbbf4158f7b9c65f1';

app.get('/api/news', async (req, res) => {
  try {
    const response = await fetch(
      `https://newsapi.org/v2/top-headlines?country=tr&category=business&apiKey=${NEWS_API_KEY}`
    );

    if (!response.ok) {
      throw new Error('NewsAPI request failed');
    }

    const data = await response.json();
    res.json(data);
  } catch (error) {
    console.error('Error fetching news:', error);
    res.status(500).json({ error: 'Failed to fetch news' });
  }
});

// Health check
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', message: 'Aden Borsa API is running' });
});

app.listen(PORT, HOST, () => {
  console.log(`🚀 Aden Borsa API server running on http://${HOST}:${PORT}`);
  console.log(`📊 Database: SQLite (aden-borsa.db)`);
});
