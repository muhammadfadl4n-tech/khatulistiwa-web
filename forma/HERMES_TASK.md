# Tugas Hermes: deploy Forma

Tujuan: jalankan Forma pada VPS secara aman dari repo ini.

1. Inventarisasi OS, Docker, port 80/443, firewall, reverse proxy, dan layanan
   yang sudah aktif. Jangan menimpa layanan yang ada.
2. Jika port 80/443 dipakai, laporkan konflik dan gunakan reverse proxy yang
   sudah ada atau minta keputusan pengguna.
3. Pasang Docker hanya bila belum tersedia dan setelah memastikan tidak ada
   konflik dengan stack produksi lain.
4. Salin `.env.selfhost.example` ke `.env`, buat password admin yang kuat,
   simpan hash Caddy di `ADMIN_PASSWORD_HASH`, dan jangan tampilkan secret pada
   log atau chat.
5. Jika domain belum tersedia, gunakan `SITE_ADDRESS=:80`. Jika domain sudah
   mengarah ke VPS, isi domain agar Caddy mengaktifkan HTTPS otomatis.
6. Jalankan `docker compose up -d --build`.
7. Verifikasi dashboard meminta login, `/f/<id>` dapat dibuka publik, respons
   tersimpan, upload gambar bekerja, dan data tetap ada setelah restart.
8. Laporkan URL, status container, lokasi backup, dan setiap risiko yang tersisa.

Jangan menghapus container, volume, database, konfigurasi proxy, atau firewall
yang sudah ada tanpa persetujuan pengguna.
