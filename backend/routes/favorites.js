/**
 * Created by: Aden Borsa Team
 * Created At: 2025
 * Subject: Kullanıcı favori hisse senedi işlemleri route'ları
 */
import express from 'express';
import { authenticateToken } from './auth.js';
import db from '../database.js';

const router = express.Router();

/**
 * Oturum açmış kullanıcının tüm favori hisselerini getirir.
 */
router.get('/', authenticateToken, (req, res) => {
  try {
    const favorites = db.prepare(
      'SELECT * FROM favorites WHERE user_id = ? ORDER BY created_at DESC'
    ).all(req.userId);

    res.json({ favorites });
  } catch (error) {
    console.error('Get favorites error:', error);
    res.status(500).json({ error: 'Favoriler alınamadı' });
  }
});

/**
 * Kullanıcının favorilerine yeni bir hisse ekler.
 * Aynı hisse zaten varsa hata döner (UNIQUE constraint).
 */
router.post('/', authenticateToken, (req, res) => {
  const { symbol, stockName } = req.body;

  if (!symbol || !stockName) {
    return res.status(400).json({ error: 'Symbol ve stockName gerekli' });
  }

  try {
    const result = db.prepare(
      'INSERT INTO favorites (user_id, symbol, stock_name) VALUES (?, ?, ?)'
    ).run(req.userId, symbol, stockName);

    const favorite = db.prepare('SELECT * FROM favorites WHERE id = ?')
      .get(result.lastInsertRowid);

    res.json({ favorite });
  } catch (error) {
    if (error.code === 'SQLITE_CONSTRAINT') {
      return res.status(400).json({ error: 'Bu hisse zaten favorilerde' });
    }
    console.error('Add favorite error:', error);
    res.status(500).json({ error: 'Favori eklenemedi' });
  }
});

/**
 * Kullanıcının favorilerinden belirtilen sembolü kaldırır.
 */
router.delete('/:symbol', authenticateToken, (req, res) => {
  const { symbol } = req.params;

  try {
    const result = db.prepare(
      'DELETE FROM favorites WHERE user_id = ? AND symbol = ?'
    ).run(req.userId, symbol);

    if (result.changes === 0) {
      return res.status(404).json({ error: 'Favori bulunamadı' });
    }

    res.json({ message: 'Favori silindi' });
  } catch (error) {
    console.error('Delete favorite error:', error);
    res.status(500).json({ error: 'Favori silinemedi' });
  }
});

/**
 * Belirtilen hissenin kullanıcının favorilerinde olup olmadığını kontrol eder.
 */
router.get('/check/:symbol', authenticateToken, (req, res) => {
  const { symbol } = req.params;

  try {
    const favorite = db.prepare(
      'SELECT id FROM favorites WHERE user_id = ? AND symbol = ?'
    ).get(req.userId, symbol);

    res.json({ isFavorite: !!favorite });
  } catch (error) {
    console.error('Check favorite error:', error);
    res.status(500).json({ error: 'Favori kontrol edilemedi' });
  }
});

export default router;
