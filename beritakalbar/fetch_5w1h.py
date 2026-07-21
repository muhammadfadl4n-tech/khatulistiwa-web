#!/usr/bin/env python3
"""
Fetch full article content (5W+1H) from real URLs for Berita Kalbar
"""
import json, re, subprocess, time, urllib.parse
from pathlib import Path

DATA_FILE = Path("/root/beritakalbar/data/berita.json")
d = json.loads(DATA_FILE.read_text(encoding="utf-8"))
berita = d["berita"]

def fetch_article_text(url):
    """Fetch full article content from URL using curl + readability extraction"""
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
        
        # Remove script/style tags
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.S | re.I)
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.S | re.I)
        html = re.sub(r'<nav[^>]*>.*?</nav>', '', html, flags=re.S | re.I)
        html = re.sub(r'<footer[^>]*>.*?</footer>', '', html, flags=re.S | re.I)
        
        # Extract text from <article> or <main> or <div class="content">
        text = ""
        
        # Try article tag
        m = re.search(r'<article[^>]*>(.*?)</article>', html, re.S | re.I)
        if m: text = m.group(1)
        
        # Try main tag
        if not text or len(text) < 500:
            m = re.search(r'<main[^>]*>(.*?)</main>', html, re.S | re.I)
            if m: text = m.group(1)
        
        # Try common content divs
        if not text or len(text) < 500:
            for cls in ['content', 'article', 'post-content', 'entry-content', 'berita', 'detail', 'read', 'main-content', 'article-detail']:
                m = re.search(rf'<div[^>]*(?:class|id)=["\'][^"\']*{cls}[^"\']*["\'][^>]*>(.*?)</div>', html, re.S | re.I)
                if m and len(m.group(1)) > 500:
                    text = m.group(1)
                    break
        
        # Fallback: get body text
        if not text or len(text) < 500:
            m = re.search(r'<body[^>]*>(.*?)</body>', html, re.S | re.I)
            if m: text = m.group(1)
        
        if not text or len(text) < 200:
            return None
        
        # Strip HTML tags
        text = re.sub(r'<[^>]+>', '\n', text)
        
        # Unescape HTML entities
        text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&#039;', "'")
        
        # Clean
        text = re.sub(r'[\U0001F300-\U0010FFFF\u2600-\u27BF\uFE0F]', '', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[ \t]{2,}', ' ', text)
        text = re.sub(r'^\s+', '', text, flags=re.MULTILINE)
        
        lines = [l.strip() for l in text.split('\n') if l.strip() and len(l.strip()) > 20]
        text = '\n'.join(lines)
        
        if len(text) > 5000:
            text = text[:5000]
        
        return text.strip()
    except Exception as e:
        print(f"      ⚠️ Error: {e}")
        return None

def build_5w1h(judul, isi, sumber, tanggal, url):
    """Structure content into 5W+1H format"""
    if isi and len(isi) > 500:
        return isi  # Already has enough content
    
    # Generate from what we have
    clean_isi = re.sub(r'[\U0001F300-\U0010FFFF\u2600-\u27BF\uFE0F]', '', isi).strip()
    clean_judul = re.sub(r'[\U0001F300-\U0010FFFF\u2600-\u27BF\uFE0F]', '', judul).strip()
    
    lines = []
    lines.append(f"What: {clean_judul}")
    
    # Try to extract Who
    who_match = re.search(r'(?:Menteri|Gubernur|Walikota|Bupati|Direktur|Ketua|Kepala|Presiden|DPR|DPRD|Pertamina|Satpol PP|Pemkot|Pemprov|Diskumdag)\s+[^,.]*', clean_isi + " " + clean_judul)
    if who_match:
        lines.append(f"Who: {who_match.group(0).strip()}")
    elif "pertamina" in (clean_isi + clean_judul).lower():
        lines.append("Who: PT Pertamina / Pertamina Patra Niaga")
    else:
        lines.append("Who: Pemerintah / Instansi terkait")
    
    # When
    if tanggal and tanggal >= '2025':
        lines.append(f"When: {tanggal}")
    
    # Where
    for wilayah in ['Pontianak', 'Kalbar', 'Kalimantan Barat', 'Singkawang', 'Sambas', 'Mempawah', 'Kubu Raya', 'Sintang', 'Sanggau', 'Kapuas Hulu', 'Ketapang', 'Bengkayang', 'Landak', 'Melawi', 'Sekadau', 'Kayong Utara']:
        if wilayah.lower() in (clean_isi + " " + clean_judul).lower():
            lines.append(f"Where: {wilayah}, Kalimantan Barat")
            break
    else:
        lines.append("Where: Kalimantan Barat")
    
    # Why
    why_keywords = {
        'kelangkaan': 'Kelangkaan pasokan',
        'kenaikan': 'Kenaikan harga',
        'ledakan': 'Insiden keamanan',
        'pengawasan': 'Pengawasan distribusi',
        'subsidi': 'Efisiensi subsidi',
        'tepat sasaran': 'Ketepatan sasaran subsidi',
        'larang': 'Pelarangan penggunaan',
        'tambah': 'Penambahan pasokan',
        'aman': 'Keamanan pasokan',
        'naik': 'Penyesuaian harga',
    }
    found_why = False
    for kw, reason in why_keywords.items():
        if kw in (clean_isi + " " + clean_judul).lower():
            lines.append(f"Why: {reason}")
            found_why = True
            break
    if not found_why:
        lines.append("Why: Memastikan distribusi LPG tepat sasaran")
    
    # How
    lines.append(f"How: Melalui kebijakan dan pengawasan oleh {sumber or 'instansi terkait'}")
    
    # Add original content
    if clean_isi and len(clean_isi) > 30:
        lines.append(f"\nDetail: {clean_isi}")
    
    return "\n".join(lines)

# Process articles with real URLs - fetch full content
for i, art in enumerate(berita):
    url = art.get("url", "")
    if not url.startswith('http') or 'example.com' in url:
        continue
    if url == 'https://pontianak.tribunnews.com/':
        continue  # generic homepage, skip
    
    # Skip if already has good content (500+ chars)
    if len(art.get("isi", "")) > 500:
        continue
    
    print(f"[{i+1}/{len(berita)}] 📰 {art['judul'][:50]}...")
    full_text = fetch_article_text(url)
    
    if full_text and len(full_text) > 200:
        art["isi"] = full_text
        print(f"      ✅ {len(full_text)} chars fetched")
    else:
        print(f"      ⚠️ Only {len(full_text or '')} chars - using 5W+1H fallback")
        art["isi"] = build_5w1h(art["judul"], art.get("isi",""), art.get("sumber",""), art.get("tanggal",""), url)
    
    time.sleep(1.5)

# Process articles WITHOUT real URLs - generate 5W+1H
for art in berita:
    url = art.get("url", "")
    if url.startswith('http') and 'example.com' not in url:
        continue  # already processed above
    
    if len(art.get("isi", "")) > 300:
        continue  # already has decent content
    
    art["isi"] = build_5w1h(art["judul"], art.get("isi",""), art.get("sumber",""), art.get("tanggal",""), url)

# Re-generate highlights based on new isi
def extract_what(isi, title):
    text = isi
    text = re.sub(r'\|[^\n]+\|', '', text)
    text = re.sub(r'[\U0001F300-\U0010FFFF\u2600-\u27BF\uFE0F]', '', text)
    text = re.sub(r'\*\*', '', text)
    text = re.sub(r'\n---+\n', '\n', text)
    text = re.sub(r'^#+\s+.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s+', ' ', text).strip()
    sentences = re.split(r'(?<=[.!?])\s+', text)
    for s in sentences:
        s = s.strip()
        if len(s) >= 25 and not re.match(r'^(sementara|adapun|selain|sedangkan|menurut|dilansir)', s.lower()):
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

stats = {}
for b in berita:
    l = len(b.get("isi", ""))
    if l >= 1000: cat = "1000+"
    elif l >= 500: cat = "500+"
    elif l >= 200: cat = "200+"
    else: cat = "<200"
    stats[cat] = stats.get(cat, 0) + 1

print(f"\n✅ Done! {len(berita)} berita")
print(f"📊 Content length: {json.dumps(stats)}")
for b in berita[:3]:
    print(f"\n📰 {b['judul'][:55]}")
    print(f"   {b['isi'][:200]}...")
