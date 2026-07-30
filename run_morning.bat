@echo off
title MarketMentor AI - Morning Pre-Market Engine
echo ==================================================
echo     RUNNING MARKETMENTOR MORNING ENGINE
echo ==================================================
cd /d "%~dp0"
.venv\Scripts\python.exe morning_screener.py
echo ==================================================
echo Done! Morning pre-market insights broadcasted.
pause
