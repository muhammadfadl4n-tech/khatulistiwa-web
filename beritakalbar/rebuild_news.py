#!/usr/bin/env python3
"""
Rebuild berita.json from scratch with proper dates and real images from article URLs.
"""
import json, re, subprocess, time, urllib.parse
from pathlib import Path

BASE_DIR = Path("/root/beritakalbar")
DATA_FILE = BASE_DIR / "data" / "berita.json"
STATIC_IMAGES = BASE_DIR / "static" / "images"
STATIC_IMAGES.mkdir(parents=True, exist_ok=True)

MONTH_MAP = {
    'jan': '01', 'januari': '01', 'feb': '02', 'februari': '02',
    'mar': '03', 'maret': '03', 'apr': '04', 'april': '04',
    'mei': '05', 'jun': '06', 'juni': '06', 'jul': '07', 'juli': '07',
    'agu': '08', 'agustus': '08', 'sep': '09', 'september': '09',
    'okt': '10', 'oktober': '10', 'nov': '11', 'november': '11',
    'des': '12', 'desember': '12'
}

def parse_inline_date(text):
    """Extract date from text like '(19 Des 2025)' or '19 Desember 2025'"""
    m = re.search(r'(\d{1,2})\s+(Jan|Feb|Mar|Apr|Mei|Jun|Jul|Agu|Sep|Okt|Nov|Des|Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|Oktober|November|Desember)\s+(\d{4})', text, re.I)
    if m:
        dd = m.group(1).zfill(2)
        mm = MONTH_MAP.get(m.group(2).lower(), '01')
        return f"{m.group(3)}-{mm}-{dd}"
    return None

def search_article_url(title, sumber):
    """Search DuckDuckGo for the article URL"""
    # Clean title: remove emoji, trim
    clean = re.sub(r'[\U0001F300-\U0010FFFF\u2600-\u27BF\uFE0F]', '', title).strip()
    clean = clean.replace('"', '').replace("'", '')
    
    # Add source site filter if known
    site_map = {
        'detik': 'site:detik.com',
        'detikcom': 'site:detik.com',
        'kompas': 'site:kompas.com',
        'cnbc': 'site:cnbcindonesia.com',
        'antaranews': 'site:antaranews.com',
        'antara': 'site:antaranews.com',
        'tribun': 'site:tribunnews.com',
        'liputan6': 'site:liputan6.com',
        'bisnis': 'site:bisnis.com',
        'kontan': 'site:kontan.co.id',
        'viva': 'site:viva.co.id',
        'pontianakpost': 'site:pontianakpost.co.id',
    }
    site_filter = ''
    for key, site in site_map.items():
        if key in sumber.lower():
            site_filter = f' {site}'
            break
    
    if not site_filter:
        site_filter = ' (site:detik.com OR site:kompas.com OR site:cnbcindonesia.com OR site:antaranews.com OR site:tribunnews.com OR site:bisnis.com)'
    
    query = urllib.parse.quote(f'"{clean}"{site_filter}')
    try:
        # Try Google
        result = subprocess.run(
            ["curl", "-sL", "--max-time", "10",
             "-H", "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
             f"https://www.google.com/search?q={query}"],
            capture_output=True, text=True, timeout=12
        )
        html = result.stdout
        urls = re.findall(r'href="https?://(?:www\.)?((?:detik|kompas|cnbcindonesia|antaranews|tribunnews|bisnis|kontan|viva|pontianakpost|liputan6)[^"]+)"', html)
        if urls:
            return 'https://www.' + urls[0]
    except:
        pass
    return None

def fetch_og_image(article_url):
    """Fetch og:image from article URL and download it"""
    if not article_url or not article_url.startswith('http'):
        return ""
    
    safe_name = re.sub(r'[^a-z0-9]', '_', re.sub(r'https?://', '', article_url)[:80].lower()) + '.jpg'
    img_path = STATIC_IMAGES / safe_name
    if img_path.exists():
        return f"/static/images/{safe_name}"
    
    try:
        result = subprocess.run(
            ["curl", "-sL", "--max-time", "10",
             "-H", "User-Agent: Mozilla/5.0 (Linux; Android 13; SM-S908E)",
             article_url],
            capture_output=True, text=True, timeout=15
        )
        html = result.stdout[:30000]
        
        # Find og:image
        img_url = None
        for pat in [
            r'<meta\s+[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']',
            r'<meta\s+[^>]*content=["\']([^"\']+)["\'][^>]*property=["\']og:image["\']',
            r'<meta\s+[^>]*name=["\']twitter:image["\'][^>]*content=["\']([^"\']+)["\']',
        ]:
            m = re.search(pat, html, re.I)
            if m:
                img_url = m.group(1)
                break
        
        if not img_url:
            # Try first reasonable img
            imgs = re.findall(r'<img[^>]+src=["\']([^"\']+\.(?:jpg|jpeg|png|webp))["\']', html, re.I)
            for img in imgs[:5]:
                if any(kw in img.lower() for kw in ['featured', 'cover', 'hero', 'main', 'article', 'content', 'lpg', 'gas', 'energi', 'pertamina']):
                    img_url = img
                    break
            if not img_url and imgs:
                img_url = imgs[2] if len(imgs) > 2 else imgs[0]  # skip first (usually logo)
        
        if img_url:
            if img_url.startswith('//'):
                img_url = 'https:' + img_url
            elif img_url.startswith('/'):
                parsed = urllib.parse.urlparse(article_url)
                img_url = f"{parsed.scheme}://{parsed.netloc}{img_url}"
            
            dl = subprocess.run(
                ["curl", "-sL", "-o", str(img_path), "-w", "%{http_code}",
                 "--max-time", "15",
                 "-H", "User-Agent: Mozilla/5.0",
                 img_url],
                capture_output=True, text=True, timeout=20
            )
            if dl.stdout.strip() == "200" and img_path.stat().st_size > 500:
                return f"/static/images/{safe_name}"
            else:
                img_path.unlink(missing_ok=True)
    except:
        pass
    return ""

# ========== MAIN ==========

# Read vault
vault_file = Path("/root/second-brain/02 - LPG Work/Berita LPG.md")
vault_content = vault_file.read_text(encoding="utf-8")

berita = []
seen_urls = set()

# Parse vault: each ### section is an article
sections = re.split(r'^### ', vault_content, flags=re.MULTILINE)

for section in sections:
    if not section.strip():
        continue
    
    lines = section.strip().split('\n')
    title = lines[0].strip()
    
    # Skip non-article sections
    if title.startswith('#') or len(title) < 5:
        continue
    
    # Extract fields
    date = ""
    sumber = ""
    url = ""
    isi_parts = []
    
    for line in lines:
        # **📅 Tanggal:** ... → ISO date
        m = re.search(r'\*\*📅 Tanggal:\*\*\s*(.*)', line)
        if m:
            raw = m.group(1).strip()
            # Try ISO format
            m2 = re.search(r'(\d{4})-(\d{2})-(\d{2})', raw)
            if m2:
                date = f"{m2.group(1)}-{m2.group(2)}-{m2.group(3)}"
        
        # **📰 Sumber:** ...
        m = re.search(r'\*\*📰 Sumber:\*\*\s*(.*)', line)
        if m:
            sumber = m.group(1).strip()
        
        # **🔗 Link:** ...
        m = re.search(r'\*\*🔗 Link:\*\*\s*(.*)', line)
        if m:
            raw_url = m.group(1).strip()
            if raw_url.startswith('http'):
                url = raw_url
    
    # If no **📅 Tanggal:** field, check inline date in content
    if not date:
        # Check full section text for inline date
        full_text = ' '.join(lines)
        inline_date = parse_inline_date(full_text)
        if inline_date:
            date = inline_date
    
    # If still no date, try to extract from context (section header)
    if not date:
        # Check for month/year in surrounding text
        for m_name, m_num in [('desember', '12'), ('januari', '01'), ('februari', '02'),
                               ('maret', '03'), ('april', '04'), ('mei', '05'), ('juni', '06'),
                               ('juli', '07'), ('agustus', '08'), ('september', '09'),
                               ('oktober', '10'), ('november', '11')]:
            if m_name in title.lower() or m_name in full_text.lower()[:200]:
                date = f"2026-{m_num}-15"
                break
    
    # If no URL found in the vault, search for it
    if not url or 'example.com' in url:
        if title and len(title) > 10:
            print(f"🔍 Cari URL: {title[:70]}...")
            found_url = search_article_url(title, sumber)
            if found_url:
                url = found_url
                print(f"   ✅ {url[:80]}")
                time.sleep(1.5)
            else:
                print(f"   ⚠️  Tidak ditemukan")
    
    # Build content
    full_text = ' '.join(lines[1:]) if len(lines) > 1 else ''
    # Remove the metadata lines
    clean_text = re.sub(r'\*\*[📅📰🔗][^:]+:\*\*\s*[^\n]*\n?', '', full_text).strip()
    
    # Skip duplicate URLs
    if url and url in seen_urls:
        continue
    if url:
        seen_urls.add(url)
    
    berita.append({
        "title": title,
        "date": date or "2026-07-01",
        "sumber": sumber or "Berita Kalbar",
        "url": url,
        "content": clean_text[:1000] if clean_text else (title),
    })

# Also add the properly dated articles from existing JSON
news_json = Path("/root/lpg_news_extracted.json")
if news_json.exists():
    existing = json.loads(news_json.read_text(encoding="utf-8"))
    for art in existing:
        title = art.get("title", "").strip()
        url = art.get("url", "").strip()
        
        # Only add if Kalbar-related AND not duplicate
        haystack = (title + (art.get("content","") or "")[:1000] + (art.get("body","") or "")).lower()
        if not any(k in haystack for k in ['kalbar', 'kalimantan barat', 'pontianak', 'singkawang']):
            continue
        if any(b["url"] == url for b in berita if b["url"]):
            continue
        if any(b["title"].lower()[:30] in title.lower() for b in berita):
            continue
        
        # Parse date
        date_str = art.get("date", "")
        m = re.search(r'(\d{4})[/-](\d{2})[/-](\d{2})', date_str)
        adate = f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else ""
        
        # Get content
        content = (art.get("content","") or "")[:1000]
        content = re.sub(r'(login|menu|beranda).*?(?=\s)', '', content, flags=re.I)[:500]
        
        berita.append({
            "title": title,
            "date": adate or "2026-07-01",
            "sumber": art.get("source", "").strip() or "Berita Kalbar",
            "url": url,
            "content": content or title,
        })

print(f"\n📰 Total artikel: {len(berita)}")

# Now categorize and fetch images
def categorize(title, content, sumber):
    text = (title + " " + content + " " + sumber).lower()
    
    # BBM first
    if re.search(r'\b(bbm|bahan bakar minyak|harga bbm)\b', title.lower()):
        return "BBM"
    if re.search(r'\b(bbm|bahan bakar)\b', text):
        if re.search(r'\b(lpg|elpiji)\b', title.lower()):
            return "LPG"
        return "BBM"
    
    # Pertamina in title
    if re.search(r'\bpertamina\b', title.lower()):
        return "Pertamina"
    
    # Pertamina in content
    if re.search(r'\bpertamina\b', text):
        return "Pertamina"
    
    # LPG default
    return "LPG"

processed = []
for i, art in enumerate(berita):
    title = art["title"]
    content = art["content"]
    sumber_val = art.get("sumber", "")
    category = categorize(title, content, sumber_val)
    
    print(f"\n[{i+1}/{len(berita)}] {category} | {art['date']} | {title[:60]}")
    
    # Fetch image from URL
    gambar = ""
    if art["url"]:
        gambar = fetch_og_image(art["url"])
        if gambar:
            print(f"   📸 Image OK")
        time.sleep(0.5)
    
    processed.append({
        "id": i + 1,
        "judul": title,
        "tanggal": art["date"],
        "sumber": sumber_val,
        "kategori": category,
        "url": art["url"],
        "isi": content,
        "gambar": gambar,
    })

# Sort by date
processed.sort(key=lambda x: (x["tanggal"] if x["tanggal"] >= '2025' else '2025-01-01', x["id"]), reverse=True)
for i, b in enumerate(processed, 1):
    b["id"] = i

# Write
output = {"berita": processed}
DATA_FILE.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

cats = {}
for b in processed:
    cats[b["kategori"]] = cats.get(b["kategori"], 0) + 1
imgs = sum(1 for b in processed if b.get("gambar"))
dated = sum(1 for b in processed if b["tanggal"] != "2026-07-01")

print(f"\n✅ Selesai! {len(processed)} berita")
print(f"📸 {imgs}/{len(processed)} punya gambar real")
print(f"📅 {dated}/{len(processed)} tanggal valid")
print(f"📊 Kategori: {json.dumps(cats, indent=2)}")
