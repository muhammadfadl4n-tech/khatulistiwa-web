"""
Script untuk reset database dan re-seed data demo.
Gunakan ini jika ingin memulai ulang database dengan data demo.

Usage:
    python reset_database.py

Note:
    - Script ini akan menghapus SEMUA data di database
    - Database akan di-seed ulang dengan data demo
    - Demo credentials:
        * admin / admin123 (Administrator)
        * pertamina / pertamina123 (Pertamina)
        * spbu01 / spbu123 (SPBU - SPBU 61.781.01)
"""

import os
import sys

# Tambahkan current directory ke path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db

def reset_database():
    """Reset database dan re-seed data demo."""
    with app.app_context():
        print("=" * 60)
        print("  RESET DATABASE")
        print("=" * 60)
        print()
        
        # Show database info
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        if 'postgresql' in db_uri:
            print("Database: PostgreSQL (Production)")
        else:
            print("Database: SQLite (Development)")
        print()
        
        # Drop all tables
        print("Dropping all tables...")
        db.drop_all()
        print("✓ All tables dropped")
        print()
        
        # Create all tables
        print("Creating all tables...")
        db.create_all()
        print("✓ All tables created")
        print()
        
        # Import seed function
        from app import seed_data
        
        # Seed data
        print("Seeding demo data...")
        seed_data()
        print()
        
        print("=" * 60)
        print("  DATABASE RESET COMPLETE!")
        print("=" * 60)
        print()
        print("Demo credentials:")
        print("  admin / admin123 (Administrator)")
        print("  pertamina / pertamina123 (Pertamina)")
        print("  spbu01 / spbu123 (SPBU - SPBU 61.781.01)")
        print()
        print("WARNING:")
        print("  - All previous data has been deleted")
        print("  - All uploads folder still exists but references are gone")
        print("  - Consider cleaning uploads/ folder manually if needed")
        print()

if __name__ == '__main__':
    # Confirmation prompt
    print("WARNING: This will delete ALL data in the database!")
    print("Are you sure you want to continue? (yes/no)")
    confirmation = input().strip().lower()
    
    if confirmation == 'yes':
        reset_database()
    else:
        print("Reset cancelled.")
        sys.exit(0)
