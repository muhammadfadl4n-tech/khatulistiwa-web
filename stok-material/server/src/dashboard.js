import { Router } from 'express';
import { getDb } from './db.js';

export const dashboardRouter = Router();

function todayDate() {
  return new Date().toISOString().slice(0, 10);
}

dashboardRouter.get('/', (req, res, next) => {
  try {
    const db = getDb();
    const today = todayDate();

    const totalMaterials = db.prepare('SELECT COUNT(*) AS count FROM materials').get().count;
    const totalStock = db.prepare('SELECT COALESCE(SUM(stock), 0) AS total FROM materials').get().total;
    const lowStock = db
      .prepare('SELECT * FROM materials WHERE min_stock > 0 AND stock <= min_stock ORDER BY stock ASC, name ASC')
      .all();
    const recentMutations = db
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
        ORDER BY mu.created_at DESC, mu.id DESC
        LIMIT 10
      `)
      .all();
    const inToday = db
      .prepare('SELECT COALESCE(SUM(qty), 0) AS total FROM mutations WHERE type = \'in\' AND date = ?')
      .get(today).total;
    const outToday = db
      .prepare('SELECT COALESCE(SUM(qty), 0) AS total FROM mutations WHERE type = \'out\' AND date = ?')
      .get(today).total;

    return res.json({
      total_materials: totalMaterials,
      total_stock: totalStock,
      low_stock: lowStock,
      recent_mutations: recentMutations,
      in_today: inToday,
      out_today: outToday,
    });
  } catch (error) {
    return next(error);
  }
});
