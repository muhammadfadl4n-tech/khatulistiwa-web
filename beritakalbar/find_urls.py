#!/usr/bin/env python3
"""
Find URLs and images for vault articles via web_search
"""
import json, re, subprocess, time, urllib.parse
from pathlib import Path

DATA_FILE = Path("/root/beritakalbar/data/berita.json")
STATIC_IMAGES = Path("/root/beritakalbar/static/images")
STATIC_IMAGES.mkdir(parents=True, exist_ok=True)

data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
berita = data["berita"]

def clean_title(t):
    return re.sub(r'[\U0001F300-\U0010FFFF\u2600-\u27BF\uFE0F]', '', t).strip()

def ddg_search(query):
    """Search DuckDuckGo via HTML endpoint"""
    try:
        q = urllib.parse.quote(query)
        r = subprocess.run(
            ["curl", "-sL", "--max-time", "10",
             "-H", "User-Agent: Mozilla/5.0 (X11; Linux x86_64)",
             f"https://html.duckduckgo.com/html/?q={q}"],
            capture_output=True, text=True, timeout=12
        )
        html = r.stdout
        results = re.findall(r'class="result__url"[^>]*href="([^"]+)"', html)
        return results[:5]
    except:
        return []

# Source-specific search
DOMAINS = {
    'detik': 'site:detik.com',
    'kompas': 'site:kompas.com',
    'cnbc': 'site:cnbcindonesia.com',
    'antara': 'site:antaranews.com',
    'tribun': 'site:tribunnews.com',
    'bisnis': 'site:bisnis.com',
    'kontan': 'site:kontan.co.id',
    'viva': 'site:viva.co.id',
    'pontianak': 'site:pontianakpost.co.id',
    'liputan6': 'site:liputan6.com',
    'katadata': 'site:katadata.co.id',
}

found_urls = 0
for i, art in enumerate(berita):
    title = art.get("judul", "")
    url = art.get("url", "")
    sumber = art.get("sumber", "")

    if url and url.startswith('http') and 'example.com' not in url:
        continue

    search_title = clean_title(title)
    if not search_title or len(search_title) < 10:
        continue

    domain = ''
    for key, d in DOMAINS.items():
        if key in sumber.lower():
            domain = f' {d}'
            break
    if not domain:
        domain = ' (site:detik.com OR site:kompas.com OR site:cnbcindonesia.com)'

    query = f'"{search_title}"{domain}'
    print(f"[{i+1}/{len(berita)}] 🔍 {search_title[:60]}...")

    urls_found = ddg_search(query)
    for u in urls_found:
        if any(s in u for s in ['detik.com', 'kompas.com', 'cnbcindonesia.com',
                                'antaranews.com', 'tribunnews.com', 'bisnis.com',
                                'kontan.co.id', 'viva.co.id', 'pontianakpost.co.id',
                                'liputan6.com', 'katadata.co.id']):
            art["url"] = u
            found_urls += 1
            print(f"   ✅ {u[:80]}")
            break
    else:
        print(f"   ⚠️ Not found")
    time.sleep(0.8)

print(f"\n🔗 {found_urls} URL baru ditemukan")

# Fetch images
new_imgs = 0
for i, art in enumerate(berita):
    url = art.get("url", "")
    if not url or 'example.com' in url or not url.startswith('http'):
        continue
    if art.get("gambar"):
        continue

    safe_name = re.sub(r'[^a-z0-9]', '_', re.sub(r'https?://', '', url)[:80].lower()) + '.jpg'
    if (STATIC_IMAGES / safe_name).exists():
        art["gambar"] = f"/static/images/{safe_name}"
        continue

    print(f"[{i+1}] 📸 {url[:60]}...")
    try:
        r = subprocess.run(
            ["curl", "-sL", "--max-time", "10",
             "-H", "User-Agent: Mozilla/5.0 (Linux; Android 13; SM-S908E)",
             url],
            capture_output=True, text=True, timeout=15
        )
        html = r.stdout[:30000]
        img_url = None
        for pat in [
            r'<meta\s+[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']',
            r'<meta\s+[^>]*content=["\']([^"\']+)["\'][^>]*property=["\']og:image["\']',
            r'<meta\s+[^>]*name=["\']twitter:image["\'][^>]*content=["\']([^"\']+)["\']',
        ]:
            m = re.search(pat, html, re.I)
            if m: img_url = m.group(1); break

        if img_url:
            if img_url.startswith('//'): img_url = 'https:' + img_url
            elif img_url.startswith('/'):
                parsed = urllib.parse.urlparse(url)
                img_url = f"{parsed.scheme}://{parsed.netloc}{img_url}"

            dl = subprocess.run(
                ["curl", "-sL", "-o", str(STATIC_IMAGES/safe_name), "-w", "%{http_code}",
                 "--max-time", "15", img_url],
                capture_output=True, text=True, timeout=20
            )
            if dl.stdout.strip() == "200" and (STATIC_IMAGES/safe_name).stat().st_size > 500:
                art["gambar"] = f"/static/images/{safe_name}"
                new_imgs += 1
                print(f"      ✅")
            else:
                (STATIC_IMAGES/safe_name).unlink(missing_ok=True)
                print(f"      ❌ DL fail")
        else:
            print(f"      ⚠️ No og:image")
    except Exception as e:
        print(f"      ❌ Error: {e}")
    time.sleep(0.5)

# Sort and save
berita.sort(key=lambda x: (x["tanggal"] if x["tanggal"] >= '2025' else '2025-01-01', x["id"]), reverse=True)
for i, b in enumerate(berita, 1):
    b["id"] = i

DATA_FILE.write_text(json.dumps({"berita": berita}, ensure_ascii=False, indent=2), encoding="utf-8")

imgs = sum(1 for b in berita if b.get("gambar"))
url_cnt = sum(1 for b in berita if b.get("url", "").startswith('http') and 'example.com' not in b.get("url",""))
ded = sum(1 for b in berita if b.get("gambar", "").endswith('.svg'))
print(f"\n✅ {len(berita)} berita")
print(f"🔗 {url_cnt} URL real (+{found_urls} baru)")
print(f"📸 {imgs} gambar ({imgs-ded} real, {ded} SVG) — {new_imgs} baru")
