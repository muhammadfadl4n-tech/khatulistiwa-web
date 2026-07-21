#!/usr/bin/env python3
"""Fix 5W+1H: remove duplication, make it clean"""
import json, re
from pathlib import Path

DATA_FILE = Path("/root/beritakalbar/data/berita.json")
d = json.loads(DATA_FILE.read_text(encoding="utf-8"))
berita = d["berita"]

# Rebuild clean 5W+1H for each article
for art in berita:
    judul = art.get("judul", "")
    sumber = art.get("sumber", "")
    tanggal = art.get("tanggal", "")
    kategori = art.get("kategori", "")
    url = art.get("url", "")
    
    # Clean judul
    jd = re.sub(r'[\U0001F300-\U0010FFFF\u2600-\u27BF\uFE0F]', '', judul).strip()
    
    # Extract original raw content (from current isi, but strip the 5W+1H header if it exists)
    isi_current = art.get("isi", "")
    
    # Try to extract the article text AFTER the 5W+1H section
    raw_text = ""
    
    # Check if there's text after the last separator
    parts = re.split(r'\n[━─]{10,}\n', isi_current)
    if len(parts) >= 2:
        # Take everything after the last separator
        after_last_sep = parts[-1].strip()
        # Remove "## Related", "## Kebijakan", etc
        after_last_sep = re.sub(r'^#+\s+\w+.*$', '', after_last_sep, flags=re.MULTILINE)
        after_last_sep = re.sub(r'\[\[.*?\]\]', '', after_last_sep)
        after_last_sep = re.sub(r'\|[^\n]+\|', '', after_last_sep)  # tables
        after_last_sep = re.sub(r'\s+', ' ', after_last_sep).strip()
        if len(after_last_sep) > 50:
            raw_text = after_last_sep
    
    # If no raw text found (first run), use the full isi
    if not raw_text:
        raw_text = isi_current
    
    # Clean raw text of emojis and markdown artifacts
    raw_text = re.sub(r'[\U0001F300-\U0010FFFF\u2600-\u27BF\uFE0F]', '', raw_text)
    raw_text = re.sub(r'\*\*📰.*?\)\s*[—–-]\s*', '', raw_text)  # source prefix
    raw_text = re.sub(r'\*\*', '', raw_text)
    raw_text = re.sub(r'#+\s+', '', raw_text)
    raw_text = re.sub(r'\n{3,}', '\n\n', raw_text)
    raw_text = re.sub(r'\s+', ' ', raw_text).strip()
    # Remove leftover 5W+1H artifacts (from previous runs)
    raw_text = re.sub(r'(?:What|Who|When|Where|Why|How)\s*\((?:Apa|Siapa|Kapan|Dimana|Mengapa|Bagaimana)\):\s*', '', raw_text)
    raw_text = re.sub(r'[━─]{5,}', '', raw_text)
    raw_text = re.sub(r'Source:\s*\S+', '', raw_text)
    raw_text = re.sub(r'^\s*▪️\s*\*\*.*?\*\*\s*', '', raw_text, flags=re.MULTILINE)
    raw_text = re.sub(r'\s{2,}', ' ', raw_text).strip()
    
    # Truncate if too long
    if len(raw_text) > 2000:
        raw_text = raw_text[:1997] + '...'
    
    # === Build clean 5W+1H ===
    
    # Who
    who_parts = []
    org_patterns = re.findall(r'(?:Pertamina Patra Niaga|Pertamina|ESDM|Satpol PP|Diskumdag|DPRD|DPR RI|Pemkot\s+\w+|Pemprov\s+\w+|Polda\s+\w+)', isi_current + judul)
    for o in org_patterns:
        if o not in who_parts:
            who_parts.append(o)
    if not who_parts:
        who_parts.append("Instansi terkait")
    
    # People
    people = re.findall(r'(?:Menteri|Gubernur|Walikota|Bupati|Direktur|Ketua|Kepala)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', isi_current + judul)
    for p in people:
        p = p.strip()
        if p not in who_parts:
            who_parts.append(p)
    
    # Common names
    for name in ['Bahlil Lahadalia', 'Bahlil', 'Satarudin', 'Ibrahim', 'Simon Aloysius Mantiri',
                 'Laode Sulaeman', 'Yuliot Tanjung', 'Prabowo Subianto', 'Ahmad Sudiyantoro']:
        if name.lower() in (isi_current + judul).lower() and name not in who_parts:
            who_parts.append(name)
    
    who = ", ".join(who_parts[:4]) if who_parts else "Instansi terkait"
    
    # Where
    where_parts = []
    for loc in ['Pontianak', 'Singkawang', 'Sambas', 'Pemangkat', 'Mempawah', 'Kubu Raya',
                'Sintang', 'Sanggau', 'Kapuas Hulu', 'Ketapang', 'Bengkayang', 'Landak',
                'Melawi', 'Sekadau', 'Kayong Utara', 'Pangkalan Bun']:
        if loc.lower() in (isi_current + judul).lower():
            where_parts.append(loc)
    where = ", ".join(where_parts[:3]) + ", Kalimantan Barat" if where_parts else "Kalimantan Barat"
    
    # Why
    txt_lower = (isi_current + judul).lower()
    if any(k in txt_lower for k in ['langka', 'kelangkaan']):
        why_cat = "Kelangkaan pasokan"
    elif any(k in txt_lower for k in ['naik', 'kenaikan', 'harga', 'meroket']):
        why_cat = "Kenaikan harga energi"
    elif any(k in txt_lower for k in ['ledakan', 'kebakaran', 'luka']):
        why_cat = "Insiden keamanan"
    elif any(k in txt_lower for k in ['larang', 'penertiban', 'satpol', 'tindak']):
        why_cat = "Penertiban penggunaan"
    elif any(k in txt_lower for k in ['tambah', 'pasokan', 'stok']):
        why_cat = "Penambahan pasokan"
    elif any(k in txt_lower for k in ['subsidi', 'anggaran']):
        why_cat = "Efisiensi subsidi"
    elif any(k in txt_lower for k in ['penyelewengan', 'oplos', 'bongkar']):
        why_cat = "Pengungkapan penyelewengan"
    elif any(k in txt_lower for k in ['cng', 'konversi', 'merah putih']):
        why_cat = "Konversi energi"
    else:
        why_cat = "Kebijakan distribusi"
    why = f"{why_cat} LPG 3 kg di Kalimantan Barat"
    
    # How
    if who_parts:
        how = f"Melalui {', '.join(who_parts[:2])}"
    else:
        how = "Melalui kebijakan pemerintah daerah dan pusat"
    if url and url.startswith('http'):
        how += f". Informasi dari {sumber or 'media'}"

    # === BUILD FINAL CONTENT ===
    lines = []
    lines.append(f"**{jd}**")
    lines.append(f"📅 {tanggal} | 📍 {where} | 🏷️ {kategori}")
    lines.append("")
    
    # 5W+1H as bullet points (clean, no duplication)
    lines.append(f"▪️ **What:** {jd}")
    lines.append(f"▪️ **Who:** {who}")
    lines.append(f"▪️ **When:** {tanggal}")
    lines.append(f"▪️ **Where:** {where}")
    lines.append(f"▪️ **Why:** {why}")
    lines.append(f"▪️ **How:** {how}")
    
    if sumber:
        lines.append(f"▪️ **Source:** {sumber}")
    
    # Append article text ONLY if substantial (not just the same as judul)
    if raw_text and len(raw_text) > 60:
        # Check if raw_text is mostly different from judul
        similarity = len(set(raw_text.lower().split()) & set(jd.lower().split())) / max(len(set(raw_text.lower().split())), 1)
        if similarity < 0.8:
            lines.append("")
            lines.append("—" * 30)
            lines.append("")
            lines.append(raw_text)
    
    art["isi"] = "\n".join(lines)

# Regenerate highlights from the new clean isi
def get_highlight(isi, judul):
    m = re.search(r'▪️\s*\*\*What:\*\*\s*(.*?)$', isi, re.MULTILINE)
    if m:
        h = m.group(1).strip()
        if len(h) > 250: h = h[:247] + '...'
        return h
    jd = re.sub(r'[\U0001F300-\U0010FFFF\u2600-\u27BF\uFE0F]', '', judul).strip()
    return jd[:150]

for art in berita:
    art["highlight"] = get_highlight(art.get("isi",""), art.get("judul",""))

# Sort & save
berita.sort(key=lambda x: (x["tanggal"] if x["tanggal"] >= '2025' else '2025-01-01', x["id"]), reverse=True)
for i, b in enumerate(berita, 1):
    b["id"] = i

DATA_FILE.write_text(json.dumps({"berita": berita}, ensure_ascii=False, indent=2), encoding="utf-8")

# Show first 3 for verification
for b in berita[:3]:
    print(b['isi'])
    print("=" * 50)
    print(f"LENGTH: {len(b['isi'])} chars")
    print()
print(f"✅ {len(berita)} berita — 5W+1H clean, no duplication")
