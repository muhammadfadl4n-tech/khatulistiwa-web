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
├── portal/                🔧 Portal LPG Backend (legacy)
│   → Python Flask
│
├── landing/               🌍 Landing Page
│   → Static HTML/CSS
│   → khatulistiwa.cloud
│
├── beritakalbar/          📰 Berita Kalbar
│   → Python Flask
│   → beritakalbar.khatulistiwa.cloud
│
├── pangkalan-map/         🗺️ Pangkalan Map
│   → Python Flask
│
├── stok-material/         📦 Stok Material
│   ├── client/            React frontend
│   └── server/            Node.js backend
│   → stok.khatulistiwa.cloud (port 3008)
│
├── forma/                 📋 Forms
│   → React
│   → forms.khatulistiwa.cloud (port 3007)
│
├── web-pangkalan/         🏪 Web Pangkalan
│   → Python Flask
│
├── daily-activity/        📊 Daily Activity
│   → Python Flask
│   → mydaily.khatulistiwa.cloud (port 5561)
│
├── file-manager/          📁 File Manager
│   → Python Flask
│
└── hermes-status/         🤖 Hermes Status
    → Python Flask
```

## 🚀 Deployment

| App | Domain | Port | Stack |
|-----|--------|------|-------|
| Portal LPG | [lpg.khatulistiwa.cloud](https://lpg.khatulistiwa.cloud) | 5555 | React + Flask |
| Doze | [doze.khatulistiwa.cloud](https://doze.khatulistiwa.cloud) | 5565 | React + Vite |
| Landing | [khatulistiwa.cloud](https://khatulistiwa.cloud) | Static | HTML/CSS |
| Berita Kalbar | beritakalbar.khatulistiwa.cloud | - | Flask |
| Stok Material | [stok.khatulistiwa.cloud](https://stok.khatulistiwa.cloud) | 3008 | React + Node.js |
| MyDaily | mydaily.khatulistiwa.cloud | 5561 | Flask |

## 🛠 Tech Stack

- **Frontend:** React 19, Vite 8, Tailwind CSS v4, shadcn/ui
- **Backend:** Python Flask, Node.js
- **Infra:** Nginx, Let's Encrypt SSL
- **Design:** NeedMCP Design Tokens

---
*Powered by Hermes Agent*
