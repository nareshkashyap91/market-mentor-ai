@echo off
title MarketMentor AI - Intraday Trading Signal Engine
echo ==================================================
echo     RUNNING MARKETMENTOR INTRADAY ENGINE (ORB)
echo ==================================================
cd /d "%~dp0"
.venv\Scripts\python.exe intraday_screener.py
echo ==================================================
echo Done! Intraday scans completed.
pause
