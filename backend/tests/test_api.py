import io
import sys
from pathlib import Path
import pytest
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import init_database, get_connection
from backend.app.security import hash_password

client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    init_database()
    # Seed a test doctor if not exists
    with get_connection() as conn:
        doc = conn.execute("SELECT id FROM users WHERE username = 'test_doctor'").fetchone()
        if not doc:
            conn.execute(
                "INSERT INTO users (username, password_hash, role, display_name) VALUES (?, ?, 'doctor', ?)",
                ("test_doctor", hash_password("DoctorPass123!"), "Dr. Test Radiologist"),
            )
            conn.commit()


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert "model_loaded" in data
    assert "db_connected" in data
    assert data["db_connected"] is True


def test_auth_registration_and_login():
    import uuid
    rand_suffix = uuid.uuid4().hex[:6]
    username = f"pt_{rand_suffix}"
    password = "StrongPassword123!"
    display_name = f"Patient {rand_suffix}"

    # 1. Register Patient
    reg_res = client.post(
        "/api/auth/register",
        json={"username": username, "password": password, "display_name": display_name},
    )
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert reg_data["username"] == username
    assert reg_data["role"] == "patient"

    # 2. Duplicate Registration Rejection
    dup_res = client.post(
        "/api/auth/register",
        json={"username": username, "password": password, "display_name": display_name},
    )
    assert dup_res.status_code == 409

    # 3. Successful Login
    login_res = client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    assert token_data["user"]["username"] == username
    assert "carelens_refresh_token" in login_res.cookies

    # 4. Access /api/me with token
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    me_res = client.get("/api/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["username"] == username


def test_login_lockout():
    import uuid
    dummy_user = f"baduser_{uuid.uuid4().hex[:6]}"
    # Register dummy
    client.post(
        "/api/auth/register",
        json={"username": dummy_user, "password": "DummyPassword123!", "display_name": "Dummy"},
    )

    # Fail 5 times
    for _ in range(5):
        fail_res = client.post(
            "/api/auth/login",
            json={"username": dummy_user, "password": "WrongPassword!"},
        )
        assert fail_res.status_code in (401, 429)

    # 6th attempt must be locked out
    locked_res = client.post(
        "/api/auth/login",
        json={"username": dummy_user, "password": "DummyPassword123!"},
    )
    assert locked_res.status_code == 429
    assert "locked" in locked_res.json()["detail"].lower()


def test_case_lifecycle_and_media_authorization():
    # 1. Login Patient A
    import uuid
    user_a = f"pta_{uuid.uuid4().hex[:6]}"
    client.post("/api/auth/register", json={"username": user_a, "password": "Password123!", "display_name": "User A"})
    login_a = client.post("/api/auth/login", json={"username": user_a, "password": "Password123!"})
    token_a = login_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Login Patient B
    user_b = f"ptb_{uuid.uuid4().hex[:6]}"
    client.post("/api/auth/register", json={"username": user_b, "password": "Password123!", "display_name": "User B"})
    login_b = client.post("/api/auth/login", json={"username": user_b, "password": "Password123!"})
    token_b = login_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. Login Doctor
    doc_login = client.post("/api/auth/login", json={"username": "test_doctor", "password": "DoctorPass123!"})
    doc_token = doc_login.json()["access_token"]
    doc_headers = {"Authorization": f"Bearer {doc_token}"}

    # 4. Patient A uploads a synthetic 224x224 bone scan
    img = Image.new("RGB", (224, 224), color=(128, 128, 128))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    img_byte_arr.seek(0)

    upload_res = client.post(
        "/api/cases",
        headers=headers_a,
        files={"file": ("synthetic_scan.png", img_byte_arr.getvalue(), "image/png")},
    )
    assert upload_res.status_code == 201
    case_data = upload_res.json()
    case_id = case_data["id"]
    assert case_id.startswith("CASE-")
    assert case_data["status"] == "AI-analyzed"
    assert "cancer_probability" in case_data
    assert case_data["risk_band"] in ("High Risk", "Borderline / Indeterminate", "Low Risk")

    # 5. Media Authorization Check:
    # Patient A can access their own scan
    media_a_res = client.get(f"/api/media/{case_id}/original", headers=headers_a)
    assert media_a_res.status_code == 200
    assert media_a_res.headers["content-type"] == "image/png"

    # Patient B CANNOT access Patient A's scan (403 Forbidden)
    media_b_res = client.get(f"/api/media/{case_id}/original", headers=headers_b)
    assert media_b_res.status_code == 403

    # Doctor CAN access Patient A's scan
    doc_media_res = client.get(f"/api/media/{case_id}/original", headers=doc_headers)
    assert doc_media_res.status_code == 200

    # 6. Doctor Queue & Review
    queue_res = client.get("/api/cases?status=pending", headers=doc_headers)
    assert queue_res.status_code == 200
    queue_items = queue_res.json()["items"]
    assert any(c["id"] == case_id for c in queue_items)

    review_res = client.post(
        f"/api/cases/{case_id}/review",
        headers=doc_headers,
        json={
            "doctor_verdict": "Benign Osteochondroma",
            "doctor_explanation": "Smooth pedunculated exostosis without cortical breach or aggressive soft tissue component.",
            "recommendation": "Routine clinical observation. Baseline follow-up radiograph in 12 months.",
        },
    )
    assert review_res.status_code == 200
    reviewed_case = review_res.json()
    assert reviewed_case["status"] == "Reviewed"
    assert reviewed_case["doctor_verdict"] == "Benign Osteochondroma"

    # 7. PDF Report Download
    pdf_res = client.get(f"/api/cases/{case_id}/report.pdf", headers=headers_a)
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert pdf_res.content[:4] == b"%PDF"
