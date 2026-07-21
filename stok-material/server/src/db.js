import Database from 'better-sqlite3';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const serverRoot = path.resolve(__dirname, '..');
const dataDir = path.join(serverRoot, 'data');
const dbPath = path.join(dataDir, 'stok.db');

let db;

function initialize(connection) {
  connection.pragma('foreign_keys = ON');

  connection.exec(`
    CREATE TABLE IF NOT EXISTS materials (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      category TEXT DEFAULT "",
      unit TEXT DEFAULT "pcs",
      stock INTEGER NOT NULL DEFAULT 0,
      min_stock INTEGER DEFAULT 0,
      image TEXT DEFAULT "",
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS mutations (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      material_id INTEGER NOT NULL REFERENCES materials(id),
      type TEXT NOT NULL CHECK(type IN ('in','out')),
      qty INTEGER NOT NULL CHECK(qty > 0),
      date TEXT NOT NULL,
      source TEXT DEFAULT "",
      destination TEXT DEFAULT "",
      notes TEXT DEFAULT "",
      created_by TEXT NOT NULL,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_mutations_material_id ON mutations(material_id);
    CREATE INDEX IF NOT EXISTS idx_mutations_date ON mutations(date);
    CREATE INDEX IF NOT EXISTS idx_mutations_type ON mutations(type);
  `);
}

export function getDb() {
  if (!db) {
    fs.mkdirSync(dataDir, { recursive: true });
    db = new Database(dbPath);
    initialize(db);
  }

  return db;
}
