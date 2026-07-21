#!/usr/bin/env python3
"""
Structure ALL article content into proper 5W+1H format.
For articles with real content fetched, wrap it in 5W+1H.
For articles without enough content, build 5W+1H from available data.
"""
import json, re
from pathlib import Path

DATA_FILE = Path("/root/beritakalbar/data/berita.json")
d = json.loads(DATA_FILE.read_text(encoding="utf-8"))
berita = d["berita"]

def build_5w1h(art):
    """Build proper 5W+1H for a single article"""
    judul = art.get("judul", "")
    isi_raw = art.get("isi", "")
    sumber = art.get("sumber", "")
    tanggal = art.get("tanggal", "")
    url = art.get("url", "")
    kategori = art.get("kategori", "")
    
    # Clean
    text = re.sub(r'[\U0001F300-\U0010FFFF\u2600-\u27BF\uFE0F]', '', isi_raw)
    text = re.sub(r'\*\*', '', text)
    text = re.sub(r'\|[^\n]+\|', '', text)  # remove markdown tables
    text = re.sub(r'\n---+\n', '\n', text)
    text = re.sub(r'^#+\s+.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s+', ' ', text).strip()
    
    title_clean = re.sub(r'[\U0001F300-\U0010FFFF\u2600-\u27BF\uFE0F]', '', judul).strip()
    
    # Parse source and date from text if available
    date_text = tanggal if tanggal and tanggal >= '2025' else ""
    source_text = sumber or ""
    
    # Find key people/orgs
    people = []
    orgs = []
    
    # Check for organizations
    for org in ['Pertamina', 'Pertamina Patra Niaga', 'ESDM', 'DPRD', 'DPR', 'Satpol PP', 
                'Pemkot Pontianak', 'Pemprov Kalbar', 'Diskumdag', 'Kemendag', 'Kemenkeu',
                'Polda Kalbar', 'Kementerian ESDM', 'BUMN']:
        if org.lower() in (text + " " + title_clean).lower():
            orgs.append(org)
    
    # Check for people
    person_patterns = re.findall(r'(?:Menteri|Gubernur|Walikota|Bupati|Direktur|Ketua|Kepala)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', text + " " + title_clean)
    for p in person_patterns:
        people.append(p.strip())
    
    if not people:
        # Check common names
        for name in ['Bahlil', 'Bahlil Lahadalia', 'Satarudin', 'Ibrahim', 'Simon Aloysius',
                     'Laode Sulaeman', 'Yuliot Tanjung', 'Prabowo', 'Ahmad Sudiyantoro',
                     'Ririn']:
            if name.lower() in (text + " " + title_clean).lower():
                people.append(name)
    
    # Determine What (from the title/content)
    what = title_clean
    
    # Determine Who
    if people:
        who = ", ".join(people[:3])
        if orgs:
            who += f" ({', '.join(orgs[:3])})"
    elif orgs:
        who = ", ".join(orgs[:3])
    else:
        who = "Pemerintah dan instansi terkait"
    
    # Determine When
    when = date_text if date_text else "Tidak disebutkan"
    
    # Determine Where
    locations = []
    for loc in ['Pontianak', 'Singkawang', 'Sambas', 'Mempawah', 'Kubu Raya', 'Sintang',
                'Sanggau', 'Kapuas Hulu', 'Ketapang', 'Bengkayang', 'Landak', 'Melawi',
                'Sekadau', 'Kayong Utara', 'Pemangkat', 'Pangkalan Bun']:
        if loc.lower() in (text + " " + title_clean).lower():
            locations.append(loc)
    
    if locations:
        where = f"{', '.join(locations[:3])}, Kalimantan Barat"
    else:
        where = "Kalimantan Barat"
    
    # Determine Why
    if any(k in (text + " " + title_clean).lower() for k in ['langka', 'kelangkaan', 'sulit']):
        why = "Kelangkaan pasokan LPG 3 kg di masyarakat"
    elif any(k in (text + " " + title_clean).lower() for k in ['naik', 'kenaikan', 'harga', 'meroket']):
        why = "Kenaikan harga dan fluktuasi pasar energi"
    elif any(k in (text + " " + title_clean).lower() for k in ['ledakan', 'kebakaran', 'luka']):
        why = "Insiden keamanan tabung gas"
    elif any(k in (text + " " + title_clean).lower() for k in ['larang', 'penertiban', 'satpol', 'tindak']):
        why = "Penertiban penggunaan LPG bersubsidi agar tepat sasaran"
    elif any(k in (text + " " + title_clean).lower() for k in ['tambah', 'tambahan', 'pasokan']):
        why = "Menjaga ketersediaan pasokan LPG untuk masyarakat"
    elif any(k in (text + " " + title_clean).lower() for k in ['subsidi', 'anggaran', 'dana']):
        why = "Efisiensi dan ketepatan sasaran subsidi energi"
    elif any(k in (text + " " + title_clean).lower() for k in ['penyelewengan', 'oplos', 'bongkar']):
        why = "Pengungkapan praktik penyelewengan distribusi LPG"
    elif any(k in (text + " " + title_clean).lower() for k in ['cng', 'konversi', 'merah putih']):
        why = "Diversifikasi energi untuk mengurangi impor LPG"
    else:
        why = "Perkembangan kebijakan dan distribusi LPG di Kalbar"
    
    # Determine How
    how_parts = []
    if orgs:
        how_parts.append(f"Melalui kebijakan dan tindakan dari {' dan '.join(orgs[:2])}")
    else:
        how_parts.append("Melalui kebijakan pemerintah dan pengawasan distribusi")
    
    if url and url.startswith('http') and 'example.com' not in url:
        how_parts.append(f"Informasi bersumber dari {sumber or 'media terkait'}")
    
    how = ". ".join(how_parts)
    
    # Build full content with 5W+1H structure
    lines = []
    lines.append(f"📰 **{title_clean}**")
    lines.append(f"📅 {when} | 📍 {where} | 🏷️ {kategori}")
    lines.append("")
    lines.append("━" * 40)
    lines.append("")
    lines.append(f"**What (Apa):** {what}")
    lines.append(f"**Who (Siapa):** {who}")
    lines.append(f"**When (Kapan):** {when}")
    lines.append(f"**Where (Dimana):** {where}")
    lines.append(f"**Why (Mengapa):** {why}")
    lines.append(f"**How (Bagaimana):** {how}")
    
    if sumber:
        lines.append(f"**Source:** {sumber}")
    
    lines.append("")
    lines.append("━" * 40)
    lines.append("")
    
    # Add full article text
    if text and len(text) > 100:
        # If we have good content, use it
        if len(text) < 400:
            # Try to expand from original isi before cleaning
            raw = re.sub(r'[\U0001F300-\U0010FFFF\u2600-\u27BF\uFE0F]', '', isi_raw)
            raw = re.sub(r'\*\*📰.*?\)\s*—\s*', '', raw)  # remove source prefix
            if len(raw) > len(text):
                text = re.sub(r'\s+', ' ', raw).strip()
        
        lines.append(text)
    
    return "\n".join(lines)

# Process all articles
for art in berita:
    art["isi"] = build_5w1h(art)

# Regenerate highlights
def extract_what(isi, title):
    """Extract 'What' from 5W+1H structured content"""
    # Try to extract directly from **What (Apa):** line
    m = re.search(r'\*\*What \(Apa\):\*\*\s*(.*?)(?:\n|$)', isi)
    if m:
        text = m.group(1).strip()
        if text and len(text) > 10:
            if len(text) > 250:
                text = text[:247] + '...'
            return text
    
    # Fallback: clean full text and find first sentence
    text = isi
    text = re.sub(r'[\U0001F300-\U0010FFFF\u2600-\u27BF\uFE0F]', '', text)
    text = re.sub(r'\*\*', '', text)
    text = re.sub(r'\|[^\n]+\|', '', text)
    text = re.sub(r'\n[━─]+\n', '\n', text)
    text = re.sub(r'^#+\s+.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s+', ' ', text).strip()
    
    sentences = re.split(r'(?<=[.!?])\s+', text)
    for s in sentences:
        s = s.strip()
        if len(s) >= 20 and not re.match(r'^(sementara|adapun|selain|sedangkan|menurut|dilansir|apa|siapa|kapan|dimana|mengapa|bagaimana)', s.lower()):
            s = re.sub(r'^[,;]\s*', '', s).strip()
            if len(s) > 250: s = s[:247] + '...'
            return s
    
    t = re.sub(r'[\U0001F300-\U0010FFFF\u2600-\u27BF\uFE0F]', '', title).strip()
    return t[:150]

for art in berita:
    art["highlight"] = extract_what(art.get("isi",""), art.get("judul",""))

# Sort & save
berita.sort(key=lambda x: (x["tanggal"] if x["tanggal"] >= '2025' else '2025-01-01', x["id"]), reverse=True)
for i, b in enumerate(berita, 1):
    b["id"] = i
DATA_FILE.write_text(json.dumps({"berita": berita}, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"✅ {len(berita)} berita dengan format 5W+1H")
for b in berita[:3]:
    print(f"\n📰 {b['judul'][:55]}")
    print(f"   {b['isi'][:300]}")
    print("   ...")
