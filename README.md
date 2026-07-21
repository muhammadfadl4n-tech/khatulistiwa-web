# 🌐 Khatulistiwa Web — Monorepo

Kumpulan aplikasi web yang di-deploy di ekosistem **khatulistiwa.cloud**.

## 📦 Daftar Aplikasi

```
khatulistiwa-web/
│
├── doze-app/              📝 Doze Task Manager
│   → React + Vite + Tailwind + PWA
│   → Dark cozy productivity theme
│   → doze.khatulistiwa.cloud (port 5565)
│
├── portal-lpg/            ⛽ Portal LPG
│   ├── frontend/          React + Vite + shadcn/ui
│   └── backend/           Python Flask API
│       Dashboard KPI Agen LPG Kalbar
│       → lpg.khatulistiwa.cloud (port 5555)
│
├── landing/               🌍 Landing Page
│   → Static HTML/CSS
│   → khatulistiwa.cloud
│
├── beritakalbar/          📰 Berita Kalbar
│   → Python Flask
│   → beritakalbar.khatulistiwa.cloud
│
├── stok-material/         📦 Stok Material
│   ├── client/            React frontend
│   └── server/            Node.js backend
│   → stok.khatulistiwa.cloud (port 3008)
│
└── qq-spbu/               ⛽ QQ-SPBU
    → Python Flask + Gunicorn + PostgreSQL
    → qq-spbu.khatulistiwa.cloud (port 5560)
```

## 🚀 Deployment

| App | Domain | Port | Stack |
|-----|--------|------|-------|
| Portal LPG | [lpg.khatulistiwa.cloud](https://lpg.khatulistiwa.cloud) | 5555 | React + Flask |
| Doze | [doze.khatulistiwa.cloud](https://doze.khatulistiwa.cloud) | 5565 | React + Vite |
| Landing | [khatulistiwa.cloud](https://khatulistiwa.cloud) | Static | HTML/CSS |
| Berita Kalbar | beritakalbar.khatulistiwa.cloud | - | Flask |
| Stok Material | [stok.khatulistiwa.cloud](https://stok.khatulistiwa.cloud) | 3008 | React + Node.js |
| QQ-SPBU | qq-spbu.khatulistiwa.cloud | 5560 | Flask + PostgreSQL |

## 🛠 Tech Stack

- **Frontend:** React 19, Vite 8, Tailwind CSS v4, shadcn/ui
- **Backend:** Python Flask, Node.js
- **Infra:** Nginx, Let's Encrypt SSL
- **Design:** NeedMCP Design Tokens

---
*Powered by Hermes Agent*
