@echo off
title Launch Document OCR System
echo ========================================================
echo        MEMULAI DOKUMEN OCR SYSTEM SWADHARMA
echo ========================================================
echo.
echo [1/2] Menjalankan Backend API FastAPI...
start "OCR Backend Server" cmd /k "cd /d %~dp0backend && venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8001"

echo [2/2] Menjalankan Frontend Web UI React Vite...
start "OCR Frontend App" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ========================================================
echo Sukses! Server Backend dan Frontend sudah berjalan.
echo ========================================================

