#!/usr/bin/env python3
"""
Background photo downloader for QQ SPBU import.
Downloads Google Drive photos and creates Upload records.
"""
import os, sys, re, time, json, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
os.environ['FLASK_ENV'] = 'production'
os.environ['DATABASE_URL'] = 'postgresql://qqspbu:qqspbu2026@localhost:5432/qqspbu'
os.environ['SECRET_KEY'] = 'qq-spbu-secret-key-2026-kalbar'

from app import app
from models import db, SPBU, User, Laporan, Upload
from datetime import datetime
import openpyxl

EXCEL = '/root/.hermes/cache/documents/doc_49ca0b261285_Laporan_Pembongkaran_dan_Penerimaan_BBM_di_SPBU_MTD_14_Juli_2026.xlsx'
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'uploads')
BATCH_SIZE = 50
STATUS_FILE = os.path.join(os.path.dirname(__file__), 'import_status.json')

def extract_id(url):
    m = re.search(r'id=([a-zA-Z0-9_-]+)', str(url)) or re.search(r'/d/([a-zA-Z0-9_-]+)', str(url))
    return m.group(1) if m else None

def download(file_id, path):
    for url in [
        f'https://drive.google.com/uc?export=download&id={file_id}',
        f'https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t'
    ]:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as resp:
                with open(path, 'wb') as f:
                    f.write(resp.read())
            return True
        except: pass
    return False

def compress_image(src, dst, max_dim=1920, quality=80):
    try:
        from PIL import Image
        img = Image.open(src)
        if img.mode in ('RGBA', 'P'): img = img.convert('RGB')
        if max(img.size) > max_dim:
            ratio = max_dim / max(img.size)
            img = img.resize((int(img.size[0]*ratio), int(img.size[1]*ratio)), Image.LANCZOS)
        img.save(dst, 'JPEG', quality=quality)
        return True
    except: return False

def load_status():
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE) as f: return json.load(f)
    return {'processed': 0, 'success': 0, 'failed': 0, 'skipped': 0, 'errors': []}

def save_status(s):
    with open(STATUS_FILE, 'w') as f: json.dump(s, f)

def run():
    status = load_status()
    start_row = status.get('last_row', 2)
    
    wb = openpyxl.load_workbook(EXCEL)
    ws = wb['Form Responses 1']
    
    with app.app_context():
        spbu_map = {s.nomor_spbu: s for s in SPBU.query.all()}
        
        for idx, row in enumerate(ws.iter_rows(min_row=start_row, values_only=True), start_row):
            ts, nama_pt, nomor_spbu, kota, *rest = row
            if isinstance(nomor_spbu, (int, float)): nomor_spbu = str(int(nomor_spbu))
            else: nomor_spbu = str(nomor_spbu or '').strip()
            
            tanggal = ts.date() if isinstance(ts, datetime) else datetime.now().date()
            
            spbu = spbu_map.get(nomor_spbu)
            if not spbu: continue
            
            laporan = Laporan.query.filter_by(id_spbu=spbu.id, tanggal=tanggal).first()
            if not laporan: continue
            
            categories = ['pembongkaran', 'spp', 'dipping', 'atg']
            for ci, cat in enumerate(categories):
                url_str = str(rest[ci] or '') if ci < len(rest) else ''
                if not url_str: continue
                
                urls = re.split(r'[,\n\r]+', url_str)
                for single_url in urls:
                    single_url = single_url.strip()
                    file_id = extract_id(single_url)
                    if not file_id: continue
                    
                    status['processed'] += 1
                    
                    # Check if already uploaded
                    existing = Upload.query.filter(
                        Upload.id_laporan == laporan.id,
                        Upload.kategori == cat,
                        Upload.path.contains(file_id[:12])
                    ).first()
                    if existing:
                        status['skipped'] += 1
                        continue
                    
                    # Download
                    temp_dir = os.path.join(UPLOAD_DIR, str(laporan.id))
                    os.makedirs(temp_dir, exist_ok=True)
                    temp_path = os.path.join(temp_dir, f'temp_{file_id}.jpg')
                    
                    if not os.path.exists(temp_path) or os.path.getsize(temp_path) < 100:
                        ok = download(file_id, temp_path)
                        if not ok:
                            status['failed'] += 1
                            status['errors'].append(f'Row {idx}: download fail {file_id[:16]}')
                            continue
                    
                    # Compress & create upload record
                    try:
                        out_name = f'{cat}_{file_id[:10]}.jpg'
                        out_path = os.path.join(temp_dir, out_name)
                        compress_image(temp_path, out_path)
                        
                        upload = Upload(
                            id_laporan=laporan.id,
                            kategori=cat,
                            filename=out_name,
                            path=f'{laporan.id}/{out_name}',
                        )
                        db.session.add(upload)
                        db.session.commit()
                        status['success'] += 1
                    except Exception as e:
                        db.session.rollback()
                        status['failed'] += 1
                        status['errors'].append(f'Row {idx}: {str(e)[:80]}')
            
            status['last_row'] = idx
            
            if idx % 50 == 0:
                save_status(status)
                elapsed = time.time() - start_time
                rate = status['processed'] / elapsed if elapsed > 0 else 0
                print(f'[Row {idx}] Processed:{status["processed"]} OK:{status["success"]} Fail:{status["failed"]} Skip:{status["skipped"]} Rate:{rate:.1f}/s')
        
        save_status(status)
        print(f'\n=== DONE ===')
        print(f'Processed: {status["processed"]}')
        print(f'Success: {status["success"]}')
        print(f'Failed: {status["failed"]}')
        print(f'Skipped: {status["skipped"]}')

start_time = time.time()
run()
