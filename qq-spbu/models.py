"""
Database models untuk Laporan Pembongkaran BBM SPBU
"""

from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """Model untuk user (SPBU, Pertamina, Administrator)."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    nama_lengkap = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='spbu')  # spbu, pertamina, administrator
    id_spbu = db.Column(db.Integer, db.ForeignKey('spbu.id'), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    spbu = db.relationship('SPBU', backref='users', lazy=True)
    laporan = db.relationship('Laporan', backref='user', lazy=True)
    
    def set_password(self, password):
        """Hash dan set password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password terhadap hash."""
        return check_password_hash(self.password_hash, password)
    
    @property
    def is_spbu(self):
        return self.role == 'spbu'
    
    @property
    def is_pertamina(self):
        return self.role == 'pertamina'
    
    @property
    def is_administrator(self):
        return self.role == 'administrator'
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'username': self.username,
            'nama_lengkap': self.nama_lengkap,
            'role': self.role,
            'id_spbu': self.id_spbu,
            'email': self.email,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    def __repr__(self):
        return f'<User {self.username} ({self.role})>'


class SPBU(db.Model):
    """Model untuk data SPBU."""
    __tablename__ = 'spbu'
    
    id = db.Column(db.Integer, primary_key=True)
    nama_pt = db.Column(db.String(200), nullable=False)
    nomor_spbu = db.Column(db.String(50), unique=True, nullable=False, index=True)
    kota = db.Column(db.String(100), nullable=False, index=True)
    alamat = db.Column(db.Text, nullable=True)
    lat = db.Column(db.Float, nullable=True)
    lng = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    laporan = db.relationship('Laporan', backref='spbu', lazy=True)
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'nama_pt': self.nama_pt,
            'nomor_spbu': self.nomor_spbu,
            'kota': self.kota,
            'alamat': self.alamat,
            'lat': self.lat,
            'lng': self.lng,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    def __repr__(self):
        return f'<SPBU {self.nomor_spbu} - {self.nama_pt}>'


class Laporan(db.Model):
    """Model untuk laporan pembongkaran BBM."""
    __tablename__ = 'laporan'
    
    id = db.Column(db.Integer, primary_key=True)
    id_spbu = db.Column(db.Integer, db.ForeignKey('spbu.id'), nullable=False, index=True)
    id_user = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    tanggal = db.Column(db.Date, nullable=False, index=True)
    jenis_bbm = db.Column(db.JSON, nullable=False)  # Array of strings: ["Biosolar", "Pertalite", ...]
    status = db.Column(db.String(20), nullable=False, default='draft', index=True)  # draft, submitted, verified
    catatan = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    uploads = db.relationship('Upload', backref='laporan', lazy=True, cascade='all, delete-orphan')
    
    @property
    def jenis_bbm_list(self):
        """Get jenis BBM as list."""
        if isinstance(self.jenis_bbm, str):
            return json.loads(self.jenis_bbm)
        return self.jenis_bbm or []
    
    @jenis_bbm_list.setter
    def jenis_bbm_list(self, value):
        """Set jenis BBM from list."""
        self.jenis_bbm = value
    
    @property
    def foto_count(self):
        """Count total uploads."""
        return len(self.uploads)
    
    @property
    def status_display(self):
        """Get display text for status."""
        status_map = {
            'draft': 'Draft',
            'submitted': 'Submitted',
            'verified': 'Verified'
        }
        return status_map.get(self.status, self.status)
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'id_spbu': self.id_spbu,
            'id_user': self.id_user,
            'tanggal': self.tanggal.isoformat() if self.tanggal else None,
            'jenis_bbm': self.jenis_bbm_list,
            'status': self.status,
            'catatan': self.catatan,
            'foto_count': self.foto_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'spbu': self.spbu.to_dict() if self.spbu else None,
        }
    
    def __repr__(self):
        return f'<Laporan {self.id} - {self.tanggal} ({self.status})>'


class Upload(db.Model):
    """Model untuk file upload (foto pembongkaran, SPP, dipping, ATG)."""
    __tablename__ = 'uploads'
    
    id = db.Column(db.Integer, primary_key=True)
    id_laporan = db.Column(db.Integer, db.ForeignKey('laporan.id'), nullable=False, index=True)
    kategori = db.Column(db.String(50), nullable=False, index=True)  # pembongkaran, spp, dipping, atg
    filename = db.Column(db.String(255), nullable=False)  # Original filename
    path = db.Column(db.String(500), nullable=False)  # Path relative to uploads folder
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'id_laporan': self.id_laporan,
            'kategori': self.kategori,
            'filename': self.filename,
            'path': self.path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    def __repr__(self):
        return f'<Upload {self.kategori} - {self.filename}>'
