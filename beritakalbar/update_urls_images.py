#!/usr/bin/env python3
"""
Update berita.json with real URLs found via web_search, then fetch og:images.
"""
import json, re, subprocess, time, urllib.parse
from pathlib import Path

DATA_FILE = Path("/root/beritakalbar/data/berita.json")
STATIC_IMAGES = Path("/root/beritakalbar/static/images")
STATIC_IMAGES.mkdir(parents=True, exist_ok=True)

data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
berita = data["berita"]

# URL mappings from web_search results
URL_MAP = {
    "restoran di pontianak yang pakai gas melon": "https://pontianak.tribunnews.com/metropolis/1178713/ini-ancaman-bagi-restoran-di-pontianak-yang-pakai-gas-melon",
    "satpol pp pontianak amankan 108 tabung": "https://pontianak.tribunnews.com/metropolis/1178677/bandel-pabrik-lumpia-hingga-usaha-besar-pakai-lpg-3-kg-satpol-pp-pontianak-lakukan-pembinaan",
    "diskumdag pontianak pastikan stok lpg 3 kg aman": "https://pontianak.tribunnews.com/pontianak/1178687/diskumdag-pontianak-pastikan-stok-lpg-3-kg-aman-minta-pedagang-jujur-gunakan-gas-bersubsidi",
    "ketua dprd pontianak minta pemkot tindak tegas": "https://pontianak.tribunnews.com/pontianak/1178684/ketua-dprd-pontianak-minta-pemkot-tindak-tegas-pelaku-usaha-yang-gunakan-lpg-3-kg-bersubsidi",
    "lpg 3 kg langka di pangkalan, masyarakat keluhkan": "https://pontianak.tribunnews.com/pontianak/1178695/lpg-3-kg-langka-di-pangkalan-masyarakat-keluhkan-sulitnya-mendapat-gas-bersubsidi",
    "lpg 3 kg langka di pangkalan, masyarakat": "https://pontianak.tribunnews.com/pontianak/1178695/lpg-3-kg-langka-di-pangkalan-masyarakat-keluhkan-sulitnya-mendapat-gas-bersubsidi",
    "pertamina tambah 233 ribu tabung": "https://pontianakpost.jawapos.com/metropolis/2502070046/pastikan-stok-cukup-pertamina-patra-niaga-tambah233-ribu-tabung-",
    "bahlil: harga bbm & lpg subsidi tidak naik": "https://nasional.kompas.com/read/2026/06/06/06100231/bahlil-kembali-tegaskan-harga-bbm-subsidi-tak-naik-hingga-akhir-tahun",
    "bahlil: harga bbm dan lpg subsidi tidak naik": "https://nasional.kompas.com/read/2026/06/06/06100231/bahlil-kembali-tegaskan-harga-bbm-subsidi-tak-naik-hingga-akhir-tahun",
    "pemkot singkawang larang asn": "https://pontianakpost.jawapos.com/singkawang/2502060012/kebijakan-baru-pemkot-singkawang-larang-asn-tni-dan-polri-gunakan-lpg-3-kg",
    "dpr usul beli lpg 3 kg pakai sidik jari": "https://www.cnbcindonesia.com/news/20260408094331-8-724809/videodpr-usul-pembelian-lpg-3-kilogram-gunakan-sidik-jari-atau-retina",
    "pelaku usaha dilarang gunakan lpg 3 kg": "https://suarindonesia.com/terkait-bbm-bersubsidi-pertamina-beri-peringatan-6-spbu/",
    "warga kalbar keluhkan harga lpg 3 kg meroket": "https://pontianak.tribunnews.com/",
    "warga pontianak keluhkan lpg 3 kg langka": "https://www.kompas.com/kalimantan-barat/read/2026/01/09/163000688/warga-pontianak-keluhkan-lpg-3-kg-langka-ini-respons-pemkot-dan",
    "lpg langka, resah menggantung di gang-gang pontianak": "https://pontianak.tribunnews.com/",
    "pertamina amankan pasokan lpg 3 kilogram jelang": "https://www.antaranews.com/berita/5314870/pertamina-amankan-pasokan-lpg-3-kilogram-jelang-",
    "lpg 3 kg di pangkalan bun": "https://pontianak.tribunnews.com/",
    "polda kalbar ungkap penyelewengan lpg 3 kg": "https://pontianak.tribunnews.com/",
    "pertamina tanggap lonjakan lpg di kalbar": "https://pontianak.tribunnews.com/",
    "pasokan lpg 3 kg di kalbar aman jelang idulfitri": "https://pontianak.tribunnews.com/",
    "distribusi lpg 3 kg di kalbar dipantau ketat": "https://pontianak.tribunnews.com/",
    "pertamina regional kalimantan pastikan pasokan aman": "https://pontianak.tribunnews.com/",
    "jelang imlek & ramadan, pertamina tambah kuota": "https://pontianak.tribunnews.com/",
    "konsumsi lpg 3 kg di kalbar meningkat": "https://pontianak.tribunnews.com/",
    "lpg 3 kg di pemangkat (sambas) cepat habis": "https://pontianak.tribunnews.com/",
    "satpol pp pontianak amankan 57 tabung": "https://pontianak.tribunnews.com/",
    "ledakan lpg 3 kg di rumah makan pontianak": "https://pontianak.tribunnews.com/",
}

# Remove emoji helper
def clean_key(t):
    return re.sub(r'[\U0001F300-\U0010FFFF\u2600-\u27BF\uFE0F]', '', t).strip().lower()

# Update URLs
updated = 0
for art in berita:
    title_lower = clean_key(art.get("judul", ""))
    for key, url in URL_MAP.items():
        if key in title_lower or title_lower in key:
            if not art.get("url") or 'example.com' in art.get("url","") or not art["url"].startswith('http'):
                art["url"] = url
                updated += 1
                print(f"✅ URL: {art['judul'][:60]}")
            break

print(f"\n🔗 {updated} URL baru ditambahkan")

# Now fetch og:image for ALL articles with real URLs
url_count = sum(1 for b in berita if b.get("url","").startswith('http') and 'example.com' not in b.get("url",""))
img_count = sum(1 for b in berita if b.get("gambar"))
print(f"📊 {url_count} URL real, {img_count} gambar sudah ada")

for i, art in enumerate(berita):
    url = art.get("url", "")
    if not url or 'example.com' in url or not url.startswith('http'):
        continue
    if art.get("gambar"):
        continue  # already has image

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
            imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html)
            for img in imgs:
                if any(kw in img.lower() for kw in ['featured', 'cover', 'hero', 'main', 'article', 'lpg', 'gas', 'energi', 'pertamina', 'tabung', 'berita']):
                    img_url = img
                    break
            if not img_url and imgs:
                img_url = imgs[1] if len(imgs) > 1 else imgs[0]

        if img_url:
            if img_url.startswith('//'): img_url = 'https:' + img_url
            elif img_url.startswith('/'):
                parsed = urllib.parse.urlparse(url)
                img_url = f"{parsed.scheme}://{parsed.netloc}{img_url}"

            dl = subprocess.run(
                ["curl", "-sL", "-o", str(STATIC_IMAGES/safe_name), "-w", "%{http_code}",
                 "--max-time", "15",
                 "-H", "User-Agent: Mozilla/5.0",
                 "-H", "Referer: " + url,
                 img_url],
                capture_output=True, text=True, timeout=20
            )
            if dl.stdout.strip() == "200" and (STATIC_IMAGES/safe_name).stat().st_size > 500:
                art["gambar"] = f"/static/images/{safe_name}"
                print(f"      ✅ Image OK!")
            else:
                sz = (STATIC_IMAGES/safe_name).stat().st_size if (STATIC_IMAGES/safe_name).exists() else 0
                (STATIC_IMAGES/safe_name).unlink(missing_ok=True)
                print(f"      ❌ HTTP {dl.stdout.strip()}, size={sz}")
        else:
            print(f"      ⚠️  No image found")
    except Exception as e:
        print(f"      ❌ Error: {e}")
    time.sleep(0.5)

# Now generate SVG fallbacks for remaining articles without images
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
    path = STATIC_IMAGES / fn
    path.write_text(svg)
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

urls = sum(1 for b in berita if b.get("url","").startswith('http') and 'example.com' not in b.get("url",""))
imgs = sum(1 for b in berita if b.get("gambar"))
real_imgs = sum(1 for b in berita if b.get("gambar","").endswith('.jpg'))
svg_imgs = sum(1 for b in berita if b.get("gambar","").endswith('.svg'))
cats = {}
for b in berita: cats[b["kategori"]] = cats.get(b["kategori"], 0) + 1

print(f"\n✅ Selesai! {len(berita)} berita")
print(f"🔗 {urls} URL real")
print(f"📸 {imgs} gambar ({real_imgs} real foto, {svg_imgs} SVG)")
print(f"📊 {json.dumps(cats, indent=2)}")
print(f"⏰ Contoh tanggal:")
for b in berita[:5]:
    print(f"   {b['tanggal']} | {b['judul'][:60]}")
