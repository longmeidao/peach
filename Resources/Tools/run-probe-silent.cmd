@echo off
chcp 65001 >nul
"%LOCALAPPDATA%\Programs\Python\Python312\python.exe" "R:\Resources\Tools\rm-probe.py" --workers 12 --interval 0.03
