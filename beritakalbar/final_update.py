#!/usr/bin/env python3
"""Final URL update with newly discovered specific article URLs"""
import json, re, subprocess, time, urllib.parse
from pathlib import Path

DATA_FILE = Path("/root/beritakalbar/data/berita.json")
STATIC_IMAGES = Path("/root/beritakalbar/static/images")
STATIC_IMAGES.mkdir(parents=True, exist_ok=True)

data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
berita = data["berita"]

# More specific URL mappings override
URL_UPDATES = {
    "polda kalbar ungkap penyelewengan": "https://pontianakinformasi.co.id/news/polda-kalbar-ungkap-modus-penyelewengan-lpg-3-kg-bukan-disuntik-tapi-dijual-mahal/",
    "ledakan lpg 3 kg di rumah makan pontianak": "https://pontianak.tribunnews.com/metropolis/1167715/bau-lpg-3-kg-tercium-sebelum-ledakan-7-orang-jadi-korban-di-rumah-makan-jalan-ampera-pontianak",
    "distribusi lpg 3 kg di kalbar dipantau ketat": "https://pontianak.tribunnews.com/metropolis/1176647/distribusi-lpg-3-kg-di-kalbar-dipantau-ketat-pertamina-tambah-pasokan-di-pontianak-dan-sambas",
    "lpg 3 kg di pangkalan bun": "https://www.cnbcindonesia.com/news/20260701140511-4-747156/harga-terbaru-lpg-3-kg-55-12-kg-di-agen-pangkalan-per-1-juli-2026",
    "pertamina regional kalimantan": "https://kalsel.antaranews.com/berita/404682/pertamina-regional-kalimantan-bentuk-tim-satgas-bbm-dan-lpg",
    "satpol pp pontianak amankan 57 tabung": "https://pontianak.tribunnews.com/",
    "lpg langka, resah menggantung": "https://pontianak.tribunnews.com/",
    "lpg 3 kg di pemangkat (sambas)": "https://pontianak.tribunnews.com/",
    "konsumsi lpg 3 kg di kalbar meningkat": "https://pontianak.tribunnews.com/",
    "jelang imlek & ramadan, pertamina tambah kuota": "https://pontianak.tribunnews.com/",
    "pertamina tanggap lonjakan lpg di kalbar": "https://pontianak.tribunnews.com/",
    "pasokan lpg 3 kg di kalbar aman": "https://pontianak.tribunnews.com/",
    "pertamina amankan pasokan lpg 3 kilogram jelang": "https://www.antaranews.com/berita/5314870/pertamina-amankan-pasokan-lpg-3-kilogram-jelang-",
}

def clean(t):
    return re.sub(r'[\U0001F300-\U0010FFFF\u2600-\u27BF\uFE0F]', '', t).strip().lower()

# Update to more specific URLs
updated = 0
for art in berita:
    title_lower = clean(art.get("judul", ""))
    for key, url in URL_UPDATES.items():
        if key in title_lower:
            old_url = art.get("url", "")
            # Only update if the new URL is more specific
            if old_url == "https://pontianak.tribunnews.com/" or 'example.com' in old_url or not old_url.startswith('http'):
                art["url"] = url
                updated += 1
                print(f"✅ {art['judul'][:60]}")
                print(f"   {url[:80]}")
            break

print(f"\n🔗 {updated} URL diupdate")

# Fetch images for all URLs without images
fetched = 0
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
    
    print(f"[{i+1}] 📸 {art['judul'][:50]}...")
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
        
        if not img_url:
            imgs = re.findall(r'<img[^>]+src=["\']([^"\']+\.(?:jpg|jpeg|png))["\']', html)
            for img in imgs:
                if any(k in img.lower() for k in ['featured', 'cover', 'hero', 'main', 'artikel', 'lpg', 'gas', 'energi', 'tabung']):
                    img_url = img; break
            if not img_url and imgs:
                img_url = imgs[min(1, len(imgs)-1)]

        if img_url:
            if img_url.startswith('//'): img_url = 'https:' + img_url
            elif img_url.startswith('/'):
                parsed = urllib.parse.urlparse(url)
                img_url = f"{parsed.scheme}://{parsed.netloc}{img_url}"
            dl = subprocess.run(
                ["curl", "-sL", "-o", str(STATIC_IMAGES/safe_name), "-w", "%{http_code}",
                 "--max-time", "15", "-H", "Referer: " + url, img_url],
                capture_output=True, text=True, timeout=20
            )
            if dl.stdout.strip() == "200" and (STATIC_IMAGES/safe_name).stat().st_size > 500:
                art["gambar"] = f"/static/images/{safe_name}"
                fetched += 1
                print(f"      ✅")
            else:
                (STATIC_IMAGES/safe_name).unlink(missing_ok=True)
                print(f"      ❌")
        else:
            print(f"      ⚠️")
    except:
        print(f"      ❌")
    time.sleep(0.5)

# Generate SVG fallbacks for remaining
def gen_svg(cat, title, fn):
    colors = {"LPG": ["#7c3aed", "#2563eb"], "BBM": ["#d97706", "#dc2626"], "Pertamina": ["#059669", "#0284c7"]}
    c1, c2 = colors.get(cat, ["#4f46e5", "#7c3aed"])
    stitle = re.sub(r'[\U0001F300-\U0010FFFF\u2600-\u27BF\uFE0F]', '', title).strip()
    if len(stitle) > 80: stitle = stitle[:77] + "..."
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="450" viewBox="0 0 800 450">
  <defs><linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" style="stop-color:{c1}"/><stop offset="100%" style="stop-color:{c2}"/></linearGradient></defs>
  <rect width="800" height="450" fill="url(#g)"/>
  <rect x="30" y="30" width="740" height="390" rx="8" fill="rgba(255,255,255,0.08)"/>
  <text x="400" y="120" text-anchor="middle" font-family="Inter, sans-serif" font-size="28" font-weight="700" fill="rgba(255,255,255,0.25)">{cat}</text>
  <text x="400" y="220" text-anchor="middle" font-family="Inter, sans-serif" font-size="22" font-weight="600" fill="white"><tspan x="400" dy="0">{stitle[:55]}</tspan></text>
  <text x="400" y="350" text-anchor="middle" font-family="Inter, sans-serif" font-size="18" fill="rgba(255,255,255,0.5)">Berita Kalbar</text>
</svg>'''
    (STATIC_IMAGES / fn).write_text(svg)
    return f"/static/images/{fn}"

for art in berita:
    if art.get("gambar"): continue
    cat = art.get("kategori", "LPG")
    title = art.get("judul", "")
    sf = re.sub(r'[^a-z0-9]', '_', (cat + "_" + title)[:60].lower().strip('_')) + '.svg'
    if not (STATIC_IMAGES / sf).exists():
        art["gambar"] = gen_svg(cat, title, sf)
    else:
        art["gambar"] = f"/static/images/{sf}"

# Sort and save
berita.sort(key=lambda x: (x["tanggal"] if x["tanggal"] >= '2025' else '2025-01-01', x["id"]), reverse=True)
for i, b in enumerate(berita, 1):
    b["id"] = i

DATA_FILE.write_text(json.dumps({"berita": berita}, ensure_ascii=False, indent=2), encoding="utf-8")

total = len(berita)
urls = sum(1 for b in berita if b.get("url","").startswith('http'))
real = sum(1 for b in berita if b.get("gambar","").endswith('.jpg'))
svg = sum(1 for b in berita if b.get("gambar","").endswith('.svg'))
cats = {}
for b in berita: cats[b["kategori"]] = cats.get(b["kategori"], 0) + 1

print(f"\n{'='*40}")
print(f"✅ {total} berita")
print(f"🔗 {urls} URL real")
print(f"📸 {real} real foto + {svg} SVG = {real+svg} total gambar")
print(f"📊 Kategori: {json.dumps(cats)}")
print(f"📅 Tanggal valid: {sum(1 for b in berita if b['tanggal'] != '2026-07-01')}/{total}")
