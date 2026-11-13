@echo off
title NetVibe LAN Chat Server
cd /d "%~dp0"
echo ===================================================
echo     Starting NetVibe LAN Real-Time Chat Server...
echo ===================================================
python server.py
pause
