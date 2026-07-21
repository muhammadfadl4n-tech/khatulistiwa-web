# 📋 Planning: Aplikasi Laporan Pembongkaran BBM SPBU

> **Form referensi:** Google Form — Laporan Pembongkaran dan Penerimaan BBM SPBU
> **Lingkungan:** Windows 10, Python 3.11, RTX 4070 Ti

---

## 1. 🎯 Ringkasan Kebutuhan

Aplikasi web untuk menggantikan Google Form manual dengan sistem terintegrasi:

| Modul | Fungsi |
|-------|--------|
| **User Management** | 3 role: SPBU, Pertamina, Administrator |
| **Form Input** | Input data pembongkaran BBM + upload foto |
| **Dashboard** | Visualisasi real-time data per SPBU/kabupaten |
| **Data View** | Tabel/rekap historis, filter, export |

---

## 2. 🏗️ Tech Stack

| Layer | Pilihan | Alasan |
|-------|---------|--------|
| **Backend** | **Flask** (Python) | Ringan, familiar, cocok buat internal tool. Bisa pakai portal port 5555. |
| **Database** | **SQLite** `bbm_reports.db` | Udah dipake (expenses.db, homework_for_life.db). Gak perlu install DB server. |
| **Frontend** | **HTML + CSS + Vanilla JS** | Static served from Flask. Bootstrap 5 / Tailwind CDN. No build step. |
| **Maps (opsional)** | Leaflet.js | Udah dipake di dashboard_agen.html |
| **File Storage** | Local folder `uploads/` | Foto disimpan lokal, path di DB |
| **Auth** | **Flask-Login** + JWT | Session-based atau token untuk API |

### Kenapa Flask?
- ✅ Udah ada Python 3.11 + uv
- ✅ Ringan, no build step
- ✅ Bisa serve HTML langsung
- ✅ Bisa jalan bareng portal LPG existing di port beda

---

## 3. 🗄️ Database Schema

### 3.1 — Users (`users`)

| Kolom | Tipe | Keterangan |
|-------|------|------------|
| id | INTEGER PK | Auto |
| username | TEXT UNIQUE | Login |
| password_hash | TEXT | bcrypt |
| nama_lengkap | TEXT | Nama asli |
| role | TEXT | `spbu`, `pertamina`, `administrator` |
| id_spbu | INT FK | Null utk Pertamina & Administrator |
| email | TEXT | |
| is_active | BOOL | |
| created_at | DATETIME | |

### 3.2 — SPBU (`spbu`)

| Kolom | Tipe | Keterangan |
|-------|------|------------|
| id | INTEGER PK | |
| nama_pt | TEXT | Nama PT/CV |
| nomor_spbu | TEXT UNIQUE | ID SPBU |
| kota | TEXT | Kabupaten/kota |
| alamat | TEXT | |
| lat | REAL | GPS latitude |
| lng | REAL | GPS longitude |
| created_at | DATETIME | |

### 3.3 — Laporan Pembongkaran (`laporan`)

| Kolom | Tipe | Keterangan |
|-------|------|------------|
| id | INTEGER PK | |
| id_spbu | INT FK | |
| id_user | INT FK | Yang ngisi |
| tanggal | DATE | |
| jenis_bbm | TEXT | JSON array: ["Biosolar","Pertalite",...] |
| status | TEXT | `draft`, `submitted`, `verified` |
| catatan | TEXT | Opsional |
| created_at | DATETIME | |
| updated_at | DATETIME | |

### 3.4 — Uploads/Foto (`uploads`)

| Kolom | Tipe | Keterangan |
|-------|------|------------|
| id | INTEGER PK | |
| id_laporan | INT FK | |
| kategori | TEXT | `pembongkaran`, `spp`, `dipping`, `atg` |
| filename | TEXT | Nama file asli |
| path | TEXT | Path di server |
| created_at | DATETIME | |

---

## 4. 👥 User Management

### 4.1 — Role & Hak Akses

| Role | Hak Akses |
|------|-----------|
| **SPBU** 🏪 | Input laporan + upload foto untuk SPBU-nya sendiri. Edit/hapus laporan milik sendiri. Lihat riwayat SPBU-nya sendiri. |
| **Pertamina** 🏢 | Lihat SEMUA laporan, dashboard, map, grafik. Verifikasi laporan. Export data. **Tidak bisa** input laporan. |
| **Administrator** ⚙️ | FULL CONTROL — manage user (CRUD), manage SPBU, manage semua laporan. Config sistem. |

### 4.2 — Fitur Auth
- Login/logout dengan session
- Halaman login dengan role-based redirect
- Profile page (ganti password)
- Session timeout

### 4.3 — Halaman Manajemen User (khusus Administrator)
- CRUD user
- Assign role (SPBU / Pertamina / Administrator)
- Assign SPBU ke akun SPBU
- Aktivasi/non-aktifkan akun
- Reset password user

---

## 5. 📝 Halaman Form Input

**URL:** `/laporan/baru` atau `/laporan/<id>/edit`

### Form Fields (cocok dengan Google Form):

```
┌─────────────────────────────────────────┐
│  LAPORAN PEMBONGKARAN BBM SPBU         │
├─────────────────────────────────────────┤
│  Nama PT/CV SPBU    : [_____________]   │  ← Auto-fill kalo login sbg admin SPBU
│  Nomor SPBU         : [_____________]   │  ← Auto-fill
│  Kota / Kabupaten   : ○ Pontianak       │  ← Dropdown/radio 14 kabupaten
│                        ○ Singkawang     │
│                        ○ ...            │
│  Tanggal Pembongkaran: [_____/____/____]│
│                                          │
│  Jenis Produk BBM:                       │
│  ☐ Biosolar  ☐ Pertalite  ☐ Pertamax   │  ← Checkbox
│  ☐ Pertamax Turbo  ☐ Dexlite  ☐ Dex    │
│                                          │
│  📸 Foto Pembongkaran BBM    [Upload]   │  ← Max 5 files, PDF/image
│  📄 Foto SPP                  [Upload]   │
│  📏 Foto Dipping              [Upload]   │
│  📊 Foto ATG                  [Upload]   │
│                                          │
│  [💾 Simpan Draft]  [📤 Submit]          │
└─────────────────────────────────────────┘
```

### Fitur:
- **Draft** — bisa disimpan dulu, dilanjut nanti
- **Auto-fill** — data SPBU otomatis dari database kalo user terasosiasi
- **Validasi client-side** — required fields, file size, format
- **Progress bar** upload
- **GPS capture** — option ambil lokasi via browser geolocation API
- **Auto-compress gambar** — foto langsung dikompres pas upload (lihat section 12)

---

## 6. 📊 Dashboard

**URL:** `/dashboard`

### 6.1 — Kartu Statistik (Top Row)
```
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ Total    │ │ Laporan  │ │ SPBU     │ │ Foto     │
│ Laporan  │ │ Bulan Ini│ │ Aktif    │ │ Terupload│
│   1,247  │ │    142   │ │    86    │ │  3,891   │
└──────────┘ └──────────┘ └──────────┘ └──────────┘
```

### 6.2 — Grafik
- **Line chart** — tren laporan per hari (7/30 hari)
- **Bar chart** — laporan per kabupaten/kota
- **Pie chart** — distribusi jenis BBM
- **Map** — Leaflet map dengan marker SPBU (warna beda berdasarkan status submit hari ini)

### 6.3 — Tabel Ringkasan
| SPBU | Kota | Laporan Bulan Ini | Terakhir Lapor | Status |
|------|------|-------------------|----------------|--------|
| SPBU A | Pontianak | 12 | 2026-07-01 | ✅ |
| SPBU B | Singkawang | 8 | 2026-06-28 | ⚠️ |

### 6.4 — Filter
- By kabupaten
- By tanggal range
- By status
- By jenis BBM

---

## 7. 📋 Halaman Data / Riwayat

**URL:** `/laporan`

### 7.1 — Tabel Data dengan fitur:
- **Search** — cari berdasarkan nama SPBU, nomor SPBU, kota
- **Filter** — by tanggal, kabupaten, jenis BBM, status
- **Sort** — klik header kolom
- **Pagination**
- **Export** — CSV / Excel / PDF

### 7.2 — Detail Laporan (modal atau halaman terpisah)
- Semua field terbaca
- Gallery foto (lightbox)
- Status verifikasi
- Tombol aksi (edit, hapus, verifikasi tergantung role)

### 7.3 — View per SPBU
**URL:** `/spbu/<id>`
- Profil SPBU
- Riwayat semua laporan
- Statistik khusus SPBU itu

---

## 8. 📁 Struktur Folder Aplikasi

```
C:\Ai Station\Hermes\bbm-report-app\
├── app.py                    # Entry point Flask
├── config.py                 # Konfigurasi
├── requirements.txt          # Dependencies
├── bbm_reports.db            # SQLite DB (auto-generated)
│
├── models/
│   ├── __init__.py
│   ├── user.py               # User model
│   ├── spbu.py               # SPBU model
│   ├── laporan.py            # Laporan model
│   └── upload.py             # Upload model
│
├── routes/
│   ├── __init__.py
│   ├── auth.py               # Login/logout/register
│   ├── laporan.py            # CRUD laporan
│   ├── spbu.py               # Data SPBU
│   ├── dashboard.py          # Dashboard API
│   └── upload.py             # File upload handler
│
├── templates/
│   ├── base.html             # Layout base (navbar, sidebar)
│   ├── login.html
│   ├── dashboard.html        # Dashboard page
│   ├── laporan_form.html     # Form input
│   ├── laporan_list.html     # Tabel riwayat
│   ├── laporan_detail.html   # Detail laporan
│   ├── spbu_detail.html      # Profil SPBU
│   └── admin/
│       ├── users.html        # Manajemen user
│       └── spbu.html         # Manajemen SPBU
│
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   ├── dashboard.js
│   │   ├── laporan.js
│   │   └── utils.js
│   └── img/
│
├── uploads/                  # Foto-foto tersimpan
│   └── [tahun]/
│       └── [bulan]/
│           └── [laporan_id]/
│               ├── pembongkaran_1.jpg
│               ├── spp_1.jpg
│               ├── dipping_1.jpg
│               └── atg_1.jpg
│
└── utils/
    ├── helpers.py            # Fungsi bantu
    └── decorators.py         # Decorators (role_required, dll)
```

---

## 9. 🧩 Halaman & Route Map

| Method | Route | Fungsi | Role |
|--------|-------|--------|------|
| GET | `/login` | Halaman login | - |
| POST | `/login` | Proses login | - |
| GET | `/logout` | Logout | All |
| | | | |
| GET | `/` | Redirect ke dashboard | All |
| GET | `/dashboard` | Dashboard utama | All |
| GET | `/api/dashboard/stats` | Data statistik API | All |
| GET | `/api/dashboard/chart` | Data grafik API | All |
| | | | |
| GET | `/laporan` | Tabel riwayat laporan | All |
| GET | `/laporan/baru` | Form laporan baru | SPBU |
| POST | `/laporan/baru` | Simpan laporan baru | SPBU |
| GET | `/laporan/<id>` | Detail laporan | All |
| GET | `/laporan/<id>/edit` | Edit laporan | SPBU (milik sendiri) |
| POST | `/laporan/<id>/edit` | Update laporan | SPBU (milik sendiri) |
| POST | `/laporan/<id>/verifikasi` | Verifikasi laporan | Pertamina |
| POST | `/laporan/<id>/hapus` | Hapus laporan | SPBU (milik sendiri), Administrator |
| GET | `/api/laporan` | Data laporan JSON | All |
| GET | `/api/laporan/export` | Export CSV/Excel | Pertamina, Administrator |
| | | | |
| POST | `/upload` | Upload foto + auto-compress | SPBU |
| GET | `/uploads/<path>` | Serve foto | All |
| | | | |
| GET | `/spbu` | Daftar SPBU | Pertamina, Administrator |
| POST | `/spbu/baru` | Tambah SPBU | Administrator |
| GET | `/spbu/<id>` | Detail SPBU | All |
| POST | `/spbu/<id>/edit` | Update SPBU | Administrator |
| | | | |
| GET | `/admin/users` | Manajemen user | Administrator |
| POST | `/admin/users/baru` | Tambah user | Administrator |
| POST | `/admin/users/<id>/edit` | Edit user | Administrator |
| POST | `/admin/users/<id>/toggle` | Aktif/nonaktif | Administrator |
| GET | `/admin/spbu` | Manajemen SPBU | Administrator |
| POST | `/admin/spbu/baru` | Tambah SPBU | Administrator |
| POST | `/admin/spbu/<id>/edit` | Edit SPBU | Administrator |

---

## 10. 📦 Dependencies (Python)

```
flask==3.1.*
flask-login==0.6.*
flask-sqlalchemy==3.1.*
werkzeug==3.1.*           # password hashing
pillow==11.*              # validasi & resize foto
python-dotenv==1.*        # config
```

Install via: `uv pip install -r requirements.txt`

---

## 11. 🖼️ Fitur Auto-Compress Image

### Kenapa?
Foto dari HP (12-48MP) bisa 3-10MB per gambar. 1 laporan = 4-20 foto. Dalam sebulan bisa puluhan GB. Auto-compress turunin ukuran **70-90%** tanpa quality loss yang berarti.

### Cara Kerja

```
User upload → PIL/Pillow buka gambar → Resize (max 1920px) → 
Compress JPEG quality 80% → Simpan di uploads/
```

### Detail Teknis

| Parameter | Value | Keterangan |
|-----------|-------|------------|
| Format output | **JPEG** | Universal, kompresi efisien |
| Max dimensi | **1920px** (longest side) | Cukup untuk dokumentasi, gak kegedean |
| Quality | **80%** | Balance size vs quality |
| Max file size | **< 500KB** per foto | Target setelah kompres |
| EXIF data | **Stripped** | Hapus metadata GPS/lokasi (kecuali butuh) |
| Thumbnail | **320px** | Untuk preview cepat di gallery |

### Flow Upload

```
┌─────────┐    ┌──────────┐    ┌──────────┐    ┌─────────┐
│ Request │ → │ Validate │ → │ Compress │ → │ Save to │
│ Upload  │    │ Type &   │    │ Resize + │    │ disk +  │
│         │    │ Size     │    │ Optimize │    │ DB      │
└─────────┘    └──────────┘    └──────────┘    └─────────┘
                    │
                    ↓ Error (format salah, >20MB)
              Return error message
```

### Kode (gambaran)

```python
from PIL import Image
import os

MAX_DIM = 1920
QUALITY = 80

def compress_image(input_path, output_path):
    img = Image.open(input_path)
    
    # Resize kalo melebihi max dimension
    if max(img.width, img.height) > MAX_DIM:
        ratio = MAX_DIM / max(img.width, img.height)
        new_size = (int(img.width * ratio), int(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)
    
    # Convert ke RGB kalo PNG (transparan → putih)
    if img.mode in ('RGBA', 'P'):
        bg = Image.new('RGB', img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = bg
    
    # Simpan dengan kompresi
    img.save(output_path, 'JPEG', quality=QUALITY, optimize=True)
    
    return os.path.getsize(output_path)
```

### Keuntungan
- 📦 **Hemat storage** — 500KB/foto vs 5MB/foto = 10x lebih kecil
- ⚡ **Load lebih cepat** — di dashboard & gallery
- 📱 **Mobile friendly** — bandwidth kecil
- 🖨️ **Tetap jelas** — 1920px di quality 80% masih bagus buat dokumen

### Tambahan di Dependencies
```
pillow==11.*              # (already included for image ops)
```

---

## 12. 🗓️ Tahapan Development

### Phase 1 — Foundation ⚡ (1-2 hari)
- [x] Inisialisasi project + struktur folder
- [ ] Setup Flask + SQLite DB
- [ ] Model User, SPBU, Laporan, Upload
- [ ] Login/logout + session management
- [ ] Seed data: 14 kabupaten Kalbar

### Phase 2 — Form Input + Upload 📝 (1-2 hari)
- [ ] Halaman form (cocok Google Form)
- [ ] File upload (foto, validasi tipe & ukuran)
- [ ] **Auto-compress image** (PIL: resize 1920px + quality 80%)
- [ ] Simpan draft + submit workflow
- [ ] Autofill data SPBU dari user login

### Phase 3 — Data View 📋 (1 hari)
- [ ] Tabel riwayat laporan
- [ ] Search, filter, sort, pagination
- [ ] Detail laporan (gallery foto)
- [ ] Export CSV/Excel

### Phase 4 — Dashboard 📊 (1 hari)
- [ ] Kartu statistik
- [ ] Grafik (Chart.js — line, bar, pie)
- [ ] Map SPBU (Leaflet, reuse dari dashboard_agen.html)
- [ ] Filter dashboard

### Phase 5 — User Management 👥 (1 hari)
- [ ] CRUD user (admin page)
- [ ] Role-based menu & route access
- [ ] CRUD SPBU

### Phase 6 — Polish ✨ (1 hari)
- [ ] Responsive (mobile friendly)
- [ ] Loading states, error handling
- [ ] Notifikasi flash messages
- [ ] Dark mode opsional

**Total estimasi: ~8-11 hari kerja**

---

## 13. 🚀 Cara Jalanin

```bash
cd /c/Ai\ Station/Hermes/bbm-report-app
uv pip install -r requirements.txt
python app.py
# → running di http://localhost:5560 (atau port lain selain 5555)
```

Atau bisa digabung dengan portal existing (port 5555) sebagai blueprint Flask.

---

## 14. Catatan Tambahan
- Backup DB otomatis tiap hari via cron Hermes
- Integrasi dengan Telegram untuk notifikasi laporan masuk
- Bisa dipasang di portal LPG existing port 5555 sebagai sub-app

---

**Dibuat:** 1 Juli 2026  
**Status:** Planning — siap eksekusi
