import express from 'express';
import cors from 'cors';
import cookieParser from 'cookie-parser';
import path from 'node:path';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';
import { authRouter, requireAuth } from './auth.js';
import { materialsRouter } from './materials.js';
import { mutationsRouter } from './mutations.js';
import { dashboardRouter } from './dashboard.js';
import { uploadRouter } from './upload.js';
import { getDb } from './db.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const uploadsDir = path.resolve(__dirname, '../uploads');

const app = express();
const port = process.env.PORT || 3008;

getDb();

// Ensure uploads dir exists
fs.mkdirSync(uploadsDir, { recursive: true });

app.use(cors({
  origin: process.env.CORS_ORIGIN || true,
  credentials: true,
}));
app.use(cookieParser());
app.use(express.json());

// Serve uploaded images
app.use('/uploads', express.static(uploadsDir));

app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', service: 'Stok Material' });
});

app.use('/api/auth', authRouter);
app.use('/api/upload', requireAuth, uploadRouter);
app.use('/api/materials', requireAuth, materialsRouter);
app.use('/api/mutations', requireAuth, mutationsRouter);
app.use('/api/dashboard', requireAuth, dashboardRouter);

if (process.env.NODE_ENV === 'production') {
  const clientDist = path.resolve(__dirname, '../../client/dist');
  const indexHtml = path.join(clientDist, 'index.html');

  app.use(express.static(clientDist));
  app.use((req, res, next) => {
    if (req.path.startsWith('/api/')) {
      return next();
    }

    if (fs.existsSync(indexHtml)) {
      return res.sendFile(indexHtml);
    }

    return res.status(404).json({ error: 'Client build not found' });
  });
}

app.use((req, res) => {
  res.status(404).json({ error: 'Not found' });
});

app.use((err, req, res, next) => {
  console.error(err);
  const status = err.status || err.statusCode || 500;
  const message = status === 500 ? 'Internal server error' : err.message;
  res.status(status).json({ error: message });
});

app.listen(port, () => {
  console.log(`Stok Material server listening on port ${port}`);
});
