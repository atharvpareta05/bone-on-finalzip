@echo off
title CareLens 2.0 - Clinical Decision-Support System
echo ===================================================
echo Starting CareLens 2.0 (FastAPI Backend + Next.js Frontend)
echo ===================================================

echo [1/2] Starting FastAPI Backend on http://localhost:8000 ...
start "CareLens Backend (Port 8000)" cmd /k ".\.venv\Scripts\python.exe backend/run.py"

echo [2/2] Starting Next.js Frontend on http://localhost:3000 ...
cd frontend
start "CareLens Frontend (Port 3000)" cmd /k "npm run dev"
cd ..

echo.
echo ===================================================
echo CareLens is starting up!
echo - Web Application: http://localhost:3000
echo - Backend API Docs: http://localhost:8000/docs
echo ===================================================
timeout /t 5
start http://localhost:3000
