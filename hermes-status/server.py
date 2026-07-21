#!/usr/bin/env python3
"""Hermes Status Dashboard — single-file http.server on port 5002.

Serves a dark-themed responsive dashboard with live system metrics collected
via subprocess calls. No external dependencies beyond the Python stdlib.
"""

import glob
import json
import os
import re
import socket
import subprocess
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

PORT = 5002
HOST = "0.0.0.0"
CRON_OUTPUT_DIR = Path.home() / ".hermes" / "cron" / "output"


def sh(cmd, default=""):
    """Run a shell command and return stripped stdout."""
    try:
        return subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return default


def uptime_text():
    raw = sh("uptime -p", "")
    if raw:
        return raw.replace("up ", "").strip()
    # Fallback for systems without -p
    raw = sh("uptime", "")
    if raw:
        return raw.split(",")[0]
    return "unknown"


def boot_time():
    try:
        secs = float(sh("awk '{print $1}' /proc/uptime", "0"))
        bt = datetime.now() - __import__("datetime").timedelta(seconds=secs)
        return bt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return "unknown"


def cpu_info():
    model = sh("awk -F: '/model name/{print $2; exit}' /proc/cpuinfo", "Unknown").strip()
    cores = sh("nproc", "0")
    load = sh("awk '{print $1, $2, $3}' /proc/loadavg", "0 0 0")
    usage = sh("top -bn1 | awk '/^%Cpu/{print int($2)}'", "")
    if not usage:
        usage = sh("awk '/cpu /{u=$2+$4; t=$2+$4+$5; if(t>0) print int(100*u/t)}' /proc/stat")
    try:
        usage_val = int(usage or 0)
    except ValueError:
        usage_val = 0
    return {"model": model, "cores": cores, "load": load, "usage": usage_val}


def mem_info():
    total = sh("awk '/MemTotal/{print int($2/1024)}' /proc/meminfo", "0")
    free = sh("awk '/MemAvailable/{print int($2/1024)}' /proc/meminfo", "0")
    buffers = sh("awk '/Buffers/{print int($2/1024)}' /proc/meminfo", "0")
    cached = sh("awk '/^Cached:/{print int($2/1024)}' /proc/meminfo", "0")
    try:
        t, f, b, c = int(total), int(free), int(buffers), int(cached)
        used = t - f
        pct = int((used / t) * 100) if t else 0
    except ValueError:
        t = f = used = pct = 0
    return {
        "total_mb": t,
        "free_mb": f,
        "used_mb": used,
        "used_percent": pct,
    }


def disk_info():
    out = sh("df -h / | awk 'NR==2{print $2, $3, $4, $5}'", "")
    parts = out.split()
    if len(parts) >= 4:
        return {
            "total": parts[0],
            "used": parts[1],
            "free": parts[2],
            "used_percent": int(parts[3].rstrip("%") or 0),
        }
    return {"total": "-", "used": "-", "free": "-", "used_percent": 0}


def check_port(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(("127.0.0.1", port)) == 0


def service_name(port):
    names = {
        5000: "Monitoring LPG Pangkalan",
        5001: "Berita Kalbar",
        5002: "Hermes Status Dashboard",
        5555: "Portal 5555 (LPG/Agen/Itinerary)",
    }
    return names.get(port, f"Port {port}")


def services_status():
    ports = [5555, 5000, 5001, 5002]
    result = []
    for p in ports:
        result.append({"port": p, "name": service_name(p), "up": check_port(p)})
    return result


def network_info():
    hostname = sh("hostname", "unknown")
    ip = sh("hostname -I | awk '{print $1}'", "127.0.0.1")
    default_iface = sh("ip route | awk '/default/{print $5; exit}'", "unknown")
    public_ip = sh("curl -s --max-time 3 https://api.ipify.org", "")
    return {
        "hostname": hostname,
        "local_ip": ip,
        "default_interface": default_iface,
        "public_ip": public_ip or "unavailable",
    }


def cron_jobs():
    if not CRON_OUTPUT_DIR.exists():
        return []
    jobs = []
    for job_dir in sorted(CRON_OUTPUT_DIR.iterdir()):
        if not job_dir.is_dir():
            continue
        md_files = sorted(job_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not md_files:
            continue
        latest = md_files[0]
        content = latest.read_text(encoding="utf-8", errors="ignore")
        title_match = re.search(r"^# Cron Job:\s*(.+)$", content, re.MULTILINE)
        schedule_match = re.search(r"^\*\*Schedule:\*\*\s*(.+)$", content, re.MULTILINE)
        status = "ok"
        if "[SILENT]" in content:
            status = "silent"
        if "error" in content.lower() or "failed" in content.lower() or "gagal" in content.lower():
            status = "error"
        mtime = datetime.fromtimestamp(latest.stat().st_mtime, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        jobs.append({
            "id": job_dir.name,
            "title": title_match.group(1).strip() if title_match else job_dir.name,
            "schedule": schedule_match.group(1).strip() if schedule_match else "unknown",
            "last_run": mtime,
            "status": status,
            "latest_file": latest.name,
        })
    return jobs


def collect_metrics():
    return {
        "uptime": uptime_text(),
        "boot_time": boot_time(),
        "cpu": cpu_info(),
        "memory": mem_info(),
        "disk": disk_info(),
        "services": services_status(),
        "network": network_info(),
        "cron_jobs": cron_jobs(),
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
    }


INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Hermes Status Dashboard</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0f0f1a;
      --surface: #1a1a2e;
      --surface-2: #252542;
      --accent: #7c3aed;
      --accent-light: #8b5cf6;
      --text: #e2e8f0;
      --text-muted: #94a3b8;
      --success: #22c55e;
      --warning: #f59e0b;
      --danger: #ef4444;
      --info: #3b82f6;
      --radius: 16px;
    }
    * { box-sizing: border-box; }
    html, body { margin: 0; padding: 0; }
    body {
      background: var(--bg);
      color: var(--text);
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      min-height: 100vh;
    }
    header {
      background: rgba(26, 26, 46, 0.8);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid rgba(255,255,255,0.06);
      padding: 18px 24px;
      position: sticky;
      top: 0;
      z-index: 10;
    }
    .header-inner {
      max-width: 1200px;
      margin: 0 auto;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      flex-wrap: wrap;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .brand-logo {
      width: 38px;
      height: 38px;
      background: linear-gradient(135deg, var(--accent), var(--accent-light));
      border-radius: 10px;
      display: grid;
      place-items: center;
      font-weight: 700;
      color: #fff;
      font-size: 18px;
    }
    .brand h1 {
      margin: 0;
      font-size: 1.25rem;
      font-weight: 700;
      letter-spacing: -0.02em;
    }
    .brand small {
      color: var(--text-muted);
      font-size: 0.75rem;
      display: block;
      margin-top: 2px;
    }
    .header-meta {
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 0.8rem;
      color: var(--text-muted);
    }
    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--success);
      box-shadow: 0 0 8px var(--success);
      animation: pulse 2s infinite;
    }
    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }
    .container {
      max-width: 1200px;
      margin: 0 auto;
      padding: 24px;
    }
    .grid {
      display: grid;
      gap: 16px;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    }
    .card {
      background: var(--surface);
      border: 1px solid rgba(255,255,255,0.05);
      border-radius: var(--radius);
      padding: 20px;
      transition: transform 0.15s ease, border-color 0.15s ease;
    }
    .card:hover {
      border-color: rgba(124, 58, 237, 0.35);
      transform: translateY(-2px);
    }
    .card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 16px;
    }
    .card-title {
      font-size: 0.85rem;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.06em;
      margin: 0;
    }
    .card-icon {
      width: 34px;
      height: 34px;
      border-radius: 10px;
      background: rgba(124, 58, 237, 0.12);
      color: var(--accent-light);
      display: grid;
      place-items: center;
      font-size: 1.1rem;
    }
    .metric {
      font-size: 2rem;
      font-weight: 700;
      margin: 0;
      line-height: 1.1;
    }
    .metric-sub {
      color: var(--text-muted);
      font-size: 0.85rem;
      margin-top: 8px;
      line-height: 1.5;
    }
    .progress {
      height: 8px;
      background: rgba(255,255,255,0.06);
      border-radius: 99px;
      margin-top: 14px;
      overflow: hidden;
    }
    .progress-fill {
      height: 100%;
      border-radius: 99px;
      transition: width 0.6s ease;
    }
    .fill-cpu { background: linear-gradient(90deg, #3b82f6, #8b5cf6); }
    .fill-mem { background: linear-gradient(90deg, #f59e0b, #ef4444); }
    .fill-disk { background: linear-gradient(90deg, #22c55e, #10b981); }
    .services-list {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .service-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 10px 12px;
      background: var(--surface-2);
      border-radius: 10px;
    }
    .service-name { font-weight: 500; font-size: 0.9rem; }
    .service-port { color: var(--text-muted); font-size: 0.8rem; margin-left: 6px; }
    .badge {
      font-size: 0.7rem;
      font-weight: 700;
      padding: 4px 10px;
      border-radius: 99px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .badge-up { background: rgba(34, 197, 94, 0.15); color: var(--success); }
    .badge-down { background: rgba(239, 68, 68, 0.15); color: var(--danger); }
    .cron-list {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .cron-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px;
      background: var(--surface-2);
      border-radius: 10px;
      gap: 12px;
    }
    .cron-title { font-weight: 500; font-size: 0.9rem; }
    .cron-meta { color: var(--text-muted); font-size: 0.75rem; margin-top: 3px; }
    .cron-status { flex-shrink: 0; }
    .badge-ok { background: rgba(34, 197, 94, 0.15); color: var(--success); }
    .badge-error { background: rgba(239, 68, 68, 0.15); color: var(--danger); }
    .badge-silent { background: rgba(148, 163, 184, 0.15); color: var(--text-muted); }
    .wide { grid-column: 1 / -1; }
    @media (min-width: 900px) {
      .wide-2 { grid-column: span 2; }
    }
    footer {
      text-align: center;
      color: var(--text-muted);
      font-size: 0.75rem;
      padding: 24px;
      border-top: 1px solid rgba(255,255,255,0.05);
      margin-top: 12px;
    }
    .skeleton {
      background: linear-gradient(90deg, rgba(255,255,255,0.04) 25%, rgba(255,255,255,0.09) 50%, rgba(255,255,255,0.04) 75%);
      background-size: 200% 100%;
      animation: shimmer 1.2s infinite;
      border-radius: 6px;
      color: transparent;
    }
    @keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
    .error-banner {
      background: rgba(239, 68, 68, 0.12);
      border: 1px solid rgba(239, 68, 68, 0.25);
      color: #fecaca;
      padding: 12px 16px;
      border-radius: var(--radius);
      margin-bottom: 16px;
      display: none;
    }
  </style>
</head>
<body>
  <header>
    <div class="header-inner">
      <div class="brand">
        <div class="brand-logo">⚕</div>
        <div>
          <h1>Hermes Status Dashboard</h1>
          <small>Live server health &amp; service monitor</small>
        </div>
      </div>
      <div class="header-meta">
        <span class="status-dot"></span>
        <span id="refreshText">Loading…</span>
      </div>
    </div>
  </header>

  <main class="container">
    <div id="errorBanner" class="error-banner"></div>
    <div class="grid" id="dashboard">
      <!-- Cards rendered by JS -->
    </div>
  </main>

  <footer>
    Served on port 5002 · Hermes Status Dashboard · <span id="footerTime">—</span>
  </footer>

  <script>
    const $ = (sel) => document.querySelector(sel);

    function esc(s) {
      return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    }

    function card(icon, title, body, extraClass = '') {
      return `<div class="card ${extraClass}">
        <div class="card-header">
          <h2 class="card-title">${esc(title)}</h2>
          <div class="card-icon">${icon}</div>
        </div>
        ${body}
      </div>`;
    }

    function progressBar(percent, cls) {
      return `<div class="progress"><div class="progress-fill ${cls}" style="width:${Math.min(100, Math.max(0, percent))}%"></div></div>`;
    }

    function renderSkeleton() {
      $('#dashboard').innerHTML = Array.from({length: 6}).map((_, i) =>
        card('⏳', 'Loading', `<div class="metric skeleton">---</div><div class="metric-sub skeleton">---</div>`, i < 2 ? 'wide-2' : '')
      ).join('');
    }

    function render(data) {
      const cpu = data.cpu || {};
      const mem = data.memory || {};
      const disk = data.disk || {};
      const net = data.network || {};
      const services = data.services || [];
      const cron = data.cron_jobs || [];

      const cards = [];

      cards.push(card('⏱️', 'System Uptime', `
        <div class="metric">${esc(data.uptime || 'unknown')}</div>
        <div class="metric-sub">Booted: ${esc(data.boot_time || 'unknown')}<br>Last updated: ${esc(data.timestamp || '—')}</div>
      `, 'wide-2'));

      cards.push(card('🌐', 'Network', `
        <div class="metric" style="font-size:1.15rem; line-height:1.5;">
          ${esc(net.hostname || '—')}<br>
          <span style="color:var(--text-muted); font-weight:500;">${esc(net.local_ip || '—')}</span>
        </div>
        <div class="metric-sub">
          Interface: ${esc(net.default_interface || '—')} · Public IP: ${esc(net.public_ip || '—')}
        </div>
      `, 'wide-2'));

      cards.push(card('🖥️', 'CPU', `
        <div class="metric">${cpu.usage ?? 0}%</div>
        <div class="metric-sub">${esc(cpu.model || '—')} · ${esc(cpu.cores || '0')} cores<br>Load: ${esc(cpu.load || '—')}</div>
        ${progressBar(cpu.usage ?? 0, 'fill-cpu')}
      `));

      cards.push(card('💾', 'Memory', `
        <div class="metric">${mem.used_percent ?? 0}%</div>
        <div class="metric-sub">Used ${esc(mem.used_mb || 0)} / ${esc(mem.total_mb || 0)} MB<br>Free: ${esc(mem.free_mb || 0)} MB</div>
        ${progressBar(mem.used_percent ?? 0, 'fill-mem')}
      `));

      cards.push(card('💿', 'Disk Usage', `
        <div class="metric">${disk.used_percent ?? 0}%</div>
        <div class="metric-sub">Used ${esc(disk.used || '—')} / ${esc(disk.total || '—')}<br>Free: ${esc(disk.free || '—')}</div>
        ${progressBar(disk.used_percent ?? 0, 'fill-disk')}
      `));

      const svcBody = `<div class="services-list">${services.map(s => `
        <div class="service-row">
          <div>
            <span class="service-name">${esc(s.name)}</span>
            <span class="service-port">:${s.port}</span>
          </div>
          <span class="badge ${s.up ? 'badge-up' : 'badge-down'}">${s.up ? 'Online' : 'Offline'}</span>
        </div>
      `).join('')}</div>`;
      cards.push(card('🧩', 'Running Services', svcBody, 'wide-2'));

      const cronBody = cron.length ? `<div class="cron-list">${cron.map(c => `
        <div class="cron-row">
          <div>
            <div class="cron-title">${esc(c.title)}</div>
            <div class="cron-meta">${esc(c.schedule)} · ${esc(c.last_run)} · ${esc(c.latest_file)}</div>
          </div>
          <span class="cron-status badge badge-${c.status}">${esc(c.status)}</span>
        </div>
      `).join('')}</div>` : `<div class="metric-sub">No cron job output found in ~/.hermes/cron/output/</div>`;
      cards.push(card('⏰', 'Cron Jobs', cronBody, 'wide'));

      $('#dashboard').innerHTML = cards.join('');
      $('#refreshText').textContent = 'Updated ' + new Date().toLocaleTimeString();
      $('#footerTime').textContent = data.timestamp || '—';
      $('#errorBanner').style.display = 'none';
    }

    function showError(msg) {
      const el = $('#errorBanner');
      el.textContent = msg;
      el.style.display = 'block';
    }

    async function fetchData() {
      try {
        const res = await fetch('/api/status');
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const data = await res.json();
        render(data);
      } catch (err) {
        showError('Failed to load status: ' + err.message);
      }
    }

    renderSkeleton();
    fetchData();
    setInterval(fetchData, 10000);
  </script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _send(self, status, content_type, body, extra_headers=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
        self.end_headers()
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/")
        if path == "" or path == "/":
            self._send(200, "text/html; charset=utf-8", INDEX_HTML)
        elif path == "/api/status":
            metrics = collect_metrics()
            self._send(200, "application/json; charset=utf-8", json.dumps(metrics, ensure_ascii=False))
        elif path == "/health":
            self._send(200, "text/plain; charset=utf-8", "ok")
        else:
            self._send(404, "text/plain; charset=utf-8", "Not found")


def main():
    server = HTTPServer((HOST, PORT), Handler)
    print(f"Hermes Status Dashboard serving on http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == "__main__":
    main()
