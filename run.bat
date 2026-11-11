@echo off
title Spot Train API (Port 8001)
cd /d D:\SPOT_TRAIN
echo ========================================================
echo Starting Spot Train API on http://127.0.0.1:8001
echo Swagger Docs: http://127.0.0.1:8001/docs
echo ReDoc:        http://127.0.0.1:8001/redoc
echo ========================================================
echo.
.\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8001
pause

