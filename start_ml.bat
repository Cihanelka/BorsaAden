@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
cd /d "%~dp0ml-service"
"%~dp0.venv\Scripts\python.exe" app.py
