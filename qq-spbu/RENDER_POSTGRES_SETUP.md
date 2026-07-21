# 🗄️ Setup PostgreSQL di Render

Panduan lengkap setup PostgreSQL untuk aplikasi QQ-SPBU agar data persisten.

## 📋 Kenapa PostgreSQL?

**SQLite (default):**
- ❌ Data hilang saat redeploy
- ❌ Tidak support multiple workers
- ❌ Tidak cocok untuk production

**PostgreSQL:**
- ✅ Data persisten meski redeploy
- ✅ Support multiple workers
- ✅ Production-ready
- ✅ Free tier tersedia di Render

---

## 🚀 Langkah-langkah Setup

### 1. Buat PostgreSQL Database di Render

1. **Login ke Render Dashboard**
   - Buka: https://dashboard.render.com
   - Login dengan GitHub

2. **Buat PostgreSQL Database**
   - Klik **"New +"** → **"PostgreSQL"**
   - Isi konfigurasi:
     - **Name:** `qq-spbu-db`
     - **Database:** `qq_spbu`
     - **User:** `qq_spbu_user`
     - **Region:** Singapore (atau yang terdekat)
     - **Instance Type:** **Free** (untuk testing) atau **Starter** ($7/bulan untuk production)
   
3. **Klik "Create PostgreSQL"**
   - Tunggu beberapa menit sampai database ready
   - Status akan berubah menjadi **"Available"**

4. **Copy Internal Database URL**
   - Klik database yang baru dibuat
   - Scroll ke bagian **"Connections"**
   - Copy **"Internal Database URL"**
   - Format: `postgresql://qq_spbu_user:password@host:5432/qq_spbu`

---

### 2. Connect Web Service ke PostgreSQL

1. **Buka Web Service `qq-spbu`**
   - Dashboard → Web Services → `qq-spbu`

2. **Tambahkan Environment Variable**
   - Klik tab **"Environment"**
   - Klik **"Add Environment Variable"**
   - Isi:
     - **Key:** `DATABASE_URL`
     - **Value:** (paste Internal Database URL yang sudah dicopy)
   
3. **Save Changes**
   - Klik **"Save Changes"**
   - Render akan otomatis redeploy

---

### 3. Verifikasi Koneksi

1. **Tunggu Deploy Selesai**
   - Deploy akan otomatis restart setelah environment variable ditambahkan
   - Tunggu sampai status **"Live"**

2. **Check Logs**
   - Klik tab **"Logs"**
   - Cari log: `"Database seeded successfully!"`
   - Jika muncul, berarti database PostgreSQL sudah connected dan ter-seed

3. **Test Aplikasi**
   - Buka URL aplikasi: `https://qq-spbu.onrender.com`
   - Login dengan credentials:
     ```
     admin / admin123
     pertamina / pertamina123
     spbu01 / spbu123
     ```

---

### 4. Reset Database (Jika Perlu)

Jika ingin reset database dan re-seed data demo:

**Via Render Shell:**
```bash
# 1. Buka Shell
Dashboard → qq-spbu → Shell

# 2. Jalankan script reset
python reset_database.py
```

**Via Environment Variable:**
```bash
# 1. Tambahkan environment variable
Key: RESET_DB
Value: true

# 2. Redeploy
Dashboard → qq-spbu → Manual Deploy → Deploy latest commit

# 3. Hapus environment variable RESET_DB setelah reset selesai
```

---

## 🔧 Troubleshooting

### Error: "could not connect to server"

**Penyebab:** DATABASE_URL tidak diset atau salah

**Solusi:**
1. Check environment variable `DATABASE_URL` sudah ada
2. Pastikan menggunakan **"Internal Database URL"** (bukan External)
3. Pastikan URL dimulai dengan `postgresql://`

### Error: "relation does not exist"

**Penyebab:** Tabel belum dibuat

**Solusi:**
```bash
# Via Render Shell
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### Data masih hilang setelah redeploy

**Penyebab:** Masih menggunakan SQLite

**Solusi:**
1. Check logs untuk memastikan PostgreSQL yang dipakai
2. Cari log: `Using database: postgresql://...`
3. Jika masih `sqlite://`, check environment variable `DATABASE_URL`

### Performance lambat

**Penyebab:** Menggunakan free tier PostgreSQL

**Solusi:**
- Upgrade ke **Starter** ($7/bulan) untuk performa lebih baik
- Atau gunakan **Standard** ($20/bulan) untuk production serious

---

## 💰 Biaya PostgreSQL di Render

| Tier | Harga | Storage | Connections | Use Case |
|------|-------|---------|-------------|----------|
| **Free** | $0/bulan | 256 MB | 10 | Testing/Development |
| **Starter** | $7/bulan | 1 GB | 20 | Small Production |
| **Standard** | $20/bulan | 10 GB | 100 | Medium Production |
| **Pro** | $50+/bulan | 100+ GB | 500+ | Large Production |

**Rekomendasi:**
- Development/Testing: **Free tier**
- Production kecil (< 100 users): **Starter**
- Production medium (100-1000 users): **Standard**

---

## 📊 Monitoring Database

### Via Render Dashboard

1. **Buka PostgreSQL Database**
2. **Tab "Metrics"**
   - CPU Usage
   - Memory Usage
   - Storage Usage
   - Connection Count

### Via Shell

```bash
# Connect ke database
psql $DATABASE_URL

# Check table size
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

# Check row count
SELECT 'users' as table_name, count(*) FROM users
UNION ALL
SELECT 'spbu', count(*) FROM spbu
UNION ALL
SELECT 'laporan', count(*) FROM laporan
UNION ALL
SELECT 'uploads', count(*) FROM uploads;
```

---

## 🔄 Backup Database

### Automatic Backup (Render)

- **Free tier:** Tidak ada automatic backup
- **Starter+:** Daily backup, retention 7 hari

### Manual Backup

```bash
# 1. Export database
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# 2. Upload ke storage (Google Drive, S3, dll)
# Atau download ke local
```

### Restore Database

```bash
# 1. Connect ke database
psql $DATABASE_URL

# 2. Restore dari backup
\i backup_20260701.sql
```

---

## 🎯 Checklist Setup PostgreSQL

- [ ] Buat PostgreSQL database di Render
- [ ] Copy Internal Database URL
- [ ] Tambahkan `DATABASE_URL` ke environment variables
- [ ] Redeploy web service
- [ ] Verify database connected (check logs)
- [ ] Test login dengan demo credentials
- [ ] Test upload foto
- [ ] Test create laporan
- [ ] Verify data persist setelah redeploy

---

## 📞 Support

Jika ada masalah saat setup PostgreSQL:

1. **Render Docs:** https://render.com/docs/databases
2. **Render Community:** https://community.render.com
3. **Check Logs:** Dashboard → qq-spbu → Logs

---

## 🎉 Selesai!

Setelah setup PostgreSQL, aplikasi kamu sekarang:
- ✅ Data persisten meski redeploy
- ✅ Support multiple workers
- ✅ Production-ready
- ✅ Scalable

**Happy coding! 🚀**
