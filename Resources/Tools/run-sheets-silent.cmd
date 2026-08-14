@echo off
chcp 65001 >nul
"%LOCALAPPDATA%\Programs\Python\Python312\python.exe" "R:\Resources\Tools\rm-sheets.py" --workers 4 --frames 9
