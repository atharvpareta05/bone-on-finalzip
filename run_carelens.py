import os
import signal
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
VENV_PYTHON = (
    PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
    if os.name == "nt"
    else PROJECT_ROOT / ".venv" / "bin" / "python"
)

# If invoked via system Python without activating venv, automatically re-exec using .venv python!
if VENV_PYTHON.exists():
    try:
        if Path(sys.executable).resolve() != VENV_PYTHON.resolve():
            sys.exit(subprocess.call([str(VENV_PYTHON)] + sys.argv))
    except Exception:
        pass

PYTHON_EXE = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable

# Find npm executable (on Windows it's usually npm.cmd)
NPM_CMD = "npm.cmd" if os.name == "nt" else "npm"


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def kill_process_on_port(port: int):
    if not is_port_in_use(port):
        return
    if os.name == "nt":
        try:
            cmd = f'powershell -Command "Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | ForEach-Object {{ Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }}"'
            subprocess.run(cmd, shell=True, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1)
        except Exception:
            pass


def wait_for_port(port: int, timeout: int = 60) -> bool:
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_port_in_use(port):
            return True
        time.sleep(0.5)
    return False


def wait_for_url(url: str, timeout: int = 30) -> bool:
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)
    return False


def main():
    print("=" * 60)
    print("   CareLens 2.0 — Clinical Decision-Support System")
    print("=" * 60)

    # 1. Clean up any stale processes on ports 8000 or 3000
    print("[1/4] Checking and freeing ports 8000 & 3000...")
    kill_process_on_port(8000)
    kill_process_on_port(3000)

    # 2. Start FastAPI Backend
    print(f"[2/4] Starting FastAPI Backend on http://localhost:8000 (using {Path(PYTHON_EXE).name}) ...")
    backend_env = os.environ.copy()
    backend_env["PYTHONUNBUFFERED"] = "1"

    backend_proc = subprocess.Popen(
        [PYTHON_EXE, str(PROJECT_ROOT / "backend" / "run.py")],
        cwd=str(PROJECT_ROOT),
        env=backend_env,
    )

    print("      Waiting for model and API to load...", end="", flush=True)
    if not wait_for_port(8000, timeout=30):
        print(" [FAILED]")
        print("ERROR: FastAPI backend failed to start on http://localhost:8000.")
        backend_proc.kill()
        sys.exit(1)
    print(" [READY]")

    # 3. Start Next.js Frontend
    print("[3/4] Starting Next.js Frontend on http://localhost:3000 ...")
    frontend_proc = subprocess.Popen(
        [NPM_CMD, "run", "dev"],
        cwd=str(FRONTEND_DIR),
        env=os.environ.copy(),
    )

    print("      Waiting for web portal...", end="", flush=True)
    if not wait_for_port(3000, timeout=60):
        print(" [FAILED]")
        print("ERROR: Next.js frontend failed to start on http://localhost:3000.")
        backend_proc.kill()
        frontend_proc.kill()
        sys.exit(1)
    print(" [READY]")

    # 4. Success Banner and Launch
    print("\n" + "=" * 60)
    print("   CareLens 2.0 is LIVE!")
    print("   - Web Portal:   http://localhost:3000")
    print("   - Backend Docs: http://localhost:8000/docs")
    print("   - Health Probe: http://localhost:8000/health")
    print("   ")
    print("   Demo Accounts:")
    print("     Doctor:  doctor1  / CareLens2026!Doctor")
    print("     Patient: patient1 / CareLens2026!Patient")
    print("=" * 60)
    print("Press CTRL+C anytime in this terminal to stop both servers.\n")

    # Open browser automatically after a brief 2-second grace period
    time.sleep(2)
    try:
        webbrowser.open("http://localhost:3000")
    except Exception:
        pass

    def cleanup(signum=None, frame=None):
        print("\n[SHUTDOWN] Stopping CareLens 2.0 servers...")
        try:
            if os.name == "nt":
                subprocess.run(f"taskkill /F /T /PID {backend_proc.pid}", shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                subprocess.run(f"taskkill /F /T /PID {frontend_proc.pid}", shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            else:
                backend_proc.terminate()
                frontend_proc.terminate()
        except Exception:
            pass
        print("[SHUTDOWN] Done. Goodbye!")
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    try:
        while True:
            # Monitor child processes; if either crashes, alert and exit
            ret_b = backend_proc.poll()
            if ret_b is not None:
                print(f"\n[ALERT] Backend process exited unexpectedly with code {ret_b}.")
                cleanup()
            ret_f = frontend_proc.poll()
            if ret_f is not None:
                print(f"\n[ALERT] Frontend process exited unexpectedly with code {ret_f}.")
                cleanup()
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    main()
