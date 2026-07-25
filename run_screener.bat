@echo off
title MarketMentor AI - Automated Stock & Mutual Fund Report
cd /d "%~dp0"

echo ========================================================
echo               MarketMentor AI System
echo ========================================================
echo.

if not exist .venv\ (
    echo [ERROR] Virtual environment .venv was not found in this folder.
    echo Please ensure the setup is run first.
    pause
    exit /b 1
)

echo [INFO] Running automated analysis...
echo [INFO] Fetching EOD market data, performing technical analysis,
echo [INFO] and calculating Mutual Fund CAGR metrics...
echo.

.venv\Scripts\python.exe screener.py

echo.
echo ========================================================
echo Execution complete. Press any key to close this window.
echo ========================================================
pause > nul
