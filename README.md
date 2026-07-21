# 🌐 Khatulistiwa Web — Monorepo

Kumpulan aplikasi web yang di-deploy di **khatulistiwa.cloud**.

## 📦 Struktur

```
khatulistiwa-web/
├── doze-app/           # 📝 Doze Task Manager
│   └── React + Vite + Tailwind CSS + PWA
│       Dark cozy productivity theme
│       → doze.khatulistiwa.cloud
│
├── portal-lpg/         # ⛽ Portal LPG
│   ├── frontend/       # React + Vite + shadcn/ui
│   └── backend/        # Python Flask API
│       Dashboard KPI Agen LPG Kalbar
│       → lpg.khatulistiwa.cloud
│
└── landing/            # 🌍 Landing Page
    └── Static HTML/CSS
        → khatulistiwa.cloud
```

## 🚀 Deployment

| App | Domain | Port | Stack |
|-----|--------|------|-------|
| Portal LPG | [lpg.khatulistiwa.cloud](https://lpg.khatulistiwa.cloud) | `:5555` | React + Flask |
| Doze | [doze.khatulistiwa.cloud](https://doze.khatulistiwa.cloud) | `:5565` | React + Vite |
| Landing | [khatulistiwa.cloud](https://khatulistiwa.cloud) | Static | HTML/CSS |

## 🛠 Tech Stack

- **Frontend:** React 19, Vite 8, Tailwind CSS v4, shadcn/ui
- **Backend:** Python Flask
- **Infra:** Nginx, Let's Encrypt SSL
- **Design:** NeedMCP Design Tokens

---
*Powered by Hermes Agent*
