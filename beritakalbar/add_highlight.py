#!/usr/bin/env python3
"""Add clean 'highlight' (What) field to each article"""
import json, re
from pathlib import Path

DATA_FILE = Path("/root/beritakalbar/data/berita.json")
d = json.loads(DATA_FILE.read_text(encoding="utf-8"))
berita = d["berita"]

def extract_what(isi, title):
    """Extract the 'What' - first clean factual sentence"""
    # Clean
    text = isi
    
    # Remove markdown tables (lines with | --- | pattern)
    text = re.sub(r'\|[^\n]+\|', '', text)
    
    # Remove emojis
    text = re.sub(r'[\U0001F300-\U0010FFFF\u2600-\u27BF\uFE0F]', '', text)
    
    # Remove ** markdown bold
    text = re.sub(r'\*\*', '', text)
    
    # Remove --- separators
    text = re.sub(r'\n---+\n', '\n', text)
    
    # Remove ### headers
    text = re.sub(r'^#+\s+.*$', '', text, flags=re.MULTILINE)
    
    # Remove leading source prefix like "📰 Tribun Pontianak (12 Jul 2026) —"
    text = re.sub(r'^[📰📅🔗🟢🔴🟡💡🔵]\s*', '', text)
    text = re.sub(r'^[A-Za-z\s]+\(\d+\s+[A-Za-z]+\s+\d+\)\s*[—–-]\s*', '', text)
    
    # Clean whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'^,\s*', '', text)
    
    if not text:
        # Fallback to title
        t = re.sub(r'[\U0001F300-\U0010FFFF\u2600-\u27BF\uFE0F]', '', title).strip()
        return t[:150]
    
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    # Find the best first factual sentence
    seen = set()
    for s in sentences:
        s = s.strip()
        if not s or len(s) < 25:
            continue
        
        # Skip if it's still metadata or a continuation
        if re.match(r'^(sementara|adapun|selain|sedangkan|menurut|dilansir|merujuk|salah|dengan|untuk|dan|atau|ini|bahwa)', s.lower()):
            continue
        
        # Remove leading comma/connector if it's mid-sentence
        s = re.sub(r'^[,;]\s*', '', s)
        s = s.strip()
        
        if s and len(s) >= 25:
            if len(s) > 250:
                s = s[:247] + '...'
            if s not in seen:
                seen.add(s)
                return s
    
    # Fallback: first long enough sentence
    for s in sentences:
        s = s.strip()
        if len(s) > 40:
            if len(s) > 250:
                s = s[:247] + '...'
            return s
    
    return text[:150]

for art in berita:
    isi = art.get("isi", "")
    title = art.get("judul", "")
    art["highlight"] = extract_what(isi, title)

DATA_FILE.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"✅ {len(berita)} highlights updated")
for b in berita[:10]:
    print(f"\n📰 {b['judul'][:55]}")
    print(f"   💡 {b['highlight'][:120]}")
