#!/usr/bin/env python3
"""
Rebuild 5W+1H with DETAILED content - fetch full article text and structure properly
"""
import json, re, subprocess, time
from pathlib import Path

DATA_FILE = Path("/root/beritakalbar/data/berita.json")
STATIC_IMAGES = Path("/root/beritakalbar/static/images")
d = json.loads(DATA_FILE.read_text(encoding="utf-8"))
berita = d["berita"]

def fetch_article_full(url):
    """Get full article text using curl with better extraction"""
    if not url or 'example.com' in url or not url.startswith('http'):
        return None
    try:
        r = subprocess.run(
            ["curl", "-sL", "--max-time", "15",
             "-H", "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
             "-H", "Accept: text/html,application/xhtml+xml",
             "-H", "Accept-Language: id-ID,id;q=0.9",
             url],
            capture_output=True, text=True, timeout=20
        )
        html = r.stdout
        
        # Extract <p> tags from article/main/content area
        # First try article or main tag
        text = ""
        for tag in ['article', 'main', '[class*=content]', '[class*=article]', '[class*=detail]', '[id*=content]', '[id*=article]']:
            # Get all p tags
            ps = re.findall(rf'<p[^>]*>(.*?)</p>', html, re.S | re.I)
            if len(ps) > 3:
                valid_ps = []
                for p in ps:
                    # Clean HTML tags inside p
                    clean = re.sub(r'<[^>]+>', '', p)
                    clean = re.sub(r'\s+', ' ', clean).strip()
                    if len(clean) > 40:
                        valid_ps.append(clean)
                if len(valid_ps) >= 2:
                    text = '\n\n'.join(valid_ps)
                    break
        
        if not text or len(text) < 200:
            # Fallback: get all text from body
            body = re.search(r'<body[^>]*>(.*?)</body>', html, re.S | re.I)
            if body:
                body_text = re.sub(r'<script[^>]*>.*?</script>', '', body.group(1), flags=re.S | re.I)
                body_text = re.sub(r'<style[^>]*>.*?</style>', '', body_text, flags=re.S | re.I)
                body_text = re.sub(r'<nav[^>]*>.*?</nav>', '', body_text, flags=re.S | re.I)
                body_text = re.sub(r'<footer[^>]*>.*?</footer>', '', body_text, flags=re.S | re.I)
                body_text = re.sub(r'<[^>]+>', '\n', body_text)
                lines = [l.strip() for l in body_text.split('\n') if l.strip() and len(l.strip()) > 30]
                text = '\n'.join(lines[:20])
        
        if text:
            # Clean
            text = re.sub(r'[\U0001F300-\U0010FFFF\u2600-\u27BF\uFE0F]', '', text)
            text = re.sub(r'&nbsp;', ' ', text)
            text = re.sub(r'&amp;', '&', text)
            text = re.sub(r'&lt;', '<', text)
            text = re.sub(r'&gt;', '>', text)
            text = re.sub(r'&quot;', '"', text)
            text = re.sub(r'&#039;', "'", text)
            text = re.sub(r'\n{3,}', '\n\n', text)
            text = re.sub(r'[ \t]{2,}', ' ', text)
            text = text.strip()
            if len(text) > 3000:
                text = text[:3000]
            return text
    except:
        pass
    return None

# Process articles
for i, art in enumerate(berita):
    judul = re.sub(r'[\U0001F300-\U0010FFFF\u2600-\u27BF\uFE0F]', '', art.get("judul", "")).strip()
    sumber = art.get("sumber", "")
    tanggal = art.get("tanggal", "")
    kategori = art.get("kategori", "")
    url = art.get("url", "")
    old_isi = art.get("isi", "")
    
    # Get detailed article text
    detail_text = None
    if url.startswith('http') and 'example.com' not in url and 'pontianak.tribunnews.com/' not in url:
        print(f"[{i+1}/{len(berita)}] 📰 Fetching {judul[:50]}...")
        detail_text = fetch_article_full(url)
        if detail_text:
            print(f"      ✅ {len(detail_text)} chars")
        else:
            print(f"      ⚠️ No content")
        time.sleep(1.5)
    elif 'pontianak.tribunnews.com/' in url:
        print(f"[{i+1}/{len(berita)}] ⏭️ Skip tribunnews (paywall): {judul[:50]}")
    
    # Build text_pool from old isi + detail
    text_pool = (detail_text or "") + " " + old_isi + " " + judul + " " + (sumber or "")
    
    # === Build detailed 5W+1H ===
    
    # What - detailed description (not just title)
    what = judul
    if detail_text:
        # First 2 sentences of article as What
        sents = re.split(r'(?<=[.!?])\s+', detail_text)
        what_parts = []
        for s in sents[:3]:
            s = s.strip()
            if len(s) > 30 and s not in what_parts:
                what_parts.append(s)
        if what_parts:
            what = " ".join(what_parts[:2])
            if len(what) > 300: what = what[:297] + '...'
    
    # Who - detailed
    who_list = []
    # People
    for pattern in [
        (r'(?:Menteri|Gubernur|Walikota|Bupati|Direktur|Ketua|Kepala)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', ''),
        (r'(?:Menteri|Gubernur|Walikota|Bupati|Direktur|Ketua|Kepala)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)(?:\s+\((?:\w+)\))?', ''),
    ]:
        for m in re.finditer(pattern[0], text_pool):
            p = m.group(1).strip()
            if p not in who_list and len(p) > 3:
                who_list.append(p)
    
    for name in ['Bahlil Lahadalia', 'Satarudin', 'Ibrahim', 'Simon Aloysius Mantiri',
                 'Laode Sulaeman', 'Yuliot Tanjung', 'Prabowo Subianto', 'Ahmad Sudiyantoro',
                 'Ririn', 'Edi', 'Achmad']:
        if name.lower() in text_pool.lower() and name not in who_list:
            who_list.append(name)
    
    # Organizations
    for org in ['Pertamina Patra Niaga', 'Pertamina', 'Satpol PP', 'Diskumdag', 'DPRD', 'DPR',
                'Kementerian ESDM', 'Polda Kalbar', 'Pemkot Pontianak', 'Pemprov Kalbar',
                'Pemkot Singkawang', 'PT Pertamina']:
        if org.lower() in text_pool.lower() and org not in who_list:
            who_list.append(org)
    
    who = ", ".join(who_list[:5]) if who_list else "Pemerintah dan instansi terkait"
    
    # When - detailed
    when = tanggal if tanggal and tanggal >= '2025' else "Tidak disebutkan"
    
    # Where - detailed
    where_list = []
    for loc in ['Pontianak', 'Singkawang', 'Sambas', 'Pemangkat', 'Mempawah', 'Kubu Raya',
                'Sintang', 'Sanggau', 'Kapuas Hulu', 'Ketapang', 'Bengkayang', 'Landak',
                'Melawi', 'Sekadau', 'Kayong Utara', 'Pangkalan Bun']:
        if loc.lower() in text_pool.lower():
            where_list.append(loc)
    where = ", ".join(where_list[:4]) + ", Kalimantan Barat" if where_list else "Kalimantan Barat"
    if 'nasional' in text_pool.lower() or 'jakarta' in text_pool.lower():
        where += " / Nasional"
    
    # Why - specific
    txt_low = text_pool.lower()
    why_detail = ""
    if 'langka' in txt_low or 'kelangkaan' in txt_low:
        why_detail = "Kelangkaan pasokan LPG 3 kg yang menyebabkan masyarakat kesulitan mendapatkan gas bersubsidi"
    elif 'ledakan' in txt_low:
        why_detail = "Insiden ledakan tabung gas LPG yang mengakibatkan korban luka dan kerusakan"
    elif 'larang' in txt_low or 'tindak' in txt_low or 'satpol' in txt_low:
        why_detail = "Penertiban penggunaan LPG 3 kg bersubsidi agar tepat sasaran kepada masyarakat yang berhak"
    elif 'harga' in txt_low and ('naik' in txt_low or 'meroket' in txt_low):
        why_detail = "Kenaikan harga LPG di tingkat konsumen yang memberatkan masyarakat"
    elif 'tambah' in txt_low or 'pasokan' in txt_low or 'stok' in txt_low:
        why_detail = "Penambahan pasokan LPG 3 kg untuk menjaga stabilitas distribusi dan harga"
    elif 'penyelewengan' in txt_low or 'oplos' in txt_low:
        why_detail = "Pengungkapan praktik penyelewengan distribusi LPG bersubsidi oleh oknum tidak bertanggung jawab"
    elif 'subsidi' in txt_low or 'anggaran' in txt_low:
        why_detail = "Efisiensi dan ketepatan sasaran subsidi energi LPG dari pemerintah"
    elif 'cng' in txt_low or 'konversi' in txt_low or 'merah putih' in txt_low:
        why_detail = "Upaya pemerintah mengurangi ketergantungan impor LPG melalui program konversi ke CNG"
    elif 'impor' in txt_low:
        why_detail = "Ketergantungan Indonesia pada impor LPG yang mencapai jutaan ton per tahun"
    else:
        why_detail = f"Perkembangan kebijakan dan distribusi LPG 3 kg di {where}"
    
    # How - specific
    how_parts = []
    if who_list:
        primary = who_list[0].split(',')[0].strip()
        how_parts.append(f"Melalui langkah dan kebijakan yang diambil oleh {primary}")
    if sumber:
        how_parts.append(f"Informasi dilaporkan oleh {sumber}")
    if detail_text:
        # Find action verbs
        actions = re.findall(r'(?:melakukan|melaksanakan|menindak|mengamankan|menambah|memastikan|menindaklanjuti|memberikan|mengeluarkan|menerbitkan|mengawasi)\s+[\w\s]+?\.', text_pool, re.I)
        if actions:
            action_text = actions[0].strip()
            if len(action_text) > 30:
                how_parts.append(f"Tindakan: {action_text[:200]}")
    how = ". ".join(how_parts) if how_parts else "Melalui kebijakan pemerintah daerah dan pusat"
    
    # === ASSEMBLE FINAL OUTPUT ===
    lines = []
    lines.append(f"**{judul}**")
    lines.append(f"📅 {when} | 📍 {where} | 🏷️ {kategori}")
    lines.append("")
    lines.append(f"▪️ **What:** {what}")
    lines.append(f"▪️ **Who:** {who}")
    lines.append(f"▪️ **When:** {when}")
    lines.append(f"▪️ **Where:** {where}")
    lines.append(f"▪️ **Why:** {why_detail}.")
    lines.append(f"▪️ **How:** {how}")
    if url and url.startswith('http') and 'example.com' not in url:
        lines.append(f"▪️ **Source:** {url}")
    
    # Append full article text if we got it
    if detail_text and len(detail_text) > 200:
        lines.append("")
        lines.append("─── Detail ───")
        lines.append("")
        lines.append(detail_text)
    
    art["isi"] = "\n".join(lines)

# Highlights from What field
for art in berita:
    m = re.search(r'▪️\s*\*\*What:\*\*\s*(.*?)$', art.get("isi", ""), re.MULTILINE)
    if m and m.group(1).strip():
        art["highlight"] = m.group(1).strip()[:250]
    else:
        art["highlight"] = re.sub(r'[\U0001F300-\U0010FFFF\u2600-\u27BF\uFE0F]', '', art.get("judul","")).strip()[:150]

# Sort & save
berita.sort(key=lambda x: (x["tanggal"] if x["tanggal"] >= '2025' else '2025-01-01', x["id"]), reverse=True)
for i, b in enumerate(berita, 1):
    b["id"] = i

DATA_FILE.write_text(json.dumps({"berita": berita}, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"\n✅ {len(berita)} berita dengan 5W+1H detail!")
for b in berita[:2]:
    print("\n" + "="*60)
    print(b['isi'])
    print(f"\n💡 Highlight: {b['highlight'][:100]}")
