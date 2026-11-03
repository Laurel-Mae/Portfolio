@echo off
setlocal EnableExtensions
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
    py -3.13 "server\tools\package.py"
) else (
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" "server\tools\package.py"
)
if errorlevel 1 (
    echo Packaging failed. Review the error above.
    pause
    exit /b 1
)
echo.
echo ZIP ready in the parent directory of this project.
pause
