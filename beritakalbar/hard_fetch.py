#!/usr/bin/env python3
"""
Keras-keras! Fetch images for articles with specific URLs using better methods.
"""
import json, re, subprocess, time, urllib.parse
from pathlib import Path

DATA_FILE = Path("/root/beritakalbar/data/berita.json")
STATIC_IMAGES = Path("/root/beritakalbar/static/images")
STATIC_IMAGES.mkdir(parents=True, exist_ok=True)

data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
berita = data["berita"]

def try_fetch_image(url):
    """Try various methods to get an image from a URL"""
    safe_name = re.sub(r'[^a-z0-9]', '_', re.sub(r'https?://', '', url)[:80].lower()) + '.jpg'
    img_path = STATIC_IMAGES / safe_name
    if img_path.exists() and img_path.stat().st_size > 500:
        return f"/static/images/{safe_name}"
    
    # Fetch page HTML
    try:
        r = subprocess.run(
            ["curl", "-sL", "--max-time", "15",
             "-H", "User-Agent: Mozilla/5.0 (Linux; Android 13; SM-S908E) AppleWebKit/537.36",
             "-H", "Accept: text/html,application/xhtml+xml",
             "-H", "Accept-Language: id-ID,id;q=0.9,en;q=0.8",
             url],
            capture_output=True, text=True, timeout=20
        )
        html = r.stdout[:50000]
    except:
        return None
    
    # Collect ALL image URLs from meta tags
    img_candidates = []
    
    # og:image
    for m in re.finditer(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I):
        img_candidates.append(m.group(1))
    for m in re.finditer(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', html, re.I):
        img_candidates.append(m.group(1))
    # twitter:image
    for m in re.finditer(r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I):
        img_candidates.append(m.group(1))
    # First large img
    for m in re.finditer(r'<img[^>]+src=["\']([^"\']+\.(?:jpg|jpeg|png|webp))["\']', html, re.I):
        src = m.group(1)
        if any(k in src.lower() for k in ['featured', 'cover', 'photo', 'foto', 'gambar', 'lpg', 'gas', 'tabung', 'artikel', 'content', 'utama', 'berita', 'post', 'image', 'assets', 'upload', '2026', '2025']):
            img_candidates.append(src)
    # Fallback: any jpg/png that's not too small (>=80 chars = likely full URL)
    for m in re.finditer(r'<img[^>]+src=["\']([^"\']+\.(?:jpg|jpeg|png))["\']', html, re.I):
        src = m.group(1)
        if len(src) >= 60 and src not in img_candidates:
            img_candidates.append(src)
    # Last resort: any img
    for m in re.finditer(r'<img[^>]+src=["\'](https?://[^"\']+\.(?:jpg|jpeg|png))["\']', html, re.I):
        src = m.group(1)
        if src not in img_candidates:
            img_candidates.append(src)
    
    if not img_candidates:
        return None
    
    # Try each candidate
    for img_url in img_candidates[:10]:
        # Normalize URL
        if img_url.startswith('//'): img_url = 'https:' + img_url
        elif img_url.startswith('/'):
            parsed = urllib.parse.urlparse(url)
            img_url = f"{parsed.scheme}://{parsed.netloc}{img_url}"
        
        try:
            dl = subprocess.run(
                ["curl", "-sL", "-o", str(img_path), "-w", "%{http_code}",
                 "--max-time", "15",
                 "-H", "User-Agent: Mozilla/5.0 (X11; Linux x86_64)",
                 "-H", "Referer: " + url,
                 "-H", "Accept: image/webp,image/*,*/*",
                 img_url],
                capture_output=True, text=True, timeout=20
            )
            code = dl.stdout.strip()
            if code == "200" and img_path.exists() and img_path.stat().st_size > 1000:
                return f"/static/images/{safe_name}"
            else:
                img_path.unlink(missing_ok=True)
        except:
            img_path.unlink(missing_ok=True)
    
    return None

# Process: only articles with SPECIFIC URLs (not tribun homepage)
target_ids = []
for art in berita:
    url = art.get("url", "")
    # Skip generic homepage URLs
    if url in ["https://pontianak.tribunnews.com/", ""]:
        continue
    if 'example.com' in url:
        continue
    if not url.startswith('http'):
        continue
    if art.get("gambar", "").endswith('.jpg'):
        continue  # already has image
    
    target_ids.append(art["id"])
    print(f"🎯 #{art['id']} {art['judul'][:60]}")

print(f"\n📸 Mencoba fetch {len(target_ids)} artikel dengan URL spesifik...\n")

success = 0
for art in berita:
    if art["id"] not in target_ids:
        continue
    url = art["url"]
    print(f"[#{art['id']}] {art['judul'][:50]}...")
    result = try_fetch_image(url)
    if result:
        art["gambar"] = result
        success += 1
        print(f"   ✅ GAMBAR DAPAT! {result}")
    else:
        print(f"   ❌ Tidak ada gambar")
    time.sleep(1)

# Sort and save
berita.sort(key=lambda x: (x["tanggal"] if x["tanggal"] >= '2025' else '2025-01-01', x["id"]), reverse=True)
for i, b in enumerate(berita, 1):
    b["id"] = i

DATA_FILE.write_text(json.dumps({"berita": berita}, ensure_ascii=False, indent=2), encoding="utf-8")

real = sum(1 for b in berita if b.get("gambar","").endswith('.jpg'))
print(f"\n✅ Total: {real} real foto (+{success} baru) dari {len(berita)} berita")
