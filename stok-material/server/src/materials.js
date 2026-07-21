import { Router } from 'express';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { getDb } from './db.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const uploadsDir = path.resolve(__dirname, '../uploads');

export const materialsRouter = Router();

function normalizeText(value, fallback = '') {
  if (value === undefined || value === null) return fallback;
  return String(value).trim();
}

function parseNonNegativeInteger(value, fieldName, { required = false, fallback = 0 } = {}) {
  if (value === undefined || value === null || value === '') {
    if (required) throw new Error(`${fieldName} wajib diisi`);
    return fallback;
  }

  const number = Number(value);
  if (!Number.isInteger(number) || number < 0) {
    throw new Error(`${fieldName} harus berupa angka 0 atau lebih`);
  }

  return number;
}

materialsRouter.get('/', (req, res, next) => {
  try {
    const db = getDb();
    const search = normalizeText(req.query.search);

    if (search) {
      const materials = db
        .prepare('SELECT * FROM materials WHERE name LIKE ? ORDER BY name ASC')
        .all(`%${search}%`);
      return res.json(materials);
    }

    const materials = db.prepare('SELECT * FROM materials ORDER BY name ASC').all();
    return res.json(materials);
  } catch (error) {
    return next(error);
  }
});

materialsRouter.post('/', (req, res, next) => {
  try {
    const name = normalizeText(req.body?.name);
    if (!name) {
      return res.status(400).json({ error: 'Nama material wajib diisi' });
    }

    const category = normalizeText(req.body?.category);
    const unit = normalizeText(req.body?.unit, 'pcs') || 'pcs';
    const minStock = parseNonNegativeInteger(req.body?.min_stock, 'Minimum stok');
    const image = normalizeText(req.body?.image || '');

    const db = getDb();
    const result = db
      .prepare('INSERT INTO materials (name, category, unit, min_stock, image) VALUES (?, ?, ?, ?, ?)')
      .run(name, category, unit, minStock, image);
    const material = db.prepare('SELECT * FROM materials WHERE id = ?').get(result.lastInsertRowid);

    return res.status(201).json(material);
  } catch (error) {
    return next(error);
  }
});

materialsRouter.put('/:id', (req, res, next) => {
  try {
    const id = Number(req.params.id);
    if (!Number.isInteger(id) || id <= 0) {
      return res.status(400).json({ error: 'ID material tidak valid' });
    }

    const name = normalizeText(req.body?.name);
    if (!name) {
      return res.status(400).json({ error: 'Nama material wajib diisi' });
    }

    const category = normalizeText(req.body?.category);
    const unit = normalizeText(req.body?.unit, 'pcs') || 'pcs';
    const minStock = parseNonNegativeInteger(req.body?.min_stock, 'Minimum stok');
    const image = normalizeText(req.body?.image || '');

    const db = getDb();

    // If image changed, delete old one
    if (req.body?.delete_image) {
      const old = db.prepare('SELECT image FROM materials WHERE id = ?').get(id);
      if (old?.image && !old.image.startsWith('http')) {
        try { fs.unlinkSync(path.join(uploadsDir, old.image)); } catch {}
      }
    }

    const existing = db.prepare('SELECT id FROM materials WHERE id = ?').get(id);
    if (!existing) {
      return res.status(404).json({ error: 'Material tidak ditemukan' });
    }

    db.prepare(`
      UPDATE materials
      SET name = ?, category = ?, unit = ?, min_stock = ?, image = ?, updated_at = CURRENT_TIMESTAMP
      WHERE id = ?
    `).run(name, category, unit, minStock, image, id);

    const material = db.prepare('SELECT * FROM materials WHERE id = ?').get(id);
    return res.json(material);
  } catch (error) {
    return next(error);
  }
});

materialsRouter.delete('/:id', (req, res, next) => {
  try {
    const id = Number(req.params.id);
    if (!Number.isInteger(id) || id <= 0) {
      return res.status(400).json({ error: 'ID material tidak valid' });
    }

    const db = getDb();
    const existing = db.prepare('SELECT id FROM materials WHERE id = ?').get(id);
    if (!existing) {
      return res.status(404).json({ error: 'Material tidak ditemukan' });
    }

    const relatedMutation = db.prepare('SELECT id FROM mutations WHERE material_id = ? LIMIT 1').get(id);
    if (relatedMutation) {
      return res.status(400).json({ error: 'Material tidak dapat dihapus karena memiliki mutasi' });
    }

    db.prepare('DELETE FROM materials WHERE id = ?').run(id);
    return res.json({ ok: true });
  } catch (error) {
    return next(error);
  }
});
