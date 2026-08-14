@echo off
echo === %DATE% %TIME% === > R:\Resources\Migration_Logs\drivetest.txt
if exist B:\ (echo B: OK) else (echo B: MISSING) >> R:\Resources\Migration_Logs\drivetest.txt
if exist A:\ (echo A: OK) else (echo A: MISSING) >> R:\Resources\Migration_Logs\drivetest.txt
dir B:\ /b 2>&1 | findstr /n "^" | findstr "^[1-3]:" >> R:\Resources\Migration_Logs\drivetest.txt
