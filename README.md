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

# 📸 Demo

| Feature          | Preview       |
| ---------------- | ------------- |
| Map Discovery    | *coming soon* |
| Cat Gallery      | *coming soon* |
| AI Cat Detection | *coming soon* |

Live Demo
👉 https://purrfect-spots.vercel.app
👉 https://purrfectspots.xyz

---

# ✨ Features

### 🗺️ Discover Cat Locations

Explore cat sightings shared by the community through an interactive location-based map.

### 🐱 AI Cat Detection

Images uploaded by users are analyzed using **Google Vision AI** to verify the presence of cats.

### 🔐 Enterprise-Grade Security

* Rate Limiting (Redis)
* CSRF Protection
* Strict Input Validation (Pydantic / Zod)
* GitHub Security Scanning
* Automated Trivy vulnerability scanning
* CodeQL static analysis

### ⚡ Performance & Observability

* Distributed tracing with **Jaeger**
* Error monitoring with **Sentry**
* Structured logging

### 🗄️ Secure Data Layer

* PostgreSQL (Supabase)
* Row Level Security (RLS)
* Object storage via AWS S3

---

# 🏗️ System Architecture

```
Frontend (Vue 3 + Vite + TypeScript)
        │
        ▼
   FastAPI Backend
        │
        ├── PostgreSQL (Supabase)
        ├── Redis Cache
        ├── AWS S3 Storage
        └── Google Vision AI
```

Infrastructure:

```
Docker
Nginx
GitHub Actions CI/CD
Vercel Deployment
```

---

# 🧰 Technology Stack

## Frontend

* Vue 3
* Vite
* TypeScript
* Pinia
* TailwindCSS

## Backend

* Python 3.12
* FastAPI (Async)
* SQLAlchemy
* Pydantic

## Infrastructure

* Supabase (PostgreSQL)
* Redis
* AWS S3
* Docker
* Nginx
* GitHub Actions

---

# 🚀 Quick Start

## 1️⃣ Clone the repository

```bash
git clone https://github.com/ChaLconner/purrfect-spots.git
cd purrfect-spots
```

---

## 2️⃣ Setup Environment Variables

```
cp .env.example .env
```

Then configure:

* Supabase credentials
* Google Vision API
* Sentry DSN
* Redis URL

See full configuration:

```
docs/ENV_SETUP.md
```

---

# 🧑‍💻 Local Development

## Backend

```bash
cd backend

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt

uvicorn main:app --reload
```

---

## Frontend

```bash
cd frontend

npm install
npm run dev
```

# 📚 Documentation

Full documentation lives inside the **docs directory**.

| Document                                 | Description               |
| ---------------------------------------- | ------------------------- |
| [docs/README.md](file:///c:/purrfect-spots/docs/README.md)                           | Documentation Hub         |
| [docs/DATABASE_SCHEMA.md](file:///c:/purrfect-spots/docs/DATABASE_SCHEMA.md)                  | Database schema           |
| [docs/ENV_SETUP.md](file:///c:/purrfect-spots/docs/ENV_SETUP.md)                        | Environment configuration |
| [docs/STRIPE_SETUP.md](file:///c:/purrfect-spots/docs/STRIPE_SETUP.md)                     | Stripe Payment Setup      |
| [docs/PRODUCTION_GUIDE.md](file:///c:/purrfect-spots/docs/PRODUCTION_GUIDE.md)                 | Production Deployment     |
| [docs/DESIGN_TOKENS.md](file:///c:/purrfect-spots/docs/DESIGN_TOKENS.md)                    | UI design system          |

---

# 📂 Project Structure

```
backend/
  middleware/
  routes/
  services/
  utils/

frontend/
  src/components
  src/views
  src/stores
  src/composables

docs/
```

---

# 🔐 Security

Security scanning is fully automated.

Tools used:

* GitHub CodeQL
* Trivy container scanning
* Dependabot
* Secret scanning

All pull requests must pass security checks before merging.

---

# 📄 License

MIT License

---

# 👨‍💻 Maintainer

Maintained by:

**ChaLconner**

If you like the project, consider giving it a ⭐
