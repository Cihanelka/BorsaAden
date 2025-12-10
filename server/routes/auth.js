import express from 'express';
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import { body, validationResult } from 'express-validator';
import db from '../database.js';

const router = express.Router();
const JWT_SECRET = 'aden-borsa-secret-key-2025'; // Production'da .env'den alın

// Register
router.post('/register',
  body('email').isEmail(),
  body('username').isLength({ min: 3 }),
  body('password').isLength({ min: 6 }),
  body('fullName').notEmpty(),
  async (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { email, username, password, fullName, profession } = req.body;

    try {
      // Check if email exists
      const existingEmail = db.prepare('SELECT id FROM users WHERE email = ?').get(email);
      if (existingEmail) {
        return res.status(400).json({ error: 'Bu email zaten kayıtlı' });
      }

      // Check if username exists
      const existingUsername = db.prepare('SELECT id FROM users WHERE username = ?').get(username);
      if (existingUsername) {
        return res.status(400).json({ error: 'Bu kullanıcı adı zaten alınmış' });
      }

      // Hash password
      const hashedPassword = await bcrypt.hash(password, 10);

      // Insert user
      const result = db.prepare(
        'INSERT INTO users (email, username, password, full_name, profession) VALUES (?, ?, ?, ?, ?)'
      ).run(email, username, hashedPassword, fullName, profession);

      const user = {
        id: result.lastInsertRowid,
        email,
        username,
        full_name: fullName,
        profession: profession
      };

      // Generate token
      const token = jwt.sign({ userId: user.id }, JWT_SECRET, { expiresIn: '7d' });

      res.json({ user, token });
    } catch (error) {
      console.error('Register error:', error);
      res.status(500).json({ error: 'Kayıt sırasında hata oluştu' });
    }
  }
);

// Login
router.post('/login',
  body('email').isEmail(),
  body('password').notEmpty(),
  async (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { email, password } = req.body;

    try {
      // Find user
      const user = db.prepare('SELECT * FROM users WHERE email = ?').get(email);
      if (!user) {
        return res.status(401).json({ error: 'Email veya şifre hatalı' });
      }

      // Check password
      const isValid = await bcrypt.compare(password, user.password);
      if (!isValid) {
        return res.status(401).json({ error: 'Email veya şifre hatalı' });
      }

      // Generate token
      const token = jwt.sign({ userId: user.id }, JWT_SECRET, { expiresIn: '7d' });

      // Remove password from response
      delete user.password;

      res.json({ user, token });
    } catch (error) {
      console.error('Login error:', error);
      res.status(500).json({ error: 'Giriş sırasında hata oluştu' });
    }
  }
);

// Get current user
router.get('/me', authenticateToken, (req, res) => {
  try {
    const user = db.prepare('SELECT id, email, username, full_name, profession, created_at FROM users WHERE id = ?')
      .get(req.userId);
    
    if (!user) {
      return res.status(404).json({ error: 'Kullanıcı bulunamadı' });
    }

    res.json({ user });
  } catch (error) {
    console.error('Get user error:', error);
    res.status(500).json({ error: 'Kullanıcı bilgileri alınamadı' });
  }
});

// Middleware to authenticate token
export function authenticateToken(req, res, next) {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];

  if (!token) {
    return res.status(401).json({ error: 'Token bulunamadı' });
  }

  jwt.verify(token, JWT_SECRET, (err, decoded) => {
    if (err) {
      return res.status(403).json({ error: 'Geçersiz token' });
    }
    req.userId = decoded.userId;
    next();
  });
}
// Update profile (sadece kullanıcı adı)
router.put('/update-profile', authenticateToken, (req, res) => {
  const { username } = req.body;
  
  if (!username || username.length < 3) {
    return res.status(400).json({ error: 'Kullanıcı adı en az 3 karakter olmalıdır' });
  }

  try {
    // Aynı kullanıcı adı kontrolü
    const existingUser = db.prepare('SELECT id FROM users WHERE username = ? AND id != ?')
      .get(username, req.userId);
      
    if (existingUser) {
      return res.status(400).json({ error: 'Bu kullanıcı adı zaten kullanılıyor' });
    }

    // Sadece kullanıcı adını güncelle
    db.prepare('UPDATE users SET username = ? WHERE id = ?')
      .run(username, req.userId);

    // Güncellenmiş kullanıcı bilgilerini döndür
    const updatedUser = db.prepare('SELECT id, email, username, created_at FROM users WHERE id = ?')
      .get(req.userId);

    res.json({ user: updatedUser });
  } catch (error) {
    console.error('Update profile error:', error);
    res.status(500).json({ error: 'Profil güncellenirken hata oluştu' });
  }
});

// Şifre değiştirme (ayrı endpoint)
router.put('/change-password', authenticateToken, async (req, res) => {
  const { currentPassword, newPassword } = req.body;

  if (!currentPassword || !newPassword) {
    return res.status(400).json({ error: 'Tüm alanları doldurun' });
  }

  if (newPassword.length < 6) {
    return res.status(400).json({ error: 'Yeni şifre en az 6 karakter olmalı' });
  }

  try {
    // Mevcut şifreyi kontrol et
    const user = db.prepare('SELECT password FROM users WHERE id = ?')
      .get(req.userId);

    if (!user) {
      return res.status(404).json({ error: 'Kullanıcı bulunamadı' });
    }

    const isMatch = await bcrypt.compare(currentPassword, user.password);
    if (!isMatch) {
      return res.status(400).json({ error: 'Mevcut şifre yanlış' });
    }

    // Yeni şifreyi hashle ve güncelle
    const hashedPassword = await bcrypt.hash(newPassword, 10);
    db.prepare('UPDATE users SET password = ? WHERE id = ?')
      .run(hashedPassword, req.userId);

    res.json({ message: 'Şifre başarıyla güncellendi' });
  } catch (error) {
    console.error('Change password error:', error);
    res.status(500).json({ error: 'Şifre değiştirilirken hata oluştu' });
  }
});

export default router;
