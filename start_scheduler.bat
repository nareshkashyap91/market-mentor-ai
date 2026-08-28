@echo off
title MarketMentor AI - 15 Min Auto Scheduler & Telegram 2-Way Bot
cd /d "%~dp0"
echo ========================================================
echo   MARKET MENTOR AI - 15 MIN AUTO SCHEDULER & BOT
echo ========================================================
echo.
echo Starting 2-Way Interactive Telegram Listener Bot...
start "MarketMentor AI Telegram Bot Listener" .venv\Scripts\python.exe run_telegram_bot_listener.py
echo.
echo Starting 15-minute automated options quant scanner...
echo Telegram alerts will be sent to your phone every 15 minutes!
echo.
.venv\Scripts\python.exe run_local_scheduler.py
pause
