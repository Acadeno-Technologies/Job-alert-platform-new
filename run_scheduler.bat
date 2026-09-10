@echo off
title Acadeno Job Alert Scheduler (10 AM & 5 PM Daily)
echo ============================================================
echo Starting Acadeno Job Alert Scheduler (10:00 AM & 5:00 PM)...
echo ============================================================
if exist ..\venv\Scripts\activate.bat (
    call ..\venv\Scripts\activate.bat
) else if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)
python scheduler.py
pause
