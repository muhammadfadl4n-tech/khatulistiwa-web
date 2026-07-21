#!/usr/bin/env python3
"""Final batch: add newly found specific URLs and fetch their images"""
import json, re, subprocess, time, urllib.parse
from pathlib import Path

DATA_FILE = Path("/root/beritakalbar/data/berita.json")
STATIC_IMAGES = Path("/root/beritakalbar/static/images")
STATIC_IMAGES.mkdir(parents=True, exist_ok=True)

data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
berita = data["berita"]

NEW = {
    "warga kalbar keluhkan harga lpg 3 kg meroket": "https://pontianakpost.jawapos.com/metropolis/2601260013/warga-kalbar-keluhkan-kelangkaan-lpg-3-kg-harga-melon-melonjak-di-sejumlah-daerah",
    "konsumsi lpg 3 kg di kalbar meningkat": "https://www.detik.com/kalimantan/bisnis/d-8267910/konsumsi-lpg-3-kg-di-kalbar-meningkat-jelang-nataru-pertamina-tambah-stok",
    "pasokan lpg 3 kg di kalbar aman": "https://www.kapuaspost.web.id/2026/03/pertamina-pastikan-pasokan-lpg-3-kg-di.html",
    "pertamina amankan pasokan lpg 3 kilogram jelang": "https://www.antaranews.com/berita/5314870/pertamina-amankan-pasokan-lpg-3-kilogram-jelang-",
}

def clean(t):
    return re.sub(r'[\U0001F300-\U0010FFFF\u2600-\u27BF\uFE0F]', '', t).strip().lower()

# Find articles with generic URLs and update
for art in berita:
    title_lower = clean(art.get("judul", ""))
    for key, url in NEW.items():
        if key in title_lower:
            old = art.get("url", "")
            if 'tribunnews.com/' in old or 'pontianak.tribunnews.com/' == old or not old.startswith('http'):
                art["url"] = url
                print(f"✅ {art['judul'][:60]}")

# Fetch images for articles without real images
def fetch(url):
    safe = re.sub(r'[^a-z0-9]', '_', re.sub(r'https?://', '', url)[:80].lower()) + '.jpg'
    p = STATIC_IMAGES / safe
    if p.exists() and p.stat().st_size > 500:
        return f"/static/images/{safe}"
    try:
        r = subprocess.run(["curl", "-sL", "--max-time", "15",
            "-H", "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "-H", "Accept: text/html,application/xhtml+xml",
            "-H", "Accept-Language: id-ID,id;q=0.9",
            url], capture_output=True, text=True, timeout=20)
        html = r.stdout[:50000]
    except:
        return None
    
    candidates = []
    for pat in [
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
        r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
    ]:
        for m in re.finditer(pat, html, re.I):
            if m.group(1) not in candidates: candidates.append(m.group(1))
    
    if not candidates:
        for m in re.finditer(r'<img[^>]+src=["\'](https?://[^"\']+\.(?:jpg|jpeg|png))["\']', html):
            s = m.group(1)
            if s not in candidates: candidates.append(s)
    
    for img_url in candidates[:10]:
        if img_url.startswith('//'): img_url = 'https:' + img_url
        elif img_url.startswith('/'):
            parsed = urllib.parse.urlparse(url)
            img_url = f"{parsed.scheme}://{parsed.netloc}{img_url}"
        try:
            dl = subprocess.run(["curl", "-sL", "-o", str(p), "-w", "%{http_code}",
                "--max-time", "15", "-H", "Referer: " + url, img_url],
                capture_output=True, text=True, timeout=20)
            if dl.stdout.strip() == "200" and p.exists() and p.stat().st_size > 1000:
                return f"/static/images/{safe}"
            else: p.unlink(missing_ok=True)
        except: p.unlink(missing_ok=True)
    return None

fetched = 0
for art in berita:
    url = art.get("url", "")
    if not url.startswith('http') or 'example.com' in url:
        continue
    if art.get("gambar", "").endswith('.jpg'):
        continue
    print(f"📸 {art['judul'][:50]}...")
    result = fetch(url)
    if result:
        art["gambar"] = result
        fetched += 1
        print(f"   ✅")
    else:
        print(f"   ❌")
    time.sleep(1)

# Sort & save
berita.sort(key=lambda x: (x["tanggal"] if x["tanggal"] >= '2025' else '2025-01-01', x["id"]), reverse=True)
for i, b in enumerate(berita, 1): b["id"] = i
DATA_FILE.write_text(json.dumps({"berita": berita}, ensure_ascii=False, indent=2), encoding="utf-8")

real = sum(1 for b in berita if b.get("gambar","").endswith('.jpg'))
svgs = sum(1 for b in berita if b.get("gambar","").endswith('.svg'))
print(f"\n✅ Total: {real} real foto (+{fetched} baru) + {svgs} SVG = {real+svgs}/{len(berita)}")
