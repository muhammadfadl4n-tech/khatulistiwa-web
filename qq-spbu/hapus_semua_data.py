#!/usr/bin/env python3
"""Hapus semua data SPBU, laporan, uploads"""
import os, sys, shutil
sys.path.insert(0, os.path.dirname(__file__))
os.environ['FLASK_ENV'] = 'production'
os.environ['DATABASE_URL'] = 'postgresql://qqspbu:qqspbu2026@localhost:5432/qqspbu'
os.environ['SECRET_KEY'] = 'qq-spbu-secret-key-2026-kalbar'
from app import app
from models import db, SPBU, User, Laporan, Upload

with app.app_context():
    print('SEBELUM:')
    print(f'  SPBU: {SPBU.query.count()}')
    print(f'  Users: {User.query.count()}')
    print(f'  Laporan: {Laporan.query.count()}')
    print(f'  Uploads: {Upload.query.count()}')
    
    # Delete upload files from disk
    upload_dir = os.path.join(os.path.dirname(__file__), 'uploads')
    if os.path.exists(upload_dir):
        for item in os.listdir(upload_dir):
            item_path = os.path.join(upload_dir, item)
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
        print('  Upload files: deleted')
    
    Upload.query.delete()
    Laporan.query.delete()
    User.query.filter_by(role='spbu').delete()
    # Nullify SPBU references on remaining users
    for u in User.query.filter(User.id_spbu.isnot(None)).all():
        u.id_spbu = None
    db.session.commit()
    SPBU.query.delete()
    db.session.commit()
    
    print()
    print('SESUDAH:')
    print(f'  SPBU: {SPBU.query.count()}')
    print(f'  Users: {User.query.count()}')
    print(f'  Laporan: {Laporan.query.count()}')
    print(f'  Uploads: {Upload.query.count()}')
    for u in User.query.all():
        print(f'  User: {u.username} ({u.role})')
