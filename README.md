# 🐱 Purrfect Spots

[![CI Pipeline](https://github.com/ChaLconner/purrfect-spots/actions/workflows/ci.yml/badge.svg)](https://github.com/ChaLconner/purrfect-spots/actions/workflows/ci.yml)
[![Production Deployment](https://github.com/ChaLconner/purrfect-spots/actions/workflows/deploy.yml/badge.svg)](https://github.com/ChaLconner/purrfect-spots/actions/workflows/deploy.yml)
[![CodeQL Security](https://github.com/ChaLconner/purrfect-spots/actions/workflows/codeql.yml/badge.svg)](https://github.com/ChaLconner/purrfect-spots/actions/workflows/codeql.yml)
[![Release](https://github.com/ChaLconner/purrfect-spots/actions/workflows/release.yml/badge.svg)](https://github.com/ChaLconner/purrfect-spots/actions/workflows/release.yml)

**Connect · Share · Discover**

Purrfect Spots is a modern social platform where cat lovers can **share, discover, and explore locations of adorable cats around the world**.

Users can upload photos, automatically detect cats using AI, and visualize their locations on an interactive map.

The platform is designed with a **Ghibli-inspired aesthetic** and built using **modern cloud-native architecture**.

---

# 📸 Demo & Status

| Feature          | Tech Stack / Implementation | Status |
| ---------------- | -------------------------- | ------ |
| Map Discovery    | Vue 3 + Google Maps API (`@googlemaps/markerclusterer`) | Available |
| Cat Gallery      | Vue 3 + `vue-virtual-scroller` | Available |
| AI Cat Detection | FastAPI + Google Vision AI API | Available |

Live Demo:
👉 https://purrfect-spots.vercel.app
👉 https://purrfectspots.xyz

---

# ✨ Features

### 🗺️ Discover Cat Locations
Explore cat sightings shared by the community through an interactive location-based map.

### 🐱 AI Cat Detection
Images uploaded by users are analyzed using **Google Vision AI** to verify the presence of cats.

### 🔐 Enterprise-Grade Security
* Rate Limiting (Redis 7.4)
* CSRF Protection & Security Headers
* Strict Input Validation (Pydantic / Zod)
* GitHub Security Scanning (TruffleHog, Semgrep)
* Automated Trivy vulnerability scanning
* CodeQL static analysis

### ⚡ Performance & Observability
* Distributed tracing with **Jaeger** / OpenTelemetry
* Error monitoring with **Sentry**
* Structured logging (`structlog`)

### 🗄️ Secure Data Layer
* PostgreSQL (Supabase) with Row Level Security (RLS)
* Object storage via AWS S3

---

# 🏗️ System Architecture

```
Frontend (Vue 3 + Vite + TypeScript)
        │
        ▼
   FastAPI Backend
        │
        ├── PostgreSQL (Supabase RLS)
        ├── Redis (Isolated Caching & Rate Limiting)
        ├── AWS S3 Storage
        └── Google Vision AI
```

---

# 🧰 Technology Stack

## Frontend (Vue 3 + TypeScript)
* **Framework**: Vue 3 (Composition API `<script setup lang="ts">`)
* **Language**: TypeScript 5.x
* **Build Tool**: Vite 8
* **State Management**: Pinia 3
* **Styling**: Tailwind CSS v4
* **API Client**: `@purrfect-spots/api-client` (OpenAPI Spec)
* **Testing**: Vitest (Unit), Playwright (E2E)

## Backend
* **Language**: Python 3.14
* **Framework**: FastAPI (Async)
* **ORM & Database**: SQLAlchemy (Asyncpg) + Supabase PostgreSQL
* **Validation**: Pydantic v2
* **Caching & Limits**: Redis 7.4 (Isolated Caching & Rate Limiting)

## Infrastructure & CI/CD
* Supabase (PostgreSQL + RLS)
* Redis 7.4 (Alpine)
* AWS S3 Object Storage
* Docker / Docker Compose
* GitHub Actions CI/CD (Node.js 24.x, Python 3.14.x)

---

# 🚀 Quick Start

## 1️⃣ Clone the repository

```bash
git clone https://github.com/ChaLconner/purrfect-spots.git
cd purrfect-spots
```

---

## 2️⃣ Setup Environment Variables

```bash
cp .env.example .env
```

Configure environment credentials in:
- [Root environment template](.env.example)
- [Frontend environment template](frontend/.env.example)
- [Backend environment template](backend/.env.example)

---

# 🧑‍💻 Local Development

## Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r backend/requirements.txt
uvicorn app.main:app --reload
```

---

## Frontend

```bash
cd frontend
npm install
npm run dev
```

---

# 📚 Documentation

Full documentation lives inside the **docs directory**.

| Document | Description |
| -------- | ----------- |
| [docs/README.md](docs/README.md) | Documentation hub |
| [System architecture](docs/architecture/ARCHITECTURE.md) | System architecture |
| [Project structure](docs/architecture/PROJECT_STRUCTURE.md) | Folder and dependency rules |
| [Coding standards](docs/development/CODING_STANDARDS.md) | Coding standards |
| [Git guidelines](docs/development/GIT_GUIDELINES.md) | Git and pull request rules |
| [Design tokens](docs/development/DESIGN_TOKENS.md) | UI design system |
| [OpenAPI baseline](docs/openapi-baseline.json) | Machine-readable API contract |

---

# 📂 Project Structure

```
backend/
  app/
    middleware/
    routes/
    schemas/
    services/
    utils/
  api/
  migrations/
  scripts/
  tests/

frontend/
  src/components
  src/generated
  src/views
  src/stores
  src/composables

packages/
  api-client/

supabase/
  migrations/

docs/
```

---

# 🔐 Security

Security scanning is fully automated:
* GitHub CodeQL
* Trivy container scanning
* Dependabot
* Secret scanning (TruffleHog & Semgrep)

All pull requests must pass security checks before merging.

---

# 📄 License

MIT License

---

# 👨‍💻 Maintainer

Maintained by **ChaLconner**.
