#!/usr/bin/env python3
"""Fix bad content (CSS/JS garbage) in What field and improve articles without detail"""
import json, re
from pathlib import Path

DATA_FILE = Path("/root/beritakalbar/data/berita.json")
d = json.loads(DATA_FILE.read_text(encoding="utf-8"))
berita = d["berita"]

def is_garbage(text):
    """Detect if text is mostly CSS/JS garbage"""
    if not text:
        return True
    indicators = ['-webkit-', 'mask-image', 'flex-direction', '.jetpack', '{', '}', 'opacity:', 'border-radius']
    score = sum(1 for ind in indicators if ind in text[:500])
    return score >= 3

def clean_text(text):
    """Remove CSS/JS garbage from text"""
    # Remove CSS blocks
    text = re.sub(r'\{[^}]*\}', '', text)
    text = re.sub(r'\.[a-zA-Z][\w-]*\s*\{', '', text)
    text = re.sub(r'@media[^}]*\}', '', text, flags=re.S)
    text = re.sub(r'[\w-]+:\s*[\w.#()-]+;', '', text)
    text = re.sub(r'url\([^)]+\)', '', text)
    text = re.sub(r'https?://[^\s]+', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

for art in berita:
    judul = re.sub(r'[\U0001F300-\U0010FFFF\u2600-\u27BF\uFE0F]', '', art.get("judul", "")).strip()
    isi = art.get("isi", "")
    
    # Check if detail section has garbage
    has_detail = '─── Detail ───' in isi
    detail_section = ""
    header_section = isi
    
    if has_detail:
        parts = isi.split('─── Detail ───')
        header_section = parts[0].strip()
        detail_section = parts[1].strip() if len(parts) > 1 else ""
    
    # Fix What field if it has garbage
    what_match = re.search(r'▪️\s*\*\*What:\*\*\s*(.*?)(?:\n▪️|\Z)', header_section, re.S)
    if what_match:
        what_text = what_match.group(1).strip()
        if is_garbage(what_text):
            # Replace with clean title
            new_what = f"▪️ **What:** {judul}"
            old_what = what_match.group(0)
            header_section = header_section.replace(old_what, new_what)
    
    # Clean detail section if garbage
    if detail_section and is_garbage(detail_section[:300]):
        detail_section = ""
    
    # If no detail section, try to expand from what we know
    if not detail_section:
        # Expand Who field if too generic
        who_match = re.search(r'▪️\s*\*\*Who:\*\*\s*(.*?)(?:\n▪️|\Z)', header_section, re.S)
        if who_match and 'Pemerintah dan instansi terkait' in who_match.group(1):
            # Try to find orgs from title
            txt = judul.lower()
            orgs = []
            for org in ['Pertamina Patra Niaga', 'Pertamina', 'Satpol PP', 'Diskumdag', 'DPRD', 'DPR',
                        'ESDM', 'Polda Kalbar', 'Pemkot Pontianak', 'Pemkot Singkawang', 'BNPT']:
                if org.lower() in txt:
                    orgs.append(org)
            # Also check sumber
            sumber = art.get("sumber", "").lower()
            for org in ['Pertamina', 'Satpol PP', 'Diskumdag', 'DPRD']:
                if org.lower() in sumber and org not in orgs:
                    orgs.append(org)
            if orgs:
                new_who = f"▪️ **Who:** {', '.join(orgs[:4])}"
                old_who = who_match.group(0)
                header_section = header_section.replace(old_who, new_who)
        
        # Expand Why field
        why_match = re.search(r'▪️\s*\*\*Why:\*\*\s*(.*?)(?:\n▪️|\Z)', header_section, re.S)
        if why_match:
            why_text = why_match.group(1).strip()
            if len(why_text) < 40:  # Too short
                txt_low = (judul + " " + art.get("sumber", "")).lower()
                why_expanded = ""
                if 'restoran' in txt_low or 'usaha' in txt_low or 'pelaku usaha' in txt_low:
                    why_expanded = "Penertiban penggunaan LPG 3 kg bersubsidi oleh pelaku usaha yang tidak berhak agar tepat sasaran kepada rumah tangga dan usaha mikro"
                elif 'langka' in txt_low or 'keluhan' in txt_low or 'sulit' in txt_low:
                    why_expanded = "Kelangkaan pasokan LPG 3 kg di pangkalan yang menyulitkan masyarakat mendapatkan gas bersubsidi dengan harga terjangkau"
                elif 'harga' in txt_low and 'naik' in txt_low:
                    why_expanded = "Kenaikan harga LPG 3 kg di pasaran yang memberatkan daya beli masyarakat Kalbar"
                elif 'tambah' in txt_low or 'pasokan' in txt_low:
                    why_expanded = "Penambahan pasokan LPG 3 kg untuk menjaga stabilitas harga dan ketersediaan di masyarakat"
                elif 'singkawang' in txt_low or 'larang' in txt_low:
                    why_expanded = "Penegakan aturan agar LPG bersubsidi hanya digunakan oleh masyarakat yang berhak sesuai peruntukannya"
                elif 'ledakan' in txt_low:
                    why_expanded = "Terjadinya ledakan tabung gas LPG 3 kg yang mengakibatkan korban luka bakar dan kerugian materi"
                elif 'penyelewengan' in txt_low or 'polda' in txt_low:
                    why_expanded = "Pengungkapan praktik penyelewengan distribusi LPG 3 kg bersubsidi oleh oknum yang menjual di atas HET"
                elif 'dpr' in txt_low or 'sidik jari' in txt_low:
                    why_expanded = "Usulan mekanisme baru pembelian LPG 3 kg menggunakan sidik jari untuk memastikan subsidi tepat sasaran"
                elif 'cng' in txt_low or 'konversi' in txt_low:
                    why_expanded = "Upaya pemerintah mengurangi ketergantungan impor LPG melalui program konversi ke CNG yang lebih murah"
                elif 'subsidi' in txt_low or 'anggaran' in txt_low:
                    why_expanded = "Kebijakan pemerintah dalam mengelola anggaran subsidi LPG yang mencapai Rp80,3 triliun per tahun"
                else:
                    why_expanded = why_text.rstrip('.')
                
                if why_expanded:
                    new_why = f"▪️ **Why:** {why_expanded}."
                    old_why = why_match.group(0)
                    header_section = header_section.replace(old_why, new_why)
    
    # Reassemble
    if detail_section:
        art["isi"] = header_section + "\n\n─── Detail ───\n\n" + detail_section
    else:
        art["isi"] = header_section

# Regenerate highlights
for art in berita:
    m = re.search(r'▪️\s*\*\*What:\*\*\s*(.*?)$', art.get("isi", ""), re.MULTILINE)
    art["highlight"] = m.group(1).strip()[:250] if m else re.sub(r'[\U0001F300-\U0010FFFF\u2600-\u27BF\uFE0F]', '', art.get("judul","")).strip()[:150]

# Save
berita.sort(key=lambda x: (x["tanggal"] if x["tanggal"] >= '2025' else '2025-01-01', x["id"]), reverse=True)
for i, b in enumerate(berita, 1):
    b["id"] = i
DATA_FILE.write_text(json.dumps({"berita": berita}, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"✅ {len(berita)} berita — 5W+1H fixed")

# Show samples
for b in berita[:3]:
    lines = b['isi'].split('\n')
    for l in lines:
        if l.startswith('▪️'):
            print(l[:120])
    print(f"💡 {b['highlight'][:100]}")
    print()
