# CareLens 2.0 — Modern Decoupled Enterprise Platform (FastAPI + Next.js 14)

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%20%7C%20OpenAPI%203.1-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2014%20App%20Router-black.svg)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/Language-TypeScript%205-blue.svg)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Styling-Tailwind%20CSS-38B2AC.svg)](https://tailwindcss.com/)
[![Docker](https://img.shields.io/badge/Deployment-Docker%20Compose-2496ED.svg)](https://www.docker.com/)
[![Status](https://img.shields.io/badge/Version-2.0.0--enterprise-success.svg)](#)

---

## Executive Overview

**CareLens 2.0** is the enterprise-grade evolution of the CareLens clinical bone tumor screening system. Engineered to overcome the scalability, security, and interface limitations of the monolithic prototype, Version 2.0 transforms CareLens into a decoupled, high-performance client/server web application.

The platform pairs a high-throughput **FastAPI** asynchronous REST backend with a modern **Next.js 14 App Router** React frontend, delivering an interactive clinical workspace with hardware-accelerated radiograph zoom/pan viewing, automated diagnostic PDF report generation, and hospital-grade security compliance.

```
+-----------------------------------------------------------------------------------------------+
|                                  CareLens 2.0 Architecture                                    |
|                                                                                               |
|   +---------------------------------------------------------------------------------------+   |
|   |                         Next.js 14 App Router Frontend (Port 3000)                    |   |
|   |  - React 18, TypeScript, Tailwind CSS, TanStack Query                                 |   |
|   |  - Interactive Zoom/Pan Radiograph Viewer (Canvas Hardware Acceleration)              |   |
|   |  - Clinician Triage Queue & Clinical Review Workspace                                 |   |
|   |  - In-Memory JWT Access Token + Silent Refresh via HTTPOnly Cookie                     |   |
|   +-------------------------------------------+-------------------------------------------+   |
|                                               |                                               |
|                      REST API / OpenAPI 3.1.0 | JSON & Form-Data                              |
|                      Bearer JWT Authorization | HTTPOnly Refresh Cookie                       |
|                                               v                                               |
|   +---------------------------------------------------------------------------------------+   |
|   |                         FastAPI Asynchronous Backend (Port 8000)                      |   |
|   |  - ASGI (Uvicorn) with Non-Blocking Concurrency & Pydantic v2 Schemas                 |   |
|   |  - Security: Bcrypt Hashing, JWT Rotation, 5-Attempt Lockout (15m Cooldown)           |   |
|   |  - Media Gateway: Strict Per-Case ID Ownership & Authorization Verification           |   |
|   |  - Diagnostic PDF Generator: ReportLab Clinical Summary with Scan & Heatmap Embeds    |   |
|   +--------------------+---------------------------------------------+--------------------+   |
|                        |                                             |                        |
|                        v                                             v                        |
|   +---------------------------------------+   +-------------------------------------------+   |
|   |       PyTorch Inference Engine        |   |           Persistence & Storage           |   |
|   |  - CUDA AMP Accelerated ResNet-50     |   |  - SQLite / PostgreSQL-ready DB           |   |
|   |  - Layer4 Grad-CAM Saliency Hook      |   |  - Secure App Uploads Media Storage       |   |
|   |  - Standardized Clinical Risk Tiers   |   |  - Comprehensive Audit Trail Logging      |   |
|   +---------------------------------------+   +-------------------------------------------+   |
+-----------------------------------------------------------------------------------------------+
```

---

## Architectural Pillars of Version 2.0

### 1. High-Performance Decoupled Backend (`backend/`)
- **FastAPI & Asynchronous ASGI**: Non-blocking request handling powered by Uvicorn and Pydantic v2 data models with automatic OpenAPI 3.1.0 schema generation.
- **PyTorch CUDA AMP Inference**: Evaluates radiographs using mixed-precision (`torch.autocast`) with zero precision loss, returning probabilities and Grad-CAM maps in milliseconds.
- **Layer4 Grad-CAM Hook Extraction**: Dynamic register of forward/backward hooks on `layer4.2.conv3` of the fine-tuned ResNet-50 model, isolating malignant activation patterns.
- **Automated Clinical PDF Service**: Generates publication-ready diagnostic summary PDFs using ReportLab, embedding patient demographics, side-by-side scans, radiologist notes, and legal disclaimers.

### 2. Clinical Web Workspace (`frontend/`)
- **Interactive Radiograph Viewer**: Custom zoom/pan canvas component allowing clinicians to inspect fine trabecular and cortical bone structures:
  - Smooth mouse-wheel zooming and click-and-drag panning.
  - One-click toggle between Side-by-Side view and direct Grad-CAM overlay.
  - Normalized JET-colormap color bar for activation interpretation.
- **Physician Triage Queue**: Real-time sorting and prioritization based on AI risk tiers:
  - 🔴 **High Risk** ($\ge 0.60$) — Flagged with red urgency badges and prioritized to the top.
  - 🟡 **Borderline** ($0.35 - 0.599$) — Flagged for secondary specialist review.
  - 🟢 **Low Risk** ($< 0.35$) — Standard screening tier.
- **Strict Clinical Validation**: Prevents incomplete reviews by enforcing non-empty diagnostic verdicts, min-length clinical justifications, and post-screening management plans.

### 3. Hospital-Grade Security & Privacy Compliance
- **Dual-Token Authentication**:
  - Short-lived JWT access tokens stored exclusively in memory (mitigating XSS and `localStorage` theft).
  - Secure `httpOnly`, `SameSite=lax` refresh cookies with automatic silent renewal on 401 responses.
- **Brute-Force Account Protection**: Tracks consecutive failed login attempts; locks accounts for 15 minutes after 5 failures.
- **Per-Case Media Authorization**: The `/media/{case_id}/{image_type}` endpoint inspects caller JWT claims: patients can only access scans from their own cases; unauthorized requests receive `403 Forbidden`.
- **Upload Boundary Enforcement**: Rejects files exceeding 10MB or outside safe image bounds ($64 \times 64$ to $4096 \times 4096$ pixels).

---

## Directory Structure

```text
carelens/
├── backend/                         # FastAPI Application Service
│   ├── app/
│   │   ├── config.py                # Pydantic BaseSettings & Environment Config
│   │   ├── database.py              # SQLite Persistence Engine & Migration Guards
│   │   ├── security.py              # Bcrypt Hashing, JWT Rotation & Lockout Logic
│   │   ├── ml/
│   │   │   └── model.py             # ResNet-50 PyTorch Loader & Grad-CAM Hooks
│   │   ├── models/
│   │   │   └── schemas.py           # Pydantic Request/Response DTOs
│   │   ├── routers/
│   │   │   ├── auth.py              # Register, Login, Refresh, Logout Routes
│   │   │   ├── cases.py             # Case Creation, Triage Queue & Reviews
│   │   │   ├── media.py             # Authorized Scan & Heatmap Delivery
│   │   │   └── health.py            # System Health & Model Status Probes
│   │   ├── services/
│   │   │   ├── case_service.py      # Business Logic & Case Management
│   │   │   └── pdf_service.py       # ReportLab Diagnostic PDF Generator
│   │   └── main.py                  # FastAPI Application Factory & CORS
│   ├── tests/
│   │   └── test_api.py              # Pytest Integration Suite (4/4 Passing)
│   ├── Dockerfile                   # Python 3.11 Production Container
│   ├── openapi.json                 # Exported OpenAPI 3.1.0 Specification
│   └── run.py                       # Standalone Backend Uvicorn Runner
│
├── frontend/                        # Next.js 14 App Router Web Client
│   ├── src/
│   │   ├── app/
│   │   │   ├── login/               # Patient & Doctor Authentication Page
│   │   │   ├── register/            # Patient Account Registration Page
│   │   │   ├── upload/              # Radiograph Ingestion & Boundary Checks
│   │   │   ├── cases/               # Patient Case History & PDF Downloads
│   │   │   ├── queue/               # Clinician Triage & Priority Workspace
│   │   │   └── reviewed/            # Historical Archive of Signed Cases
│   │   ├── components/
│   │   │   ├── ui/                  # Badges, Buttons, Cards, Disclaimer Banner
│   │   │   └── zoom-pan-viewer.tsx  # Hardware-Accelerated Radiograph Viewer
│   │   ├── context/
│   │   │   └── AuthContext.tsx      # Auth State & 25m Inactivity Warning
│   │   ├── lib/
│   │   │   ├── api-client.ts        # Axios Client with Silent Token Refresh
│   │   │   └── validation.ts        # Input Boundaries & Risk Cutoffs
│   │   └── tests/
│   │       └── validation.test.ts   # Node Test Suite (19/19 Passing)
│   ├── Dockerfile                   # Multi-Stage Next.js Production Container
│   └── tailwind.config.ts           # Tailwind Clinical Design Tokens
│
├── run_carelens.py                  # Single-Command Unified Multi-Process Runner
├── start_carelens.bat               # Single-Click Windows Desktop Launcher
└── docker-compose.yml               # Container Orchestration with Healthchecks
```

---

## How to Run CareLens 2.0

### Option 1: Unified Single-Command Runner (Recommended)
Launches both the FastAPI backend and Next.js frontend concurrently. Auto-detects the virtual environment, cleans orphaned ports, verifies healthchecks, and launches the browser:

```powershell
python run_carelens.py
```
*Or double-click **`start_carelens.bat`** on Windows.*

### Option 2: Docker Compose (Production Setup)
```powershell
docker compose up --build
```
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000` (auto-monitored by Docker health probe)

### Option 3: Two-Terminal Manual Execution

**Terminal 1 — FastAPI Backend:**
```powershell
.\.venv\Scripts\python.exe backend/run.py
```
- API Docs: **[http://localhost:8000/docs](http://localhost:8000/docs)**
- Health Probe: **[http://localhost:8000/health](http://localhost:8000/health)**

**Terminal 2 — Next.js Frontend:**
```powershell
cd frontend
npm install
npm run dev
```
- Web Application: **[http://localhost:3000](http://localhost:3000)**

---

## Demo Accounts

| Role | Username | Password | Capabilities |
|---|---|---|---|
| **Clinician / Radiologist** | `doctor1` | `CareLens2026!Doctor` | Prioritized triage queue, interactive review workspace, diagnostic sign-off, PDF generation |
| **Patient** | `patient1` | `CareLens2026!Patient` | Scan upload with boundary checks, real-time risk classification, personal case history |

---

## Test Suites & Continuous Integration

```powershell
# 1. Backend Integration Tests (Health, Auth, Lockout, Media Ownership)
.\.venv\Scripts\pytest backend/tests/test_api.py -v

# 2. Frontend Boundary & Form Validation Tests (19 tests)
cd frontend
npm test

# 3. TypeScript Typecheck (Zero drift against OpenAPI schemas)
npm run typecheck

# 4. Next.js Production Build
npm run build
```
All tests are integrated into GitHub Actions CI via [`.github/workflows/ci.yml`](.github/workflows/ci.yml).
