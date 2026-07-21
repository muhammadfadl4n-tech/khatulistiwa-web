"""
Aplikasi Laporan Pembongkaran BBM SPBU
Flask backend dengan SQLite database, authentication, dan file upload.
"""

import os
from datetime import datetime, date, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from functools import wraps

from config import config
from models import db, User, SPBU, Laporan, Upload
from utils import (
    save_upload, allowed_file, role_required, spbu_owner_required,
    export_spbu_to_excel, export_users_to_excel,
    generate_spbu_template, generate_user_template,
    import_spbu_from_excel, import_users_from_excel
)

# ============================================================
# APP INITIALIZATION
# ============================================================

app = Flask(__name__)

# Use environment variable to determine config
env = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(config[env])

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize extensions
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
login_manager.session_protection = 'strong'
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

# ============================================================
# CONSTANTS
# ============================================================

KABUPATEN_KALBAR = [
    'Pontianak', 'Singkawang', 'Kubu Raya', 'Mempawah', 'Sambas',
    'Bengkayang', 'Landak', 'Sanggau', 'Sekadau', 'Sintang',
    'Melawi', 'Kapuas Hulu', 'Kayong Utara', 'Ketapang'
]

JENIS_BBM = ['Biosolar', 'Pertalite', 'Pertamax', 'Pertamax Turbo', 'Dexlite', 'Dex']

# ============================================================
# LOGIN MANAGER
# ============================================================

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ============================================================
# CONTEXT PROCESSOR
# ============================================================

@app.context_processor
def inject_globals():
    """Inject global variables for all templates."""
    return {
        'kabupaten_list': KABUPATEN_KALBAR,
        'jenis_bbm_list': JENIS_BBM,
    }

# ============================================================
# SEED DATA
# ============================================================

def seed_data():
    """Seed initial data ke database."""
    # Check jika sudah ada data
    if User.query.first():
        return
    
    print("Seeding database...")
    
    # Create SPBU data (only 1 demo SPBU)
    spbu_data = [
        {'nama_pt': 'SPBU 61.781.01', 'nomor_spbu': '61.781.01', 'kota': 'Pontianak', 'alamat': 'Jl. Demo SPBU No. 1', 'lat': -0.0263, 'lng': 109.3425},
    ]
    
    spbu_list = []
    for data in spbu_data:
        spbu = SPBU(**data)
        db.session.add(spbu)
        spbu_list.append(spbu)
    
    db.session.flush()  # Get IDs
    
    # Create users
    users_data = [
        {'username': 'admin', 'nama_lengkap': 'Administrator', 'role': 'administrator', 'email': 'admin@bbm.com', 'password': 'admin123'},
        {'username': 'pertamina', 'nama_lengkap': 'Budi Pertamina', 'role': 'pertamina', 'email': 'budi@pertamina.com', 'password': 'pertamina123'},
        {'username': 'spbu01', 'nama_lengkap': 'Operator SPBU 61.781.01', 'role': 'spbu', 'id_spbu': spbu_list[0].id, 'email': 'spbu6178101@bbm.com', 'password': 'spbu123'},
    ]
    
    for data in users_data:
        user = User(
            username=data['username'],
            nama_lengkap=data['nama_lengkap'],
            role=data['role'],
            email=data['email'],
            id_spbu=data.get('id_spbu'),
        )
        user.set_password(data['password'])
        db.session.add(user)
    
    db.session.flush()
    
    # Create sample laporan
    import random
    statuses = ['draft', 'submitted', 'verified']
    base_date = datetime.now().date()
    
    # Get the single demo SPBU and its user
    demo_spbu = spbu_list[0]
    spbu_user = User.query.filter_by(id_spbu=demo_spbu.id).first()
    
    for i in range(20):
        tanggal = base_date - timedelta(days=random.randint(0, 60))
        status = random.choice(statuses)
        jenis = random.sample(JENIS_BBM, random.randint(1, 4))
        
        laporan = Laporan(
            id_spbu=demo_spbu.id,
            id_user=spbu_user.id if spbu_user else 3,
            tanggal=tanggal,
            jenis_bbm=jenis,
            status=status,
            catatan=random.choice(['Tidak ada catatan', 'Pembongkaran berjalan lancar', 'Cuaca hujan saat pembongkaran', '']),
        )
        db.session.add(laporan)
    
    db.session.commit()
    print("Database seeded successfully!")
    print("  Default users:")
    print("    admin / admin123 (Administrator)")
    print("    pertamina / pertamina123 (Pertamina)")
    print("    spbu01 / spbu123 (SPBU - SPBU 61.781.01)")

# ============================================================
# AUTH ROUTES
# ============================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=remember)
            
            # Update last login
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            flash(f'Selamat datang, {user.nama_lengkap}!', 'success')
            
            # Redirect berdasarkan role
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            if user.role == 'spbu':
                return redirect(url_for('laporan_baru'))
            return redirect(url_for('dashboard'))
        
        flash('Username atau password salah', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Anda telah logout', 'info')
    return redirect(url_for('login'))

@app.route('/daftar', methods=['GET', 'POST'])
def daftar():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        nomor_spbu = request.form.get('nomor_spbu', '').strip()
        nama_pt = request.form.get('nama_pt', '').strip().upper()
        kota = request.form.get('kota', '').strip().title()
        alamat = request.form.get('alamat', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        nama_lengkap = request.form.get('nama_lengkap', '').strip()
        email = request.form.get('email', '').strip()
        
        # Validation
        errors = []
        if not nomor_spbu: errors.append('Nomor SPBU wajib diisi')
        if not nama_pt: errors.append('Nama PT wajib diisi')
        if not kota: errors.append('Kota wajib diisi')
        if not username: errors.append('Username wajib diisi')
        if not nama_lengkap: errors.append('Nama lengkap wajib diisi')
        if len(password) < 6: errors.append('Password minimal 6 karakter')
        if password != password_confirm: errors.append('Konfirmasi password tidak cocok')
        
        if User.query.filter_by(username=username).first():
            errors.append('Username sudah terdaftar')
        
        if not errors:
            # Create or find SPBU
            spbu = SPBU.query.filter_by(nomor_spbu=nomor_spbu).first()
            if not spbu:
                spbu = SPBU(
                    nomor_spbu=nomor_spbu, nama_pt=nama_pt,
                    kota=kota, alamat=alamat or None
                )
                db.session.add(spbu)
                db.session.flush()
            
            # Create user
            user = User(
                username=username, nama_lengkap=nama_lengkap,
                email=email or None, role='spbu', id_spbu=spbu.id
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            flash('Akun berhasil dibuat! Silakan login.', 'success')
            return redirect(url_for('login'))
        
        for e in errors:
            flash(e, 'error')
    
    return render_template('daftar.html', kabupaten_list=KABUPATEN_KALBAR)

# ============================================================
# INDEX ROUTE
# ============================================================

@app.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    if current_user.role == 'spbu':
        return redirect(url_for('laporan_baru'))
    return redirect(url_for('dashboard'))

# ============================================================
# DASHBOARD ROUTES
# ============================================================

@app.route('/dashboard')
@login_required
@role_required('pertamina', 'administrator')
def dashboard():
    # Hitung statistik
    total_laporan = Laporan.query.count()
    
    start_of_month = date.today().replace(day=1)
    laporan_bulan_ini = Laporan.query.filter(Laporan.tanggal >= start_of_month).count()
    
    spbu_aktif = db.session.query(Laporan.id_spbu).filter(
        Laporan.status == 'submitted'
    ).distinct().count()
    
    total_foto = Upload.query.count()
    
    # Data chart - tren 30 hari
    tren_labels = []
    tren_data = []
    for i in range(29, -1, -1):
        d = date.today() - timedelta(days=i)
        label = d.strftime('%d %b')
        count = Laporan.query.filter(Laporan.tanggal == d).count()
        tren_labels.append(label)
        tren_data.append(count)
    
    # Data chart - per kabupaten
    kota_count = {}
    laporan_all = Laporan.query.all()
    for l in laporan_all:
        if l.spbu:
            kota = l.spbu.kota
            kota_count[kota] = kota_count.get(kota, 0) + 1
    
    # Data chart - jenis BBM
    bbm_count = {}
    for l in laporan_all:
        for j in l.jenis_bbm_list:
            bbm_count[j] = bbm_count.get(j, 0) + 1
    
    # Ringkasan per SPBU
    spbu_summary = []
    for spbu in SPBU.query.limit(5).all():
        laporan_spbu = Laporan.query.filter_by(id_spbu=spbu.id).all()
        terakhir = max([l.tanggal for l in laporan_spbu], default=None)
        spbu_summary.append({
            'id': spbu.id,
            'nama_pt': spbu.nama_pt,
            'nomor_spbu': spbu.nomor_spbu,
            'kota': spbu.kota,
            'total_laporan': len(laporan_spbu),
            'terakhir_lapor': terakhir.isoformat() if terakhir else 'Belum pernah',
            'status': 'active' if len(laporan_spbu) > 0 else 'inactive',
        })
    
    # SPBU list for map
    spbu_all = SPBU.query.all()
    spbu_list_json = [s.to_dict() for s in spbu_all]
    
    return render_template('dashboard.html',
        total_laporan=total_laporan,
        laporan_bulan_ini=laporan_bulan_ini,
        spbu_aktif=spbu_aktif,
        total_foto=total_foto,
        tren_labels=tren_labels,
        tren_data=tren_data,
        kota_labels=list(kota_count.keys()),
        kota_data=list(kota_count.values()),
        bbm_labels=list(bbm_count.keys()),
        bbm_data=list(bbm_count.values()),
        spbu_summary=spbu_summary,
        spbu_list_json=spbu_list_json,
    )

# ============================================================
# LAPORAN ROUTES
# ============================================================

@app.route('/laporan')
@login_required
def laporan_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    filter_kota = request.args.get('kota', '')
    filter_status = request.args.get('status', '')
    filter_bbm = request.args.get('bbm', '')
    
    # Base query
    query = Laporan.query
    
    # SPBU hanya bisa lihat laporan miliknya
    if current_user.role == 'spbu':
        query = query.filter_by(id_spbu=current_user.id_spbu)
    
    # Apply filters
    if search:
        query = query.join(SPBU).filter(
            db.or_(
                SPBU.nama_pt.ilike(f'%{search}%'),
                SPBU.nomor_spbu.ilike(f'%{search}%')
            )
        )
    
    if filter_kota:
        query = query.join(SPBU).filter(SPBU.kota == filter_kota)
    
    if filter_status:
        query = query.filter_by(status=filter_status)
    
    if filter_bbm:
        # Filter by jenis BBM (JSON contains)
        query = query.filter(Laporan.jenis_bbm.contains(filter_bbm))
    
    # Pagination
    per_page = 10
    total = query.count()
    total_pages = (total + per_page - 1) // per_page
    laporan_list = query.order_by(Laporan.tanggal.desc()).offset((page - 1) * per_page).limit(per_page).all()
    
    # Convert to dict-like objects for template
    laporan_data = []
    for l in laporan_list:
        laporan_data.append({
            'id': l.id,
            'id_spbu': l.id_spbu,
            'nama_spbu': l.spbu.nama_pt if l.spbu else '-',
            'nomor_spbu': l.spbu.nomor_spbu if l.spbu else '-',
            'kota': l.spbu.kota if l.spbu else '-',
            'tanggal': l.tanggal.isoformat() if l.tanggal else '',
            'jenis_bbm': l.jenis_bbm_list,
            'status': l.status,
            'foto_count': l.foto_count,
            'created_at': l.created_at.strftime('%Y-%m-%d %H:%M') if l.created_at else '',
        })
    
    return render_template('laporan_list.html',
        laporan_list=laporan_data,
        page=page,
        total_pages=total_pages,
        total=total,
        search=search,
        filter_kota=filter_kota,
        filter_status=filter_status,
        filter_bbm=filter_bbm,
    )

@app.route('/laporan/export')
@login_required
def laporan_export():
    """Export laporan ke CSV — server-side, dengan filter."""
    search = request.args.get('search', '')
    filter_kota = request.args.get('kota', '')
    filter_status = request.args.get('status', '')
    filter_bbm = request.args.get('bbm', '')

    query = Laporan.query

    if current_user.role == 'spbu':
        query = query.filter_by(id_spbu=current_user.id_spbu)

    if search:
        query = query.join(SPBU).filter(
            db.or_(
                SPBU.nama_pt.ilike(f'%{search}%'),
                SPBU.nomor_spbu.ilike(f'%{search}%')
            )
        )

    if filter_kota:
        query = query.join(SPBU).filter(SPBU.kota == filter_kota)

    if filter_status:
        query = query.filter_by(status=filter_status)

    if filter_bbm:
        query = query.filter(Laporan.jenis_bbm.contains(filter_bbm))

    laporan_list = query.order_by(Laporan.tanggal.desc()).all()

    import csv, io
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Tanggal', 'SPBU', 'Nomor SPBU', 'Kota', 'Jenis BBM', 'Status', 'Foto'])

    for l in laporan_list:
        spbu = l.spbu
        writer.writerow([
            l.tanggal.isoformat() if l.tanggal else '',
            spbu.nama_pt if spbu else '-',
            spbu.nomor_spbu if spbu else '-',
            spbu.kota if spbu else '-',
            ', '.join(l.jenis_bbm_list),
            l.status,
            l.foto_count,
        ])

    output.seek(0)
    from flask import Response
    return Response(
        output.getvalue(),
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename=laporan_bbm_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
    )


@app.route('/laporan/baru', methods=['GET', 'POST'])
@login_required
@role_required('spbu')
def laporan_baru():
    spbu = SPBU.query.get(current_user.id_spbu)
    
    if not spbu:
        flash('Data SPBU tidak ditemukan untuk akun Anda', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        action = request.form.get('action', 'draft')
        tanggal_str = request.form.get('tanggal')
        jenis_bbm = request.form.getlist('jenis_bbm')
        catatan = request.form.get('catatan', '')
        
        # Validate required fields for submit
        if action == 'submit':
            errors = []
            if not tanggal_str:
                errors.append('Tanggal pembongkaran wajib diisi')
            if not jenis_bbm:
                errors.append('Pilih minimal satu jenis BBM')
            
            # Check all required uploads
            categories = ['pembongkaran', 'spp', 'dipping', 'atg']
            category_names = {
                'pembongkaran': 'Foto Pembongkaran',
                'spp': 'Foto SPP',
                'dipping': 'Foto Dipping',
                'atg': 'Foto ATG'
            }
            
            for kategori in categories:
                files = request.files.getlist(f'foto_{kategori}')
                if not files or all(not f.filename for f in files):
                    errors.append(f'{category_names[kategori]} wajib diupload')
            
            if errors:
                for error in errors:
                    flash(error, 'error')
                return render_template('spbu_form.html', spbu=spbu)
        
        # Parse tanggal
        tanggal = None
        if tanggal_str:
            tanggal = datetime.strptime(tanggal_str, '%Y-%m-%d').date()
        
        # Create laporan
        status = 'submitted' if action == 'submit' else 'draft'
        laporan = Laporan(
            id_spbu=spbu.id,
            id_user=current_user.id,
            tanggal=tanggal or date.today(),
            jenis_bbm=jenis_bbm,
            status=status,
            catatan=catatan,
        )
        db.session.add(laporan)
        db.session.flush()  # Get ID
        
        # Handle file uploads
        categories = ['pembongkaran', 'spp', 'dipping', 'atg']
        max_files = app.config.get('MAX_FILES_PER_CATEGORY', 10)

        for kategori in categories:
            files = request.files.getlist(f'foto_{kategori}')

            # Check file limit per category
            if len(files) > max_files:
                flash(f'Maksimal {max_files} file per kategori untuk {kategori}', 'error')
                files = files[:max_files]  # Only process first N files

            for file in files:
                if file and file.filename:
                    try:
                        result = save_upload(file, laporan.id, kategori)
                        if result:
                            upload = Upload(
                                id_laporan=laporan.id,
                                kategori=kategori,
                                filename=result['filename'],
                                path=result['path'],
                            )
                            db.session.add(upload)
                    except ValueError as e:
                        flash(str(e), 'error')
        
        db.session.commit()
        
        if action == 'submit':
            flash('Laporan berhasil dikirim!', 'success')
        else:
            flash('Draft berhasil disimpan', 'success')
        
        return redirect(url_for('laporan_list'))
    
    return render_template('spbu_form.html', spbu=spbu)

@app.route('/laporan/<int:id>')
@login_required
@spbu_owner_required
def laporan_detail(id):
    laporan = Laporan.query.get_or_404(id)
    spbu = laporan.spbu
    
    # Group uploads by kategori
    uploads_by_kategori = {}
    for upload in laporan.uploads:
        if upload.kategori not in uploads_by_kategori:
            uploads_by_kategori[upload.kategori] = []
        uploads_by_kategori[upload.kategori].append(upload)
    
    return render_template('laporan_detail.html',
        laporan=laporan,
        spbu=spbu,
        uploads=uploads_by_kategori,
    )

@app.route('/laporan/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@spbu_owner_required
def laporan_edit(id):
    laporan = Laporan.query.get_or_404(id)
    spbu = laporan.spbu
    
    if request.method == 'POST':
        action = request.form.get('action', 'draft')
        tanggal_str = request.form.get('tanggal')
        jenis_bbm = request.form.getlist('jenis_bbm')
        catatan = request.form.get('catatan', '')
        
        # Update laporan
        if tanggal_str:
            laporan.tanggal = datetime.strptime(tanggal_str, '%Y-%m-%d').date()
        laporan.jenis_bbm = jenis_bbm
        laporan.catatan = catatan
        
        if action == 'submit':
            laporan.status = 'submitted'
        
        # Handle new file uploads
        categories = ['pembongkaran', 'spp', 'dipping', 'atg']
        for kategori in categories:
            files = request.files.getlist(f'foto_{kategori}')
            for file in files:
                if file and file.filename:
                    try:
                        result = save_upload(file, laporan.id, kategori)
                        if result:
                            upload = Upload(
                                id_laporan=laporan.id,
                                kategori=kategori,
                                filename=result['filename'],
                                path=result['path'],
                            )
                            db.session.add(upload)
                    except ValueError as e:
                        flash(str(e), 'error')
        
        db.session.commit()
        flash('Laporan berhasil diupdate', 'success')
        return redirect(url_for('laporan_detail', id=laporan.id))
    
    return render_template('laporan_form.html', laporan=laporan, spbu=spbu, mode='edit')

@app.route('/laporan/<int:id>/verifikasi', methods=['POST'])
@login_required
@role_required('pertamina', 'administrator')
def laporan_verifikasi(id):
    laporan = Laporan.query.get_or_404(id)
    laporan.status = 'verified'
    db.session.commit()
    flash('Laporan berhasil diverifikasi', 'success')
    return redirect(url_for('laporan_detail', id=laporan.id))

@app.route('/laporan/<int:id>/hapus', methods=['POST'])
@login_required
@spbu_owner_required
def laporan_hapus(id):
    laporan = Laporan.query.get_or_404(id)
    
    # Delete associated files
    for upload in laporan.uploads:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], upload.path)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete thumbnail if exists
        upload_dir = os.path.dirname(upload.path)
        filename = os.path.basename(upload.path)
        thumb_path = os.path.join(app.config['UPLOAD_FOLDER'], upload_dir, 'thumb_' + filename)
        if os.path.exists(thumb_path):
            os.remove(thumb_path)
    
    db.session.delete(laporan)
    db.session.commit()
    flash('Laporan berhasil dihapus', 'success')
    return redirect(url_for('laporan_list'))

# ============================================================
# SPBU ROUTES
# ============================================================

@app.route('/spbu')
@login_required
@role_required('pertamina', 'administrator')
def spbu_list():
    spbu_all = SPBU.query.order_by(SPBU.kota, SPBU.nama_pt).all()
    return render_template('admin/spbu.html', spbu_list=spbu_all, kabupaten_list=KABUPATEN_KALBAR)

@app.route('/spbu/<int:id>')
@login_required
def spbu_detail(id):
    spbu = SPBU.query.get_or_404(id)
    laporan_spbu = Laporan.query.filter_by(id_spbu=spbu.id).order_by(Laporan.tanggal.desc()).all()
    
    # Convert to dict-like for template
    laporan_data = []
    for l in laporan_spbu:
        laporan_data.append({
            'id': l.id,
            'tanggal': l.tanggal.isoformat() if l.tanggal else '',
            'jenis_bbm': l.jenis_bbm_list,
            'status': l.status,
            'foto_count': l.foto_count,
        })
    
    return render_template('spbu_detail.html', spbu=spbu, laporan_list=laporan_data, kabupaten_list=KABUPATEN_KALBAR)

@app.route('/spbu/baru', methods=['POST'])
@login_required
@role_required('administrator')
def spbu_baru():
    nama_pt = request.form.get('nama_pt', '').strip()
    nomor_spbu = request.form.get('nomor_spbu', '').strip()
    kota = request.form.get('kota', '').strip()
    alamat = request.form.get('alamat', '').strip()
    lat = request.form.get('lat', type=float)
    lng = request.form.get('lng', type=float)
    
    if not all([nama_pt, nomor_spbu, kota]):
        flash('Nama PT, Nomor SPBU, dan Kota wajib diisi', 'error')
        return redirect(url_for('admin_spbu'))
    
    # Check duplicate
    if SPBU.query.filter_by(nomor_spbu=nomor_spbu).first():
        flash('Nomor SPBU sudah terdaftar', 'error')
        return redirect(url_for('admin_spbu'))
    
    spbu = SPBU(
        nama_pt=nama_pt,
        nomor_spbu=nomor_spbu,
        kota=kota,
        alamat=alamat,
        lat=lat,
        lng=lng,
    )
    db.session.add(spbu)
    db.session.commit()
    flash('SPBU berhasil ditambahkan', 'success')
    return redirect(url_for('admin_spbu'))

@app.route('/spbu/<int:id>/edit', methods=['POST'])
@login_required
@role_required('administrator', 'pertamina')
def spbu_edit(id):
    spbu = SPBU.query.get_or_404(id)
    
    spbu.nama_pt = request.form.get('nama_pt', spbu.nama_pt).strip()
    spbu.kota = request.form.get('kota', spbu.kota).strip()
    spbu.alamat = request.form.get('alamat', spbu.alamat or '').strip()
    
    lat = request.form.get('lat', type=float)
    lng = request.form.get('lng', type=float)
    if lat is not None:
        spbu.lat = lat
    if lng is not None:
        spbu.lng = lng
    
    db.session.commit()
    flash('SPBU berhasil diupdate', 'success')
    return redirect(url_for('spbu_detail', id=spbu.id))

# ============================================================
# ADMIN USER ROUTES
# ============================================================

@app.route('/admin/users')
@login_required
@role_required('administrator')
def admin_users():
    users = User.query.order_by(User.role, User.nama_lengkap).all()
    spbu_all = SPBU.query.order_by(SPBU.nama_pt).all()
    return render_template('admin/users.html', users=users, spbu_list=spbu_all)

@app.route('/admin/users/baru', methods=['POST'])
@login_required
@role_required('administrator')
def admin_users_baru():
    username = request.form.get('username', '').strip()
    nama_lengkap = request.form.get('nama_lengkap', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    role = request.form.get('role', 'spbu')
    id_spbu = request.form.get('id_spbu', type=int)
    
    if not all([username, nama_lengkap, password]):
        flash('Username, nama lengkap, dan password wajib diisi', 'error')
        return redirect(url_for('admin_users'))
    
    # Check duplicate
    if User.query.filter_by(username=username).first():
        flash('Username sudah terdaftar', 'error')
        return redirect(url_for('admin_users'))
    
    user = User(
        username=username,
        nama_lengkap=nama_lengkap,
        email=email,
        role=role,
        id_spbu=id_spbu if role == 'spbu' else None,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    flash('User berhasil ditambahkan', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:id>/edit', methods=['POST'])
@login_required
@role_required('administrator')
def admin_users_edit(id):
    user = User.query.get_or_404(id)
    
    user.nama_lengkap = request.form.get('nama_lengkap', user.nama_lengkap).strip()
    user.email = request.form.get('email', user.email or '').strip()
    user.role = request.form.get('role', user.role)
    
    if user.role == 'spbu':
        user.id_spbu = request.form.get('id_spbu', type=int)
    else:
        user.id_spbu = None
    
    password = request.form.get('password', '')
    if password:
        user.set_password(password)
    
    db.session.commit()
    flash('User berhasil diupdate', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:id>/toggle', methods=['POST'])
@login_required
@role_required('administrator')
def admin_users_toggle(id):
    user = User.query.get_or_404(id)
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'diaktifkan' if user.is_active else 'dinonaktifkan'
    flash(f'User {user.username} berhasil {status}', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:id>/reset-password', methods=['POST'])
@login_required
@role_required('administrator')
def admin_users_reset_password(id):
    user = User.query.get_or_404(id)
    new_password = request.form.get('new_password', 'password123')
    user.set_password(new_password)
    db.session.commit()
    flash(f'Password user {user.username} berhasil direset', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/spbu')
@login_required
@role_required('administrator')
def admin_spbu():
    spbu_all = SPBU.query.order_by(SPBU.kota, SPBU.nama_pt).all()
    return render_template('admin/spbu.html', spbu_list=spbu_all, kabupaten_list=KABUPATEN_KALBAR)

@app.route('/spbu/<int:id>/hapus', methods=['POST'])
@login_required
@role_required('administrator')
def spbu_hapus(id):
    spbu = SPBU.query.get_or_404(id)
    nama = spbu.nama_pt
    
    # Delete related users
    for user in User.query.filter_by(id_spbu=id).all():
        db.session.delete(user)
    
    # Delete related laporan and uploads
    for laporan in Laporan.query.filter_by(id_spbu=id).all():
        for upload in laporan.uploads:
            if upload.path:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], upload.path)
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except: pass
        db.session.delete(laporan)
    
    db.session.delete(spbu)
    db.session.commit()
    flash(f'SPBU {nama} dan semua data terkait berhasil dihapus', 'success')
    return redirect(url_for('admin_spbu'))

@app.route('/admin/users/<int:id>/hapus', methods=['POST'])
@login_required
@role_required('administrator')
def admin_users_hapus(id):
    user = User.query.get_or_404(id)
    if user.role == 'administrator':
        flash('Tidak bisa menghapus administrator', 'error')
        return redirect(url_for('admin_users'))
    username = user.username
    db.session.delete(user)
    db.session.commit()
    flash(f'User {username} berhasil dihapus', 'success')
    return redirect(url_for('admin_users'))

# ============================================================
# EXPORT/IMPORT EXCEL (ADMIN ONLY)
# ============================================================

@app.route('/admin/export/spbu')
@login_required
@role_required('administrator')
def export_spbu_excel():
    """Export data SPBU ke Excel."""
    spbu_list = SPBU.query.order_by(SPBU.kota, SPBU.nama_pt).all()
    excel_file = export_spbu_to_excel(spbu_list)
    
    filename = f"Data_SPBU_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return send_file(
        excel_file,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

@app.route('/admin/export/users')
@login_required
@role_required('administrator')
def export_users_excel():
    """Export data User ke Excel."""
    user_list = User.query.order_by(User.role, User.username).all()
    excel_file = export_users_to_excel(user_list)
    
    filename = f"Data_User_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return send_file(
        excel_file,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

@app.route('/admin/template/spbu')
@login_required
@role_required('administrator')
def template_spbu():
    """Download template Excel untuk import SPBU."""
    template_file = generate_spbu_template()
    return send_file(
        template_file,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='Template_Import_SPBU.xlsx'
    )

@app.route('/admin/template/users')
@login_required
@role_required('administrator')
def template_users():
    """Download template Excel untuk import User."""
    template_file = generate_user_template()
    return send_file(
        template_file,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='Template_Import_User.xlsx'
    )

@app.route('/admin/import/spbu', methods=['POST'])
@login_required
@role_required('administrator')
def import_spbu_excel():
    """Import data SPBU dari Excel."""
    if 'file' not in request.files:
        flash('Tidak ada file yang diupload', 'error')
        return redirect(url_for('admin_spbu'))
    
    file = request.files['file']
    if file.filename == '':
        flash('Tidak ada file yang dipilih', 'error')
        return redirect(url_for('admin_spbu'))
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        flash('File harus berformat Excel (.xlsx)', 'error')
        return redirect(url_for('admin_spbu'))
    
    try:
        success_count, error_list = import_spbu_from_excel(file)
        
        if success_count > 0:
            flash(f'Berhasil import {success_count} data SPBU', 'success')
        
        if error_list:
            for error in error_list[:5]:  # Show max 5 errors
                flash(error, 'error')
            if len(error_list) > 5:
                flash(f'Dan {len(error_list) - 5} error lainnya...', 'error')
        
        if success_count == 0 and error_list:
            flash('Tidak ada data yang berhasil diimport', 'error')
    
    except Exception as e:
        flash(f'Error saat memproses file: {str(e)}', 'error')
    
    return redirect(url_for('admin_spbu'))

@app.route('/admin/import/users', methods=['POST'])
@login_required
@role_required('administrator')
def import_users_excel():
    """Import data User dari Excel."""
    if 'file' not in request.files:
        flash('Tidak ada file yang diupload', 'error')
        return redirect(url_for('admin_users'))
    
    file = request.files['file']
    if file.filename == '':
        flash('Tidak ada file yang dipilih', 'error')
        return redirect(url_for('admin_users'))
    
    if not file.filename.endswith(('.xlsx', '.xls')):
        flash('File harus berformat Excel (.xlsx)', 'error')
        return redirect(url_for('admin_users'))
    
    try:
        success_count, error_list = import_users_from_excel(file)
        
        if success_count > 0:
            flash(f'Berhasil import {success_count} data User', 'success')
        
        if error_list:
            for error in error_list[:5]:  # Show max 5 errors
                flash(error, 'error')
            if len(error_list) > 5:
                flash(f'Dan {len(error_list) - 5} error lainnya...', 'error')
        
        if success_count == 0 and error_list:
            flash('Tidak ada data yang berhasil diimport', 'error')
    
    except Exception as e:
        flash(f'Error saat memproses file: {str(e)}', 'error')
    
    return redirect(url_for('admin_users'))

# ============================================================
# PROFILE
# ============================================================

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Halaman profil user."""
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_profile':
            # Update nama dan email
            nama_lengkap = request.form.get('nama_lengkap', '').strip()
            email = request.form.get('email', '').strip()
            
            if nama_lengkap:
                current_user.nama_lengkap = nama_lengkap
            if email:
                current_user.email = email
            
            db.session.commit()
            flash('Profil berhasil diperbarui', 'success')
        
        elif action == 'change_password':
            # Ganti password
            old_password = request.form.get('old_password', '')
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            if not current_user.check_password(old_password):
                flash('Password lama salah', 'error')
            elif len(new_password) < 6:
                flash('Password baru minimal 6 karakter', 'error')
            elif new_password != confirm_password:
                flash('Konfirmasi password tidak cocok', 'error')
            else:
                current_user.set_password(new_password)
                db.session.commit()
                flash('Password berhasil diubah', 'success')
        
        return redirect(url_for('profile'))
    
    # Get SPBU info if user is SPBU role
    spbu_info = None
    if current_user.role == 'spbu' and current_user.id_spbu:
        spbu_info = SPBU.query.get(current_user.id_spbu)
    
    return render_template('profile.html', spbu_info=spbu_info)

# ============================================================
# UPLOAD SERVE
# ============================================================

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ============================================================
# API ROUTES (JSON)
# ============================================================

@app.route('/api/dashboard/stats')
@login_required
def api_dashboard_stats():
    total_laporan = Laporan.query.count()
    start_of_month = date.today().replace(day=1)
    laporan_bulan_ini = Laporan.query.filter(Laporan.tanggal >= start_of_month).count()
    spbu_aktif = db.session.query(Laporan.id_spbu).filter(Laporan.status == 'submitted').distinct().count()
    total_foto = Upload.query.count()
    
    return jsonify({
        'total_laporan': total_laporan,
        'laporan_bulan_ini': laporan_bulan_ini,
        'spbu_aktif': spbu_aktif,
        'total_foto': total_foto,
    })

@app.route('/api/laporan')
@login_required
def api_laporan_list():
    query = Laporan.query
    
    if current_user.role == 'spbu':
        query = query.filter_by(id_spbu=current_user.id_spbu)
    
    laporan_list = query.order_by(Laporan.tanggal.desc()).limit(100).all()
    
    return jsonify([l.to_dict() for l in laporan_list])

# ============================================================
# DATABASE INITIALIZATION
# ============================================================

with app.app_context():
    db.create_all()
    seed_data()

# ============================================================
# RUN
# ============================================================

@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['Strict-Transport-Security'] = 'max-age=63072000; includeSubDomains; preload'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    return response

if __name__ == '__main__':
    print("=" * 60)
    print("  Aplikasi Laporan Pembongkaran BBM SPBU")
    print("  http://localhost:5560")
    print("")
    print("  Default users:")
    print("    admin / admin123 (Administrator)")
    print("    pertamina / pertamina123 (Pertamina)")
    print("    spbu01 / spbu123 (SPBU)")
    print("=" * 60)
    
    # Only run debug server in development
    if env == 'development':
        app.run(debug=True, port=5560)
    else:
        print("\n  Production mode - use gunicorn:")
        print("  gunicorn -w 4 -b 0.0.0.0:5560 app:app")
