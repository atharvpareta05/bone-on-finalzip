import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Generator

from backend.app.config import settings


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(settings.db_path)
    connection.row_factory = sqlite3.Row
    return connection


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


def init_database() -> None:
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('patient', 'doctor')),
                display_name TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
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

            CREATE TABLE IF NOT EXISTS login_attempts (
                username TEXT PRIMARY KEY,
                failed_attempts INTEGER NOT NULL DEFAULT 0,
                locked_until TEXT
            );

            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                case_id TEXT,
                details TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )

        # Migration guard: Ensure gradcam_path column exists in cases
        try:
            conn.execute("ALTER TABLE cases ADD COLUMN gradcam_path TEXT")
        except sqlite3.OperationalError:
            pass

        # Migration guard: Ensure created_at column exists in users
        try:
            conn.execute("ALTER TABLE users ADD COLUMN created_at TEXT")
            conn.execute("UPDATE users SET created_at = datetime('now') WHERE created_at IS NULL")
            conn.commit()
        except sqlite3.OperationalError:
            pass

        # Seed initial demo accounts if database is empty and config exists
        user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if user_count == 0 and settings.demo_users_path.exists():
            from backend.app.security import hash_password

            try:
                with settings.demo_users_path.open("r", encoding="utf-8") as f:
                    demo_configs = json.load(f)
                    demo_users = [
                        (
                            u["username"],
                            hash_password(u["password"]),
                            u["role"],
                            u["display_name"],
                            datetime.now().isoformat(timespec="seconds"),
                        )
                        for u in demo_configs
                    ]
                    conn.executemany(
                        "INSERT OR IGNORE INTO users (username, password_hash, role, display_name, created_at) VALUES (?, ?, ?, ?, ?)",
                        demo_users,
                    )
                    conn.commit()
            except Exception as e:
                print(f"[WARN] Failed seeding demo users: {e}")
