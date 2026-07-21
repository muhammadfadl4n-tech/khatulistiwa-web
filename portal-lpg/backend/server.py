#!/usr/bin/env python3
"""
LPG Khatulistiwa — Portal LPG
Threaded HTTP server with modern UI
Composition layer: pure functions + effects.
"""
import http.server
import socketserver
import json
import mimetypes
import os
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from toolz import pipe

import effects
import pure

PORT = 5555
BASE_DIR = Path(__file__).parent
SPA_DIR = Path("/root/portal-frontend/dist")
STATIC_DIR = SPA_DIR
TEMPLATES_DIR = BASE_DIR / "templates"  # kept for fallback

SESSIONS = {}  # token -> creation_datetime
SESSION_DURATION_SECONDS = pure.SESSION_DURATION_SECONDS


def _load_auth_config():
    return effects.load_auth_config()


class PortalHandler(http.server.BaseHTTPRequestHandler):
    """Handler for portal requests"""

    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {self.address_string()} - {format % args}")

    # --- Authentication Helpers ---

    def _get_session_token(self):
        cookie = self.headers.get("Cookie", "")
        for part in cookie.split(";"):
            part = part.strip()
            if part.startswith("session="):
                return part[8:]
        return None

    def _is_authenticated(self):
        token = self._get_session_token()
        if token and token in SESSIONS:
            created = SESSIONS[token]
            if (datetime.now() - created).total_seconds() < SESSION_DURATION_SECONDS:
                return True
            del SESSIONS[token]
        return False

    def _set_session_cookie(self, location="/"):
        token = secrets.token_hex(32)
        SESSIONS[token] = datetime.now()
        self.send_response(302)
        self.send_header("Location", location)
        self.send_header(
            "Set-Cookie",
            f"session={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age={SESSION_DURATION_SECONDS}"
        )
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _clear_session_cookie(self):
        token = self._get_session_token()
        if token and token in SESSIONS:
            del SESSIONS[token]
        self.send_response(302)
        self.send_header("Location", "/login")
        self.send_header(
            "Set-Cookie",
            "session=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0"
        )
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _require_auth(self, path):
        if self._is_authenticated():
            return True
        if path.startswith("/api/"):
            self._json_response({"error": "Unauthorized — silakan login di /login"}, 401)
            return False
        next_q = f"?next={self.path}" if self.path != "/login" else ""
        self.send_response(302)
        self.send_header("Location", f"/login{next_q}")
        self.send_header("Content-Length", "0")
        self.end_headers()
        return False

    def _is_public_path(self, path):
        return pure.is_public_path(path)

    def _send_login_page(self, error=None):
        filepath = TEMPLATES_DIR / "login.html"
        if not filepath.exists():
            return self._error(500, "Login page not found")
        content = filepath.read_text(encoding="utf-8")
        if error:
            content = content.replace(
                "<!--ERROR_PLACEHOLDER-->",
                f'<div class="error-message">{error}</div>'
            )
        else:
            content = content.replace("<!--ERROR_PLACEHOLDER-->", "")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content.encode("utf-8"))))
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

    def _handle_login(self):
        qs = parse_qs(urlparse(self.path).query)
        next_url = qs.get("next", ["/"])[0]
        if not next_url or next_url == "/login":
            next_url = "/"
        if self._is_authenticated():
            self.send_response(302)
            self.send_header("Location", next_url)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        self._send_login_page()

    def _handle_login_post(self):
        qs = parse_qs(urlparse(self.path).query)
        next_url = qs.get("next", ["/"])[0]
        if not next_url or next_url == "/login":
            next_url = "/"
        try:
            cl = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(cl).decode("utf-8")
            form = parse_qs(raw)
            username = form.get("username", [""])[0].strip()
            password = form.get("password", [""])[0].strip()
        except Exception:
            username = ""
            password = ""
        config = _load_auth_config()
        if username == config.get("username") and password == config.get("password"):
            print(f"[auth] ✅ Login berhasil: {username}")
            self._set_session_cookie(location=next_url)
            return
        print(f"[auth] ❌ Login gagal: {username}")
        self._send_login_page(error="Username atau password salah")

    def _handle_logout(self):
        print(f"[auth] Logout: {self._get_session_token()}")
        self._clear_session_cookie()

    # --- HTTP Verbs ---

    def _serve_spa(self):
        """Serve the React SPA index.html for client-side routing."""
        filepath = SPA_DIR / "index.html"
        if not filepath.exists():
            return self._error(500, "SPA build not found. Run: cd /root/portal-frontend && npm run build")
        try:
            content = filepath.read_text(encoding="utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content.encode("utf-8"))))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(content.encode("utf-8"))
        except Exception as e:
            self._error(500, f"Error reading SPA: {e}")

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if not self._is_public_path(path) and not self._require_auth(path):
            return

        if path == "/login":
            # Authenticated users go straight to dashboard
            if self._is_authenticated():
                self.send_response(302)
                self.send_header("Location", "/")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            return self._serve_spa()

        if path == "/logout":
            return self._handle_logout()

        if path == "/api/health":
            return self._json_response({"status": "ok", "service": "Portal LPG"})

        if path == "/api/auth/check":
            if self._is_authenticated():
                return self._json_response({"authenticated": True})
            return self._json_response({"authenticated": False}, 401)

        if path == "/api/agen":
            return self._handle_agen_api("list")
        if path == "/api/agen/stats":
            return self._handle_agen_api("stats")
        if path == "/api/agen/detail":
            return self._handle_agen_api("detail")

        if path.startswith("/api/lpg/"):
            raw = path[len("/api/lpg/"):]
            endpoint = raw.split("?")[0]
            return self._handle_lpg_api(endpoint)

        if path == "/api/kpi/psokuota":
            return self._handle_kpi_psokuota()

        if path == "/api/kpi/npsotargets":
            return self._handle_kpi_npsotargets()

        if path == "/api/settings/targets":
            return self._handle_get_targets()

        if path == "/api/pangkalan/check":
            return self._handle_pangkalan_check()
        if path == "/api/pangkalan/stats":
            return self._handle_pangkalan_stats()
        if path == "/api/pangkalan/list":
            return self._handle_pangkalan_list()
        if path == "/api/pangkalan/export":
            return self._handle_pangkalan_export()

        if path.startswith("/static/"):
            return self._serve_static(path[len("/static/"):])

        if path.startswith("/assets/") or path.startswith("/favicon.svg") or path.startswith("/icons.svg"):
            # Served from SPA_DIR (dist)
            rel = path.lstrip("/")
            full_path = SPA_DIR / rel
            if full_path.exists() and full_path.is_file():
                ext = full_path.suffix.lower()
                content_type = pure.MIME_TYPES.get(ext, "application/octet-stream")
                try:
                    content = full_path.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", content_type)
                    self.send_header("Content-Length", str(len(content)))
                    self.send_header("Cache-Control", "max-age=3600")
                    self.end_headers()
                    self.wfile.write(content)
                    return
                except Exception as e:
                    return self._error(500, f"Error: {e}")
            return self._error(404, "Asset not found")

        page_map = {}
        if path in page_map:
            return self._serve_page(page_map[path])

        # Fallback: try static template file, then SPA
        if path in ("/", "/lpg", "/agen", "/pangkalan", "/map", "/profile-agen"):
            return self._serve_spa()
        # Try serving as template first for backward compat
        template_file = path.strip("/") + ".html"
        tmpl_path = TEMPLATES_DIR / template_file
        if tmpl_path.exists():
            return self._serve_page(template_file)

        return self._serve_spa()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path == "/login":
            return self._handle_login_post()
        if not self._require_auth(path):
            return

        return self._json_response({"error": "Not found"}, 404)

    def do_PUT(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if not self._require_auth(path):
            return

        if path == "/api/agen/update":
            return self._handle_agen_update()

        if path == "/api/settings/targets":
            return self._handle_update_targets()

        return self._json_response({"error": "Not found"}, 404)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if not self._require_auth(path):
            return

        return self._json_response({"error": "Not found"}, 404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_HEAD(self):
        self.do_GET()

    # --- Response Helpers ---

    def _serve_page(self, filename, status=200):
        filepath = TEMPLATES_DIR / filename
        if not filepath.exists():
            return self._error(404, f"Page not found: {filename}")
        try:
            content = filepath.read_text(encoding="utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content.encode("utf-8"))))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(content.encode("utf-8"))
        except Exception as e:
            self._error(500, f"Error reading page: {e}")

    def _serve_static(self, filepath):
        full_path = STATIC_DIR / filepath
        try:
            full_path = full_path.resolve()
            if not str(full_path).startswith(str(STATIC_DIR.resolve())):
                return self._error(403, "Forbidden")
        except (ValueError, OSError):
            return self._error(403, "Forbidden")

        if not full_path.exists() or not full_path.is_file():
            return self._error(404, "File not found")

        ext = full_path.suffix.lower()
        content_type = pure.MIME_TYPES.get(ext, "application/octet-stream")

        try:
            content = full_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "max-age=3600")
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self._error(500, f"Error reading file: {e}")

    def _json_response(self, data, status=200):
        content = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(content)

    def _read_json_body(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            if not content_length:
                return {}
            raw = self.rfile.read(content_length)
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON body")

    def _error(self, status, message):
        content = f"""<!DOCTYPE html>
<html lang="id">
<head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{status} — Portal LPG</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
body {{ font-family: Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif; font-size: 14px; line-height: 1.5; -webkit-font-smoothing: antialiased; text-rendering: optimizeLegibility;
display: flex; justify-content: center; align-items: center; min-height: 100vh;
margin: 0; background: #0f172a; color: #e8edf5; text-align: center; }}
.card {{ background: #1e293b; padding: 3rem; border-radius: 1rem; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5); }}
h1 {{ font-size: clamp(28px,4vw,46px); margin: 0; color: #ef4444; }}
p {{ font-size: 1.2rem; color: #7a8ba8; }}
a {{ color: #3b82f6; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
</style></head>
<body><div class="card">
<h1>{status}</h1>
<p>{message}</p>
<a href="/">&larr; Kembali ke Beranda</a>
</div></body></html>"""
        content = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    # --- Agen Handlers ---

    def _handle_agen_api(self, endpoint):
        try:
            qs = parse_qs(urlparse(self.path).query)
            result = effects.fetch_agen(endpoint, qs)
            if isinstance(result, dict) and "_error" in result:
                status = int(result.get("_status", 500))
                return self._json_response({"error": result["_error"]}, status)
            return self._json_response(result)
        except FileNotFoundError as e:
            return self._json_response({"error": str(e)}, 500)
        except Exception as e:
            return self._json_response({"error": str(e)}, 500)

    def _handle_agen_update(self):
        try:
            body = self._read_json_body()
            result = effects.update_agen(body)
            if "_error" in result:
                status = int(result.get("_status", 500))
                return self._json_response({"error": result["_error"]}, status)
            return self._json_response(result)
        except Exception as e:
            return self._json_response({"error": str(e)}, 500)

    # --- LPG Handlers ---

    def _handle_lpg_api(self, endpoint):
        try:
            qs = parse_qs(urlparse(self.path).query)
            month = qs.get("month", [None])[0]
            year = qs.get("year", [None])[0]
            district = qs.get("district", [None])[0]
            ptype = qs.get("type", ["all"])[0]

            if endpoint == "rekap":
                rows = effects.fetch_lpg_rekap(qs)
                return self._json_response(pure.format_rekap_data(rows))

            if endpoint == "rekap/export":
                rows = effects.fetch_lpg_rekap(qs)
                content = effects.export_rekap_excel(rows, None)
                self.send_response(200)
                self.send_header("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                self.send_header("Content-Disposition", "attachment; filename=rekap_agen.xlsx")
                self.send_header("Content-Length", str(len(content)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(content)
                return

            if endpoint == "performa":
                rows, monthly_rows, perf_year = effects.fetch_lpg_performa(qs)
                alokasi_data = effects.load_alokasi(perf_year)
                sort_by = qs.get("sort_by", ["pct_asc"])[0]
                try:
                    threshold = float(qs.get("threshold", ["100"])[0])
                except ValueError:
                    return self._json_response({"error": "threshold harus berupa angka"}, 400)
                data_rows = pure.format_performa_data(rows, alokasi_data, sort_by)
                total_alokasi = sum(r["alokasi"] for r in data_rows)
                total_realisasi = sum(r["realisasi_mt"] for r in data_rows)
                over_perform = [r for r in data_rows if r["pct_realisasi"] >= 100 and r["alokasi"] > 0]
                prognosis_data = pure.calculate_prognosis(monthly_rows, perf_year, total_alokasi)
                data = {
                    "summary": {
                        "total_wilayah": len(data_rows),
                        "total_alokasi": round(total_alokasi, 2),
                        "total_realisasi": round(total_realisasi, 2),
                        "avg_pct": round(total_realisasi / total_alokasi * 100, 2) if total_alokasi else 0,
                        "over_perform_count": len(over_perform),
                        "threshold": threshold,
                        "tahun": perf_year,
                        "alokasi_loaded": len(alokasi_data) > 0,
                    },
                    "prognosis": prognosis_data,
                    "data": data_rows,
                }
                return self._json_response(data)

            where, params = pure.raw_where(ptype, month, year, district)
            result = effects.fetch_lpg_data(endpoint, qs, where, params)
            if isinstance(result, dict) and "_error" in result:
                status = int(result.get("_status", 500))
                return self._json_response({"error": result["_error"]}, status)
            return self._json_response(result)
        except FileNotFoundError as e:
            return self._json_response({"error": str(e)}, 500)
        except Exception as e:
            return self._json_response({"error": str(e)}, 500)

    # --- Pangkalan Handlers ---

    def _handle_pangkalan_check(self):
        try:
            qs = parse_qs(urlparse(self.path).query)
            result = effects.fetch_pangkalan_check(qs)
            if "_error" in result:
                status = int(result.get("_status", 500))
                return self._json_response({"error": result["_error"]}, status)
            return self._json_response(result)
        except FileNotFoundError as e:
            return self._json_response({"error": str(e)}, 500)
        except Exception as e:
            return self._json_response({"error": str(e)}, 500)

    def _handle_pangkalan_stats(self):
        try:
            return self._json_response(effects.fetch_pangkalan_stats())
        except FileNotFoundError as e:
            return self._json_response({"error": str(e)}, 500)
        except Exception as e:
            return self._json_response({"error": str(e)}, 500)

    def _handle_pangkalan_list(self):
        try:
            qs = parse_qs(urlparse(self.path).query)
            result = effects.fetch_pangkalan_list(qs)
            if "_error" in result:
                status = int(result.get("_status", 500))
                return self._json_response({"error": result["_error"]}, status)
            return self._json_response(result)
        except FileNotFoundError as e:
            return self._json_response({"error": str(e)}, 500)
        except Exception as e:
            return self._json_response({"error": str(e)}, 500)

    def _handle_pangkalan_export(self):
        try:
            qs = parse_qs(urlparse(self.path).query)
            content = effects.export_pangkalan_excel(qs)
            self.send_response(200)
            self.send_header("Content-Type", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            self.send_header("Content-Disposition", "attachment; filename=pangkalan.xlsx")
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            return self._json_response({"error": str(e)}, 500)


    # --- KPI & Settings Handlers ---

    @staticmethod
    def _and_year(yr):
        if yr: return f" AND SUBSTR(cal_year_month,4) = '{yr}'"
        return ""

    @staticmethod
    def _and_month(mo):
        if mo: return f" AND cal_year_month LIKE '{mo}.%'"
        return ""

    def _handle_kpi_psokuota(self):
        """PSO realisasi vs kuota per wilayah."""
        try:
            from urllib.parse import parse_qs
            qs = parse_qs(urlparse(self.path).query)
            perf_year = qs.get("year", ["2026"])[0]
            perf_month = qs.get("month", [None])[0]
            perf_type = qs.get("type", ["PSO"])[0]
            from pure import raw_where
            where, params = raw_where(perf_type, perf_month, perf_year, None)
            db = effects.get_lpg_db()
            try:
                rows = db.execute(f"""
                    SELECT sales_district AS wilayah,
                           SUM(billing_qty_mt) AS realisasi_mt,
                           COUNT(*) AS transaksi
                    FROM raw_data{where}
                    GROUP BY sales_district
                    ORDER BY sales_district
                """, params).fetchall()
            finally:
                db.close()
            alokasi = effects.load_alokasi(perf_year)
            # Hitung bulan berjalan dari data realisasi
            months_elapsed = 6
            if perf_month and perf_month != 'all':
                months_elapsed = int(perf_month)
            else:
                # Ambil bulan terakhir dari data
                db2 = effects.get_lpg_db()
                latest = db2.execute(f"""
                    SELECT MAX(SUBSTR(cal_year_month,4,4) || '-' || SUBSTR(cal_year_month,1,2)) as ym
                    FROM raw_data{where}
                """, params).fetchone()
                if latest and latest["ym"]:
                    parts = latest["ym"].split('-')
                    months_elapsed = int(parts[1])  # month number
                db2.close()
            result = []
            for row in rows:
                wil = row["wilayah"]
                real = float(row["realisasi_mt"] or 0)
                kuota = float(alokasi.get(wil, 0))
                pct_thn = (real / kuota * 100) if kuota else 0
                proyeksi = (real / months_elapsed * 12) if months_elapsed else 0
                result.append({
                    "wilayah": wil,
                    "realisasi_mt": round(real, 2),
                    "kuota_tahunan": round(kuota, 2),
                    "pct_realisasi": round(pct_thn, 2),
                    "proyeksi_akhir_tahun": round(proyeksi, 2),
                    "status": "aman" if pct_thn <= 100 else "perhatian",
                })
            for wil, kuota in alokasi.items():
                if kuota and not any(r["wilayah"] == wil for r in result):
                    result.append({
                        "wilayah": wil, "realisasi_mt": 0,
                        "kuota_tahunan": round(float(kuota), 2),
                        "pct_realisasi": 0, "proyeksi_akhir_tahun": 0,
                        "status": "kritis",
                    })
            result.sort(key=lambda r: r["pct_realisasi"])
            total_real = sum(r["realisasi_mt"] for r in result)
            total_kuota = sum(r["kuota_tahunan"] for r in result)
            total_proy = (total_real / months_elapsed * 12) if months_elapsed else 0
            return self._json_response({
                "tahun": perf_year, "bulan_berjalan": months_elapsed,
                "data": result,
                "total_realisasi": round(total_real, 2),
                "total_kuota": round(total_kuota, 2),
                "proyeksi_akhir_tahun": round(total_proy, 2),
            })
        except Exception as e:
            return self._json_response({"error": str(e)}, 500)

    def _handle_kpi_npsotargets(self):
        try:
            from urllib.parse import parse_qs
            qs = parse_qs(urlparse(self.path).query)
            perf_year = qs.get("year", ["2026"])[0]
            perf_month = qs.get("month", [None])[0]
            targets = effects.load_npso_targets()
            db = effects.get_lpg_db()
            try:
                rt_row = db.execute(f"""
                    SELECT SUM(billing_qty_mt) as mt FROM raw_data 
                    WHERE kategori = 'NPSO RT' {self._and_year(perf_year)} {self._and_month(perf_month)}
                """).fetchone()
                nrt_row = db.execute(f"""
                    SELECT SUM(billing_qty_mt) as mt FROM raw_data 
                    WHERE kategori = 'NPSO NRT' {self._and_year(perf_year)} {self._and_month(perf_month)}
                """).fetchone()
            finally:
                db.close()
            rt_real = float(rt_row["mt"] or 0); nrt_real = float(nrt_row["mt"] or 0)
            # Hitung bulan berjalan
            months_elapsed = 7  # default July
            if perf_month and perf_month != 'all':
                months_elapsed = int(perf_month)
            def make_seg(label, real, target):
                pct = (real / target * 100) if target else 0
                proy = (real / months_elapsed * 12) if months_elapsed else 0
                return {"label": label, "realisasi_mt": round(real, 2), "target_tahunan": round(target, 2), "pct_realisasi": round(pct, 2), "proyeksi_akhir_tahun": round(proy, 2)}
            return self._json_response({
                "tahun": perf_year,
                "bulan_berjalan": months_elapsed,
                "segments": [
                    make_seg("NPSO_RT", rt_real, float(targets.get("NPSO_RT", 0))),
                    make_seg("NPSO_NRT", nrt_real, float(targets.get("NPSO_NRT", 0))),
                ],
            })
        except Exception as e:
            return self._json_response({"error": str(e)}, 500)

    def _handle_get_targets(self):
        return self._json_response(effects.load_npso_targets())

    def _handle_update_targets(self):
        try:
            body = self._read_json_body()
            import json as j
            path = effects.ALOKASI_JSON
            data = j.loads(path.read_text(encoding="utf-8"))
            data["npso_targets"] = {
                "NPSO_RT": float(body.get("NPSO_RT", data.get("npso_targets", {}).get("NPSO_RT", 0))),
                "NPSO_NRT": float(body.get("NPSO_NRT", data.get("npso_targets", {}).get("NPSO_NRT", 0))),
            }
            data["metadata"]["last_updated"] = __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M")
            path.write_text(j.dumps(data, indent=2), encoding="utf-8")
            return self._json_response({"success": True, "message": "Target berhasil disimpan"})
        except Exception as e:
            return self._json_response({"error": str(e)}, 500)


class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def main():
    print(f"╔══════════════════════════════════════════╗")
    print(f"║       🚀 LPG Khatulistiwa — Portal          ║")
    print(f"╠══════════════════════════════════════════╣")
    print(f"║  Server:  https://lpg.khatulistiwa.cloud  ║")
    print(f"║  Apps:    LPG · KPI                      ║")
    auth = _load_auth_config()
    print(f"║  Auth:   ✓ Login required (user: {auth['username']})   ║")
    print(f"║  Threads: ✓                             ║")
    print(f"╚══════════════════════════════════════════╝")
    print()

    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    STATIC_DIR.mkdir(parents=True, exist_ok=True)

    server = ThreadedHTTPServer(("0.0.0.0", PORT), PortalHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n⏹  Server stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
