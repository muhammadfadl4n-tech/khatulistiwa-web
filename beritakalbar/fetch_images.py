#!/usr/bin/env python3
"""
Generate category-based gradient thumbnail SVGs for articles without real images.
Also try harder to get images from URLs.
"""
import json, re, os, subprocess, time
from pathlib import Path

BASE_DIR = Path("/root/beritakalbar")
DATA_FILE = BASE_DIR / "data" / "berita.json"
STATIC_IMAGES = BASE_DIR / "static" / "images"
STATIC_IMAGES.mkdir(parents=True, exist_ok=True)

data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
berita = data["berita"]

# 1. Try to search for article URLs for vault entries without URLs
def search_article(title):
    """Search for article by title to get URL"""
    try:
        # Strip emoji and clean title
        clean = re.sub(r'[\U0001F300-\U0001FAFF\U0001F600-\U0001F9FF\u2600-\u26FF\u2700-\u27BF\u2B50\uFE0F\U0001F1E0-\U0001F1FF]', '', title).strip()
        clean = clean[:80]
        # Use ddgs if available
        import urllib.parse
        query = urllib.parse.quote(f'"{clean}" site:kompas.com OR site:detik.com OR site:cnbcindonesia.com OR site:antaranews.com')
        result = subprocess.run(
            ["curl", "-sL", "--max-time", "8",
             f"https://html.duckduckgo.com/html/?q={query}",
             "-H", "User-Agent: Mozilla/5.0"],
            capture_output=True, text=True, timeout=10
        )
        # Find first real URL
        urls = re.findall(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"', result.stdout)
        for u in urls:
            if any(s in u for s in ['kompas.com', 'detik.com', 'cnbcindonesia.com', 'antaranews.com', 'tribunnews.com']):
                # Fix duckduckgo redirect
                u = re.sub(r'^.*uddg=(https?://[^&]+).*$', r'\1', u)
                u = urllib.parse.unquote(u)
                return u
    except:
        pass
    return None

# Try to find URLs for vault articles
for article in berita:
    url = article.get("url", "")
    if url and 'example.com' not in url and url.startswith('http'):
        continue  # Already has real URL
    if article.get("gambar"):
        continue  # Already has image
    
    title = article.get("judul", "")
    sumber = article.get("sumber", "")
    
    # Search for the article
    print(f"🔍 Mencari: {title[:60]}...")
    real_url = search_article(title)
    if real_url:
        article["url"] = real_url
        print(f"   ✅ URL: {real_url[:80]}")
        time.sleep(1)  # Rate limit
        
        # Now fetch image from this URL
        safe_name = re.sub(r'[^a-z0-9]', '_', re.sub(r'https?://', '', real_url)[:80].lower()) + '.jpg'
        if not (STATIC_IMAGES / safe_name).exists():
            print(f"   🔍 Fetching image...")
            result = subprocess.run(
                ["curl", "-sL", "--max-time", "10",
                 "-H", "User-Agent: Mozilla/5.0 (Linux; Android 13)",
                 real_url],
                capture_output=True, text=True, timeout=15
            )
            html = result.stdout[:30000]
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
            if img_url:
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                elif img_url.startswith('/'):
                    from urllib.parse import urlparse
                    parsed = urlparse(real_url)
                    img_url = f"{parsed.scheme}://{parsed.netloc}{img_url}"
                print(f"   📷 Downloading: {img_url[:60]}...")
                dl = subprocess.run(
                    ["curl", "-sL", "-o", str(STATIC_IMAGES/safe_name), "-w", "%{http_code}",
                     "--max-time", "15", img_url],
                    capture_output=True, text=True, timeout=20
                )
                if dl.stdout.strip() == "200" and (STATIC_IMAGES/safe_name).stat().st_size > 500:
                    article["gambar"] = f"/static/images/{safe_name}"
                    print(f"      ✅ OK")
                else:
                    (STATIC_IMAGES/safe_name).unlink(missing_ok=True)
                    print(f"      ❌ Gagal")
        else:
            article["gambar"] = f"/static/images/{safe_name}"
    else:
        print(f"   ⚠️  Tidak ditemukan")

# 2. Generate category gradient SVGs for remaining articles without images
def gen_svg(category, title, filename):
    """Generate a category-themed gradient SVG thumbnail"""
    colors = {
        "LPG": ["#7c3aed", "#2563eb"],  # Purple to Blue
        "BBM": ["#d97706", "#dc2626"],  # Amber to Red
        "Pertamina": ["#059669", "#0284c7"],  # Emerald to Sky
    }
    c1, c2 = colors.get(category, ["#4f46e5", "#7c3aed"])
    
    # Clean title for display
    short_title = re.sub(r'[\U0001F300-\U0010FFFF\u2600-\u27BF]', '', title).strip()
    if len(short_title) > 80:
        short_title = short_title[:77] + "..."
    
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="450" viewBox="0 0 800 450">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:{c1};stop-opacity:1" />
      <stop offset="100%" style="stop-color:{c2};stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="800" height="450" fill="url(#bg)"/>
  <rect x="30" y="30" width="740" height="390" rx="8" fill="rgba(255,255,255,0.08)"/>
  <text x="400" y="120" text-anchor="middle" font-family="Inter, sans-serif" font-size="28" font-weight="700" fill="rgba(255,255,255,0.25)">{category}</text>
  <text x="400" y="220" text-anchor="middle" font-family="Inter, sans-serif" font-size="22" font-weight="600" fill="white">
    <tspan x="400" dy="0">{short_title[:55]}</tspan>
  </text>
  <text x="400" y="350" text-anchor="middle" font-family="Inter, sans-serif" font-size="18" fill="rgba(255,255,255,0.5)">Berita Kalbar</text>
</svg>'''
    path = STATIC_IMAGES / filename
    path.write_text(svg)
    return f"/static/images/{filename}"

for article in berita:
    if article.get("gambar"):
        continue
    category = article.get("kategori", "LPG")
    title = article.get("judul", "")
    safe = re.sub(r'[^a-z0-9]', '_', (category + "_" + title)[:60].lower().strip('_')) + '.svg'
    if not (STATIC_IMAGES / safe).exists():
        print(f"🎨 SVG fallback: {title[:50]}...")
        article["gambar"] = gen_svg(category, title, safe)
    else:
        article["gambar"] = f"/static/images/{safe}"

# Sort & save
berita.sort(key=lambda x: (x["tanggal"], x["id"]), reverse=True)
for i, b in enumerate(berita, 1):
    b["id"] = i

output = {"berita": berita}
DATA_FILE.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

cats = {}
for b in berita:
    cats[b["kategori"]] = cats.get(b["kategori"], 0) + 1
imgs = sum(1 for b in berita if b.get("gambar"))
real = sum(1 for b in berita if b.get("gambar", "").endswith('.jpg'))
svg_count = sum(1 for b in berita if b.get("gambar", "").endswith('.svg'))

print(f"\n✅ Selesai! {len(berita)} berita")
print(f"📸 {imgs}/{len(berita)} gambar ({real} real, {svg_count} SVG fallback)")
print(f"📊 Kategori: {json.dumps(cats, indent=2)}")
