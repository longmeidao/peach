@echo off
chcp 65001 >nul
title 全库 ffprobe (无人值守，可关窗口重开续跑)
set PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe
echo.
echo   全库 ffprobe —— 给账本补时长/分辨率/编码，以及情境层的时长档/屏向/画质
echo.
echo   * 可以随时 Ctrl-C 或直接关窗口，重新运行会自动续跑
echo   * 日志写在 R:\Resources\Migration_Logs\probe-*.log
echo.
"%PY%" "R:\Resources\Tools\rm-probe.py" --workers 6 --interval 0.15 %*
echo.
echo   完成。按任意键关闭。
pause >nul
