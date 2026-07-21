import { Router } from 'express';
import multer from 'multer';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import fs from 'node:fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const uploadsDir = path.resolve(__dirname, '../uploads');

// Allowed image types
const ALLOWED = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];
const MAX_SIZE = 5 * 1024 * 1024; // 5MB

const storage = multer.diskStorage({
  destination: (_req, _file, cb) => cb(null, uploadsDir),
  filename: (_req, file, cb) => {
    const ext = path.extname(file.originalname).toLowerCase() || '.jpg';
    const name = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}${ext}`;
    cb(null, name);
  },
});

const upload = multer({
  storage,
  limits: { fileSize: MAX_SIZE },
  fileFilter: (_req, file, cb) => {
    if (ALLOWED.includes(file.mimetype)) {
      cb(null, true);
    } else {
      cb(new Error('Format file tidak didukung. Gunakan JPG, PNG, WebP, atau GIF.'));
    }
  },
});

export const uploadRouter = Router();

uploadRouter.post('/', (req, res, next) => {
  upload.single('image')(req, res, (err) => {
    if (err) {
      if (err instanceof multer.MulterError && err.code === 'LIMIT_FILE_SIZE') {
        return res.status(400).json({ error: 'Ukuran file maksimal 5MB' });
      }
      return res.status(400).json({ error: err.message || 'Upload gagal' });
    }

    if (!req.file) {
      return res.status(400).json({ error: 'File tidak ditemukan' });
    }

    return res.json({
      filename: req.file.filename,
      url: `/uploads/${req.file.filename}`,
    });
  });
});

// DELETE uploaded file
uploadRouter.delete('/:filename', (req, res) => {
  const filepath = path.join(uploadsDir, req.params.filename);

  // Prevent path traversal
  if (req.params.filename.includes('..') || req.params.filename.includes('/')) {
    return res.status(400).json({ error: 'Invalid filename' });
  }

  try {
    if (fs.existsSync(filepath)) {
      fs.unlinkSync(filepath);
      return res.json({ ok: true });
    }
    return res.status(404).json({ error: 'File not found' });
  } catch {
    return res.status(500).json({ error: 'Gagal menghapus file' });
  }
});
