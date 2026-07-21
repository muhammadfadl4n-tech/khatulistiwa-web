#!/usr/bin/env python3
"""Fix file-manager: make API calls use relative paths (not absolute) for sub-path deployment"""
import re
from pathlib import Path

fp = Path("/root/file-manager/server.py")
content = fp.read_text(encoding="utf-8")

# Fix: replace absolute fetch paths like '/api/files' with relative 'api/files'
# 1. Find all fetch('/api/...') calls in JavaScript
# 2. Replace them with relative paths

changes = [
    ("'/api/files'", "'api/files'"),
    ('"/api/files"', '"api/files"'),
    ("'/api/upload'", "'api/upload'"),
    ('"/api/upload"', '"api/upload"'),
    ("'/api/mkdir'", "'api/mkdir'"),
    ('"/api/mkdir"', '"api/mkdir"'),
    ("'/api/download'", "'api/download'"),
    ('"/api/download"', '"api/download"'),
]

for old, new in changes:
    if old in content:
        content = content.replace(old, new)
        print(f"✅ {old} → {new}")

fp.write_text(content, encoding="utf-8")
print("\n✅ Server.py updated")
