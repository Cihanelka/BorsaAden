/**
 * Created by: Aden Borsa Team
 * Created At: 2025
 * Subject: Hisse senedi yorum (alım-satım görüşü) işlemleri route'ları
 */
import express from 'express';
import { authenticateToken } from './auth.js';
import db from '../database.js';

const router = express.Router();

/**
 * Belirtilen hisse senedi için tüm yorumları kullanıcı bilgileriyle birlikte getirir.
 */
router.get('/:symbol', (req, res) => {
  const { symbol } = req.params;

  try {
    const comments = db.prepare(`
      SELECT 
        c.*,
        u.email as user_email,
        u.full_name as user_full_name,
        u.profession as user_profession
      FROM comments c
      JOIN users u ON c.user_id = u.id
      WHERE c.symbol = ?
      ORDER BY c.created_at DESC
    `).all(symbol);

    // Format response
    const formattedComments = comments.map(comment => ({
      id: comment.id,
      user_id: comment.user_id,
      symbol: comment.symbol,
      content: comment.content,
      created_at: comment.created_at,
      updated_at: comment.updated_at,
      user: {
        email: comment.user_email,
        full_name: comment.user_full_name,
        profession: comment.user_profession
      }
    }));

    res.json({ comments: formattedComments });
  } catch (error) {
    console.error('Get comments error:', error);
    res.status(500).json({ error: 'Yorumlar alınamadı' });
  }
});

/**
 * Belirtilen hisse senedi için yeni yorum ekler.
 */
router.post('/', authenticateToken, (req, res) => {
  const { symbol, content } = req.body;

  if (!symbol || !content) {
    return res.status(400).json({ error: 'Symbol ve content gerekli' });
  }

  try {
    const result = db.prepare(
      'INSERT INTO comments (user_id, symbol, content) VALUES (?, ?, ?)'
    ).run(req.userId, symbol, content);

    const comment = db.prepare(`
      SELECT 
        c.*,
        u.email as user_email,
        u.full_name as user_full_name,
        u.profession as user_profession
      FROM comments c
      JOIN users u ON c.user_id = u.id
      WHERE c.id = ?
    `).get(result.lastInsertRowid);

    const formattedComment = {
      id: comment.id,
      user_id: comment.user_id,
      symbol: comment.symbol,
      content: comment.content,
      created_at: comment.created_at,
      updated_at: comment.updated_at,
      user: {
        email: comment.user_email,
        full_name: comment.user_full_name,
        profession: comment.user_profession
      }
    };

    res.json({ comment: formattedComment });
  } catch (error) {
    console.error('Add comment error:', error);
    res.status(500).json({ error: 'Yorum eklenemedi' });
  }
});

/**
 * Mevcut yorumu günceller.
 * Sadece yorumun sahibi düzenleyebilir.
 */
router.put('/:id', authenticateToken, (req, res) => {
  const { id } = req.params;
  const { content } = req.body;

  if (!content) {
    return res.status(400).json({ error: 'Content gerekli' });
  }

  try {
    // Check if comment belongs to user
    const comment = db.prepare('SELECT user_id FROM comments WHERE id = ?').get(id);
    if (!comment) {
      return res.status(404).json({ error: 'Yorum bulunamadı' });
    }
    if (comment.user_id !== req.userId) {
      return res.status(403).json({ error: 'Bu yorumu düzenleme yetkiniz yok' });
    }

    // Update comment
    db.prepare(
      'UPDATE comments SET content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?'
    ).run(content, id);

    const updatedComment = db.prepare(`
      SELECT 
        c.*,
        u.email as user_email,
        u.full_name as user_full_name,
        u.profession as user_profession
      FROM comments c
      JOIN users u ON c.user_id = u.id
      WHERE c.id = ?
    `).get(id);

    const formattedComment = {
      id: updatedComment.id,
      user_id: updatedComment.user_id,
      symbol: updatedComment.symbol,
      content: updatedComment.content,
      created_at: updatedComment.created_at,
      updated_at: updatedComment.updated_at,
      user: {
        email: updatedComment.user_email,
        full_name: updatedComment.user_full_name,
        profession: updatedComment.user_profession
      }
    };

    res.json({ comment: formattedComment });
  } catch (error) {
    console.error('Update comment error:', error);
    res.status(500).json({ error: 'Yorum güncellenemedi' });
  }
});

/**
 * Yorumu siler.
 * Sadece yorumun sahibi silebilir.
 */
router.delete('/:id', authenticateToken, (req, res) => {
  const { id } = req.params;

  try {
    // Check if comment belongs to user
    const comment = db.prepare('SELECT user_id FROM comments WHERE id = ?').get(id);
    if (!comment) {
      return res.status(404).json({ error: 'Yorum bulunamadı' });
    }
    if (comment.user_id !== req.userId) {
      return res.status(403).json({ error: 'Bu yorumu silme yetkiniz yok' });
    }

    db.prepare('DELETE FROM comments WHERE id = ?').run(id);

    res.json({ message: 'Yorum silindi' });
  } catch (error) {
    console.error('Delete comment error:', error);
    res.status(500).json({ error: 'Yorum silinemedi' });
  }
});

export default router;
