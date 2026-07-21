#!/usr/bin/env python3
"""
Dark-themed web-based File Manager using only stdlib http.server.
Restricted to BASE_DIR (/root).

Endpoints:
  GET  /                      - main UI
  GET  /api/files?path=...    - list directory
  GET  /api/tree?path=...     - folder tree (recursive directories)
  GET  /api/stats?path=...    - file/folder counts + disk usage
  GET  /api/search?path=...&query=... - search recursively
  GET  /api/preview?path=...  - inline preview (text/image/pdf)
  GET  /download?path=...     - download file
  POST /api/upload            - upload file(s)
  POST /api/mkdir             - create folder
  POST /api/rename            - rename file/folder
  POST /api/move              - move file/folder
  POST /api/copy              - copy file/folder
  POST /api/delete            - delete file/folder
  POST /api/bulk-delete       - delete multiple items
  POST /api/bulk-download     - download selected files as zip
"""
import cgi
import html
import io
import json
import mimetypes
import os
import posixpath
import re
import shutil
import urllib.parse
import zipfile
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 5003
BASE_DIR = "/root"
BASE_DIR_REAL = os.path.realpath(BASE_DIR)


def _safe_path(rel, resolve=True):
    """Resolve a relative path under BASE_DIR and reject traversal above it."""
    if rel is None:
        rel = ""
    rel = rel.replace("\\", "/")
    rel = posixpath.normpath(rel)
    if rel in (".", "/"):
        rel = ""
    if rel.startswith("/"):
        rel = rel[1:]
    if rel == "":
        full = BASE_DIR_REAL
    else:
        full = os.path.abspath(os.path.join(BASE_DIR_REAL, rel))
    if resolve:
        try:
            full = os.path.realpath(full)
        except OSError:
            pass
    if not (full == BASE_DIR_REAL or full.startswith(BASE_DIR_REAL + os.sep)):
        return None
    return full


def _rel_path(full):
    r = os.path.relpath(full, BASE_DIR_REAL).replace("\\", "/")
    if r == ".":
        return ""
    return r


def _sanitize_name(name):
    name = re.sub(r'[\\/:*?"<>|]', "_", name).strip().strip(".")
    if not name:
        return "unnamed"
    return name


class FileManagerHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    # ------------------------------------------------------------------
    # Response helpers
    # ------------------------------------------------------------------
    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, content, status=200):
        body = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, message, status=400):
        self._send_json({"error": message}, status)

    def _send_bytes(self, data, ctype, filename=None, inline=False, status=200):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        if filename:
            disp = "inline" if inline else "attachment"
            safe = filename.replace('"', '\\"')
            self.send_header("Content-Disposition", f'{disp}; filename="{safe}"')
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        if length <= 0:
            return {}
        body = self.rfile.read(length).decode("utf-8", errors="replace")
        try:
            return json.loads(body)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------
    def _human_size(self, size):
        try:
            size = float(size)
        except Exception:
            return "0 B"
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024:
                if unit == "B":
                    return f"{int(size)} B"
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"

    def _file_icon(self, name, is_dir):
        if is_dir:
            return "📁"
        ext = os.path.splitext(name)[1].lower()
        icons = {
            ".txt": "📄", ".md": "📝", ".py": "🐍", ".js": "📜", ".json": "🔧",
            ".html": "🌐", ".css": "🎨", ".jpg": "🖼️", ".jpeg": "🖼️", ".png": "🖼️",
            ".gif": "🖼️", ".svg": "🖼️", ".webp": "🖼️", ".mp4": "🎬", ".mov": "🎬",
            ".mp3": "🎵", ".wav": "🎵", ".zip": "🗜️", ".tar": "🗜️", ".gz": "🗜️",
            ".rar": "🗜️", ".7z": "🗜️", ".pdf": "📕", ".doc": "📘", ".docx": "📘",
            ".xls": "📊", ".xlsx": "📊", ".csv": "📊", ".ppt": "📽️", ".pptx": "📽️",
        }
        return icons.get(ext, "📄")

    def _is_text_file(self, name):
        ext = os.path.splitext(name)[1].lower()
        text_exts = {".txt", ".md", ".py", ".js", ".json", ".html", ".htm", ".css",
                     ".xml", ".csv", ".log", ".sh", ".bash", ".zsh", ".c", ".cpp",
                     ".h", ".hpp", ".java", ".go", ".rs", ".php", ".yaml", ".yml",
                     ".ini", ".cfg", ".conf", ".toml", ".sql", ".rb", ".pl"}
        if ext in text_exts:
            return True
        ctype, _ = mimetypes.guess_type(name)
        if ctype and ctype.startswith("text/"):
            return True
        return False

    def _count_items(self, full):
        files = 0
        folders = 0
        total_size = 0
        try:
            for root, dirs, files_list in os.walk(full):
                folders += len(dirs)
                files += len(files_list)
                for f in files_list:
                    try:
                        total_size += os.path.getsize(os.path.join(root, f))
                    except OSError:
                        pass
        except PermissionError:
            pass
        return files, folders, total_size

    def _build_tree(self, full, depth=0, max_depth=12):
        node = {
            "name": os.path.basename(full) or "root",
            "path": _rel_path(full),
            "children": [],
        }
        if depth >= max_depth:
            return node
        try:
            entries = sorted(os.listdir(full))
        except (PermissionError, OSError):
            return node
        for name in entries:
            child = os.path.join(full, name)
            if os.path.isdir(child):
                node["children"].append(self._build_tree(child, depth + 1, max_depth))
        return node

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        params = urllib.parse.parse_qs(parsed.query)

        if path == "/":
            self._send_html(INDEX_HTML)
            return
        if path == "/api/files":
            self._handle_api_files(params)
            return
        if path == "/api/tree":
            self._handle_api_tree(params)
            return
        if path == "/api/stats":
            self._handle_api_stats(params)
            return
        if path == "/api/search":
            self._handle_api_search(params)
            return
        if path == "/api/preview":
            self._handle_preview(params)
            return
        if path == "/download":
            self._handle_download(params)
            return
        self._send_error("Not found", 404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        route = path.lstrip("/")

        routes = {
            "api/upload": self._handle_upload,
            "api/mkdir": self._handle_mkdir,
            "api/rename": self._handle_rename,
            "api/move": self._handle_move,
            "api/copy": self._handle_copy,
            "api/delete": self._handle_delete,
            "api/bulk-delete": self._handle_bulk_delete,
            "api/bulk-download": self._handle_bulk_download,
        }
        handler = routes.get(route)
        if handler:
            try:
                handler()
            except ValueError as e:
                self._send_error(str(e), 400)
            except Exception as e:
                self._send_error(str(e), 500)
            return
        self._send_error("Not found", 404)

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------
    def _handle_api_files(self, params):
        rel = params.get("path", [""])[0]
        full = _safe_path(rel)
        if full is None:
            self._send_error("Access denied", 403)
            return
        if not os.path.exists(full):
            self._send_error("Path not found", 404)
            return
        if not os.path.isdir(full):
            self._send_error("Not a directory", 400)
            return

        try:
            entries = sorted(os.listdir(full), key=lambda x: (not os.path.isdir(os.path.join(full, x)), x.lower()))
        except PermissionError:
            self._send_error("Permission denied", 403)
            return

        items = []
        for name in entries:
            item_path = os.path.join(full, name)
            is_dir = os.path.isdir(item_path)
            try:
                stat = os.stat(item_path)
                size = stat.st_size
                mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
            except OSError:
                size = 0
                mtime = "-"
            items.append({
                "name": name,
                "is_dir": is_dir,
                "size": size,
                "size_human": self._human_size(size) if not is_dir else "-",
                "modified": mtime,
                "icon": self._file_icon(name, is_dir),
            })

        self._send_json({"path": _rel_path(full), "items": items})

    def _handle_api_tree(self, params):
        rel = params.get("path", [""])[0]
        full = _safe_path(rel)
        if full is None or not os.path.isdir(full):
            self._send_error("Invalid path", 400)
            return
        tree = self._build_tree(full)
        self._send_json(tree)

    def _handle_api_stats(self, params):
        rel = params.get("path", [""])[0]
        full = _safe_path(rel)
        if full is None or not os.path.isdir(full):
            self._send_error("Invalid path", 400)
            return
        files, folders, total_size = self._count_items(full)
        try:
            du = shutil.disk_usage(BASE_DIR_REAL)
            disk = {
                "total": du.total,
                "total_human": self._human_size(du.total),
                "used": du.used,
                "used_human": self._human_size(du.used),
                "free": du.free,
                "free_human": self._human_size(du.free),
                "percent": round(du.used / du.total * 100, 1) if du.total else 0,
            }
        except OSError:
            disk = {"total": 0, "total_human": "-", "used": 0, "used_human": "-",
                    "free": 0, "free_human": "-", "percent": 0}
        self._send_json({
            "path": _rel_path(full),
            "files": files,
            "folders": folders,
            "size": total_size,
            "size_human": self._human_size(total_size),
            "disk": disk,
        })

    def _handle_api_search(self, params):
        rel = params.get("path", [""])[0]
        query = params.get("query", [""])[0].lower()
        full = _safe_path(rel)
        if full is None or not os.path.isdir(full):
            self._send_error("Invalid path", 400)
            return
        if not query:
            self._send_json({"results": []})
            return

        results = []
        try:
            for root, dirs, files_list in os.walk(full):
                for name in dirs + files_list:
                    if query in name.lower():
                        item_path = os.path.join(root, name)
                        is_dir = os.path.isdir(item_path)
                        results.append({
                            "name": name,
                            "path": _rel_path(item_path),
                            "is_dir": is_dir,
                            "icon": self._file_icon(name, is_dir),
                        })
                        if len(results) >= 200:
                            break
                if len(results) >= 200:
                    break
        except PermissionError:
            pass
        self._send_json({"results": results})

    def _handle_preview(self, params):
        rel = params.get("path", [""])[0]
        full = _safe_path(rel)
        if full is None:
            self._send_error("Access denied", 403)
            return
        if not os.path.isfile(full):
            self._send_error("File not found", 404)
            return
        ctype, _ = mimetypes.guess_type(full)
        ctype = ctype or "application/octet-stream"
        filename = os.path.basename(full)
        try:
            with open(full, "rb") as f:
                data = f.read()
        except PermissionError:
            self._send_error("Permission denied", 403)
            return
        except OSError as e:
            self._send_error(f"Read failed: {e}", 500)
            return

        if self._is_text_file(filename):
            text = data.decode("utf-8", errors="replace")
            out = text.encode("utf-8")
            self._send_bytes(out, "text/plain; charset=utf-8", filename, inline=True)
            return
        self._send_bytes(data, ctype, filename, inline=True)

    def _handle_download(self, params):
        rel = params.get("path", [""])[0]
        full = _safe_path(rel)
        if full is None:
            self._send_error("Access denied", 403)
            return
        if not os.path.exists(full) or os.path.isdir(full):
            self._send_error("File not found", 404)
            return
        ctype, _ = mimetypes.guess_type(full)
        ctype = ctype or "application/octet-stream"
        try:
            with open(full, "rb") as f:
                data = f.read()
            self._send_bytes(data, ctype, os.path.basename(full), inline=False)
        except PermissionError:
            self._send_error("Permission denied", 403)

    def _handle_upload(self):
        ctype, pdict = cgi.parse_header(self.headers.get("Content-Type", ""))
        if ctype != "multipart/form-data":
            self._send_error("Expected multipart/form-data", 400)
            return

        length = int(self.headers.get("Content-Length", 0))
        if length <= 0:
            self._send_error("No content", 400)
            return

        boundary = pdict.get("boundary")
        if not boundary:
            self._send_error("Missing boundary", 400)
            return

        data = self.rfile.read(length)
        fp = BytesIOWrapper(data)
        pdict["boundary"] = boundary.encode() if isinstance(boundary, str) else boundary
        try:
            form = cgi.parse_multipart(fp, pdict)
        except Exception as e:
            self._send_error(f"Upload parse error: {e}", 400)
            return

        path_field = form.get("path", [b""])[0]
        if isinstance(path_field, bytes):
            path_field = path_field.decode("utf-8", errors="replace")
        target_dir = _safe_path(path_field)
        if target_dir is None:
            self._send_error("Access denied", 403)
            return
        if not os.path.isdir(target_dir):
            self._send_error("Target directory not found", 404)
            return

        file_values = form.get("file", [])
        file_bytes = file_values[0] if file_values else None
        field_name = "file"
        if file_bytes is None:
            self._send_error("No file provided", 400)
            return

        raw_filename = self._extract_filename_from_multipart(data, boundary, field_name)
        if not raw_filename:
            raw_filename = "uploaded_file"

        filename = _sanitize_name(raw_filename)
        dest = os.path.join(target_dir, filename)
        if os.path.exists(dest):
            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(dest):
                dest = os.path.join(target_dir, f"{base}_{counter}{ext}")
                counter += 1

        try:
            with open(dest, "wb") as f:
                f.write(file_bytes)
            self._send_json({"ok": True, "name": os.path.basename(dest)})
        except PermissionError:
            self._send_error("Permission denied", 403)
        except OSError as e:
            self._send_error(f"Write failed: {e}", 500)

    def _extract_filename_from_multipart(self, data, boundary, field_name="file"):
        b = boundary.encode() if isinstance(boundary, str) else boundary
        parts = data.split(b"--" + b)
        for part in parts:
            header_end = part.find(b"\r\n\r\n")
            if header_end == -1:
                continue
            headers = part[:header_end].decode("utf-8", errors="replace")
            name_match = re.search(r'name\s*=\s*"([^"]+)"', headers, re.IGNORECASE)
            if not name_match or name_match.group(1) != field_name:
                continue
            if 'filename=' not in headers.lower():
                continue
            m = re.search(r'filename\s*=\s*"([^"]*)"', headers, re.IGNORECASE)
            if m:
                return m.group(1) or ""
            m = re.search(r"filename\*\s*=\s*UTF-8''(.+)", headers, re.IGNORECASE)
            if m:
                try:
                    return urllib.parse.unquote(m.group(1))
                except Exception:
                    return m.group(1)
        return ""

    def _handle_mkdir(self):
        payload = self._read_json()
        rel = payload.get("path", "")
        name = payload.get("name", "")
        if not name or not isinstance(name, str):
            self._send_error("Folder name required", 400)
            return
        safe_name = _sanitize_name(name)
        parent = _safe_path(rel)
        if parent is None:
            self._send_error("Access denied", 403)
            return
        if not os.path.isdir(parent):
            self._send_error("Parent directory not found", 404)
            return
        dest = os.path.join(parent, safe_name)
        if os.path.exists(dest):
            self._send_error("Folder already exists", 409)
            return
        try:
            os.makedirs(dest, exist_ok=False)
            self._send_json({"ok": True, "name": safe_name})
        except PermissionError:
            self._send_error("Permission denied", 403)
        except OSError as e:
            self._send_error(f"Create failed: {e}", 500)

    def _handle_rename(self):
        payload = self._read_json()
        rel = payload.get("path", "")
        new_name = payload.get("new_name", "")
        if not new_name or not isinstance(new_name, str):
            self._send_error("New name required", 400)
            return
        src = _safe_path(rel)
        if src is None:
            self._send_error("Access denied", 403)
            return
        if not os.path.exists(src):
            self._send_error("Source not found", 404)
            return
        parent = os.path.dirname(src)
        safe_name = _sanitize_name(new_name)
        dst = os.path.join(parent, safe_name)
        if os.path.exists(dst):
            self._send_error("Target already exists", 409)
            return
        try:
            os.rename(src, dst)
            self._send_json({"ok": True, "name": safe_name})
        except PermissionError:
            self._send_error("Permission denied", 403)
        except OSError as e:
            self._send_error(f"Rename failed: {e}", 500)

    def _handle_move(self):
        payload = self._read_json()
        from_rel = payload.get("from_path", "")
        to_rel = payload.get("to_path", "")
        src = _safe_path(from_rel)
        dst_dir = _safe_path(to_rel)
        if src is None or dst_dir is None:
            self._send_error("Access denied", 403)
            return
        if not os.path.exists(src):
            self._send_error("Source not found", 404)
            return
        if not os.path.isdir(dst_dir):
            self._send_error("Destination must be a folder", 400)
            return
        dst = os.path.join(dst_dir, os.path.basename(src))
        if os.path.exists(dst):
            self._send_error("Target already exists", 409)
            return
        if src == dst_dir or dst.startswith(src + os.sep):
            self._send_error("Cannot move a folder into itself", 400)
            return
        try:
            shutil.move(src, dst)
            self._send_json({"ok": True, "path": _rel_path(dst)})
        except PermissionError:
            self._send_error("Permission denied", 403)
        except OSError as e:
            self._send_error(f"Move failed: {e}", 500)

    def _handle_copy(self):
        payload = self._read_json()
        from_rel = payload.get("from_path", "")
        to_rel = payload.get("to_path", "")
        src = _safe_path(from_rel)
        dst_dir = _safe_path(to_rel)
        if src is None or dst_dir is None:
            self._send_error("Access denied", 403)
            return
        if not os.path.exists(src):
            self._send_error("Source not found", 404)
            return
        if not os.path.isdir(dst_dir):
            self._send_error("Destination must be a folder", 400)
            return
        dst = os.path.join(dst_dir, os.path.basename(src))
        if dst.startswith(src + os.sep):
            self._send_error("Cannot copy a folder into itself", 400)
            return
        # Auto-rename on conflict
        original_dst = dst
        if os.path.exists(dst):
            base, ext = os.path.splitext(os.path.basename(src))
            counter = 1
            while os.path.exists(dst):
                suffix = f" - Copy{' (' + str(counter) + ')' if counter > 1 else ''}"
                new_name = base + suffix + ext
                dst = os.path.join(dst_dir, new_name)
                counter += 1
        try:
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
            self._send_json({"ok": True, "path": _rel_path(dst)})
        except PermissionError:
            self._send_error("Permission denied", 403)
        except OSError as e:
            self._send_error(f"Copy failed: {e}", 500)

    def _handle_delete(self):
        payload = self._read_json()
        rel = payload.get("path", "")
        full = _safe_path(rel)
        if full is None:
            self._send_error("Access denied", 403)
            return
        if not os.path.exists(full):
            self._send_error("Path not found", 404)
            return
        if full == BASE_DIR_REAL:
            self._send_error("Cannot delete the root directory", 403)
            return
        try:
            if os.path.isdir(full):
                shutil.rmtree(full)
            else:
                os.remove(full)
            self._send_json({"ok": True})
        except PermissionError:
            self._send_error("Permission denied", 403)
        except OSError as e:
            self._send_error(f"Delete failed: {e}", 500)

    def _handle_bulk_delete(self):
        payload = self._read_json()
        paths = payload.get("paths", [])
        if not isinstance(paths, list):
            self._send_error("paths must be a list", 400)
            return
        deleted = []
        errors = {}
        for rel in paths:
            full = _safe_path(rel)
            if full is None:
                errors[rel] = "Access denied"
                continue
            if not os.path.exists(full):
                errors[rel] = "Not found"
                continue
            if full == BASE_DIR_REAL:
                errors[rel] = "Cannot delete root"
                continue
            try:
                if os.path.isdir(full):
                    shutil.rmtree(full)
                else:
                    os.remove(full)
                deleted.append(rel)
            except Exception as e:
                errors[rel] = str(e)
        self._send_json({"ok": True, "deleted": deleted, "errors": errors})

    def _handle_bulk_download(self):
        payload = self._read_json()
        paths = payload.get("paths", [])
        if not isinstance(paths, list) or not paths:
            self._send_error("paths must be a non-empty list", 400)
            return

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for rel in paths:
                full = _safe_path(rel)
                if full is None or not os.path.exists(full):
                    continue
                arcname = os.path.basename(full)
                try:
                    if os.path.isdir(full):
                        for root, _, files in os.walk(full):
                            for f in files:
                                fp = os.path.join(root, f)
                                zf.write(fp, os.path.join(arcname, os.path.relpath(fp, full)))
                    else:
                        zf.write(full, arcname)
                except (PermissionError, OSError):
                    pass
        data = buf.getvalue()
        self._send_bytes(data, "application/zip", "download.zip", inline=False)


class BytesIOWrapper:
    """Wrap bytes to behave like a file for cgi.parse_multipart."""
    def __init__(self, data):
        self._fp = io.BytesIO(data)

    def read(self, size=-1):
        return self._fp.read(size)

    def readline(self, size=-1):
        return self._fp.readline(size)

    def __iter__(self):
        return iter(self._fp)


INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>File Manager</title>
<style>
:root {
  --bg: #0b0b12;
  --panel: #13131f;
  --card: #1c1c2b;
  --card-hover: #25253a;
  --accent: #7c3aed;
  --accent-hover: #6d28d9;
  --accent-soft: rgba(124,58,237,.15);
  --text: #e9ecf2;
  --text2: #94a3b8;
  --border: #2a2a40;
  --danger: #ef4444;
  --danger-hover: #dc2626;
  --success: #22c55e;
  --radius: 12px;
  --shadow: 0 12px 40px rgba(0,0,0,.45);
}
* { box-sizing: border-box; }
html, body { height: 100%; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, sans-serif;
  display: flex;
  overflow: hidden;
}

/* Sidebar */
aside {
  width: 270px;
  background: var(--panel);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}
.brand {
  padding: 18px 20px;
  font-size: 18px;
  font-weight: 700;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 10px;
}
.sidebar-scroll {
  flex: 1;
  overflow: auto;
  padding: 16px;
}
.tree-title {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: .08em;
  color: var(--text2);
  margin: 0 0 10px 4px;
}
.tree {
  font-size: 13px;
  user-select: none;
}
.tree-node {
  margin: 2px 0;
}
.tree-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 8px;
  cursor: pointer;
  color: var(--text);
}
.tree-row:hover, .tree-row.active {
  background: var(--card-hover);
}
.tree-toggle {
  width: 14px;
  text-align: center;
  color: var(--text2);
  cursor: pointer;
}
.tree-children {
  padding-left: 18px;
  display: none;
}
.tree-children.open { display: block; }
.tree-leaf .tree-toggle { visibility: hidden; }

.stats {
  border-top: 1px solid var(--border);
  padding: 16px;
  font-size: 12px;
}
.stats-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  color: var(--text2);
}
.stats-row b { color: var(--text); font-weight: 600; }
.disk-bar {
  height: 6px;
  background: var(--card);
  border-radius: 3px;
  overflow: hidden;
  margin: 10px 0 6px;
}
.disk-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent), #a78bfa);
  width: 0%;
  transition: width .4s ease;
}

/* Main */
main { flex: 1; display: flex; flex-direction: column; min-width: 0; }
header {
  background: var(--panel);
  border-bottom: 1px solid var(--border);
  padding: 14px 22px;
}
.header-top {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}
header h1 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 10px;
}
.breadcrumb {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  min-width: 0;
  overflow-x: auto;
  padding-bottom: 2px;
}
.breadcrumb::-webkit-scrollbar { height: 4px; }
.breadcrumb::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }
.breadcrumb a {
  color: var(--text2);
  text-decoration: none;
  font-size: 13px;
  white-space: nowrap;
  padding: 4px 8px;
  border-radius: 6px;
}
.breadcrumb a:hover { background: var(--card-hover); color: var(--text); }
.breadcrumb .sep { color: var(--text2); font-size: 12px; }

.header-bottom {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.search-wrap {
  position: relative;
  flex: 1;
  min-width: 180px;
  max-width: 420px;
}
.search-wrap input {
  width: 100%;
  background: var(--bg);
  border: 1px solid var(--border);
  color: var(--text);
  padding: 9px 12px 9px 34px;
  border-radius: var(--radius);
  font-size: 13px;
}
.search-wrap input:focus { outline: none; border-color: var(--accent); }
.search-wrap .icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text2);
  font-size: 13px;
}
.actions { display: flex; gap: 8px; flex-wrap: wrap; }
.btn {
  background: var(--accent);
  color: #fff;
  border: none;
  padding: 9px 14px;
  border-radius: var(--radius);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: background .15s, transform .05s, opacity .15s;
}
.btn:hover { background: var(--accent-hover); }
.btn:active { transform: scale(.98); }
.btn:disabled { opacity: .45; cursor: not-allowed; }
.btn.secondary { background: var(--card); border: 1px solid var(--border); color: var(--text); }
.btn.secondary:hover { background: var(--card-hover); }
.btn.danger { background: var(--danger); }
.btn.danger:hover { background: var(--danger-hover); }

.toolbar {
  padding: 10px 22px;
  border-bottom: 1px solid var(--border);
  background: rgba(19,19,31,.7);
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  font-size: 13px;
}
.toolbar label {
  display: flex; align-items: center; gap: 6px; cursor: pointer; color: var(--text2);
}
.toolbar input[type=checkbox] { accent-color: var(--accent); }
.selection-info { color: var(--text2); margin-left: auto; }

.content { flex: 1; overflow: auto; padding: 20px 22px; }
.dropzone {
  border: 2px dashed var(--border);
  border-radius: var(--radius);
  padding: 24px;
  text-align: center;
  color: var(--text2);
  margin-bottom: 20px;
  transition: border-color .2s, background .2s;
  cursor: pointer;
  font-size: 13px;
}
.dropzone.dragover { border-color: var(--accent); background: var(--accent-soft); color: var(--text); }
.file-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 14px;
}
.file-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 14px;
  cursor: pointer;
  transition: transform .1s, border-color .1s, background .1s;
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.file-card:hover { background: var(--card-hover); border-color: var(--accent); transform: translateY(-2px); }
.file-card.selected { border-color: var(--accent); background: var(--accent-soft); }
.file-card .chk {
  position: absolute;
  top: 10px; left: 10px;
  width: 16px; height: 16px;
  accent-color: var(--accent);
  cursor: pointer;
}
.file-icon { font-size: 36px; line-height: 1; text-align: center; margin-top: 6px; }
.file-name {
  font-size: 13px;
  font-weight: 500;
  word-break: break-word;
  text-align: center;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.file-meta {
  font-size: 11px;
  color: var(--text2);
  text-align: center;
  line-height: 1.5;
}
.list-view .file-grid {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.list-view .file-card {
  flex-direction: row;
  align-items: center;
  padding: 10px 14px;
}
.list-view .file-card .chk { position: static; }
.list-view .file-icon { font-size: 22px; margin: 0 6px 0 4px; }
.list-view .file-name { text-align: left; flex: 1; -webkit-line-clamp: 1; }
.list-view .file-meta { text-align: right; min-width: 150px; }
.empty {
  text-align: center;
  color: var(--text2);
  padding: 60px 20px;
}
.empty .big { font-size: 48px; margin-bottom: 10px; }

/* Context menu */
.context-menu {
  position: fixed;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 10px;
  box-shadow: var(--shadow);
  padding: 6px 0;
  min-width: 160px;
  z-index: 10000;
  display: none;
  font-size: 13px;
  overflow: hidden;
}
.context-menu.active { display: block; }
.context-menu button {
  width: 100%;
  background: transparent;
  border: none;
  color: var(--text);
  padding: 9px 16px;
  text-align: left;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
}
.context-menu button:hover { background: var(--card-hover); }
.context-menu button.danger { color: var(--danger); }
.context-menu hr {
  border: 0;
  border-top: 1px solid var(--border);
  margin: 6px 0;
}

/* Clipboard indicator */
.clipboard {
  position: fixed;
  bottom: 22px;
  left: 292px;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 10px 16px;
  box-shadow: var(--shadow);
  display: none;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  z-index: 9000;
}
.clipboard.active { display: flex; }

/* Toast */
.toast {
  position: fixed;
  bottom: 24px;
  right: 24px;
  background: var(--card);
  border: 1px solid var(--border);
  color: var(--text);
  padding: 14px 20px;
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  font-size: 13px;
  z-index: 10001;
  opacity: 0;
  transform: translateY(10px);
  transition: opacity .2s, transform .2s;
  pointer-events: none;
}
.toast.show { opacity: 1; transform: translateY(0); }

/* Modals */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.7);
  display: none;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 20px;
}
.modal-overlay.active { display: flex; }
.modal {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  width: 100%;
  max-width: 440px;
  padding: 22px;
  box-shadow: var(--shadow);
}
.modal.wide { max-width: 900px; max-height: 90vh; display: flex; flex-direction: column; }
.modal h3 { margin: 0 0 16px; font-size: 17px; }
.modal input[type="text"], .modal input[type="file"] {
  width: 100%;
  background: var(--bg);
  border: 1px solid var(--border);
  color: var(--text);
  padding: 11px;
  border-radius: 8px;
  font-size: 14px;
  margin-bottom: 16px;
}
.modal input:focus { outline: none; border-color: var(--accent); }
.modal .row { display: flex; gap: 10px; justify-content: flex-end; }
.preview-body {
  flex: 1;
  overflow: auto;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 10px;
  min-height: 260px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.preview-body img { max-width: 100%; max-height: 70vh; object-fit: contain; }
.preview-body iframe { width: 100%; height: 70vh; border: none; }
.preview-body pre {
  width: 100%; height: 100%; margin: 0; padding: 16px;
  overflow: auto; white-space: pre-wrap; word-break: break-word;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 13px; color: var(--text);
}
.spinner {
  display: inline-block;
  width: 18px; height: 18px;
  border: 2px solid rgba(255,255,255,.2);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin .8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 760px) {
  aside { display: none; }
  .clipboard { left: 22px; }
}
</style>
</head>
<body>
<aside>
  <div class="brand">📂 File Manager</div>
  <div class="sidebar-scroll">
    <div class="tree-title">Folders</div>
    <div class="tree" id="tree"></div>
  </div>
  <div class="stats">
    <div class="tree-title">Current Folder</div>
    <div class="stats-row"><span>Files</span><b id="statFiles">-</b></div>
    <div class="stats-row"><span>Folders</span><b id="statFolders">-</b></div>
    <div class="stats-row"><span>Size</span><b id="statSize">-</b></div>
    <div class="tree-title" style="margin-top:14px">Disk Usage</div>
    <div class="disk-bar"><div class="disk-fill" id="diskFill"></div></div>
    <div class="stats-row"><span id="diskText">-</span><b id="diskPercent">-</b></div>
  </div>
</aside>

<main>
  <header>
    <div class="header-top">
      <h1>🗂️ Files</h1>
      <nav class="breadcrumb" id="breadcrumb"></nav>
      <div class="actions">
        <button class="btn secondary" id="btnGrid" title="Grid view">⊞</button>
        <button class="btn secondary" id="btnList" title="List view">☰</button>
        <button class="btn secondary" id="btnNewFolder">+ Folder</button>
        <button class="btn" id="btnUpload">↑ Upload</button>
      </div>
    </div>
    <div class="header-bottom">
      <div class="search-wrap">
        <span class="icon">🔎</span>
        <input type="text" id="searchInput" placeholder="Search files..." autocomplete="off">
      </div>
      <div class="actions">
        <button class="btn secondary" id="btnCopy" disabled>⧉ Copy</button>
        <button class="btn secondary" id="btnCut" disabled>✂ Cut</button>
        <button class="btn secondary" id="btnPaste" disabled>📋 Paste</button>
        <button class="btn danger" id="btnBulkDelete" disabled>🗑 Delete</button>
        <button class="btn secondary" id="btnBulkDownload" disabled>⬇ Download</button>
      </div>
    </div>
  </header>

  <div class="toolbar">
    <label><input type="checkbox" id="selectAll"> Select all</label>
    <span class="selection-info" id="selectionInfo"></span>
  </div>

  <div class="content">
    <div class="dropzone" id="dropzone">
      <div><b>Drop files here to upload</b></div>
      <div style="font-size:12px;opacity:.8;margin-top:4px">or click the Upload button</div>
    </div>
    <div class="file-grid" id="fileGrid"></div>
  </div>
</main>

<div class="context-menu" id="contextMenu"></div>

<div class="clipboard" id="clipboard">
  <span id="clipboardText"></span>
  <button class="btn" id="clipboardPaste" style="padding:6px 10px;font-size:12px">Paste</button>
  <button class="btn secondary" id="clipboardClear" style="padding:6px 10px;font-size:12px">Clear</button>
</div>

<div class="toast" id="toast"></div>

<div class="modal-overlay" id="mkdirModal">
  <div class="modal">
    <h3>Create new folder</h3>
    <input type="text" id="mkdirName" placeholder="Folder name" autocomplete="off">
    <div class="row">
      <button class="btn secondary" id="mkdirCancel">Cancel</button>
      <button class="btn" id="mkdirOk">Create</button>
    </div>
  </div>
</div>

<div class="modal-overlay" id="renameModal">
  <div class="modal">
    <h3>Rename</h3>
    <input type="text" id="renameName" placeholder="New name" autocomplete="off">
    <div class="row">
      <button class="btn secondary" id="renameCancel">Cancel</button>
      <button class="btn" id="renameOk">Rename</button>
    </div>
  </div>
</div>

<div class="modal-overlay" id="previewModal">
  <div class="modal wide">
    <h3 id="previewTitle">Preview</h3>
    <div class="preview-body" id="previewBody"><div class="spinner"></div></div>
    <div class="row" style="margin-top:16px">
      <button class="btn secondary" id="previewClose">Close</button>
      <button class="btn" id="previewDownload">Download</button>
    </div>
  </div>
</div>

<input type="file" id="fileInput" multiple style="display:none">

<script>
const state = { path: '', view: 'grid' };
let items = [];
let visibleItems = [];
let selected = new Set();
let clipboard = null;
let contextItem = null;
const $ = id => document.getElementById(id);

function showToast(msg, type='info') {
  const t = $('toast');
  t.textContent = msg;
  t.style.borderColor = type === 'error' ? 'var(--danger)' : type === 'success' ? 'var(--success)' : 'var(--border)';
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 3200);
}

function esc(s) {
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

function relPath(name) {
  return state.path ? state.path + '/' + name : name;
}

function dirname(path) {
  const parts = (path || '').split('/').filter(Boolean);
  parts.pop();
  return parts.join('/');
}

function setPath(p) {
  state.path = p || '';
  selected.clear();
  updateSelectionUI();
  window.history.replaceState(null, '', '?path=' + encodeURIComponent(state.path));
  loadFiles();
  loadTree();
  loadStats();
}

function renderBreadcrumb() {
  const bc = $('breadcrumb');
  const parts = state.path ? state.path.split('/').filter(Boolean) : [];
  let html = '<a href="#" data-path="">root</a>';
  let acc = '';
  parts.forEach(part => {
    acc = acc ? acc + '/' + part : part;
    html += '<span class="sep">/</span><a href="#" data-path="' + esc(acc) + '">' + esc(part) + '</a>';
  });
  bc.innerHTML = html;
  bc.querySelectorAll('a').forEach(a => {
    a.addEventListener('click', e => { e.preventDefault(); setPath(a.dataset.path); });
  });
}

async function loadFiles() {
  const grid = $('fileGrid');
  grid.innerHTML = '<div class="empty"><div class="spinner"></div><div>Loading...</div></div>';
  try {
    const res = await fetch('/api/files?path=' + encodeURIComponent(state.path));
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    items = data.items;
    applyFilter();
    renderBreadcrumb();
  } catch (e) {
    grid.innerHTML = '<div class="empty"><div class="big">⚠️</div><div>' + esc(e.message) + '</div></div>';
    showToast(e.message, 'error');
  }
}

function renderFiles(list) {
  const grid = $('fileGrid');
  visibleItems = list;
  if (!list.length) {
    const q = $('searchInput').value.trim();
    grid.innerHTML = q
      ? '<div class="empty"><div class="big">🔍</div><div>No matches found</div></div>'
      : '<div class="empty"><div class="big">📂</div><div>This folder is empty</div></div>';
    updateSelectionUI();
    return;
  }
  grid.innerHTML = list.map((item) => {
    const sel = selected.has(item.name) ? 'selected' : '';
    return `
      <div class="file-card ${sel}" data-name="${esc(item.name)}">
        <input type="checkbox" class="chk" ${selected.has(item.name)?'checked':''} data-name="${esc(item.name)}">
        <div class="file-icon">${item.icon}</div>
        <div class="file-name" title="${esc(item.name)}">${esc(item.name)}</div>
        <div class="file-meta">
          ${item.is_dir ? 'Folder' : item.size_human}<br>${item.modified}
        </div>
      </div>`;
  }).join('');

  grid.querySelectorAll('.file-card').forEach(card => {
    card.addEventListener('click', e => {
      const name = card.dataset.name;
      if (e.target.classList.contains('chk')) {
        e.stopPropagation();
        toggleSelect(name);
        return;
      }
      const item = items.find(i => i.name === name);
      if (!item) return;
      if (item.is_dir) openItemByName(name);
      else previewFile(item.name);
    });
    card.addEventListener('contextmenu', e => {
      e.preventDefault();
      const name = card.dataset.name;
      if (!selected.has(name)) { selected.clear(); selected.add(name); updateSelectionUI(); renderFiles(visibleItems); }
      showContextMenu(e.clientX, e.clientY, name);
    });
  });
  updateSelectionUI();
}

function openItem(idx) {
  const item = items[idx];
  if (!item || !item.is_dir) return;
  setPath(relPath(item.name));
}

function previewFile(name) {
  const rel = relPath(name);
  const ext = name.split('.').pop().toLowerCase();
  const modal = $('previewModal');
  $('previewTitle').textContent = name;
  const body = $('previewBody');
  body.innerHTML = '<div class="spinner"></div>';
  modal.classList.add('active');
  $('previewDownload').onclick = () => { window.location.href = '/download?path=' + encodeURIComponent(rel); };

  const imgExts = ['jpg','jpeg','png','gif','svg','webp','bmp','ico'];
  const pdfExts = ['pdf'];
  if (imgExts.includes(ext)) {
    body.innerHTML = '<img src="/api/preview?path=' + encodeURIComponent(rel) + '">';
  } else if (pdfExts.includes(ext)) {
    body.innerHTML = '<iframe src="/api/preview?path=' + encodeURIComponent(rel) + '"></iframe>';
  } else {
    fetch('/api/preview?path=' + encodeURIComponent(rel))
      .then(r => { if (!r.ok) throw new Error('Preview failed'); return r.text(); })
      .then(text => { body.innerHTML = '<pre>' + esc(text) + '</pre>'; })
      .catch(e => { body.innerHTML = '<div class="empty"><div class="big">📄</div><div>' + esc(e.message) + '</div></div>'; });
  }
}

function toggleSelect(name) {
  if (selected.has(name)) selected.delete(name);
  else selected.add(name);
  updateSelectionUI();
  renderFiles(visibleItems);
}

function selectAll() {
  const names = visibleItems.map(i => i.name);
  const allVisibleSelected = names.length > 0 && names.every(n => selected.has(n));
  if (allVisibleSelected) names.forEach(n => selected.delete(n));
  else names.forEach(n => selected.add(n));
  updateSelectionUI();
  renderFiles(visibleItems);
}

function updateSelectionUI() {
  const visibleNames = visibleItems.map(i => i.name);
  $('selectAll').checked = visibleNames.length > 0 && visibleNames.every(n => selected.has(n));
  $('selectionInfo').textContent = selected.size ? `${selected.size} selected` : '';
  $('btnCopy').disabled = !selected.size;
  $('btnCut').disabled = !selected.size;
  $('btnBulkDelete').disabled = !selected.size;
  $('btnBulkDownload').disabled = !selected.size;
}

// ---- Context menu ----
function showContextMenu(x, y, name) {
  contextItem = name;
  const menu = $('contextMenu');
  const item = items.find(i => i.name === name);
  if (!item) return;
  const rel = relPath(name);
  let html = '';
  if (item.is_dir) html += `<button data-action="open">📂 Open</button>`;
  else html += `<button data-action="preview">👁 Preview</button>`;
  html += `<button data-action="download">⬇ Download</button><hr>`;
  html += `<button data-action="rename">✏️ Rename</button>`;
  html += `<button data-action="copy">📄 Copy</button>`;
  html += `<button data-action="cut">✂️ Cut</button>`;
  html += `<button class="danger" data-action="delete">🗑 Delete</button>`;
  menu.innerHTML = html;
  menu.querySelectorAll('button[data-action]').forEach(btn => {
    btn.addEventListener('click', () => runContextAction(btn.dataset.action, name));
  });
  menu.classList.add('active');
  const rect = menu.getBoundingClientRect();
  menu.style.left = Math.min(x, window.innerWidth - rect.width - 8) + 'px';
  menu.style.top = Math.min(y, window.innerHeight - rect.height - 8) + 'px';
}

function hideContextMenu() {
  $('contextMenu').classList.remove('active');
  contextItem = null;
}

function runContextAction(action, name) {
  if (action === 'open') openItemByName(name);
  if (action === 'preview') { hideContextMenu(); previewFile(name); }
  if (action === 'download') downloadByName(name);
  if (action === 'rename') startRename(name);
  if (action === 'copy') copyByName(name);
  if (action === 'cut') cutByName(name);
  if (action === 'delete') deleteByName(name);
}

function openItemByName(name) {
  hideContextMenu();
  const idx = items.findIndex(i => i.name === name);
  if (idx >= 0) openItem(idx);
}
function downloadByName(name) {
  hideContextMenu();
  window.location.href = '/download?path=' + encodeURIComponent(relPath(name));
}
function copyByName(name) { hideContextMenu(); copySelectedPaths([relPath(name)], [name]); }
function cutByName(name) { hideContextMenu(); cutSelectedPaths([relPath(name)], [name]); }
function deleteByName(name) {
  hideContextMenu();
  selected.clear();
  selected.add(name);
  updateSelectionUI();
  renderFiles(visibleItems);
  deleteSelected();
}

// ---- Clipboard ----
function setClipboard(mode, paths, names) {
  clipboard = { mode, paths: paths || [], names: names || [] };
  renderClipboard();
}
function clearClipboard() {
  clipboard = null;
  renderClipboard();
}
function renderClipboard() {
  const el = $('clipboard');
  if (!clipboard || !clipboard.paths.length) {
    el.classList.remove('active');
    $('btnPaste').disabled = true;
    return;
  }
  const label = clipboard.mode === 'cut' ? 'cut' : 'copied';
  $('clipboardText').textContent = `${clipboard.names.length} item${clipboard.names.length>1?'s':''} ${label}`;
  el.classList.add('active');
  $('btnPaste').disabled = false;
}
function copySelected() { copySelectedPaths(Array.from(selected).map(relPath), Array.from(selected)); }
function cutSelected() { cutSelectedPaths(Array.from(selected).map(relPath), Array.from(selected)); }
function copySelectedPaths(paths, names) {
  if (!paths.length) return;
  setClipboard('copy', paths, names);
  showToast(`${names.length} item(s) copied`, 'success');
}
function cutSelectedPaths(paths, names) {
  if (!paths.length) return;
  setClipboard('cut', paths, names);
  showToast(`${names.length} item(s) cut`, 'success');
}

async function paste() {
  if (!clipboard || !clipboard.paths.length) return;
  const target = state.path || '';
  const op = clipboard.mode === 'cut' ? 'move' : 'copy';
  let okCount = 0;
  let err = '';
  for (const p of clipboard.paths) {
    try {
      const res = await fetch('/api/' + op, {
        method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ from_path: p, to_path: target })
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      okCount++;
    } catch (e) { err = e.message; }
  }
  if (clipboard.mode === 'cut') clearClipboard();
  if (okCount) showToast(`Pasted ${okCount} item(s)`, 'success');
  if (err) showToast(err, 'error');
  loadFiles(); loadTree(); loadStats();
}

// ---- CRUD ----
async function deleteSelected() {
  if (!selected.size) return;
  const names = Array.from(selected);
  if (!confirm(`Delete ${names.length} selected item(s)?`)) return;
  const paths = names.map(relPath);
  try {
    const res = await fetch('/api/bulk-delete', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ paths })
    });
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    const errs = Object.keys(data.errors || {}).length;
    showToast(`Deleted ${data.deleted.length} item(s)${errs ? ' ('+errs+' failed)' : ''}`, errs ? 'error' : 'success');
  } catch (e) { showToast(e.message, 'error'); }
  selected.clear();
  updateSelectionUI();
  loadFiles(); loadTree(); loadStats();
}

async function bulkDownload() {
  if (!selected.size) return;
  const paths = Array.from(selected).map(relPath);
  try {
    const res = await fetch('/api/bulk-download', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ paths })
    });
    if (!res.ok) throw new Error('Bulk download failed');
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'download.zip';
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
  } catch (e) { showToast(e.message, 'error'); }
}

function startRename(name) {
  hideContextMenu();
  selected.clear();
  selected.add(name);
  updateSelectionUI();
  renderFiles(visibleItems);
  $('renameName').value = name;
  $('renameModal').classList.add('active');
  $('renameName').focus();
  $('renameName').select();
}

async function doRename() {
  const name = Array.from(selected)[0] || contextItem;
  const newName = $('renameName').value.trim();
  if (!name || !newName) return;
  try {
    const res = await fetch('/api/rename', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ path: relPath(name), new_name: newName })
    });
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    $('renameModal').classList.remove('active');
    showToast('Renamed', 'success');
    selected.clear();
    updateSelectionUI();
    loadFiles(); loadTree(); loadStats();
  } catch (e) { showToast(e.message, 'error'); }
}

async function createFolder() {
  const name = $('mkdirName').value.trim();
  if (!name) return;
  try {
    const res = await fetch('/api/mkdir', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ path: state.path, name })
    });
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    $('mkdirName').value = '';
    $('mkdirModal').classList.remove('active');
    showToast('Folder created', 'success');
    loadFiles(); loadTree(); loadStats();
  } catch (e) { showToast(e.message, 'error'); }
}

async function uploadFiles(files) {
  if (!files.length) return;
  for (const file of files) {
    const form = new FormData();
    form.append('path', state.path);
    form.append('filename', file.name);
    form.append('file', file);
    try {
      const res = await fetch('/api/upload', { method: 'POST', body: form });
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      showToast('Uploaded ' + data.name, 'success');
    } catch (e) { showToast('Upload failed: ' + e.message, 'error'); }
  }
  loadFiles(); loadStats();
}

// ---- Tree & stats ----
async function loadTree() {
  try {
    const res = await fetch('/api/tree?path=');
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    $('tree').innerHTML = renderTreeNode(data, true);
    attachTreeEvents();
  } catch (e) { /* silent */ }
}

function renderTreeNode(node, open=false) {
  const isLeaf = !node.children || !node.children.length;
  const cls = isLeaf ? 'tree-leaf' : '';
  const openCls = open ? 'open' : '';
  let html = `<div class="tree-node ${cls}">`;
  html += `<div class="tree-row ${node.path === state.path ? 'active' : ''}" data-path="${esc(node.path)}">`;
  html += `<span class="tree-toggle">${isLeaf ? '' : '▶'}</span>`;
  html += `<span>📁 ${esc(node.name)}</span></div>`;
  if (!isLeaf) {
    html += `<div class="tree-children ${openCls}">`;
    node.children.forEach(c => { html += renderTreeNode(c, false); });
    html += '</div>';
  }
  html += '</div>';
  return html;
}

function attachTreeEvents() {
  document.querySelectorAll('.tree-toggle').forEach(t => {
    t.addEventListener('click', e => {
      e.stopPropagation();
      const children = t.closest('.tree-node').querySelector('.tree-children');
      if (!children) return;
      children.classList.toggle('open');
      t.textContent = children.classList.contains('open') ? '▼' : '▶';
    });
  });
  document.querySelectorAll('.tree-row').forEach(r => {
    r.addEventListener('click', () => setPath(r.dataset.path));
  });
}

async function loadStats() {
  try {
    const res = await fetch('/api/stats?path=' + encodeURIComponent(state.path));
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    $('statFiles').textContent = data.files;
    $('statFolders').textContent = data.folders;
    $('statSize').textContent = data.size_human;
    $('diskFill').style.width = data.disk.percent + '%';
    $('diskText').textContent = `Used ${data.disk.used_human} / ${data.disk.total_human}`;
    $('diskPercent').textContent = data.disk.percent + '%';
  } catch (e) { /* silent */ }
}

// ---- Search ----
let searchTimer = null;
function onSearch() {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(applyFilter, 120);
}

function applyFilter() {
  const q = $('searchInput').value.trim().toLowerCase();
  const list = q ? items.filter(i => i.name.toLowerCase().includes(q)) : items.slice();
  renderFiles(list);
}

function renderSearchResults(results) {
  const grid = $('fileGrid');
  if (!results.length) {
    grid.innerHTML = '<div class="empty"><div class="big">🔍</div><div>No matches found</div></div>';
    return;
  }
  grid.innerHTML = results.map(r => {
    const click = r.is_dir ? `setPath('${esc(r.path)}')` : `previewFileFromPath('${esc(r.path)}','${esc(r.name)}')`;
    return `
      <div class="file-card" onclick="${click}">
        <div class="file-icon">${r.icon}</div>
        <div class="file-name" title="${esc(r.name)}">${esc(r.name)}</div>
        <div class="file-meta">${esc(r.path)}</div>
      </div>`;
  }).join('');
}

function previewFileFromPath(path, name) {
  state.path = dirname(path);
  previewFile(name);
  loadFiles(); renderBreadcrumb(); loadStats();
}

// ---- View ----
function setView(view) {
  state.view = view;
  document.body.classList.toggle('list-view', view === 'list');
  $('btnGrid').style.opacity = view === 'grid' ? '1' : '.5';
  $('btnList').style.opacity = view === 'list' ? '1' : '.5';
}

// ---- Event bindings ----
$('btnUpload').addEventListener('click', () => $('fileInput').click());
$('fileInput').addEventListener('change', e => uploadFiles(e.target.files));
$('btnNewFolder').addEventListener('click', () => { $('mkdirModal').classList.add('active'); $('mkdirName').focus(); });
$('mkdirCancel').addEventListener('click', () => $('mkdirModal').classList.remove('active'));
$('mkdirOk').addEventListener('click', createFolder);
$('mkdirName').addEventListener('keydown', e => { if (e.key === 'Enter') createFolder(); if (e.key === 'Escape') $('mkdirModal').classList.remove('active'); });

$('renameCancel').addEventListener('click', () => $('renameModal').classList.remove('active'));
$('renameOk').addEventListener('click', doRename);
$('renameName').addEventListener('keydown', e => { if (e.key === 'Enter') doRename(); if (e.key === 'Escape') $('renameModal').classList.remove('active'); });

$('previewClose').addEventListener('click', () => $('previewModal').classList.remove('active'));

$('btnGrid').addEventListener('click', () => setView('grid'));
$('btnList').addEventListener('click', () => setView('list'));

$('selectAll').addEventListener('change', selectAll);
$('btnCopy').addEventListener('click', copySelected);
$('btnCut').addEventListener('click', cutSelected);
$('btnBulkDelete').addEventListener('click', deleteSelected);
$('btnBulkDownload').addEventListener('click', bulkDownload);
$('btnPaste').addEventListener('click', paste);
$('clipboardPaste').addEventListener('click', paste);
$('clipboardClear').addEventListener('click', clearClipboard);

$('searchInput').addEventListener('input', onSearch);

const dz = $('dropzone');
['dragenter','dragover'].forEach(ev => dz.addEventListener(ev, e => { e.preventDefault(); dz.classList.add('dragover'); }));
['dragleave','drop'].forEach(ev => dz.addEventListener(ev, e => { e.preventDefault(); dz.classList.remove('dragover'); }));
dz.addEventListener('drop', e => uploadFiles(e.dataTransfer.files));
dz.addEventListener('click', () => $('fileInput').click());

document.addEventListener('click', e => {
  if (!e.target.closest('#contextMenu')) hideContextMenu();
});
document.addEventListener('contextmenu', e => {
  if (e.target.closest('.file-card') || e.target.closest('.context-menu') || e.target.closest('aside') || e.target.closest('header')) return;
  e.preventDefault();
  showEmptyContextMenu(e.clientX, e.clientY);
});

function showEmptyContextMenu(x, y) {
  const menu = $('contextMenu');
  let html = `<button data-action="select-all">☑ Select all</button>`;
  html += `<button data-action="refresh">🔄 Refresh</button>`;
  if (clipboard && clipboard.paths.length) html += `<button data-action="paste">📋 Paste</button>`;
  menu.innerHTML = html;
  menu.querySelectorAll('button[data-action]').forEach(btn => {
    btn.addEventListener('click', () => {
      const action = btn.dataset.action;
      if (action === 'select-all') selectAll();
      if (action === 'refresh') loadFiles();
      if (action === 'paste') paste();
      hideContextMenu();
    });
  });
  menu.classList.add('active');
  const rect = menu.getBoundingClientRect();
  menu.style.left = Math.min(x, window.innerWidth - rect.width - 8) + 'px';
  menu.style.top = Math.min(y, window.innerHeight - rect.height - 8) + 'px';
}

window.addEventListener('keydown', e => {
  if (e.target.matches('input,textarea')) {
    if (e.key === 'Escape') { $('mkdirModal').classList.remove('active'); $('renameModal').classList.remove('active'); $('previewModal').classList.remove('active'); }
    return;
  }
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'a') { e.preventDefault(); selectAll(); }
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'c') { e.preventDefault(); copySelected(); }
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'x') { e.preventDefault(); cutSelected(); }
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'v') { e.preventDefault(); paste(); }
  if (e.key === 'Delete') { e.preventDefault(); deleteSelected(); }
  if (e.key === 'F2') { e.preventDefault(); if (selected.size === 1) startRename(Array.from(selected)[0]); }
  if (e.key === 'Escape') { hideContextMenu(); $('mkdirModal').classList.remove('active'); $('renameModal').classList.remove('active'); $('previewModal').classList.remove('active'); }
});

// Init
const qp = new URLSearchParams(window.location.search);
state.path = qp.get('path') || '';
setView('grid');
loadFiles();
loadTree();
loadStats();
</script>
</body>
</html>
"""


def run():
    server = HTTPServer(("0.0.0.0", PORT), FileManagerHandler)
    print(f"File Manager serving at http://0.0.0.0:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
