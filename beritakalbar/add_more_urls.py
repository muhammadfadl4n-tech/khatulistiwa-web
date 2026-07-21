#!/usr/bin/env python3
"""
Add newly discovered specific URLs and fetch their og:images
"""
import json, re, subprocess, time, urllib.parse
from pathlib import Path

DATA_FILE = Path("/root/beritakalbar/data/berita.json")
STATIC_IMAGES = Path("/root/beritakalbar/static/images")
STATIC_IMAGES.mkdir(parents=True, exist_ok=True)

data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
berita = data["berita"]

NEW_URLS = {
    "lpg langka, resah menggantung": "https://www.liputan6.com/regional/read/6160074/lpg-langka-resah-menggantung-di-gang-gang-pontianak",
    "lpg 3 kg di pemangkat": "https://www.wartaindonesianews.co.id/2026/01/lpg-3-kg-di-pemangkat-cepat-habis-warga.html",
    "satpol pp pontianak amankan 57 tabung": "https://pontianak.go.id/pontianak-hari-ini/berita/Satpol-PP-Pontianak-Tertibkan-Penggunaan-LPG-3kg-oleh-Pelaku-Usaha",
    "pertamina tanggap lonjakan lpg di kalbar": "https://www.inidata.id/kalimantan-kita/40115910362/pertamina-tanggap-lonjakan-lpg-3-kg-pasokan-aman-pasca-libur-panjang-kalbar",
    "jelang imlek & ramadan, pertamina tambah kuota": "https://www.ruangenergi.com/catat-jelang-imlek-dan-ramadan-pertamina-tambah-78-juta-tabung-lpg-3-kg/",
    "warga kalbar keluhkan harga lpg 3 kg meroket": "https://pontianak.tribunnews.com/",
    "pasokan lpg 3 kg di kalbar aman": "https://pontianak.tribunnews.com/",
    "pertamina amankan pasokan lpg 3 kilogram jelang": "https://www.antaranews.com/berita/5314870/pertamina-amankan-pasokan-lpg-3-kilogram-jelang-",
    "konsumsi lpg 3 kg di kalbar meningkat": "https://pontianak.tribunnews.com/",
}

def clean(t):
    return re.sub(r'[\U0001F300-\U0010FFFF\u2600-\u27BF\uFE0F]', '', t).strip().lower()

# Update URLs
for art in berita:
    title_lower = clean(art.get("judul", ""))
    for key, url in NEW_URLS.items():
        if key in title_lower:
            old = art.get("url", "")
            if old == "https://pontianak.tribunnews.com/" or not old.startswith('http') or 'example.com' in old:
                art["url"] = url
                print(f"✅ URL: {art['judul'][:60]}")
                break

# Fetch images for all articles with specific URLs that lack images
def fetch_image(url):
    safe = re.sub(r'[^a-z0-9]', '_', re.sub(r'https?://', '', url)[:80].lower()) + '.jpg'
    p = STATIC_IMAGES / safe
    if p.exists() and p.stat().st_size > 500:
        return f"/static/images/{safe}"
    
    try:
        r = subprocess.run(["curl", "-sL", "--max-time", "15",
            "-H", "User-Agent: Mozilla/5.0 (Linux; Android 13; SM-S908E)",
            "-H", "Accept-Language: id-ID,id",
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
            else:
                p.unlink(missing_ok=True)
        except:
            p.unlink(missing_ok=True)
    return None

fetched = 0
for art in berita:
    url = art.get("url", "")
    if not url.startswith('http') or 'example.com' in url:
        continue
    if url in ["https://pontianak.tribunnews.com/", ""]:
        continue  # Skip generic homepages
    if art.get("gambar", "").endswith('.jpg'):
        continue
    
    print(f"📸 {art['judul'][:50]}...")
    result = fetch_image(url)
    if result:
        art["gambar"] = result
        fetched += 1
        print(f"   ✅")
    else:
        print(f"   ❌")
    time.sleep(1)

# Sort and save
berita.sort(key=lambda x: (x["tanggal"] if x["tanggal"] >= '2025' else '2025-01-01', x["id"]), reverse=True)
for i, b in enumerate(berita, 1):
    b["id"] = i

DATA_FILE.write_text(json.dumps({"berita": berita}, ensure_ascii=False, indent=2), encoding="utf-8")

real = sum(1 for b in berita if b.get("gambar","").endswith('.jpg'))
svgs = sum(1 for b in berita if b.get("gambar","").endswith('.svg'))
print(f"\n✅ {real} real foto (+{fetched} baru) + {svgs} SVG = {real+svgs}/{len(berita)} gambar")
