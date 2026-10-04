# CareLens 1.0 — Clinical Monolith Prototype (Streamlit)

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.14-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![Deep Learning](https://img.shields.io/badge/Deep%20Learning-PyTorch%20%2B%20ResNet--50-EE4C2C.svg)](https://pytorch.org/)
[![Explainability](https://img.shields.io/badge/XAI-Grad--CAM%20Layer4-success.svg)](https://arxiv.org/abs/1610.02391)
[![Status](https://img.shields.io/badge/Version-1.0.0--prototype-orange.svg)](#)

---

## Executive Overview

**CareLens 1.0** represents the initial clinical prototype phase of the CareLens initiative. Developed as an interactive, single-process Python web application using **Streamlit**, Version 1.0 was designed to provide rapid proof-of-concept validation for AI-assisted bone tumor screening on plain radiographs.

Version 1.0 integrates fine-tuned **ResNet-50** deep learning inference, **Grad-CAM** visual saliency interpretability, and direct **SQLite** relational persistence into a unified, human-in-the-loop diagnostic review portal.

```
+-------------------------------------------------------------------------+
|                       CareLens 1.0 Architecture                         |
|                                                                         |
|   +-----------------------------------------------------------------+   |
|   |                        Web Browser Client                       |   |
|   |             (Streamlit Reactive Python UI / WebSockets)         |   |
|   +--------------------------------+--------------------------------+   |
|                                    |                                    |
|                                    v                                    |
|   +-----------------------------------------------------------------+   |
|   |                   Monolithic Streamlit Process                  |   |
|   |  - Session State Authentication (Role: Patient / Clinician)     |   |
|   |  - Input Validation & Scan Ingestion (PNG/JPEG, 10MB bounds)    |   |
|   |  - Direct SQLite Persistence (Users, Cases, Diagnostic Reviews) |   |
|   |  - Synchronous Matplotlib Grad-CAM Heatmap Generation           |   |
|   +--------------------------------+--------------------------------+   |
|                                    |                                    |
|                                    v                                    |
|   +-----------------------------------------------------------------+   |
|   |                 Embedded PyTorch Runtime (CUDA/CPU)             |   |
|   |  - ResNet-50 Binary Classifier (outputs/resnet50_augmented)     |   |
|   |  - Forward & Backward Hook Extraction on layer4.2.conv3         |   |
|   +-----------------------------------------------------------------+   |
+-------------------------------------------------------------------------+
```

---

## Key Features in CareLens 1.0

### 1. Dual-Role Clinical Portals
- **Patient Portal**:
  - Secure patient account registration with bcrypt password hashing.
  - Radiograph image ingestion with dimension boundary checks (64px to 4096px, 10MB limit).
  - Instant AI classification and risk tier output (<0.35 Low Risk, 0.35–0.599 Borderline, ≥0.60 High Risk).
  - Prominent mandatory disclaimer banner: *"AI decision-support tool — not a medical diagnosis."*
- **Physician & Radiologist Review Portal**:
  - Triage queue displaying all scans awaiting specialist evaluation.
  - Side-by-side inspection comparing raw radiograph and visual Grad-CAM saliency map.
  - Interactive clinical sign-off: confirm or overrule AI prediction, record clinical reasoning, and specify patient management recommendations.
  - Audit logging of clinical decisions.

### 2. Deep Visual Interpretability (Grad-CAM)
- Directly hooks into the final convolutional layer of ResNet-50 (`layer4.2.conv3`).
- Computes feature activation gradients against the positive malignant class:
  $$L_{\text{Grad-CAM}}^c = \text{ReLU}\left(\sum_k \alpha_k^c A^k\right), \quad \alpha_k^c = \frac{1}{Z}\sum_i \sum_j \frac{\partial Y^c}{\partial A_{i,j}^k}$$
- Generates a JET-colormap heatmap normalized across $[0, 1]$ and dynamically alpha-blended over the bone radiograph, allowing radiologists to verify anatomical tumor localization rather than background artifacts.

### 3. Fortified Security & Persistence
- Passwords salted and hashed with **bcrypt**.
- SQLite storage with migration protection for schemas:
  - `users` (id, username, password_hash, role, created_at)
  - `cases` (id, patient_id, image_path, pred_class, pred_prob, gradcam_path, status, created_at)
  - `doctor_reviews` (id, case_id, doctor_id, doctor_verdict, explanation, recommendations, reviewed_at)
  - `audit_logs` (id, user_id, action, details, timestamp)
- Path traversal sanitization preventing arbitrary filesystem read/write.

---

## Quick Launch Instructions

### Prerequisites
- Python 3.11+ (or project virtual environment `.venv`)
- Model weights placed in `outputs/resnet50_augmented/best_resnet50.pt`

### Launch Option A — Single-Click Windows Batch Script
Simply double-click:
```text
start_streamlit.bat
```
*(Or inside the dedicated folder: `carelens-v1-streamlit\start_streamlit.bat`)*

### Launch Option B — Terminal Command
```powershell
# From project root:
.\.venv\Scripts\streamlit.exe run carelens-v1-streamlit/streamlit_app.py
```
*Streamlit will automatically open on **[http://localhost:8501](http://localhost:8501)**.*

---

## Demo Credentials

| Role | Username | Password | Access Privileges |
|---|---|---|---|
| **Clinician / Radiologist** | `doctor1` | `CareLens2026!Doctor` | Full triage queue, Grad-CAM review, diagnostic sign-off |
| **Patient** | `patient1` | `CareLens2026!Patient` | Scan upload, personal case history, AI screening output |

---

## Architectural Learnings & Motivation for CareLens 2.0

While CareLens 1.0 successfully validated the clinical ML pipeline and Grad-CAM interpretability, production clinical deployment revealed fundamental architectural constraints inherent to Streamlit:

| Capability | CareLens 1.0 (Streamlit Monolith) | CareLens 2.0 (FastAPI + Next.js 14) |
|---|---|---|
| **Architecture** | Single Python process UI + Backend | Decoupled Client/Server (REST API + SPA) |
| **API Accessibility** | None (HTML coupled to Python script) | OpenAPI 3.1.0 JSON REST API |
| **Authentication** | In-memory session state | Stateless JWT access + `httpOnly` secure refresh cookies |
| **Brute-Force Protection**| None | 5-attempt rate limit + 15-minute cooldown |
| **Image Manipulation** | Static Matplotlib server-rendered PNG | Interactive canvas (hardware-accelerated zoom, pan, overlay toggle) |
| **PDF Reporting** | Not supported | Formal diagnostic PDF generation (ReportLab) |
| **Concurrency** | Python Global Interpreter Lock (GIL) | Async ASGI (FastAPI/Uvicorn) + static client assets |
| **Containerization** | Single container | Multi-container Docker Compose with healthchecks |

To address these limitations, the platform was re-architected into **[CareLens 2.0](CARELENS_V2_FULLSTACK.md)**.
