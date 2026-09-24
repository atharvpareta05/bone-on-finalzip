"""Academic doctor-assisted image review prototype with Grad-CAM explainability."""

import html
import json
import os
import re
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

import bcrypt
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st
import torch
import torch.nn.functional as F
from PIL import Image
from torchvision import models, transforms

ROOT = Path(__file__).resolve().parent
MODEL_PATH = ROOT / "outputs" / "resnet50_augmented" / "best_resnet50.pt"
DB_PATH = ROOT / "app_data.sqlite3"
UPLOAD_DIR = ROOT / "app_uploads"
CONFIG_PATH = ROOT / ".demo_users.json"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

SESSION_TIMEOUT_MINUTES = 30
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB limit
MAX_IMAGE_DIMENSION = 4096
MIN_IMAGE_DIMENSION = 64


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt with automatic salting."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def resolve_path(rel_or_abs_path: str) -> Path:
    """Resolve stored image path relative to ROOT to prevent hardcoded absolute path failures."""
    if not rel_or_abs_path:
        return None
    p = Path(rel_or_abs_path)
    if p.is_absolute() and p.exists():
        return p
    if (ROOT / p).exists():
        return ROOT / p
    if (UPLOAD_DIR / p.name).exists():
        return UPLOAD_DIR / p.name
    return ROOT / p


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_database():
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('patient', 'doctor')),
                display_name TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS cases (
                id TEXT PRIMARY KEY,
                patient_id INTEGER NOT NULL,
                image_path TEXT NOT NULL,
                gradcam_path TEXT,
                model_prediction TEXT NOT NULL,
                cancer_probability REAL NOT NULL,
                status TEXT NOT NULL,
                doctor_verdict TEXT,
                doctor_explanation TEXT,
                recommendation TEXT,
                created_at TEXT NOT NULL,
                reviewed_at TEXT,
                FOREIGN KEY(patient_id) REFERENCES users(id)
            );
            """
        )
        try:
            connection.execute("ALTER TABLE cases ADD COLUMN gradcam_path TEXT")
        except sqlite3.OperationalError:
            pass

        # Load initial demo accounts from external config (never hardcoded in source)
        user_count = connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if user_count == 0 and CONFIG_PATH.exists():
            try:
                with CONFIG_PATH.open("r", encoding="utf-8") as f:
                    demo_configs = json.load(f)
                    demo_users = [
                        (
                            u["username"],
                            hash_password(u["password"]),
                            u["role"],
                            u["display_name"],
                        )
                        for u in demo_configs
                    ]
                    connection.executemany(
                        "INSERT OR IGNORE INTO users (username, password_hash, role, display_name) VALUES (?, ?, ?, ?)",
                        demo_users,
                    )
            except Exception as e:
                st.error(f"Error loading demo accounts from {CONFIG_PATH.name}: {e}")


@st.cache_resource(show_spinner="Loading the ResNet-50 model...")
def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model checkpoint not found: {MODEL_PATH}")
    model = models.resnet50(weights=None)
    model.fc = torch.nn.Linear(model.fc.in_features, 2)
    checkpoint = torch.load(MODEL_PATH, map_location=DEVICE, weights_only=True)
    model.load_state_dict(checkpoint["model"])
    model.to(DEVICE)
    model.eval()
    return model


@st.cache_resource
def get_transform():
    return transforms.Compose(
        [
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )


def generate_gradcam_overlay(image):
    """
    Compute ResNet-50 cancer prediction, probability, and Grad-CAM heatmap.
    Hooks into layer4[-1] to generate saliency overlay for class 1 (cancer).
    """
    model = load_model()
    tensor = get_transform()(image).unsqueeze(0).to(DEVICE)

    activations = []
    gradients = []

    def forward_hook(module, input, output):
        activations.append(output)

    def backward_hook(module, grad_in, grad_out):
        gradients.append(grad_out[0])

    target_layer = model.layer4[-1]
    handle_fwd = target_layer.register_forward_hook(forward_hook)
    handle_bwd = target_layer.register_full_backward_hook(backward_hook)

    model.eval()
    model.zero_grad()

    logits = model(tensor)
    probs = F.softmax(logits, dim=1)
    cancer_prob = float(probs[0, 1].item())
    prediction = "cancer" if cancer_prob >= 0.5 else "no_cancer"

    # Backward pass on the cancer class logit to pinpoint suspicious regions
    score = logits[0, 1]
    score.backward()

    handle_fwd.remove()
    handle_bwd.remove()

    grad = gradients[0].detach()
    act = activations[0].detach()

    # Global Average Pooling on gradients across spatial dimensions
    weights = torch.mean(grad, dim=(2, 3), keepdim=True)
    cam = torch.sum(weights * act, dim=1, keepdim=True)
    cam = F.relu(cam)

    cam = cam.squeeze().cpu().numpy()
    if cam.max() > cam.min():
        cam = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)
    else:
        cam = np.zeros_like(cam)

    # Process original image with matching crop for alignment
    orig_crop = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224)
    ])(image)

    cam_img = Image.fromarray(np.uint8(255 * cam)).resize((224, 224), Image.Resampling.BILINEAR)
    cam_arr = np.array(cam_img) / 255.0

    colormap = plt.get_cmap("jet")
    heatmap_colored = colormap(cam_arr)[:, :, :3]
    orig_arr = np.array(orig_crop.convert("RGB")) / 255.0

    alpha = 0.45
    overlay = (1 - alpha) * orig_arr + alpha * heatmap_colored
    overlay = np.uint8(np.clip(overlay * 255, 0, 255))
    overlay_image = Image.fromarray(overlay)

    return prediction, cancer_prob, overlay_image


def authenticate(username, password):
    if not username or not password:
        return None
    with get_connection() as connection:
        user = connection.execute(
            "SELECT id, username, password_hash, role, display_name FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if user and verify_password(password, user["password_hash"]):
            return {
                "id": user["id"],
                "username": user["username"],
                "role": user["role"],
                "display_name": user["display_name"],
            }
    return None


def register_patient(username, password, display_name):
    """Register a new patient account with bcrypt hashing and validation."""
    username_clean = username.strip()
    display_clean = display_name.strip()

    if not re.match(r"^[a-zA-Z0-9_-]{3,30}$", username_clean):
        return False, "Username must be 3-30 characters long and contain only letters, numbers, hyphens, and underscores."
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if len(display_clean) < 2 or len(display_clean) > 60:
        return False, "Display name must be between 2 and 60 characters."

    with get_connection() as connection:
        cursor = connection.cursor()
        existing = cursor.execute("SELECT id FROM users WHERE username = ?", (username_clean,)).fetchone()
        if existing:
            return False, "This username is already taken. Please choose another."
        cursor.execute(
            "INSERT INTO users (username, password_hash, role, display_name) VALUES (?, ?, 'patient', ?)",
            (username_clean, hash_password(password), display_clean),
        )
        connection.commit()
        user_id = cursor.lastrowid
        return True, {"id": user_id, "username": username_clean, "role": "patient", "display_name": display_clean}


def create_case(patient_id, image, prediction, probability, gradcam_img):
    case_id = uuid.uuid4().hex[:10].upper()
    UPLOAD_DIR.mkdir(exist_ok=True)
    img_filename = f"{case_id}.png"
    cam_filename = f"{case_id}_gradcam.png"

    image.save(UPLOAD_DIR / img_filename, format="PNG")
    gradcam_img.save(UPLOAD_DIR / cam_filename, format="PNG")

    rel_image_path = f"app_uploads/{img_filename}"
    rel_cam_path = f"app_uploads/{cam_filename}"

    with get_connection() as connection:
        connection.execute(
            """INSERT INTO cases
            (id, patient_id, image_path, gradcam_path, model_prediction, cancer_probability, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'Pending doctor review', ?)""",
            (case_id, patient_id, rel_image_path, rel_cam_path, prediction, probability, datetime.now().isoformat(timespec="seconds")),
        )
    return case_id


def get_or_generate_gradcam(case):
    """Retrieve existing Grad-CAM image or generate one on the fly if missing."""
    gradcam_path = resolve_path(case["gradcam_path"])
    if gradcam_path and gradcam_path.exists():
        return str(gradcam_path)
    image_path = resolve_path(case["image_path"])
    if not image_path or not image_path.exists():
        return None
    img = Image.open(image_path).convert("RGB")
    _, _, overlay_img = generate_gradcam_overlay(img)
    new_filename = f"{case['id']}_gradcam.png"
    new_abs_path = UPLOAD_DIR / new_filename
    overlay_img.save(new_abs_path, format="PNG")
    rel_path = f"app_uploads/{new_filename}"
    with get_connection() as connection:
        connection.execute("UPDATE cases SET gradcam_path = ? WHERE id = ?", (rel_path, case["id"]))
    return str(new_abs_path)


def patient_cases(patient_id):
    with get_connection() as connection:
        return connection.execute(
            "SELECT * FROM cases WHERE patient_id = ? ORDER BY created_at DESC", (patient_id,)
        ).fetchall()


def pending_cases():
    with get_connection() as connection:
        return connection.execute(
            """SELECT cases.*, users.display_name AS patient_name
            FROM cases JOIN users ON users.id = cases.patient_id
            WHERE cases.status = 'Pending doctor review' ORDER BY cases.created_at"""
        ).fetchall()


def reviewed_cases():
    with get_connection() as connection:
        return connection.execute(
            """SELECT cases.*, users.display_name AS patient_name
            FROM cases JOIN users ON users.id = cases.patient_id
            WHERE cases.status = 'Reviewed' ORDER BY cases.reviewed_at DESC"""
        ).fetchall()


def save_review(case_id, verdict, explanation, recommendation):
    with get_connection() as connection:
        connection.execute(
            """UPDATE cases SET status = 'Reviewed', doctor_verdict = ?, doctor_explanation = ?,
            recommendation = ?, reviewed_at = ? WHERE id = ?""",
            (verdict, explanation, recommendation, datetime.now().isoformat(timespec="seconds"), case_id),
        )


def check_session_timeout():
    """Enforce a session inactivity timeout."""
    if "user" in st.session_state:
        now = datetime.now().timestamp()
        last_activity = st.session_state.get("last_activity", now)
        if now - last_activity > SESSION_TIMEOUT_MINUTES * 60:
            st.session_state.clear()
            st.warning("Your session has expired due to inactivity. Please sign in again.")
            st.rerun()
        st.session_state.last_activity = now


def setup_page():
    st.set_page_config(page_title="CareLens - AI Bone Tumor Review", page_icon="🦴", layout="wide")
    st.markdown(
        """
        <style>
        .block-container { max-width: 1200px; padding-top: 1.5rem; }
        .brand { color: #0f766e; font-size: 0.95rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
        .hero { background: linear-gradient(120deg, #ecfdf5, #f0fdfa); border: 1px solid #99f6e4; padding: 1.25rem 1.5rem; border-radius: 10px; margin-bottom: 1.2rem; }
        .hero h1 { color: #134e4a; margin: 0; font-size: 2rem; }
        .notice { background: #fff7ed; border-left: 4px solid #f97316; padding: .8rem 1rem; border-radius: 6px; margin: 0.75rem 0; font-size: 0.95rem; }
        .cam-legend { background: #f8fafc; border: 1px solid #e2e8f0; padding: 0.75rem; border-radius: 8px; font-size: 0.85rem; margin-top: 0.5rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def login_screen():
    st.markdown('<div class="brand">CareLens Clinical Prototype</div>', unsafe_allow_html=True)
    st.markdown("## AI-Assisted Bone Tumor Analysis")
    st.write("A prototype clinical platform featuring human-in-the-loop review and Grad-CAM visual interpretability.")

    tab_signin, tab_register = st.tabs(["🔑 Sign In", "📝 Register New Patient"])

    with tab_signin:
        with st.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)

        # Only display demo hints in development mode
        show_hints = os.getenv("CARELENS_ENV") == "development" or os.getenv("SHOW_DEMO_HINTS", "1") == "1"
        if show_hints and CONFIG_PATH.exists():
            st.caption("Demo mode active. Demo accounts configured in `.demo_users.json`.")

        if submitted:
            user = authenticate(username.strip(), password)
            if user:
                st.session_state.user = user
                st.session_state.last_activity = datetime.now().timestamp()
                st.rerun()
            st.error("Invalid username or password.")

    with tab_register:
        st.markdown("#### Patient Registration")
        st.caption("Create an account to submit bone radiographs and receive physician reviews.")
        with st.form("register_form"):
            reg_display_name = st.text_input("Full Name", placeholder="e.g. Walter White", key="reg_name")
            reg_username = st.text_input("Desired Username", placeholder="e.g. Walterw", key="reg_user")
            c_p1, c_p2 = st.columns(2)
            with c_p1:
                reg_password = st.text_input("Password (min 8 chars)", type="password", key="reg_pass")
            with c_p2:
                reg_confirm = st.text_input("Confirm Password", type="password", key="reg_confirm")
            reg_submitted = st.form_submit_button("Create Account & Sign In", type="primary", use_container_width=True)

        if reg_submitted:
            name_clean = reg_display_name.strip()
            user_clean = reg_username.strip()
            if not name_clean:
                st.error("Please enter your full name.")
            elif not user_clean:
                st.error("Please enter a username.")
            elif not reg_password:
                st.error("Please enter a password.")
            elif reg_password != reg_confirm:
                st.error("Passwords do not match.")
            else:
                success, result = register_patient(user_clean, reg_password, name_clean)
                if success:
                    st.success(f"Welcome, {name_clean}! Account created successfully.")
                    st.session_state.user = result
                    st.session_state.last_activity = datetime.now().timestamp()
                    st.rerun()
                else:
                    st.error(result)


def patient_page(user):
    st.markdown('<div class="brand">Patient Workspace</div>', unsafe_allow_html=True)
    st.markdown("# Submit a Radiograph")
    st.write("Upload a bone X-ray scan for preliminary AI feature extraction and comprehensive doctor review.")
    st.markdown(
        '<div class="notice"><strong>Notice:</strong> All uploads undergo clinical review by a physician before a final diagnostic assessment is issued. AI outputs are decision support and do not constitute an autonomous diagnosis.</div>',
        unsafe_allow_html=True,
    )
    uploaded = st.file_uploader("Choose an X-ray image (PNG or JPEG, max 10MB)", type=["png", "jpg", "jpeg"])
    if uploaded:
        if uploaded.size > MAX_UPLOAD_SIZE_BYTES:
            st.error(f"Uploaded file exceeds maximum permitted size of {MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)}MB.")
        else:
            try:
                image = Image.open(uploaded)
                if image.format not in ("PNG", "JPEG", "MPO"):
                    st.error("Invalid image format. Only PNG and JPEG scans are supported.")
                elif (
                    image.width > MAX_IMAGE_DIMENSION
                    or image.height > MAX_IMAGE_DIMENSION
                    or image.width < MIN_IMAGE_DIMENSION
                    or image.height < MIN_IMAGE_DIMENSION
                ):
                    st.error(
                        f"Image dimensions ({image.width}x{image.height}) are outside allowed boundaries "
                        f"({MIN_IMAGE_DIMENSION}x{MIN_IMAGE_DIMENSION} to {MAX_IMAGE_DIMENSION}x{MAX_IMAGE_DIMENSION})."
                    )
                else:
                    image = image.convert("RGB")
                    col_img, col_btn = st.columns([1, 1])
                    with col_img:
                        st.image(image, caption="Uploaded Radiograph", width=360)
                    with col_btn:
                        st.write("Ready to analyze. The system will extract feature representations and queue the scan for doctor evaluation.")
                        if st.button("Submit for Doctor Review", type="primary"):
                            with st.spinner("Analyzing radiograph and computing Grad-CAM saliency..."):
                                prediction, probability, gradcam_img = generate_gradcam_overlay(image)
                                case_id = create_case(user["id"], image, prediction, probability, gradcam_img)
                            st.success(f"Case {case_id} successfully registered and queued for physician review.")
            except Exception as e:
                st.error(f"Failed to process image file: {e}")

    st.divider()
    st.markdown("## My Submissions")
    cases = patient_cases(user["id"])
    if not cases:
        st.info("No cases submitted yet.")
        return
    for case in cases:
        with st.container(border=True):
            left, right = st.columns([2, 1])
            with left:
                st.markdown(f"**Case Reference: `{html.escape(str(case['id']))}`**")
                st.caption(f"Submitted on {html.escape(str(case['created_at']))}")
                status_color = "#0f766e" if case["status"] == "Reviewed" else "#d97706"
                escaped_status = html.escape(str(case["status"]))
                st.markdown(f"Status: <span style='color:{status_color}; font-weight:700;'>{escaped_status}</span>", unsafe_allow_html=True)
                if case["status"] == "Reviewed":
                    st.write(f"**Attending Physician Verdict:** {case['doctor_verdict']}")
                    st.write(f"**Physician Notes:** {case['doctor_explanation']}")
                    st.info(f"**Recommended Next Step:** {case['recommendation']}")
                else:
                    st.caption("Awaiting review from the attending radiologist/oncologist.")
            with right:
                resolved_img = resolve_path(case["image_path"])
                if resolved_img and resolved_img.exists():
                    st.image(str(resolved_img), caption="Submitted Scan", use_container_width=True)
                else:
                    st.warning("Scan image unavailable.")


def doctor_page():
    st.markdown('<div class="brand">Physician Workspace</div>', unsafe_allow_html=True)
    st.markdown("# Radiograph Clinical Review")
    st.caption("ResNet-50 decision support with Grad-CAM deep visual explainability. The clinician provides the final medical verdict.")

    pending = pending_cases()
    reviewed = reviewed_cases()

    col1, col2, col3 = st.columns(3)
    col1.metric("Pending Reviews", len(pending))
    col2.metric("Completed Reviews", len(reviewed))
    col3.metric("Active Model", "ResNet-50 (Augmented)")

    if not pending:
        st.success("All pending scans have been reviewed. New patient submissions will appear here.")
    else:
        st.divider()
        selected_id = st.selectbox(
            "Select Pending Case",
            [case["id"] for case in pending],
            format_func=lambda cid: next(f"Case {c['id']} — Patient: {c['patient_name']} (Submitted {c['created_at']})" for c in pending if c["id"] == cid),
        )
        case = next(case for case in pending if case["id"] == selected_id)
        gradcam_path = get_or_generate_gradcam(case)
        resolved_orig_path = resolve_path(case["image_path"])

        image_col, analysis_col = st.columns([1.3, 1])

        with image_col:
            st.markdown("### Radiograph & Visual Interpretability")
            tab_compare, tab_cam, tab_orig = st.tabs(["Side-by-Side Comparison", "Grad-CAM Heatmap", "Original Scan"])

            with tab_compare:
                sub_c1, sub_c2 = st.columns(2)
                with sub_c1:
                    if resolved_orig_path and resolved_orig_path.exists():
                        st.image(str(resolved_orig_path), caption="Original Radiograph", use_container_width=True)
                    else:
                        st.warning("Original scan unavailable.")
                with sub_c2:
                    if gradcam_path and Path(gradcam_path).exists():
                        st.image(gradcam_path, caption="Grad-CAM Lesion Saliency", use_container_width=True)
                    else:
                        st.warning("Heatmap unavailable.")

            with tab_cam:
                if gradcam_path and Path(gradcam_path).exists():
                    st.image(gradcam_path, caption="Grad-CAM Saliency Overlay (Layer4 Conv Features)", use_container_width=True)
                    st.markdown(
                        """
                        <div class="cam-legend">
                        <strong>Grad-CAM Color Interpretation:</strong><br>
                        🟥 <strong>Red / Warm:</strong> High convolutional activation driving cancer prediction (critical focal region).<br>
                        🟨 <strong>Yellow / Green:</strong> Moderate structural attention.<br>
                        🟦 <strong>Blue / Cool:</strong> Low influence / baseline background bone tissue.
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    st.warning("Heatmap unavailable.")

            with tab_orig:
                if resolved_orig_path and resolved_orig_path.exists():
                    st.image(str(resolved_orig_path), caption=f"Full Radiograph — Patient: {case['patient_name']}", use_container_width=True)
                else:
                    st.warning("Original scan unavailable.")

        with analysis_col:
            st.markdown("### AI Decision Support")
            prob = case["cancer_probability"]
            pred = case["model_prediction"]

            st.metric("Predicted Class", pred.replace("_", " ").title())
            st.metric("Cancer Probability Score", f"{prob:.1%}")

            if prob >= 0.70:
                st.error("⚠️ High malignancy probability detected. Correlate with clinical history and Grad-CAM focal zones.")
            elif prob >= 0.40:
                st.warning("⚖️ Borderline probability score. Careful radiological evaluation recommended.")
            else:
                st.success("✅ Low probability of malignancy indicated by the model.")

            st.markdown("---")
            with st.form(f"review_form_{case['id']}"):
                st.markdown("#### Clinical Assessment")
                verdict = st.selectbox(
                    "Physician Verdict",
                    ["Cancer suspected", "Cancer not suspected", "Inconclusive / Further imaging required"],
                )
                explanation = st.text_area(
                    "Physician Findings & Explanation",
                    placeholder="Document your radiological observations (e.g. cortical destruction, periosteal reaction, soft tissue mass) and how the AI heatmap was considered.",
                    height=100,
                )
                recommendation = st.text_area(
                    "Recommended Next Step",
                    placeholder="e.g., Urgent orthopedic oncology referral, dedicated MRI with contrast, core needle biopsy, or routine follow-up.",
                    height=80,
                )
                submit_review = st.form_submit_button("Submit Diagnostic Review", type="primary", use_container_width=True)

            if submit_review:
                if not explanation.strip() or not recommendation.strip():
                    st.error("Please complete both the clinical explanation and recommended next steps.")
                else:
                    save_review(case["id"], verdict, explanation.strip(), recommendation.strip())
                    st.success(f"Review for Case {case['id']} recorded successfully.")
                    st.rerun()

    # Reviewed history section
    if reviewed:
        st.divider()
        with st.expander(f"Archived & Completed Reviews ({len(reviewed)})"):
            for r in reviewed:
                with st.container(border=True):
                    rc1, rc2 = st.columns([2, 1])
                    with rc1:
                        st.markdown(f"**Case `{html.escape(str(r['id']))}`** — Patient: {html.escape(str(r['patient_name']))}")
                        st.write(f"**Verdict:** {r['doctor_verdict']}")
                        st.write(f"**Doctor Notes:** {r['doctor_explanation']}")
                        st.caption(f"Recommendation: {r['recommendation']} | Reviewed at {r['reviewed_at']}")
                    with rc2:
                        rc_cam = resolve_path(r["gradcam_path"])
                        if rc_cam and rc_cam.exists():
                            st.image(str(rc_cam), caption="Grad-CAM Saliency", use_container_width=True)
                        else:
                            rc_img = resolve_path(r["image_path"])
                            if rc_img and rc_img.exists():
                                st.image(str(rc_img), caption="Scan", use_container_width=True)


def main():
    check_session_timeout()
    setup_page()
    init_database()
    if "user" not in st.session_state:
        login_screen()
        return
    user = st.session_state.user
    with st.sidebar:
        st.markdown("### CareLens Clinical System")
        st.write(f"**{user['display_name']}**")
        st.caption(f"Role: `{user['role']}`")
        st.markdown("---")
        if st.button("Sign out", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    if user["role"] == "patient":
        patient_page(user)
    else:
        doctor_page()


if __name__ == "__main__":
    main()
