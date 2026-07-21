#!/usr/bin/env python3
"""
Import akun SPBU dari file Excel.
Baca template_akun_spbu.xlsx, buat SPBU + User sekaligus.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

os.environ['FLASK_ENV'] = 'production'
os.environ['DATABASE_URL'] = 'postgresql://qqspbu:qqspbu2026@localhost:5432/qqspbu'
os.environ['SECRET_KEY'] = 'qq-spbu-secret-key-2026-kalbar'

from app import app
from models import db, SPBU, User

EXCEL_FILE = os.path.join(os.path.dirname(__file__), "template_akun_spbu.xlsx")

def import_akun():
    import openpyxl
    if not os.path.exists(EXCEL_FILE):
        print(f"ERROR: File '{EXCEL_FILE}' tidak ditemukan!")
        print("Isi dulu file template_akun_spbu.xlsx, lalu jalankan script ini lagi.")
        return False

    wb = openpyxl.load_workbook(EXCEL_FILE)
    ws = wb.active

    success = 0
    errors = []

    with app.app_context():
        for row in ws.iter_rows(min_row=2, values_only=True):
            nomor_spbu, nama_pt, kota, alamat, lat, lng, username, password, nama_lengkap = row

            # Skip empty rows
            if not nomor_spbu or not str(nomor_spbu).strip():
                continue

            nomor_spbu = str(nomor_spbu).strip()
            nama_pt = str(nama_pt or '').strip()
            kota = str(kota or '').strip()
            username = str(username or '').strip()
            password = str(password or '').strip()
            nama_lengkap = str(nama_lengkap or '').strip()

            # Validate required fields
            missing = []
            if not nama_pt: missing.append('Nama PT')
            if not kota: missing.append('Kota')
            if not username: missing.append('Username')
            if not password: missing.append('Password')
            if not nama_lengkap: missing.append('Nama Lengkap')

            if missing:
                errors.append(f"Row {nomor_spbu}: field wajib kosong: {', '.join(missing)}")
                continue

            try:
                # Check duplicate SPBU
                existing_spbu = SPBU.query.filter_by(nomor_spbu=nomor_spbu).first()
                if existing_spbu:
                    errors.append(f"SPBU {nomor_spbu} sudah ada, skip")
                    continue

                # Check duplicate username
                existing_user = User.query.filter_by(username=username).first()
                if existing_user:
                    errors.append(f"Username '{username}' sudah ada, skip")
                    continue

                # Create SPBU
                spbu = SPBU(
                    nama_pt=nama_pt,
                    nomor_spbu=nomor_spbu,
                    kota=kota,
                    alamat=alamat or None,
                    lat=float(lat) if lat else None,
                    lng=float(lng) if lng else None,
                )
                db.session.add(spbu)
                db.session.flush()  # Get spbu.id

                # Create User
                user = User(
                    username=username,
                    nama_lengkap=nama_lengkap,
                    role='spbu',
                    id_spbu=spbu.id,
                )
                user.set_password(password)
                db.session.add(user)
                db.session.commit()

                success += 1
                print(f"  ✅ {nomor_spbu} - {nama_pt} → user: {username}")

            except Exception as e:
                db.session.rollback()
                errors.append(f"{nomor_spbu}: {str(e)}")

    print(f"\n=== HASIL ===")
    print(f"Berhasil: {success} akun SPBU")
    if errors:
        print(f"Gagal/Skip: {len(errors)}")
        for e in errors:
            print(f"  ⚠️  {e}")
    print(f"\nFile excel: {EXCEL_FILE}")
    return success > 0

if __name__ == '__main__':
    import_akun()
