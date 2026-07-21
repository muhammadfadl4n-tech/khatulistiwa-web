import { Router } from 'express';
import { getDb } from './db.js';

export const mutationsRouter = Router();

function normalizeText(value, fallback = '') {
  if (value === undefined || value === null) return fallback;
  return String(value).trim();
}

function parsePositiveInteger(value, fieldName) {
  const number = Number(value);
  if (!Number.isInteger(number) || number <= 0) {
    throw new Error(`${fieldName} harus lebih dari 0`);
  }
  return number;
}

function parsePagination(query) {
  const page = Number(query.page || 1);
  const limit = Number(query.limit || 20);

  return {
    page: Number.isInteger(page) && page > 0 ? page : 1,
    limit: Number.isInteger(limit) && limit > 0 && limit <= 100 ? limit : 20,
  };
}

function todayDate() {
  return new Date().toISOString().slice(0, 10);
}

mutationsRouter.get('/', (req, res, next) => {
  try {
    const db = getDb();
    const { page, limit } = parsePagination(req.query);
    const offset = (page - 1) * limit;
    const conditions = [];
    const params = {};

    const materialId = Number(req.query.material_id);
    if (req.query.material_id !== undefined) {
      if (!Number.isInteger(materialId) || materialId <= 0) {
        return res.status(400).json({ error: 'ID material tidak valid' });
      }
      conditions.push('mu.material_id = @material_id');
      params.material_id = materialId;
    }

    if (req.query.type !== undefined) {
      const type = normalizeText(req.query.type);
      if (!['in', 'out'].includes(type)) {
        return res.status(400).json({ error: 'Tipe mutasi tidak valid' });
      }
      conditions.push('mu.type = @type');
      params.type = type;
    }

    const startDate = normalizeText(req.query.start_date);
    if (startDate) {
      conditions.push('mu.date >= @start_date');
      params.start_date = startDate;
    }

    const endDate = normalizeText(req.query.end_date);
    if (endDate) {
      conditions.push('mu.date <= @end_date');
      params.end_date = endDate;
    }

    const search = normalizeText(req.query.search);
    if (search) {
      conditions.push(`(
        ma.name LIKE @search OR
        mu.source LIKE @search OR
        mu.destination LIKE @search OR
        mu.notes LIKE @search
      )`);
      params.search = `%${search}%`;
    }

    const where = conditions.length ? `WHERE ${conditions.join(' AND ')}` : '';
    const total = db
      .prepare(`SELECT COUNT(*) AS count FROM mutations mu JOIN materials ma ON ma.id = mu.material_id ${where}`)
      .get(params).count;

    const data = db
      .prepare(`
        SELECT
          mu.id,
          mu.material_id,
          ma.name AS material_name,
          mu.type,
          mu.qty,
          mu.date,
          mu.source,
          mu.destination,
          mu.notes,
          mu.created_by,
          mu.created_at
        FROM mutations mu
        JOIN materials ma ON ma.id = mu.material_id
        ${where}
        ORDER BY mu.created_at DESC, mu.id DESC
        LIMIT @limit OFFSET @offset
      `)
      .all({ ...params, limit, offset });

    return res.json({ data, page, limit, total });
  } catch (error) {
    return next(error);
  }
});

function recordMutation(type) {
  return (req, res, next) => {
    try {
      const materialId = Number(req.body?.material_id);
      if (!Number.isInteger(materialId) || materialId <= 0) {
        return res.status(400).json({ error: 'ID material tidak valid' });
      }

      const qty = parsePositiveInteger(req.body?.qty, 'Jumlah');
      const date = normalizeText(req.body?.date, todayDate()) || todayDate();
      const source = normalizeText(req.body?.source);
      const destination = normalizeText(req.body?.destination);
      const notes = normalizeText(req.body?.notes);
      const createdBy = req.user.username;
      const db = getDb();

      const transaction = db.transaction(() => {
        const material = db.prepare('SELECT id, stock FROM materials WHERE id = ?').get(materialId);
        if (!material) {
          return { status: 404, body: { error: 'Material tidak ditemukan' } };
        }

        if (type === 'out' && qty > material.stock) {
          return { status: 400, body: { error: 'Stok tidak mencukupi' } };
        }

        const result = db.prepare(`
          INSERT INTO mutations (material_id, type, qty, date, source, destination, notes, created_by)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        `).run(materialId, type, qty, date, source, destination, notes, createdBy);

        const stockOperator = type === 'in' ? '+' : '-';
        db.prepare(`
          UPDATE materials
          SET stock = stock ${stockOperator} ?, updated_at = CURRENT_TIMESTAMP
          WHERE id = ?
        `).run(qty, materialId);

        const mutation = db.prepare(`
          SELECT
            mu.id,
            mu.material_id,
            ma.name AS material_name,
            mu.type,
            mu.qty,
            mu.date,
            mu.source,
            mu.destination,
            mu.notes,
            mu.created_by,
            mu.created_at
          FROM mutations mu
          JOIN materials ma ON ma.id = mu.material_id
          WHERE mu.id = ?
        `).get(result.lastInsertRowid);

        return { status: 201, body: mutation };
      });

      const result = transaction();
      return res.status(result.status).json(result.body);
    } catch (error) {
      if (error.message?.includes('harus lebih dari 0')) {
        return res.status(400).json({ error: error.message });
      }
      return next(error);
    }
  };
}

mutationsRouter.post('/in', recordMutation('in'));
mutationsRouter.post('/out', recordMutation('out'));
