#!/usr/bin/env python3
"""Daily Activity Dashboard — REST API server.

Zero external dependencies. Uses Python http.server + json + uuid.
Serves index.html on GET /, data.json file persistence on port 5561.
"""

import http.server
import json
import os
import uuid
import re
import datetime
import urllib.parse

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_data(activities):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(activities, f, indent=2, ensure_ascii=False)

def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def today_str():
    return datetime.datetime.now().strftime("%Y-%m-%d")

def parse_path(path):
    """Parse request path, return (route, params) where params are extracted from path."""
    # Strip query string for path matching
    path = urllib.parse.urlparse(path).path
    # /api/today
    if path == "/api/today":
        return ("today", {})
    # /api/week
    if path == "/api/week":
        return ("week", {})
    # /api/activities
    if path == "/api/activities":
        return ("activities", {})
    # /api/activities/:id
    m = re.match(r"^/api/activities/([a-f0-9\-]+)$", path)
    if m:
        return ("activity_detail", {"id": m.group(1)})
    # /api/activities/:id/status
    m = re.match(r"^/api/activities/([a-f0-9\-]+)/status$", path)
    if m:
        return ("activity_status", {"id": m.group(1)})
    # /api/reminder
    if path == "/api/reminder":
        return ("reminder", {})
    return ("static", {"path": path})


class ActivityHandler(http.server.BaseHTTPRequestHandler):

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, PATCH, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, text, status=200, content_type="text/plain; charset=utf-8"):
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}

    def _parse_query(self):
        parsed = urllib.parse.urlparse(self.path)
        return urllib.parse.parse_qs(parsed.query)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, PATCH, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        route, params = parse_path(self.path)

        if route == "today":
            data = load_data()
            today = today_str()
            items = [a for a in data if a["date"] == today]
            items.sort(key=lambda x: x.get("time", "00:00"))
            self._send_json(items)

        elif route == "week":
            data = load_data()
            today = datetime.datetime.now()
            week_dates = set()
            for i in range(7):
                d = today + datetime.timedelta(days=i)
                week_dates.add(d.strftime("%Y-%m-%d"))
            items = [a for a in data if a["date"] in week_dates]
            items.sort(key=lambda x: (x["date"], x.get("time", "00:00")))
            self._send_json(items)

        elif route == "activities":
            data = load_data()
            qs = self._parse_query()
            if "date" in qs:
                date_val = qs["date"][0]
                data = [a for a in data if a["date"] == date_val]
            if "status" in qs:
                status_val = qs["status"][0]
                data = [a for a in data if a["status"] == status_val]
            data.sort(key=lambda x: (x["date"], x.get("time", "00:00")))
            self._send_json(data)

        elif route == "activity_detail":
            data = load_data()
            item = next((a for a in data if a["id"] == params["id"]), None)
            if item is None:
                self._send_json({"error": "Not found"}, 404)
            else:
                self._send_json(item)

        elif route == "reminder":
            data = load_data()
            now = datetime.datetime.now()
            results = []
            for a in data:
                if a["status"] != "pending":
                    continue
                if a["date"] != today_str():
                    continue
                try:
                    h, m = a["time"].split(":")
                    activity_dt = now.replace(hour=int(h), minute=int(m), second=0, microsecond=0)
                    diff = (activity_dt - now).total_seconds()
                    if 0 <= diff <= 300:  # within 5 minutes
                        results.append(a)
                except (ValueError, IndexError):
                    continue
            self._send_json(results)

        elif route == "static":
            file_path = params["path"]
            if file_path == "/" or file_path == "":
                file_path = "/index.html"
            full_path = os.path.normpath(os.path.join(STATIC_DIR, file_path.lstrip("/")))
            if not full_path.startswith(STATIC_DIR):
                self._send_json({"error": "Forbidden"}, 403)
                return
            if not os.path.isfile(full_path):
                self._send_json({"error": "Not found"}, 404)
                return
            ext = os.path.splitext(full_path)[1].lower()
            mime_map = {
                ".html": "text/html; charset=utf-8",
                ".css": "text/css; charset=utf-8",
                ".js": "application/javascript; charset=utf-8",
                ".json": "application/json; charset=utf-8",
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".gif": "image/gif",
                ".svg": "image/svg+xml",
                ".ico": "image/x-icon",
            }
            mime = mime_map.get(ext, "application/octet-stream")
            with open(full_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        else:
            self._send_json({"error": "Not found"}, 404)

    def do_POST(self):
        route, params = parse_path(self.path)

        if route == "activities":
            body = self._read_body()
            if not body.get("title") or not body.get("date") or not body.get("time"):
                self._send_json({"error": "date, time, and title are required"}, 400)
                return
            activity = {
                "id": str(uuid.uuid4()),
                "date": body["date"],
                "time": body["time"],
                "title": body["title"],
                "note": body.get("note", ""),
                "status": "pending",
                "created_at": now_iso(),
                "updated_at": now_iso(),
            }
            data = load_data()
            data.append(activity)
            save_data(data)
            self._send_json(activity, 201)

        else:
            self._send_json({"error": "Not found"}, 404)

    def do_PUT(self):
        route, params = parse_path(self.path)
        if route == "activity_detail":
            body = self._read_body()
            data = load_data()
            for i, a in enumerate(data):
                if a["id"] == params["id"]:
                    if "title" in body:
                        a["title"] = body["title"]
                    if "date" in body:
                        a["date"] = body["date"]
                    if "time" in body:
                        a["time"] = body["time"]
                    if "note" in body:
                        a["note"] = body["note"]
                    if "status" in body:
                        a["status"] = body["status"]
                    a["updated_at"] = now_iso()
                    data[i] = a
                    save_data(data)
                    self._send_json(a)
                    return
            self._send_json({"error": "Not found"}, 404)
        else:
            self._send_json({"error": "Not found"}, 404)

    def do_DELETE(self):
        route, params = parse_path(self.path)
        if route == "activity_detail":
            data = load_data()
            for i, a in enumerate(data):
                if a["id"] == params["id"]:
                    deleted = data.pop(i)
                    save_data(data)
                    self._send_json(deleted)
                    return
            self._send_json({"error": "Not found"}, 404)
        else:
            self._send_json({"error": "Not found"}, 404)

    def do_PATCH(self):
        route, params = parse_path(self.path)
        if route == "activity_status":
            body = self._read_body()
            if "status" not in body or body["status"] not in ("completed", "pending", "cancelled"):
                self._send_json({"error": "status must be completed, pending, or cancelled"}, 400)
                return
            data = load_data()
            for i, a in enumerate(data):
                if a["id"] == params["id"]:
                    a["status"] = body["status"]
                    a["updated_at"] = now_iso()
                    data[i] = a
                    save_data(data)
                    self._send_json(a)
                    return
            self._send_json({"error": "Not found"}, 404)
        else:
            self._send_json({"error": "Not found"}, 404)

    def log_message(self, format, *args):
        # Quieter logging
        print(f"[{self.log_date_time_string()}] {args[0]}" if args else "")


def run():
    port = 5561
    server = http.server.HTTPServer(("0.0.0.0", port), ActivityHandler)
    print(f"🌙 Daily Activity Dashboard running on http://0.0.0.0:{port}")
    print(f"📁 Data file: {DATA_FILE}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    run()
