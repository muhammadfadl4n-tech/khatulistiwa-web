"""
Konfigurasi aplikasi Laporan Pembongkaran BBM SPBU
"""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database - Support PostgreSQL for production, SQLite for development
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL:
        # PostgreSQL (Render, Heroku, dll)
        # Handle postgres:// vs postgresql:// URL scheme
        if DATABASE_URL.startswith('postgres://'):
            DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        # SQLite (development)
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(BASE_DIR, "bbm_reports.db")}'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
    }
    
    # Upload
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024 * 1024  # 2GB max total upload
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_FILES_PER_CATEGORY = 10  # Maximum files per upload category
    
    # Image compression
    IMAGE_MAX_DIMENSION = 1920  # pixels (longest side)
    IMAGE_QUALITY = 80  # JPEG quality
    IMAGE_MAX_SIZE = 500 * 1024  # 500KB target after compression
    THUMBNAIL_SIZE = 320  # pixels
    
    # Session
    PERMANENT_SESSION_LIFETIME = 30 * 60  # 30 minutes
    
    # Allowed file extensions
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'pdf'}


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY')  # Must be set in production


class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
