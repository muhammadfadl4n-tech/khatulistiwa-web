#!/usr/bin/env python3
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from effects import ensure_data_file, load_news_data
from pure import guess_mime, guess_mime_from_bytes, filter_berita


HOST = "0.0.0.0"
PORT = 5001
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "berita.json"


HTML_PAGE = """<!doctype html>
<html lang="id">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Berita Kalbar</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0f0f1a;
      --card: #1a1a2e;
      --card-strong: #20203a;
      --accent: #7c3aed;
      --accent-strong: #8b5cf6;
      --text: #e2e8f0;
      --muted: #94a3b8;
      --line: rgba(148, 163, 184, 0.18);
      --danger: #fb7185;
      --shadow: 0 20px 60px rgba(0, 0, 0, 0.32);
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      min-height: 100vh;
      background: var(--bg);
      color: var(--text);
      font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      letter-spacing: 0;
    }

    button,
    input {
      font: inherit;
    }

    a {
      color: inherit;
    }

    .site-shell {
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }

    .topbar {
      position: sticky;
      top: 0;
      z-index: 20;
      border-bottom: 1px solid var(--line);
      background: rgba(15, 15, 26, 0.88);
      backdrop-filter: blur(18px);
    }

    .topbar-inner,
    .main,
    .footer-inner {
      width: min(1180px, calc(100% - 32px));
      margin: 0 auto;
    }

    .topbar-inner {
      display: flex;
      align-items: center;
      justify-content: space-between;
      min-height: 76px;
      gap: 20px;
    }

    .brand {
      display: flex;
      flex-direction: column;
      gap: 4px;
      min-width: 180px;
    }

    .brand-title {
      margin: 0;
      color: var(--text);
      font-size: clamp(1.45rem, 3vw, 2rem);
      font-weight: 800;
      letter-spacing: 0;
      line-height: 1.05;
    }

    .brand-subtitle {
      color: var(--muted);
      font-size: 0.86rem;
      font-weight: 500;
    }

    .status-pill {
      flex: 0 0 auto;
      display: inline-flex;
      align-items: center;
      gap: 9px;
      color: var(--muted);
      border: 1px solid var(--line);
      background: rgba(26, 26, 46, 0.74);
      border-radius: 999px;
      padding: 9px 13px;
      font-size: 0.86rem;
      white-space: nowrap;
    }

    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 999px;
      background: var(--accent-strong);
      box-shadow: 0 0 0 5px rgba(124, 58, 237, 0.18);
    }

    .main {
      flex: 1;
      padding: 34px 0 44px;
    }

    .controls {
      display: grid;
      grid-template-columns: minmax(220px, 1fr) auto;
      gap: 16px;
      align-items: start;
      margin-bottom: 28px;
    }

    .date-filters {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: flex-end;
      gap: 8px;
    }

    .date-filters label {
      color: var(--muted);
      font-size: 0.86rem;
      font-weight: 500;
    }

    .date-input {
      min-height: 40px;
      padding: 0 12px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--card);
      color: var(--text);
      outline: none;
      font-size: 0.9rem;
      transition: border-color 160ms ease, box-shadow 160ms ease, background 160ms ease;
    }

    .date-input:focus {
      border-color: rgba(124, 58, 237, 0.78);
      box-shadow: 0 0 0 4px rgba(124, 58, 237, 0.18);
      background: #1d1d34;
    }

    .date-input::-webkit-calendar-picker-indicator {
      filter: invert(0.8);
      cursor: pointer;
    }

    .search-wrap {
      position: relative;
    }

    .search-wrap svg {
      position: absolute;
      left: 16px;
      top: 50%;
      transform: translateY(-50%);
      width: 20px;
      height: 20px;
      color: var(--muted);
      pointer-events: none;
    }

    .search-input {
      width: 100%;
      min-height: 48px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--card);
      color: var(--text);
      outline: none;
      padding: 0 16px 0 48px;
      transition: border-color 160ms ease, box-shadow 160ms ease, background 160ms ease;
    }

    .search-input::placeholder {
      color: #64748b;
    }

    .search-input:focus {
      border-color: rgba(124, 58, 237, 0.78);
      box-shadow: 0 0 0 4px rgba(124, 58, 237, 0.18);
      background: #1d1d34;
    }

    .filters {
      display: flex;
      flex-wrap: wrap;
      justify-content: flex-end;
      gap: 8px;
    }

    .filter-btn,
    .page-btn,
    .modal-close {
      border: 1px solid var(--line);
      background: var(--card);
      color: var(--muted);
      border-radius: 8px;
      cursor: pointer;
      transition: transform 160ms ease, border-color 160ms ease, color 160ms ease, background 160ms ease;
    }

    .filter-btn {
      min-height: 40px;
      padding: 0 13px;
      font-size: 0.9rem;
      font-weight: 700;
    }

    .filter-btn:hover,
    .page-btn:hover,
    .modal-close:hover {
      transform: translateY(-1px);
      border-color: rgba(124, 58, 237, 0.68);
      color: var(--text);
    }

    .filter-btn.active,
    .page-btn.active {
      background: var(--accent);
      border-color: var(--accent);
      color: #ffffff;
    }

    .results-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      color: var(--muted);
      font-size: 0.94rem;
      margin-bottom: 16px;
    }

    .news-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 18px;
    }

    .news-card {
      min-height: 338px;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--card);
      cursor: pointer;
      box-shadow: 0 12px 34px rgba(0, 0, 0, 0.12);
      transition: transform 180ms ease, border-color 180ms ease, box-shadow 180ms ease, background 180ms ease;
    }

    .news-card:hover {
      transform: translateY(-4px);
      border-color: rgba(124, 58, 237, 0.62);
      background: var(--card-strong);
      box-shadow: var(--shadow);
    }

    .thumb {
      position: relative;
      height: 164px;
      background:
        linear-gradient(135deg, rgba(124, 58, 237, 0.48), rgba(14, 165, 233, 0.2)),
        #151526;
      overflow: hidden;
    }

    .thumb img {
      width: 100%;
      height: 100%;
      display: block;
      object-fit: cover;
      transition: transform 240ms ease;
    }

    .news-card:hover .thumb img {
      transform: scale(1.045);
    }

    .thumb-fallback {
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
      color: rgba(226, 232, 240, 0.84);
      font-weight: 800;
      text-align: center;
      line-height: 1.2;
    }

    .card-body {
      display: flex;
      flex: 1;
      flex-direction: column;
      padding: 16px;
      gap: 12px;
    }

    .meta {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 8px;
      color: var(--muted);
      font-size: 0.82rem;
      font-weight: 600;
    }

    .category {
      display: inline-flex;
      align-items: center;
      min-height: 24px;
      border-radius: 999px;
      padding: 0 10px;
      background: rgba(124, 58, 237, 0.18);
      color: #c4b5fd;
    }

    .card-title {
      margin: 0;
      color: var(--text);
      font-size: 1.08rem;
      line-height: 1.34;
      font-weight: 800;
    }

    .excerpt {
      margin: 0;
      color: var(--muted);
      font-size: 0.94rem;
      line-height: 1.6;
      display: -webkit-box;
      -webkit-box-orient: vertical;
      -webkit-line-clamp: 3;
      overflow: hidden;
    }

    .card-source {
      margin-top: auto;
      padding-top: 4px;
      color: #cbd5e1;
      font-size: 0.86rem;
      font-weight: 700;
    }

    .pagination {
      display: flex;
      justify-content: center;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 28px;
    }

    .page-btn {
      min-width: 42px;
      min-height: 40px;
      padding: 0 12px;
      font-weight: 800;
    }

    .empty-state,
    .error-state {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--card);
      color: var(--muted);
      padding: 34px;
      text-align: center;
    }

    .error-state {
      color: var(--danger);
    }

    .footer {
      border-top: 1px solid var(--line);
      background: #0c0c15;
    }

    .footer-inner {
      min-height: 78px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--muted);
      text-align: center;
      font-size: 0.94rem;
    }

    .modal {
      position: fixed;
      inset: 0;
      z-index: 50;
      display: none;
      align-items: center;
      justify-content: center;
      padding: 20px;
      background: rgba(3, 7, 18, 0.78);
      backdrop-filter: blur(12px);
    }

    .modal.open {
      display: flex;
      animation: fadeIn 160ms ease both;
    }

    .modal-panel {
      width: min(860px, 100%);
      max-height: min(84vh, 860px);
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--card);
      box-shadow: var(--shadow);
      animation: liftIn 180ms ease both;
    }

    .modal-image {
      height: min(320px, 38vh);
      background:
        linear-gradient(135deg, rgba(124, 58, 237, 0.5), rgba(20, 184, 166, 0.18)),
        #151526;
    }

    .modal-image img {
      width: 100%;
      height: 100%;
      display: block;
      object-fit: cover;
    }

    .modal-content {
      padding: 24px;
    }

    .modal-head {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 14px;
    }

    .modal-title {
      margin: 0;
      color: var(--text);
      font-size: clamp(1.45rem, 3.4vw, 2.35rem);
      line-height: 1.16;
      font-weight: 800;
    }

    .modal-close {
      flex: 0 0 auto;
      width: 42px;
      height: 42px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      color: var(--text);
      font-size: 1.35rem;
      line-height: 1;
    }

    .modal-text {
      color: #cbd5e1;
      font-size: 1rem;
      line-height: 1.75;
      white-space: pre-wrap;
    }

    .source-link {
      display: inline-flex;
      align-items: center;
      margin-top: 20px;
      color: #c4b5fd;
      font-weight: 800;
      text-decoration: none;
    }

    .source-link:hover {
      text-decoration: underline;
    }

    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }

    @keyframes liftIn {
      from { opacity: 0; transform: translateY(14px) scale(0.98); }
      to { opacity: 1; transform: translateY(0) scale(1); }
    }

    @media (max-width: 920px) {
      .controls {
        grid-template-columns: 1fr;
      }

      .filters {
        justify-content: flex-start;
      }

      .news-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
    }

    @media (max-width: 640px) {
      .topbar-inner,
      .main,
      .footer-inner {
        width: min(100% - 24px, 1180px);
      }

      .topbar-inner {
        align-items: flex-start;
        flex-direction: column;
        justify-content: center;
        padding: 14px 0;
        gap: 12px;
      }

      .status-pill {
        white-space: normal;
      }

      .main {
        padding-top: 24px;
      }

      .news-grid {
        grid-template-columns: 1fr;
      }

      .news-card {
        min-height: 0;
      }

      .modal {
        align-items: stretch;
        padding: 10px;
      }

      .modal-panel {
        max-height: none;
        height: 100%;
      }

      .modal-content {
        padding: 18px;
      }
    }
  </style>
</head>
<body>
  <div class="site-shell">
    <header class="topbar">
      <div class="topbar-inner">
        <div class="brand">
          <h1 class="brand-title">Berita Kalbar</h1>
          <div class="brand-subtitle">Portal berita Kalimantan Barat</div>
        </div>
        <div class="status-pill" aria-live="polite"><span class="status-dot"></span><span id="todayLabel">Memuat berita...</span></div>
      </div>
    </header>

    <main class="main">
      <section class="controls" aria-label="Kontrol berita">
        <div class="search-wrap">
          <svg aria-hidden="true" viewBox="0 0 24 24" fill="none">
            <path d="m21 21-4.3-4.3m1.3-5.2a6.5 6.5 0 1 1-13 0 6.5 6.5 0 0 1 13 0Z" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          <input id="searchInput" class="search-input" type="search" placeholder="Cari judul atau isi berita..." autocomplete="off">
        </div>
        <div id="filters" class="filters" aria-label="Filter kategori"></div>
        <div class="search-wrap">
          <div class="date-filters" aria-label="Filter tanggal">
            <label for="dateFrom">Dari</label>
            <input id="dateFrom" class="date-input" type="date">
            <label for="dateTo">Ke</label>
            <input id="dateTo" class="date-input" type="date">
          </div>
        </div>
      </section>

      <div class="results-row">
        <span id="resultCount">Memuat...</span>
        <span id="pageInfo"></span>
      </div>

      <section id="newsGrid" class="news-grid" aria-live="polite"></section>
      <div id="pagination" class="pagination" aria-label="Paginasi"></div>
    </main>

    <footer class="footer">
      <div class="footer-inner">Berita Kalbar - Portal Berita Kalimantan Barat</div>
    </footer>
  </div>

  <div id="modal" class="modal" role="dialog" aria-modal="true" aria-labelledby="modalTitle">
    <article class="modal-panel">
      <div id="modalImage" class="modal-image"></div>
      <div class="modal-content">
        <div class="modal-head">
          <div>
            <div id="modalMeta" class="meta"></div>
            <h2 id="modalTitle" class="modal-title"></h2>
          </div>
          <button id="modalClose" class="modal-close" type="button" aria-label="Tutup">&times;</button>
        </div>
        <div id="modalText" class="modal-text"></div>
        <a id="modalLink" class="source-link" href="#" target="_blank" rel="noopener noreferrer">Buka sumber berita</a>
      </div>
    </article>
  </div>

  <script>
    const categories = ["Semua", "LPG", "BBM", "Pertamina"];
    const perPage = 12;
    let articles = [];
    let filtered = [];
    let activeCategory = "Semua";
    let searchTerm = "";
    let dateFrom = "";
    let dateTo = "";
    let currentPage = 1;

    const grid = document.getElementById("newsGrid");
    const filters = document.getElementById("filters");
    const searchInput = document.getElementById("searchInput");
    const resultCount = document.getElementById("resultCount");
    const pageInfo = document.getElementById("pageInfo");
    const pagination = document.getElementById("pagination");
    const todayLabel = document.getElementById("todayLabel");
    const dateFromInput = document.getElementById("dateFrom");
    const dateToInput = document.getElementById("dateTo");
    const modal = document.getElementById("modal");
    const modalImage = document.getElementById("modalImage");
    const modalMeta = document.getElementById("modalMeta");
    const modalTitle = document.getElementById("modalTitle");
    const modalText = document.getElementById("modalText");
    const modalLink = document.getElementById("modalLink");
    const modalClose = document.getElementById("modalClose");

    function escapeHtml(value) {
      return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }

    function formatDate(value) {
      if (!value) return "";
      const date = new Date(`${value}T00:00:00`);
      if (Number.isNaN(date.getTime())) return value;
      return new Intl.DateTimeFormat("id-ID", {
        day: "2-digit",
        month: "long",
        year: "numeric"
      }).format(date);
    }

    const BASE_PATH = window.location.pathname.replace(/\\/[^/]*$/, '') || '/';
    function imgPath(path) {
      if (path.startsWith('/') && BASE_PATH !== '/') {
        return BASE_PATH + path;
      }
      return path;
    }
    function articleImage(article, className = "") {
      if (article.gambar) {
        const src = escapeHtml(imgPath(article.gambar));
        return `<img src="${src}" alt="${escapeHtml(article.judul)}" loading="lazy" onerror="this.parentElement.innerHTML='<div class=&quot;thumb-fallback&quot;>Berita Kalbar</div>'">`;
      }
      return `<div class="thumb-fallback ${className}">Berita Kalbar</div>`;
    }

    function renderFilters() {
      filters.innerHTML = categories.map((category) => `
        <button class="filter-btn ${category === activeCategory ? "active" : ""}" type="button" data-category="${escapeHtml(category)}">
          ${escapeHtml(category)}
        </button>
      `).join("");
    }

    function applyFilters() {
      const term = searchTerm.trim().toLowerCase();
      filtered = articles.filter((article) => {
        const matchesCategory = activeCategory === "Semua" || article.kategori === activeCategory;
        const matchesDate = (!dateFrom || (article.tanggal || "") >= dateFrom) && (!dateTo || (article.tanggal || "") <= dateTo);
        const haystack = `${article.judul || ""} ${article.highlight || ""} ${article.isi || ""} ${article.sumber || ""}`.toLowerCase();
        return matchesCategory && matchesDate && (!term || haystack.includes(term));
      });
      currentPage = Math.min(currentPage, Math.max(1, Math.ceil(filtered.length / perPage)));
      render();
    }

    function render() {
      const totalPages = Math.max(1, Math.ceil(filtered.length / perPage));
      const start = (currentPage - 1) * perPage;
      const pageItems = filtered.slice(start, start + perPage);

      resultCount.textContent = `${filtered.length} berita ditemukan`;
      pageInfo.textContent = filtered.length ? `Halaman ${currentPage} dari ${totalPages}` : "";

      if (!pageItems.length) {
        grid.innerHTML = `<div class="empty-state">Tidak ada berita yang cocok dengan pencarian ini.</div>`;
      } else {
        grid.innerHTML = pageItems.map((article) => `
          <article class="news-card" tabindex="0" role="button" data-id="${article.id}" aria-label="${escapeHtml(article.judul)}">
            <div class="thumb">${articleImage(article)}</div>
            <div class="card-body">
              <div class="meta">
                <span class="category">${escapeHtml(article.kategori)}</span>
                <span>${escapeHtml(formatDate(article.tanggal))}</span>
              </div>
              <h2 class="card-title">${escapeHtml(article.judul)}</h2>
              <p class="excerpt">${escapeHtml(article.highlight || article.isi)}</p>
              <div class="card-source">${escapeHtml(article.sumber)}</div>
            </div>
          </article>
        `).join("");
      }

      renderPagination(totalPages);
    }

    function renderPagination(totalPages) {
      if (totalPages <= 1) {
        pagination.innerHTML = "";
        return;
      }

      const buttons = [];
      buttons.push(`<button class="page-btn" type="button" data-page="${Math.max(1, currentPage - 1)}" ${currentPage === 1 ? "disabled" : ""}>Prev</button>`);
      for (let page = 1; page <= totalPages; page += 1) {
        buttons.push(`<button class="page-btn ${page === currentPage ? "active" : ""}" type="button" data-page="${page}">${page}</button>`);
      }
      buttons.push(`<button class="page-btn" type="button" data-page="${Math.min(totalPages, currentPage + 1)}" ${currentPage === totalPages ? "disabled" : ""}>Next</button>`);
      pagination.innerHTML = buttons.join("");
    }

    function openArticle(id) {
      const article = articles.find((item) => String(item.id) === String(id));
      if (!article) return;

      modalImage.innerHTML = articleImage(article, "modal-fallback");
      modalMeta.innerHTML = `
        <span class="category">${escapeHtml(article.kategori)}</span>
        <span>${escapeHtml(formatDate(article.tanggal))}</span>
        <span>${escapeHtml(article.sumber)}</span>
      `;
      modalTitle.textContent = article.judul || "";
      modalText.textContent = article.isi || "";
      modalLink.href = article.url || "#";
      modalLink.style.display = article.url ? "inline-flex" : "none";
      modal.classList.add("open");
      document.body.style.overflow = "hidden";
      modalClose.focus();
    }

    function closeModal() {
      modal.classList.remove("open");
      document.body.style.overflow = "";
    }

    filters.addEventListener("click", (event) => {
      const button = event.target.closest("button[data-category]");
      if (!button) return;
      activeCategory = button.dataset.category;
      currentPage = 1;
      renderFilters();
      loadNews();
    });

    searchInput.addEventListener("input", (event) => {
      searchTerm = event.target.value;
      currentPage = 1;
      applyFilters();
    });

    dateFromInput.addEventListener("input", (event) => {
      dateFrom = event.target.value;
      currentPage = 1;
      loadNews();
    });

    dateToInput.addEventListener("input", (event) => {
      dateTo = event.target.value;
      currentPage = 1;
      loadNews();
    });

    grid.addEventListener("click", (event) => {
      const card = event.target.closest(".news-card");
      if (card) openArticle(card.dataset.id);
    });

    grid.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" && event.key !== " ") return;
      const card = event.target.closest(".news-card");
      if (!card) return;
      event.preventDefault();
      openArticle(card.dataset.id);
    });

    pagination.addEventListener("click", (event) => {
      const button = event.target.closest("button[data-page]");
      if (!button || button.disabled) return;
      currentPage = Number(button.dataset.page);
      render();
      window.scrollTo({ top: 0, behavior: "smooth" });
    });

    modalClose.addEventListener("click", closeModal);
    modal.addEventListener("click", (event) => {
      if (event.target === modal) closeModal();
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && modal.classList.contains("open")) closeModal();
    });

    async function loadNews() {
      renderFilters();
      todayLabel.textContent = new Intl.DateTimeFormat("id-ID", {
        weekday: "long",
        day: "2-digit",
        month: "long",
        year: "numeric"
      }).format(new Date());

      try {
        const params = new URLSearchParams();
        if (activeCategory !== "Semua") params.set("kategori", activeCategory);
        if (dateFrom) params.set("date_from", dateFrom);
        if (dateTo) params.set("date_to", dateTo);
        const query = params.toString() ? `?${params.toString()}` : "";
        const response = await fetch(`/api/berita${query}`, { headers: { "Accept": "application/json" } });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const payload = await response.json();
        articles = Array.isArray(payload.berita) ? payload.berita : [];
        articles.sort((a, b) => String(b.tanggal || "").localeCompare(String(a.tanggal || "")) || Number(b.id || 0) - Number(a.id || 0));
        filtered = articles.slice();
        applyFilters();
      } catch (error) {
        console.error(error);
        resultCount.textContent = "Gagal memuat berita";
        pageInfo.textContent = "";
        grid.innerHTML = `<div class="error-state">Data berita tidak dapat dimuat. Periksa file data/berita.json.</div>`;
      }
    }

    loadNews();
  </script>
</body>
</html>
"""


class BeritaKalbarHandler(BaseHTTPRequestHandler):
    server_version = "BeritaKalbarHTTP/1.0"

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path == "/":
            self.send_text(HTML_PAGE, "text/html; charset=utf-8")
            return

        if path == "/api/berita":
            query = parse_qs(parsed.query)
            date_from = query.get("date_from", [""])[0].strip() or None
            date_to = query.get("date_to", [""])[0].strip() or None
            kategori = query.get("kategori", [""])[0].strip() or None
            data = load_news_data(DATA_FILE)
            filtered = filter_berita(
                data.get("berita", []),
                date_from=date_from,
                date_to=date_to,
                kategori=kategori,
            )
            response = {"berita": filtered}
            if data.get("error"):
                response["error"] = data["error"]
            self.send_json(response)
            return

        if path.startswith("/static/"):
            file_path = BASE_DIR / path.lstrip("/")
            if file_path.exists() and file_path.is_file():
                raw = file_path.read_bytes()
                content_type = guess_mime_from_bytes(raw, file_path.suffix.lstrip("."))
                self.send_text(raw, content_type)
                return

        self.send_error(404, "Halaman tidak ditemukan")

    def do_HEAD(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            return

        if path == "/api/berita":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            return

        if path.startswith("/static/"):
            file_path = BASE_DIR / path.lstrip("/")
            if file_path.exists() and file_path.is_file():
                raw = file_path.read_bytes()
                content_type = guess_mime_from_bytes(raw, file_path.suffix.lstrip("."))
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(raw)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                return

        self.send_error(404, "Halaman tidak ditemukan")

    def send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def send_text(self, text, content_type="text/plain; charset=utf-8", status=200):
        body = text if isinstance(text, bytes) else text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print("%s - - [%s] %s" % (self.client_address[0], self.log_date_time_string(), fmt % args))


def main():
    ensure_data_file(DATA_FILE)
    mimetypes.add_type("application/json", ".json")
    httpd = ThreadingHTTPServer((HOST, PORT), BeritaKalbarHandler)
    print(f"Berita Kalbar running at http://{HOST}:{PORT}")
    print(f"Serving data from {DATA_FILE}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
