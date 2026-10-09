# CareLens: AI-Assisted Bone Tumor Screening & Clinical Decision Support

[![CareLens 2.0](https://img.shields.io/badge/CareLens%202.0-Enterprise%20Full--Stack-success.svg)](CARELENS_V2_FULLSTACK.md)
[![CareLens 1.0](https://img.shields.io/badge/CareLens%201.0-Streamlit%20Prototype-orange.svg)](CARELENS_V1_STREAMLIT.md)
[![Model](https://img.shields.io/badge/Model-ResNet--50%20(97.19%25%20Acc)-blue.svg)](#4-model-training-setup)
[![XAI](https://img.shields.io/badge/XAI-Layer4%20Grad--CAM-purple.svg)](#7-grad-cam-visual-explainability)
[![CI](https://github.com/atharvpareta05/bone-on-finalzip/actions/workflows/ci.yml/badge.svg)](https://github.com/atharvpareta05/bone-on-finalzip/actions/workflows/ci.yml)

> **Important Clinical Notice**: CareLens is an investigative decision-support platform designed to assist certified oncologists and radiologists. It does not provide automated diagnoses nor replace tissue biopsy, CT/MRI cross-sectional imaging, or licensed medical evaluation.

---

## 🌟 Dual-Version Showcase: CareLens 1.0 vs. CareLens 2.0

This repository contains **two complete, functional implementations** reflecting the engineering evolution from a rapid clinical prototype to a production-grade decoupled enterprise web platform:

| Version | Focus | Frontend | Backend / API | Key Highlights | Documentation & Code |
|---|---|---|---|---|---|
| **CareLens 1.0** *(Classic)* | Rapid Clinical Validation | Reactive Python UI (Streamlit) | Monolithic Python Process | Instant setup, inline Grad-CAM review, SQLite auth, single-script execution | 📖 [CareLens 1.0 Guide](CARELENS_V1_STREAMLIT.md)<br>📁 [`carelens-v1-streamlit/`](carelens-v1-streamlit/) |
| **CareLens 2.0** *(NextGen)* | Decoupled Enterprise Platform | Next.js 14 App Router (React 18 + TS + Tailwind) | FastAPI (Uvicorn ASGI + OpenAPI 3.1) | Canvas zoom/pan radiograph viewer, priority triage queue, JWT rotation, ReportLab PDF reports, Docker | 📖 [CareLens 2.0 Guide](CARELENS_V2_FULLSTACK.md)<br>📁 [`backend/`](backend/) & [`frontend/`](frontend/) |

### 🚀 Instant Launch Guide

First complete the environment setup in [Section 10](#10-setup--reproduction), then pick a version:

```text
               +-------------------------------------------------------------+
               |               Which version would you like to run?          |
               +------------------------------+------------------------------+
                                              |
                     +------------------------+------------------------+
                     |                                                 |
                     v                                                 v
      [ CareLens 2.0 (Modern Web App) ]                 [ CareLens 1.0 (Streamlit Monolith) ]
      - Port 3000 (UI) & Port 8000 (API)                - Port 8501 (Interactive Prototype)
      - Run: python run_carelens.py                     - Run: streamlit run streamlit_app.py
      - Or click: start_carelens.bat                    - Or click: start_streamlit.bat
```

#### Launching CareLens 2.0 (Full-Stack Next.js + FastAPI)
```powershell
# One-command unified launcher (auto-detects virtualenv, cleans ports & opens browser):
python run_carelens.py
# Or on Windows: double-click start_carelens.bat
```
- Web Application: **[http://localhost:3000](http://localhost:3000)**
- Interactive API Docs: **[http://localhost:8000/docs](http://localhost:8000/docs)**

#### Launching CareLens 1.0 (Streamlit Monolithic Prototype)
```powershell
# From project root:
.\.venv\Scripts\streamlit.exe run carelens-v1-streamlit/streamlit_app.py
# Or on Windows: double-click start_streamlit.bat
```
- Clinical Prototype: **[http://localhost:8501](http://localhost:8501)**

#### 🔑 Demo Accounts
Demo credentials are not published in this README. To create local demo accounts (one clinician, one patient), copy `.demo_users.json.example` to `.demo_users.json` and see [Section 9](#demo-accounts-configuration).

---

## 1. Objective

This project aims to build an end-to-end deep learning framework and clinical decision-support portal for detecting bone tumors and malignancies from plain radiograph (X-ray) images. The final model is based on an ImageNet-pretrained **ResNet-50** architecture, adapted for binary classification (`no_cancer` vs. `cancer`), fortified with **Grad-CAM (Gradient-weighted Class Activation Mapping)** for visual interpretability, and deployed via an interactive human-in-the-loop web portal (`CareLens`).

The workflow followed in this project includes:
- Dataset inspection and class-imbalance characterization
- Offline geometric and photometric dataset augmentation
- CUDA GPU environment configuration on an NVIDIA GeForce RTX 4050
- Pilot training and baseline ResNet-50 model convergence
- Augmented dataset training with early stopping
- Comprehensive validation and test generalization analysis (checking for overfitting)
- Deep Grad-CAM visual interpretability integration
- Interactive multi-user clinical portal deployment with SQLite persistence

---

## 2. Project Files

The following directories and files constitute the primary codebase:

### Presentation & Architecture Guides
- [CARELENS_V1_STREAMLIT.md](CARELENS_V1_STREAMLIT.md) — Comprehensive architecture and clinical workflow guide for CareLens 1.0
- [CARELENS_V2_FULLSTACK.md](CARELENS_V2_FULLSTACK.md) — Comprehensive architecture and enterprise full-stack guide for CareLens 2.0
- [AUDIT_shortcut_learning.md](AUDIT_shortcut_learning.md) — Shortcut learning and multi-source dataset leakage audit report
- [PROJECT_SECURITY_AUDIT.md](PROJECT_SECURITY_AUDIT.md) — Comprehensive clinical security audit and remediation roadmap

### CareLens 2.0 (Modern Enterprise Platform)
- [backend/](backend/) — FastAPI REST application with JWT rotation, Grad-CAM hooks, ReportLab PDF generation, and OpenAPI 3.1
- [frontend/](frontend/) — Next.js 14 App Router React client with interactive canvas radiograph viewer and triage queue
- [run_carelens.py](run_carelens.py) — Unified single-command runner for both backend and frontend daemons
- [start_carelens.bat](start_carelens.bat) — One-click Windows desktop launcher for CareLens 2.0
- [docker-compose.yml](docker-compose.yml) — Production container orchestration

### CareLens 1.0 (Streamlit Monolithic Prototype)
- [carelens-v1-streamlit/](carelens-v1-streamlit/) — Dedicated folder containing the self-contained Streamlit prototype and launcher
- [streamlit_app.py](streamlit_app.py) — Interactive Python monolith with Grad-CAM visualization and doctor review tabs
- [start_streamlit.bat](start_streamlit.bat) — One-click Windows desktop launcher for CareLens 1.0

### Machine Learning Core & Provenance
- [final/train_resnet50.py](final/train_resnet50.py) — ResNet-50 training, validation, early stopping, and metric evaluation script
- [final/augment_dataset.py](final/augment_dataset.py) — Offline dataset augmentation script applying spatial and photometric transformations
- [notebooks/](notebooks/) — End-to-end dataset provenance and inspection notebooks (`01_...` through `05_duplicate_analysis.ipynb`)
- [outputs/resnet50_augmented/](outputs/resnet50_augmented/) — Final augmented model checkpoint (`best_resnet50.pt`), metrics JSON, and test predictions CSV
- [requirements.txt](requirements.txt) — Python dependencies (PyTorch CUDA 12.8, FastAPI, Streamlit, Pandas, Pillow, bcrypt, ReportLab)

---

## 3. Dataset Preparation

The original bone radiograph corpus was loaded from the `final/final` directory, integrated from two distinct radiograph collections (BTXRD and Dataset 2). Because medical imaging datasets frequently exhibit class imbalance, the splits were inspected to determine exact class frequencies:

### Dataset Splits and Distribution

| Split | Images | Benign / Non-Cancer (Class 0) | Malignant / Cancer (Class 1) | Class Ratio |
|---|---:|---:|---:|:---:|
| `train` | 10,052 | 6,697 | 3,355 | ~ 2.0 : 1 |
| `valid` | 1,084 | 653 | 431 | ~ 1.5 : 1 |
| `test` | 1,067 | 650 | 417 | ~ 1.6 : 1 |
| **Total** | **12,203** | **8,000** | **4,203** | **1.90 : 1** |

To prevent the model from biasing toward the majority benign class, training utilized **class-weighted cross-entropy loss**:
$$w_c = \frac{N}{2 \cdot N_c} \implies w_0 \approx 0.75, \quad w_1 \approx 1.50$$

### Datasets Used

- `final/final` — Original dataset containing `train/`, `valid/`, and `test/` partitions with corresponding `metadata.csv` files.
- `final/final_augmented` — Augmented dataset expanding training diversity to improve feature invariance and reduce overfitting.

For a review of shortcut learning and cross-source leakage between the two merged collections, see [AUDIT_shortcut_learning.md](AUDIT_shortcut_learning.md).

### Augmentation Command

```powershell
# From the project root:
.\.venv\Scripts\python.exe final/augment_dataset.py `
  --data-root final/final `
  --output-root final/final_augmented `
  --copies 1 `
  --seed 42
```

This script preserves the exact `valid` and `test` splits while generating augmented copies of the training split using:
- Horizontal mirroring ($p = 0.5$)
- Vertical flipping ($p = 0.25$)
- Random rotation ($\pm 12^\circ$)
- Brightness and contrast adjustments ($\pm 15\%$)

---

## 4. Model Training Setup

The core model is an ImageNet-pretrained **ResNet-50** (`IMAGENET1K_V2` weights) with its final classification head adapted for binary projection.

### Model Architecture

```python
import torch
from torch import nn
from torchvision import models

weights = models.ResNet50_Weights.IMAGENET1K_V2
model = models.resnet50(weights=weights)
model.fc = nn.Linear(model.fc.in_features, 2)
```

### Training Loop & Metric Tracking

The training script uses PyTorch AMP (`torch.autocast`) for mixed-precision GPU acceleration and tracks accuracy, balanced accuracy, sensitivity, and specificity at each epoch:

```python
def run_epoch(model, loader, criterion, device, optimizer=None, scaler=None):
    training = optimizer is not None
    model.train(training)
    total_loss = 0.0
    predictions, targets = [], []

    for images, labels, _ in loader:
        images, labels = images.to(device), labels.to(device)
        if training:
            optimizer.zero_grad(set_to_none=True)
        with torch.set_grad_enabled(training):
            with torch.autocast(device_type=device.type, enabled=device.type == "cuda"):
                logits = model(images)
                loss = criterion(logits, labels)
            if training:
                scaler.scale(loss).backward()
                scaler.step(optimizer)
                scaler.update()

        total_loss += loss.item() * labels.size(0)
        predictions.extend(logits.argmax(1).detach().cpu().tolist())
        targets.extend(labels.cpu().tolist())

    predictions = np.asarray(predictions)
    targets = np.asarray(targets)
    accuracy = float((predictions == targets).mean())
    recalls = [float((predictions[targets == c] == c).mean()) for c in (0, 1)]

    return {
        "loss": total_loss / len(loader.dataset),
        "accuracy": accuracy,
        "balanced_accuracy": sum(recalls) / 2,
        "sensitivity": recalls[1],
        "specificity": recalls[0],
    }
```

---

## 5. Phase-by-Phase Experimental Results

### Phase 1: 1-Epoch Pilot GPU Feasibility Run
Before initiating multi-epoch training, a 1-epoch pilot run was conducted on the NVIDIA GeForce RTX 4050 GPU to verify CUDA initialization and memory throughput.

```powershell
python .\final\train_resnet50.py --data-root .\final\final --epochs 1 --patience 1
```

- **Test Accuracy**: `90.44%`
- **Balanced Accuracy**: `90.91%`
- **Sensitivity (Cancer Recall)**: `93.05%`
- **Specificity (Normal Recall)**: `88.77%`

---

### Phase 2: Full Baseline Training on the Original Dataset
The baseline model was trained for 15 epochs on the raw dataset (`final/final`) using AdamW ($\eta = 10^{-4}, \lambda = 10^{-4}$) and a `ReduceLROnPlateau` scheduler.

```powershell
python .\final\train_resnet50.py `
  --data-root .\final\final `
  --output-dir .\outputs\resnet50 `
  --epochs 15 `
  --batch-size 32 `
  --patience 5 `
  --workers 0
```

- **Best Validation Balanced Accuracy**: `96.57%`
- **Test Loss**: `0.1375`
- **Test Accuracy**: `97.00%`
- **Test Balanced Accuracy**: `96.72%`
- **Test Sensitivity**: `95.44%`
- **Test Specificity**: `98.00%`
- **Saved Checkpoint**: `outputs/resnet50/best_resnet50.pt`

---

### Phase 3: Training on the Augmented Dataset (Winner Model)
To improve feature generalization and test-set robustness, training was executed on `final/final_augmented`. The model reached optimal generalization at **Epoch 12** before early stopping engaged.

```powershell
python .\final\train_resnet50.py `
  --data-root .\final\final_augmented `
  --output-dir .\outputs\resnet50_augmented `
  --epochs 15 `
  --batch-size 32 `
  --patience 5 `
  --workers 0
```

- **Best Validation Balanced Accuracy**: `97.11%`
- **Test Loss**: `0.1004`
- **Test Accuracy**: `97.19%`
- **Test Balanced Accuracy**: `96.96%`
- **Test Sensitivity**: `95.92%`
- **Test Specificity**: `98.00%`
- **Saved Checkpoint**: `outputs/resnet50_augmented/best_resnet50.pt`

---

### Phase Comparison Summary

| Phase | Model | Dataset | Epochs | Test Loss | Test Accuracy | Balanced Acc | Sensitivity | Specificity |
|---|---|---|---:|---:|---:|---:|---:|---:|
| **Phase 1** | 1-Epoch Pilot | `final/final` | 1 | — | 90.44% | 90.91% | 93.05% | 88.77% |
| **Phase 2** | Baseline ResNet-50 | `final/final` | 15 | 0.1375 | 97.00% | 96.72% | 95.44% | 98.00% |
| **Phase 3** | Augmented ResNet-50 | `final_augmented` | 12 | **0.1004** | **97.19%** | **96.96%** | **95.92%** | **98.00%** |

---

## 6. Model Generalization & Overfitting Analysis

To check whether the model memorized the training data, the selected winner checkpoint (`outputs/resnet50_augmented/best_resnet50.pt`) was re-evaluated across all **12,203 images** in the training, validation, and test partitions:

### Full Dataset Split Evaluation

| Dataset Split | Sample Count | Cross-Entropy Loss | Overall Accuracy | Balanced Accuracy | Sensitivity (Cancer) | Specificity (Normal) |
|---|---:|---:|---:|---:|---:|---:|
| **Train Split** | 10,052 | 0.0043 | **99.90%** | **99.91%** | 99.94% | 99.88% |
| **Validation Split** | 1,084 | 0.1269 | **97.23%** | **97.11%** | 96.52% | 97.70% |
| **Test Split** | 1,067 | 0.1131 | **97.19%** | **96.96%** | 95.92% | 98.00% |

> **Note on test loss:** the loss values in this table come from a separate full-split evaluation pass of the final checkpoint, so the test loss (0.1131) differs slightly from the 0.1004 reported by the training script in Phase 3. Accuracy, sensitivity, and specificity are identical in both.

### Key Findings

1. **No Sign of Harmful Overfitting**:
   The gap between training accuracy (99.90%) and unseen test accuracy (97.19%) is 2.71 percentage points. For a high-capacity architecture (ResNet-50 has ~23.5 million parameters), this is a modest gap.
2. **Validation and Test Parity**:
   Validation accuracy (**97.23%**) and test accuracy (**97.19%**) agree within 0.04 percentage points, suggesting the model was not tuned to the validation set.
3. **Consistent Test Loss**:
   The test loss (`0.1131`) is slightly lower than the validation loss (`0.1269`), indicating similar calibration on held-out radiographs.
4. **Clinical Performance**:
   On the test split, the model reaches **95.92% sensitivity** (400 of 417 malignant cases detected) and **98.00% specificity** (637 of 650 benign scans correctly identified).

> **Scope of these results:** these figures come from a single held-out test split drawn from two merged public collections. They do not establish performance on images from other hospitals, scanners, or patient populations. See [AUDIT_shortcut_learning.md](AUDIT_shortcut_learning.md) for the leakage and shortcut-learning review, and treat external validation as future work.

---

## 7. Grad-CAM Visual Explainability

To reduce the "black box" nature of deep neural networks in oncology, **Grad-CAM (Gradient-weighted Class Activation Mapping)** was integrated into the inference pipeline.

### Mathematical Formulation

Gradients of the cancer logit $y^c$ ($c = 1$) are computed with respect to feature activation maps $A^k$ of the final convolutional layer (`model.layer4[-1]`):

$$\alpha_k^c = \frac{1}{Z} \sum_{i} \sum_{j} \frac{\partial y^c}{\partial A_{i,j}^k}$$

$$L_{\text{Grad-CAM}}^c = \text{ReLU}\left(\sum_k \alpha_k^c A^k\right)$$

The resulting 2D saliency map is normalized, upsampled to $224 \times 224$ via bilinear interpolation, mapped through the **Jet** colormap, and blended onto the original X-ray ($\alpha = 0.45$).

### Clinical Interpretation Key

- 🟥 **Red / Warm Areas**: Regions with the strongest influence on the malignancy prediction.
- 🟨 **Yellow / Green Areas**: Moderate attention, often around lesion margins.
- 🟦 **Blue / Cool Areas**: Little contribution to the prediction (background bone or soft tissue).

Heatmaps show where the model looked, not why a region is clinically suspicious; they should be interpreted by a qualified radiologist.

---

## 8. Final Winner Checkpoint

The strongest result across all experiments was achieved by the **Augmented ResNet-50** model:

- **Checkpoint File**: `outputs/resnet50_augmented/best_resnet50.pt`
- **Best Validation Balanced Accuracy**: `0.9711`
- **Test Accuracy**: `97.19%`
- **Test Sensitivity**: `95.92%`
- **Test Specificity**: `98.00%`

This checkpoint is loaded dynamically by the `CareLens` clinical application for all real-time inference and Grad-CAM generations.

---

## 9. CareLens Clinical Web Portal

An interactive web application was constructed in [streamlit_app.py](streamlit_app.py) to provide a complete human-in-the-loop diagnostic portal:

### Core Portal Modules

1. **Authentication & Self-Registration**:
   - Tabbed landing interface: **🔑 Sign In** and **📝 Register New Patient**.
   - Direct patient self-onboarding.
   - Automatic routing based on user role (`patient` vs. `doctor`).
2. **Patient Workspace**:
   - Bone radiograph file uploader (PNG, JPEG).
   - Automated backend inference and Grad-CAM generation upon submission.
   - Status tracking ("Pending doctor review" vs. "Reviewed") with physician verdict display.
3. **Physician Review Workspace**:
   - Real-time queue metrics (Pending Reviews, Completed Reviews, Active Model).
   - Side-by-side inspection tabs:
     - **Side-by-Side Comparison** (Original scan alongside Grad-CAM overlay).
     - **Grad-CAM Heatmap** (Detailed saliency view with visual interpretation legend).
     - **Original Scan** (Full-resolution unprocessed radiograph).
   - Risk stratification:
     - ⚠️ **High Risk** ($\ge 70\%$)
     - ⚖️ **Borderline** ($40\% - 70\%$)
     - ✅ **Low Probability** ($< 40\%$)
   - Diagnostic assessment submission form (Verdict, Physician Findings, Recommended Next Steps).
   - Historical review archive with persistent SQLite storage in [app_data.sqlite3](app_data.sqlite3).

### Demo Accounts Configuration

Demo accounts are decoupled from code and configured via [`.demo_users.json.example`](.demo_users.json.example). To seed local development accounts:

1. Copy the example configuration:
   ```powershell
   Copy-Item .demo_users.json.example .demo_users.json
   ```
2. When the application initializes, accounts defined in `.demo_users.json` are automatically hashed with salted `bcrypt` and stored in SQLite.
3. `.demo_users.json` is ignored by Git to prevent accidental credential leakage.

> **Known limitation:** in the CareLens 1.0 Streamlit prototype, passwords for *self-registered* patients are hashed with SHA-256, which is weaker than the salted bcrypt used for seeded demo accounts. This is acceptable for a local prototype but must be replaced with bcrypt (or Argon2) before any real deployment. See [PROJECT_SECURITY_AUDIT.md](PROJECT_SECURITY_AUDIT.md) for the full remediation roadmap.

---

## 10. Setup & Reproduction

### 1. Environment Setup

```powershell
git clone https://github.com/atharvpareta05/bone-on-finalzip.git
cd bone-on-finalzip

# Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install CUDA-accelerated PyTorch and dependencies
pip install -r requirements.txt
```

### 2. Running CareLens 2.0 Manually (Two Terminals)

**Terminal 1: FastAPI backend**
```powershell
.\.venv\Scripts\python.exe backend/run.py
```
- Backend API: **http://localhost:8000**
- Swagger / OpenAPI docs: **http://localhost:8000/docs**
- Health & model probe: **http://localhost:8000/health**

**Terminal 2: Next.js frontend**
```powershell
cd frontend
npm install
npm run dev
```
- Frontend UI: **http://localhost:3000**

### 3. Running via Docker Compose

```powershell
docker compose up --build
```
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000` (monitored by Docker healthcheck)

### 4. Running Test Suites

```powershell
# Backend pytest suite (4 integration tests)
.\.venv\Scripts\pytest backend/tests/test_api.py -v

# Frontend unit & boundary tests (19 tests)
cd frontend
npm run test

# TypeScript compilation check
npm run typecheck

# Next.js production build
npm run build
```

### 5. Re-running Dataset Augmentation and Training (Optional)

```powershell
.\.venv\Scripts\python.exe final/augment_dataset.py `
  --data-root final/final `
  --output-root final/final_augmented `
  --copies 1

.\.venv\Scripts\python.exe final/train_resnet50.py `
  --data-root final/final_augmented `
  --output-dir outputs/resnet50_augmented `
  --epochs 15 `
  --batch-size 32 `
  --workers 0
```

---

## 11. Conclusion

The experimental outcomes show that transfer learning with **ResNet-50**, combined with class-weighted cross-entropy loss and targeted dataset augmentation, reaches **97.19% accuracy** and **95.92% sensitivity** on a held-out split of plain bone radiographs. Validation (97.23%) and test (97.19%) accuracy are nearly identical, and the train/test gap is modest, which suggests the model is not badly overfit.

Paired with **Grad-CAM visual saliency mapping** and the **CareLens** clinical portal, the system offers an interpretable, deployable prototype for AI-assisted bone tumor screening. Validation on external, independently collected data is the key next step before any clinical claims can be made.

---

> **Notice**: CareLens is designed as an investigative decision-support tool. It does not replace histopathological biopsy, comprehensive multi-modal imaging (MRI/CT), or the clinical judgment of certified oncologists and radiologists.
