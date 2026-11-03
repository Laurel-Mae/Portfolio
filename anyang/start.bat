@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Mae Ann Laurel - Portfolio (Python 3.13)

REM Use Python 3.13 explicitly; never pick the default Python 3.14.
where py >nul 2>nul
if not errorlevel 1 (
    py -3.13 -c "import sys; raise SystemExit(sys.version_info[:2] != (3, 13))" >nul 2>nul
    if not errorlevel 1 (
        py -3.13 "server\tools\dev.py" %*
        if errorlevel 1 goto :failed
        exit /b 0
    )
)

REM Fallback for installations without the py launcher.
if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" "server\tools\dev.py" %*
    if errorlevel 1 goto :failed
    exit /b 0
)

python -c "import sys; raise SystemExit(sys.version_info[:2] != (3, 13))" >nul 2>nul
if not errorlevel 1 (
    python "server\tools\dev.py" %*
    if errorlevel 1 goto :failed
    exit /b 0
)

echo [ERROR] Python 3.13 was not found. Python 3.14 may remain installed.
echo Check with: py -3.13 --version
goto :failed

:failed
echo.
echo Startup did not complete. Review the error above.
pause
exit /b 1
