#!/usr/bin/env python3
"""Rapikan nomor SPBU - satu per satu"""
import os, sys, re
sys.path.insert(0, os.path.dirname(__file__))
os.environ['FLASK_ENV'] = 'production'
os.environ['DATABASE_URL'] = 'postgresql://qqspbu:qqspbu2026@localhost:5432/qqspbu'
os.environ['SECRET_KEY'] = 'qq-spbu-secret-key-2026-kalbar'
from app import app
from models import db, SPBU

with app.app_context():
    all_spbu = list(SPBU.query.order_by(SPBU.id).all())
    used = {s.nomor_spbu for s in all_spbu}
    changes = 0
    
    for s in all_spbu:
        old = s.nomor_spbu
        digits = re.sub(r'[^0-9]', '', str(old))
        if not digits:
            continue
        
        if len(digits) == 7:
            new = f"{digits[:2]}.{digits[2:5]}.{digits[5:]}"
        elif len(digits) == 8:
            new = f"{digits[:2]}.{digits[2:5]}.{digits[5:]}"
        elif len(digits) == 6:
            new = f"{digits[:1]}.{digits[1:4]}.{digits[4:]}"
        else:
            new = digits
        
        if new == old:
            continue
        
        # Remove old from used, check new
        used.discard(old)
        if new in used:
            sfx = 2
            while f"{new}.{sfx}" in used:
                sfx += 1
            new = f"{new}.{sfx}"
        
        s.nomor_spbu = new
        used.add(new)
        db.session.commit()
        changes += 1
        print(f"  ID {s.id:3d}: '{old}' → '{new}'")
    
    print(f"\n✅ {changes} nomor SPBU dirapikan")
