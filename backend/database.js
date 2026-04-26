/**
 * Created by: Aden Borsa Team
 * Created At: 2025
 * Subject: SQLite veritabanı bağlantısı ve şema başlatma
 */
import Database from 'better-sqlite3';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const dbPath = join(__dirname, '..', 'database', 'aden-borsa.db');
const db = new Database(dbPath);

// Foreign key kısıtlamalarını aktif et
db.pragma('foreign_keys = ON');

/**
 * Veritabanı tablolarını ve indekslerini oluşturur.
 * Uygulama her başlatıldığında çağrılır; IF NOT EXISTS sayesinde mevcut verilere dokunmaz.
 */
export function initDatabase() {
  // Users table
  db.exec(`
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      email TEXT UNIQUE NOT NULL,
      username TEXT UNIQUE NOT NULL,
      password TEXT NOT NULL,
      full_name TEXT,
      profession TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
  `);

  // Add profession column if it doesn't exist (for existing databases)
  try {
    db.exec(`ALTER TABLE users ADD COLUMN profession TEXT`);
  } catch (err) {
    // Column already exists, ignore error
  }

  // Favorites table
  db.exec(`
    CREATE TABLE IF NOT EXISTS favorites (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      symbol TEXT NOT NULL,
      stock_name TEXT NOT NULL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
      UNIQUE(user_id, symbol)
    )
  `);

  // Comments table
  db.exec(`
    CREATE TABLE IF NOT EXISTS comments (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      symbol TEXT NOT NULL,
      content TEXT NOT NULL,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
  `);

  // Create indexes
  db.exec(`
    CREATE INDEX IF NOT EXISTS idx_favorites_user_id ON favorites(user_id);
    CREATE INDEX IF NOT EXISTS idx_favorites_symbol ON favorites(symbol);
    CREATE INDEX IF NOT EXISTS idx_comments_user_id ON comments(user_id);
    CREATE INDEX IF NOT EXISTS idx_comments_symbol ON comments(symbol);
    CREATE INDEX IF NOT EXISTS idx_comments_created_at ON comments(created_at DESC);
  `);

  console.log('✅ Database initialized successfully');
}

export default db;
