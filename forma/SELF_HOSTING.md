# Menjalankan Forma di VPS

Versi VPS menggunakan Docker, SQLite, volume persisten untuk media, dan Caddy.
Dashboard serta API pengelolaan membutuhkan login. Formulir publik, pengiriman
jawaban, dan upload media dari formulir tetap dapat diakses tanpa akun ChatGPT.

## Persiapan

1. Pasang Docker Engine dan plugin Docker Compose.
2. Clone repo ini lalu masuk ke direktorinya.
3. Salin `.env.selfhost.example` menjadi `.env`.
4. Buat hash password:

   ```bash
   docker run --rm caddy:2.10-alpine caddy hash-password --plaintext 'PASSWORD_ANDA'
   ```

5. Masukkan hasil hash ke `ADMIN_PASSWORD_HASH` di `.env`. Tanda `$` tidak
   perlu diubah bila nilai ditulis langsung di berkas `.env`.
6. Untuk domain, arahkan DNS ke VPS lalu isi `SITE_ADDRESS=form.example.com`.
   Untuk akses awal lewat IP, biarkan `SITE_ADDRESS=:80`.

## Jalankan

```bash
docker compose up -d --build
docker compose ps
```

Data formulir dan media tersimpan di volume `forma_data`. Backup volume ini
sebelum update besar.

## Update

```bash
git pull --ff-only
docker compose up -d --build
```

## Pemeriksaan

```bash
docker compose ps
docker compose logs --tail=100 app caddy
```

Jangan membuka port aplikasi internal 3000 ke internet; akses publik harus
melalui Caddy pada port 80/443.
