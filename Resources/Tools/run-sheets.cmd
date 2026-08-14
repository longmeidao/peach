@echo off
chcp 65001 >nul
title 全库关键帧接触表 (无人值守，可关窗口重开续跑)
set PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe
echo.
echo   全库关键帧接触表 —— 每个视频抽 9 帧拼一张图
echo.
echo   前置：必须先跑完 run-probe.cmd（需要 duration 才能定位抽帧点）
echo   * 可随时关窗口，重开自动续跑
echo   * 产物在 R:\Resources\Intake\snapshots\cloud\
echo   * 日志在 R:\Resources\Migration_Logs\sheets-*.log
echo.
"%PY%" "R:\Resources\Tools\rm-sheets.py" --workers 4 --frames 9 %*
echo.
pause >nul
