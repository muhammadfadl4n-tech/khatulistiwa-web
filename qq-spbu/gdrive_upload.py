#!/usr/bin/env python3
"""
Upload file ke Google Drive via rclone.
Gunakan setelah rclone dikonfigurasi dengan 'rclone config'.
"""
import os, sys, subprocess, json

RCLONE_REMOTE = 'gdrive'
PARENT_FOLDER = 'QQ SPBU Uploads'

def ensure_folder():
    """Buat folder di Google Drive jika belum ada"""
    result = subprocess.run(
        ['rclone', 'mkdir', f'{RCLONE_REMOTE}:{PARENT_FOLDER}'],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        return True
    # Maybe folder already exists, try uploading anyway
    return True

def upload_file(local_path):
    """Upload file ke Google Drive, return link"""
    if not os.path.exists(local_path):
        return None, f"File not found: {local_path}"
    
    filename = os.path.basename(local_path)
    dest = f'{RCLONE_REMOTE}:{PARENT_FOLDER}/{filename}'
    
    # Upload
    result = subprocess.run(
        ['rclone', 'copy', local_path, f'{RCLONE_REMOTE}:{PARENT_FOLDER}/'],
        capture_output=True, text=True
    )
    
    if result.returncode != 0:
        return None, result.stderr.strip()
    
    # Get shareable link using rclone link
    link_result = subprocess.run(
        ['rclone', 'link', dest],
        capture_output=True, text=True
    )
    
    link = link_result.stdout.strip() if link_result.returncode == 0 else None
    return link, None

def upload_files(file_paths):
    """Upload multiple files, return results"""
    results = []
    for path in file_paths:
        link, error = upload_file(path)
        results.append({'path': path, 'link': link, 'error': error})
    return results

if __name__ == '__main__':
    ensure_folder()
    
    if len(sys.argv) > 1:
        files = sys.argv[1:]
    else:
        files = []
    
    if not files:
        print(f"Gunakan: python3 {sys.argv[0]} <file1> [file2] ...")
        print()
        print("Cek koneksi ke Google Drive...")
        result = subprocess.run(['rclone', 'ls', f'{RCLONE_REMOTE}:'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Koneksi Google Drive OK!")
            ensure_folder()
            print(f"📁 Folder '{PARENT_FOLDER}' siap")
        else:
            print("❌ Belum terkoneksi. Jalankan: rclone config")
            print("   Atau: rclone authorize 'drive'")
        sys.exit(0)
    
    ensure_folder()
    for path in files:
        link, error = upload_file(path)
        if link:
            print(f"✅ {os.path.basename(path)} → {link}")
        else:
            print(f"❌ {os.path.basename(path)}: {error}")
