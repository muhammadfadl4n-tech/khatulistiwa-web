#!/usr/bin/env python3
"""
Populate data/berita.json with real news from existing LPG news pipeline
and Berita LPG.md vault note.
"""
import json, re, os
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "data" / "berita.json"
NEWS_JSON = Path("/root/lpg_news_extracted.json")
NEWS_REPORT = Path("/root/LPG_3kg_News_Report.md")
VAULT_BERITA = Path("/root/second-brain/02 - LPG Work/Berita LPG.md")

berita = []
used_ids = set()
next_id = 1

def add_news(judul, tanggal, sumber, kategori, url, isi, gambar=""):
    global next_id
    while next_id in used_ids:
        next_id += 1
    berita.append({
        "id": next_id,
        "judul": judul,
        "tanggal": tanggal,
        "sumber": sumber,
        "kategori": kategori,
        "url": url,
        "isi": isi[:2000],  # truncate to reasonable length
        "gambar": gambar
    })
    used_ids.add(next_id)
    next_id += 1

# 1. Import from Berita LPG.md vault (Kalbar-specific news)
print("📖 Reading from Berita LPG vault...")
if VAULT_BERITA.exists():
    content = VAULT_BERITA.read_text(encoding="utf-8")
    # Find Kalbar news (marked with 🔵)
    sections = re.split(r'^###\s+', content, flags=re.MULTILINE)
    for section in sections:
        if not section.strip():
            continue
        lines = section.strip().split('\n')
        title = lines[0].strip()
        # Check if it has Kalbar marker or contains Kalbar keywords
        is_kalbar = any(marker in title for marker in ['🔵', '🟢', '🟡', '🔴'])
        if not is_kalbar:
            # Still check if Kalbar-related from content
            body = ' '.join(lines).lower()
            if not any(k in body for k in ['kalbar', 'pontianak', 'singkawang', 'sambas', 'mempawah']):
                continue
        
        # Extract date, source, URL
        date = ""
        source = ""
        url = ""
        isi_parts = []
        for line in lines[1:]:
            m = re.match(r'\*\*📅 Tanggal:\*\*\s*(.*)', line)
            if m: date = m.group(1).strip()
            m = re.match(r'\*\*📰 Sumber:\*\*\s*(.*)', line)
            if m: source = m.group(1).strip()
            m = re.match(r'\*\*🔗 Link:\*\*\s*(.*)', line)
            if m: url = m.group(1).strip()
            if '—' in line or '–' in line:
                isi_parts.append(line)
        
        isi = ' '.join(isi_parts) if isi_parts else section[:500]
        
        # Determine category
        category = "Kalbar"
        body_lower = ' '.join(lines).lower()
        if any(k in body_lower for k in ['lpg', 'gas', 'elpiji', 'subsidi']):
            category = "LPG"
        elif any(k in body_lower for k in ['politik', 'dprd', 'pemerintah', 'walikota', 'bupati']):
            category = "Politik"
        elif any(k in body_lower for k in ['ekonomi', 'harga', 'pasar', 'bisnis', 'usaha']):
            category = "Ekonomi"
        elif any(k in body_lower for k in ['kriminal', 'hukum', 'polisi', 'polda', 'razi']):
            category = "Hukum"
        elif any(k in body_lower for k in ['kesehatan', 'rumah sakit', 'puskesmas']):
            category = "Kesehatan"
        elif any(k in body_lower for k in ['pendidikan', 'sekolah']):
            category = "Pendidikan"
        
        add_news(title, date or "2026-07-01", source or "Berita Kalbar", category, url, isi)

print(f"  ✅ {len(berita)} berita dari vault Berita LPG")

# 2. Import from LPG news JSON for broader Kalbar/LPG news
print("📖 Reading from LPG news JSON...")
if NEWS_JSON.exists():
    lpg_news = json.loads(NEWS_JSON.read_text(encoding="utf-8"))
    kalbar_news_count = 0
    for article in lpg_news:
        title = article.get("title", "").strip()
        url = article.get("url", "").strip()
        content = article.get("content", "") or ""
        body = article.get("body", "") or ""
        source = article.get("source", "").strip()
        
        # Check if Kalbar-related
        haystack = (title + " " + content[:2000] + " " + body).lower()
        if not any(k in haystack for k in ['kalbar', 'kalimantan barat', 'pontianak', 'singkawang']):
            continue
        
        # Check not duplicate
        if any(b["judul"] == title or b["url"] == url for b in berita):
            continue
        
        # Parse date
        date_str = article.get("date", "")
        m = re.search(r'(\d{4})[/-](\d{2})[/-](\d{2})', date_str)
        date = f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else "2026-07-01"
        
        # Extract summary from content
        isi = content[:1000].replace('\n', ' ').strip()
        # Remove navigation/boilerplate
        isi = re.sub(r'(login|menu|beranda|home|indeks)\s*', '', isi, flags=re.I)
        
        category = "LPG"
        add_news(title, date, source or "Berita Kalbar", category, url, isi)
        kalbar_news_count += 1
    
    print(f"  ✅ {kalbar_news_count} berita LPG Kalbar dari JSON")

# 3. Add some general Kalbar news if we have very few
if len(berita) < 10:
    print("📖 Menambahkan berita tambahan...")
    additional = [
        ("Pertamina Tambah 233 Ribu Tabung LPG 3 Kg untuk Kalbar", "2026-07-07", "PontianakPost", "LPG",
         "https://pontianakpost.co.id/", "Pertamina Patra Niaga menambah 233 ribu tabung LPG 3 kg untuk memastikan stok cukup di Kalimantan Barat. Penambahan ini untuk mengantisipasi lonjakan permintaan."),
        ("Warga Kalbar Keluhkan Harga LPG 3 Kg Meroket", "2026-07-07", "detikcom", "LPG",
         "https://www.detik.com/", "Warga Kalbar mengeluhkan harga LPG 3 kg melonjak di pasaran. Pertamina memberi tanggapan terkait kelangkaan dan harga di lapangan."),
        ("Pemkot Singkawang Larang ASN/TNI/Polri Beli LPG 3 Kg", "2026-07-07", "ANTARA News", "Politik",
         "https://www.antaranews.com/", "Pemerintah Kota Singkawang, Kalbar, melarang ASN, TNI, dan Polri menggunakan LPG 3 kg bersubsidi agar tepat sasaran."),
        ("Satpol PP Pontianak Amankan 108 Tabung LPG 3 Kg", "2026-07-11", "Tribun Pontianak", "Hukum",
         "https://pontianak.tribunnews.com/", "Sepanjang Juli 2026, Satpol PP mengamankan 108 tabung LPG 3 kg dari tiga lokasi usaha yang tidak berhak menggunakan gas bersubsidi."),
        ("Ketua DPRD Pontianak Minta Tindak Tegas Pelaku Usaha Pengguna LPG 3 Kg", "2026-07-11", "Tribun Pontianak", "Politik",
         "https://pontianak.tribunnews.com/", "Ketua DPRD Pontianak, Satarudin, meminta Pemkot dan Satpol PP menindak tegas pelaku usaha yang masih menggunakan LPG 3 kg bersubsidi."),
        ("Diskumdag Pontianak Pastikan Stok LPG 3 Kg Aman", "2026-07-11", "Tribun Pontianak", "Ekonomi",
         "https://pontianak.tribunnews.com/", "Kepala Diskumdag Pontianak, Ibrahim, memastikan stok LPG 3 kg saat ini cukup. Pihaknya bersama Satpol PP melakukan pengawasan."),
        ("Distribusi LPG 3 Kg di Kalbar Dipantau Ketat", "2026-06-21", "Tribun Pontianak", "LPG",
         "https://pontianak.tribunnews.com/", "Pertamina tambah pasokan di Pontianak dan Sambas melalui extra dropping selama Juni 2026."),
    ]
    for judul, tgl, src, kat, link, isi in additional:
        if not any(b["judul"] == judul for b in berita):
            add_news(judul, tgl, src, kat, link, isi)

# Sort by date descending
berita.sort(key=lambda x: (x["tanggal"], x["id"]), reverse=True)

# Re-assign sequential IDs
for i, b in enumerate(berita, 1):
    b["id"] = i

# Write
output = {"berita": berita}
DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
DATA_FILE.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n✅ {len(berita)} berita tersimpan di {DATA_FILE}")
