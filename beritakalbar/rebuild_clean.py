#!/usr/bin/env python3
"""Clean rebuild: 5W+1H only, no duplicate raw text"""
import json, re
from pathlib import Path
from urllib.parse import urlparse

DATA_FILE = Path("/root/beritakalbar/data/berita.json")
d = json.loads(DATA_FILE.read_text(encoding="utf-8"))
berita = d["berita"]

# First pass: strip ALL text after any separator/detail section
for art in berita:
    isi = art.get("isi", "")
    # Remove everything after the last 5W+1H section (after the separator line)
    # Keep only the 5W+1H bullet points (before any separator)
    parts = re.split(r'\n[—–━]{5,}\n', isi)
    if parts:
        isi = parts[0].strip()
    
    # Also clean up the header
    isi = re.sub(r'[\U0001F300-\U0010FFFF\u2600-\u27BF\uFE0F]', '', isi)
    isi = re.sub(r'\*\*(.+?)\*\*', r'\1', isi)  # remove ** but keep text
    
    art["isi"] = isi

# Second pass: rebuild clean 5W+1H
for art in berita:
    judul = re.sub(r'[\U0001F300-\U0010FFFF\u2600-\u27BF\uFE0F]', '', art.get("judul", "")).strip()
    sumber = art.get("sumber", "")
    tanggal = art.get("tanggal", "")
    kategori = art.get("kategori", "")
    old_isi = art.get("isi", "")
    url = art.get("url", "")
    
    # Extract Who/Where from old isi + judul
    text_pool = old_isi + " " + judul
    
    who_list = []
    for org in ['Pertamina Patra Niaga', 'Pertamina', 'Satpol PP', 'Diskumdag', 'DPRD', 'DPR',
                'Pemkot Pontianak', 'Pemprov Kalbar', 'Polda Kalbar', 'Kementerian ESDM',
                'Pemkot Singkawang', 'Pemkot']:
        if org.lower() in text_pool.lower():
            who_list.append(org)
    
    for name in ['Bahlil Lahadalia', 'Satarudin', 'Ibrahim', 'Simon Aloysius Mantiri',
                 'Laode Sulaeman', 'Yuliot Tanjung', 'Ahmad Sudiyantoro', 'Ririn']:
        if name.lower() in text_pool.lower():
            who_list.append(name)
    
    who = ", ".join(who_list[:4]) if who_list else "Instansi terkait"
    
    where_list = []
    for loc in ['Pontianak', 'Singkawang', 'Sambas', 'Pemangkat', 'Mempawah', 'Kubu Raya',
                'Sintang', 'Sanggau', 'Kapuas Hulu', 'Ketapang', 'Bengkayang', 'Landak',
                'Melawi', 'Sekadau', 'Kayong Utara', 'Pangkalan Bun', 'Kalbar']:
        if loc.lower() in text_pool.lower():
            where_list.append(loc)
    where = ", ".join([w for w in where_list[:3] if w != 'Kalbar']) + ", Kalimantan Barat" if any(w != 'Kalbar' for w in where_list[:3]) else "Kalimantan Barat"
    
    # Why
    txt_low = text_pool.lower()
    if 'langka' in txt_low: why = "Kelangkaan pasokan LPG 3 kg"
    elif 'naik' in txt_low or 'kenaikan' in txt_low or 'meroket' in txt_low: why = "Kenaikan harga LPG 3 kg"
    elif 'ledakan' in txt_low: why = "Insiden keamanan tabung gas"
    elif 'larang' in txt_low or 'satpol' in txt_low or 'tindak' in txt_low: why = "Penertiban penggunaan LPG bersubsidi"
    elif 'tambah' in txt_low or 'pasokan' in txt_low: why = "Penambahan pasokan LPG 3 kg"
    elif 'subsidi' in txt_low: why = "Efisiensi subsidi LPG"
    elif 'penyelewengan' in txt_low: why = "Pengungkapan penyelewengan distribusi"
    elif 'cng' in txt_low or 'konversi' in txt_low: why = "Konversi ke energi alternatif CNG"
    else: why = "Perkembangan distribusi LPG 3 kg"
    
    # How
    if who_list:
        how = f"Melalui kebijakan dan tindakan dari {who_list[0]}"
    else:
        how = "Melalui kebijakan pemerintah daerah"
    if sumber:
        how += f" (sumber: {sumber})"
    
    # Build clean output
    lines = [
        f"{judul}",
        f"📅 {tanggal} | 📍 {where} | 🏷️ {kategori}",
        "",
        f"▪️ **What:** {judul[:200]}",
        f"▪️ **Who:** {who}",
        f"▪️ **When:** {tanggal}",
        f"▪️ **Where:** {where}",
        f"▪️ **Why:** {why}",
        f"▪️ **How:** {how}",
    ]
    
    art["isi"] = "\n".join(lines)

# Highlights from What field
for art in berita:
    m = re.search(r'▪️\s*\*\*What:\*\*\s*(.*)', art.get("isi", ""))
    art["highlight"] = m.group(1).strip()[:250] if m else re.sub(r'[\U0001F300-\U0010FFFF\u2600-\u27BF\uFE0F]', '', art.get("judul","")).strip()[:150]

# Sort & save
berita.sort(key=lambda x: (x["tanggal"] if x["tanggal"] >= '2025' else '2025-01-01', x["id"]), reverse=True)
for i, b in enumerate(berita, 1):
    b["id"] = i

DATA_FILE.write_text(json.dumps({"berita": berita}, ensure_ascii=False, indent=2), encoding="utf-8")

# Verify
for b in berita[:3]:
    print(b['isi'])
    print(f"→ highlight: {b['highlight'][:80]}")
    print("=" * 50)

print(f"\n✅ {len(berita)} berita — 5W+1H clean, no duplication")
