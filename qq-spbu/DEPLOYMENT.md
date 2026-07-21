# 🚀 Panduan Deploy Aplikasi Laporan BBM SPBU

## 📊 Pilihan Database

### SQLite (Development)
- ✅ Mudah setup, tidak perlu konfigurasi
- ❌ Data hilang saat redeploy di platform cloud
- ❌ Tidak support multiple workers
- **Cocok untuk:** Development, testing, demo lokal

### PostgreSQL (Production)
- ✅ Data persisten meski redeploy
- ✅ Support multiple workers
- ✅ Production-ready
- ✅ Free tier tersedia di Render
- **Cocok untuk:** Production, staging

**👉 Panduan lengkap setup PostgreSQL:** [RENDER_POSTGRES_SETUP.md](RENDER_POSTGRES_SETUP.md)

---

## 📦 Persiapan Sebelum Deploy

### 1. Setup Environment Production

Buat file `.env` untuk production:

```env
SECRET_KEY=your-super-secret-key-here-change-this
FLASK_ENV=production
DATABASE_URL=postgresql://user:password@host:5432/dbname
```

**PENTING:** Ganti `SECRET_KEY` dengan random string yang panjang!

Generate random key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 2. Update app.py untuk Production

Pastikan app.py menggunakan config production:
```python
import os
env = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(config[env])
```

### 3. Install Gunicorn (sudah ada di requirements.txt)

Gunicorn adalah WSGI server untuk production.

---

## 🐙 Deploy ke GitHub

```bash
cd "C:\Ai Station\form-qq-spbu"
git init
git add .
git commit -m "Initial commit: Aplikasi Laporan Pembongkaran BBM SPBU"
git branch -M main
git remote add origin https://github.com/USERNAME/form-qq-spbu.git
git push -u origin main
```

---

## 🛤️ Opsi 1: Railway (Recommended - Paling Mudah)

**Kelebihan:** Gratis, auto-deploy dari GitHub, SSL otomatis

### Langkah-langkah:

1. **Buat akun** di [railway.app](https://railway.app) (login dengan GitHub)

2. **Install Railway CLI:**
   ```bash
   npm i -g @railway/cli
   railway login
   ```

3. **Deploy:**
   ```bash
   cd "C:\Ai Station\form-qq-spbu"
   railway init
   railway up
   ```

4. **Set Environment Variables:**
   ```bash
   railway variables set SECRET_KEY="your-secret-key"
   railway variables set FLASK_ENV="production"
   ```

5. **Generate Domain:**
   - Buka dashboard Railway
   - Klik project → Settings → Networking → Generate Domain
   - URL akan seperti: `https://your-app.up.railway.app`

**Catatan:** Railway free tier = $5 credit/bulan (cukup untuk aplikasi kecil)

---

## 🎨 Opsi 2: Render (Gratis dengan Batasan)

**Kelebihan:** Free tier, auto-deploy dari GitHub

### Langkah-langkah:

1. **Push code ke GitHub** (lihat bagian Deploy ke GitHub)

2. **Buat akun** di [render.com](https://render.com) (login dengan GitHub)

3. **Create New Web Service:**
   - Klik "New" → "Web Service"
   - Connect repository GitHub
   - Pilih repository `form-qq-spbu`

4. **Konfigurasi:**
   - **Name:** `form-qq-spbu`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`

5. **Add Environment Variables:**
   - Klik "Environment"
   - Tambahkan:
     - `SECRET_KEY` = your-secret-key
     - `FLASK_ENV` = production

6. **Deploy!**
   - Klik "Create Web Service"
   - URL akan seperti: `https://form-qq-spbu.onrender.com`

**Catatan:** Render free tier = service tidur setelah 15 menit tidak aktif (cold start ~30 detik)

---

## 🐳 Opsi 3: VPS (DigitalOcean, AWS, dll)

**Kelebihan:** Full control, performa terbaik, cocok untuk production serius

### Langkah-langkah:

1. **Setup VPS Ubuntu 22.04:**
   ```bash
   ssh root@your-server-ip
   apt update && apt upgrade -y
   apt install python3 python3-pip python3-venv nginx -y
   ```

2. **Upload code:**
   ```bash
   git clone https://github.com/username/form-qq-spbu.git
   cd form-qq-spbu
   ```

3. **Setup Virtual Environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Setup Gunicorn systemd service:**
   
   Buat file `/etc/systemd/system/form-qq-spbu.service`:
   ```ini
   [Unit]
   Description=Gunicorn instance for form-qq-spbu
   After=network.target

   [Service]
   User=www-data
   Group=www-data
   WorkingDirectory=/root/form-qq-spbu
   Environment="PATH=/root/form-qq-spbu/venv/bin"
   Environment="FLASK_ENV=production"
   Environment="SECRET_KEY=your-secret-key"
   ExecStart=/root/form-qq-spbu/venv/bin/gunicorn -w 4 -b 127.0.0.1:5560 app:app

   [Install]
   WantedBy=multi-user.target
   ```

   ```bash
   systemctl start form-qq-spbu
   systemctl enable form-qq-spbu
   ```

5. **Setup Nginx reverse proxy:**
   
   Buat file `/etc/nginx/sites-available/form-qq-spbu`:
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://127.0.0.1:5560;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           client_max_body_size 100M;
       }

       location /uploads/ {
           alias /root/form-qq-spbu/uploads/;
           expires 30d;
           add_header Cache-Control "public, immutable";
       }
   }
   ```

   ```bash
   ln -s /etc/nginx/sites-available/form-qq-spbu /etc/nginx/sites-enabled/
   nginx -t
   systemctl reload nginx
   ```

6. **Setup SSL dengan Let's Encrypt:**
   ```bash
   apt install certbot python3-certbot-nginx -y
   certbot --nginx -d your-domain.com
   ```

---

## 🗄️ Migrasi Database ke PostgreSQL (Production)

Untuk production, gunakan PostgreSQL bukan SQLite:

1. **Install PostgreSQL di server:**
   ```bash
   apt install postgresql postgresql-contrib -y
   ```

2. **Buat database:**
   ```bash
   sudo -u postgres psql
   CREATE DATABASE bbm_reports;
   CREATE USER bbm_user WITH PASSWORD 'your-password';
   GRANT ALL PRIVILEGES ON DATABASE bbm_reports TO bbm_user;
   \q
   ```

3. **Update .env:**
   ```env
   DATABASE_URL=postgresql://bbm_user:your-password@localhost:5432/bbm_reports
   ```

4. **Install psycopg2:**
   ```bash
   pip install psycopg2-binary
   ```

5. **Tambahkan ke requirements.txt:**
   ```
   psycopg2-binary==2.9.*
   ```

---

## 🔒 Checklist Keamanan Production

- [ ] Ganti `SECRET_KEY` dengan random string panjang
- [ ] Set `FLASK_ENV=production`
- [ ] Set `DEBUG=False`
- [ ] Gunakan PostgreSQL (bukan SQLite)
- [ ] Setup HTTPS/SSL
- [ ] Backup database rutin
- [ ] Setup firewall (ufw)
- [ ] Disable directory listing untuk /uploads
- [ ] Setup rate limiting untuk login
- [ ] Ganti password default semua user

---

## 📊 Monitoring & Backup

### Backup Database SQLite:
```bash
# Cron job harian
0 2 * * * cp /path/to/bbm_reports.db /backup/bbm_reports_$(date +\%Y\%m\%d).db
```

### Backup Uploads:
```bash
# Cron job mingguan
0 3 * * 0 tar -czf /backup/uploads_$(date +\%Y\%m\%d).tar.gz /path/to/uploads/
```

---

## 🆘 Troubleshooting

### Error: "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### Error: "Permission denied" untuk uploads/
```bash
chmod 755 uploads/
chown www-data:www-data uploads/
```

### Error: "Database locked" (SQLite)
- Gunakan PostgreSQL untuk production
- Atau pastikan hanya 1 worker gunicorn

### App tidak bisa diakses
- Check log: `journalctl -u form-qq-spbu -f`
- Check port: `netstat -tlnp | grep 5560`
- Check nginx: `tail -f /var/log/nginx/error.log`

---

## 📞 Support

Jika ada masalah saat deploy, silakan buat issue di GitHub repository.

**Happy deploying! 🎉**
