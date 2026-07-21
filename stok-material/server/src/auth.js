import { Router } from 'express';
import bcrypt from 'bcryptjs';
import { SignJWT, jwtVerify } from 'jose';
import { getDb } from './db.js';

export const authRouter = Router();

const loginAttempts = new Map();
const RATE_LIMIT_WINDOW_MS = 60 * 1000;
const RATE_LIMIT_MAX_ATTEMPTS = 5;
const COOKIE_NAME = 'token';

function jwtSecret() {
  const secret = process.env.JWT_SECRET || 'stok-material-development-secret';
  return new TextEncoder().encode(secret);
}

function seedAdminUser() {
  const db = getDb();
  const username = process.env.ADMIN_USERNAME || 'admin';
  const password = process.env.ADMIN_PASSWORD || 'pertamina123';
  const existing = db.prepare('SELECT id FROM users WHERE username = ?').get(username);

  if (!existing) {
    const passwordHash = bcrypt.hashSync(password, 10);
    db.prepare('INSERT INTO users (username, password_hash) VALUES (?, ?)').run(username, passwordHash);
  }
}

function getClientIp(req) {
  return req.ip || req.socket?.remoteAddress || 'unknown';
}

function isRateLimited(ip) {
  const now = Date.now();
  const current = loginAttempts.get(ip);

  if (!current || now - current.startedAt > RATE_LIMIT_WINDOW_MS) {
    loginAttempts.set(ip, { count: 1, startedAt: now });
    return false;
  }

  current.count += 1;
  return current.count > RATE_LIMIT_MAX_ATTEMPTS;
}

function clearRateLimit(ip) {
  loginAttempts.delete(ip);
}

async function createToken(user) {
  return new SignJWT({ username: user.username })
    .setProtectedHeader({ alg: 'HS256' })
    .setSubject(String(user.id))
    .setIssuedAt()
    .setExpirationTime('24h')
    .sign(jwtSecret());
}

function cookieOptions() {
  return {
    httpOnly: true,
    sameSite: 'lax',
    secure: process.env.NODE_ENV === 'production',
    maxAge: 24 * 60 * 60 * 1000,
  };
}

seedAdminUser();

authRouter.post('/login', async (req, res, next) => {
  try {
    const ip = getClientIp(req);
    if (isRateLimited(ip)) {
      return res.status(429).json({ error: 'Terlalu banyak percobaan login' });
    }

    const { username, password } = req.body || {};
    if (!username || !password || typeof username !== 'string' || typeof password !== 'string') {
      return res.status(400).json({ error: 'Username dan password wajib diisi' });
    }

    const db = getDb();
    const user = db.prepare('SELECT id, username, password_hash FROM users WHERE username = ?').get(username);
    const validPassword = user ? await bcrypt.compare(password, user.password_hash) : false;

    if (!user || !validPassword) {
      return res.status(401).json({ error: 'Username atau password salah' });
    }

    clearRateLimit(ip);
    const token = await createToken(user);
    res.cookie(COOKIE_NAME, token, cookieOptions());
    return res.json({ user: { username: user.username } });
  } catch (error) {
    return next(error);
  }
});

authRouter.get('/me', requireAuth, (req, res) => {
  return res.json({ user: { username: req.user.username } });
});

authRouter.post('/logout', requireAuth, (req, res) => {
  res.clearCookie(COOKIE_NAME, {
    httpOnly: true,
    sameSite: 'lax',
    secure: process.env.NODE_ENV === 'production',
  });
  return res.json({ ok: true });
});

export async function requireAuth(req, res, next) {
  try {
    const token = req.cookies?.[COOKIE_NAME];
    if (!token) {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    const { payload } = await jwtVerify(token, jwtSecret());
    const id = Number(payload.sub);
    const username = payload.username;

    if (!id || typeof username !== 'string') {
      return res.status(401).json({ error: 'Unauthorized' });
    }

    req.user = { id, username };
    return next();
  } catch {
    return res.status(401).json({ error: 'Unauthorized' });
  }
}
