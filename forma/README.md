# Forma — self-hosted form builder

Forma adalah pembuat formulir bergaya Google Forms dengan dashboard untuk
membuat banyak formulir, menerbitkan tautan publik, melihat respons, dan
menerima upload gambar. Setiap formulir dapat memilih **Compress otomatis**
atau **Simpan kualitas asli**.

Repo ini mendukung dua target:

- **VPS/self-hosted:** Node.js, SQLite, volume media lokal, Docker Compose,
  dan Caddy. Dashboard dilindungi login; formulir dan pengiriman respons tetap
  publik.
- **OpenAI Sites:** vinext, Cloudflare D1/R2, dan Sign in with ChatGPT.

## Deploy ke VPS

Ikuti [SELF_HOSTING.md](SELF_HOSTING.md). Ringkasnya:

```bash
cp .env.selfhost.example .env
# Isi ADMIN_PASSWORD_HASH dan SITE_ADDRESS di .env
docker compose up -d --build
```

Untuk menyerahkan deployment ke Hermes Agent, minta Hermes clone repo ini lalu
mengikuti [HERMES_TASK.md](HERMES_TASK.md).

## Pengembangan

Prasyarat: Node.js 22.13 atau lebih baru.

```bash
npm install
npm run dev
```

Validasi kedua target:

```bash
npm run build
npm run build:selfhost
```

Data self-hosted disimpan pada volume Docker `forma_data`. Jangan menghapus
volume tersebut saat memperbarui container.
