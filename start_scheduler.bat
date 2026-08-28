@echo off
title MarketMentor AI - 15 Min Auto Scheduler & Telegram Broadcast
cd /d "%~dp0"
echo ========================================================
echo   MARKET MENTOR AI - 15 MIN AUTO SCHEDULER & TELEGRAM
echo ========================================================
echo.
echo Starting 15-minute automated options quant scanner...
echo Telegram alerts will be sent to your phone every 15 minutes!
echo.
.venv\Scripts\python.exe run_local_scheduler.py
pause
