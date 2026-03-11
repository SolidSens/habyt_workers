@echo off
REM Script to start Chrome with remote debugging enabled on port 9222
REM This allows the worker to connect to an existing Chrome instance

echo Starting Chrome with remote debugging on port 9222...
echo.

REM Windows path to Chrome executable
REM Modify this path if your Chrome is installed elsewhere
set CHROME_PATH="C:\Program Files\Google\Chrome\Application\chrome.exe"

REM Check if Chrome exists at default location
if not exist %CHROME_PATH% (
    echo Chrome not found at default location.
    echo Please edit this script and set CHROME_PATH to your Chrome executable path.
    echo.
    echo Common Chrome locations:
    echo   C:\Program Files\Google\Chrome\Application\chrome.exe
    echo   C:\Program Files (x86)\Google\Chrome\Application\chrome.exe
    echo   %LOCALAPPDATA%\Google\Chrome\Application\chrome.exe
    pause
    exit /b 1
)

REM Start Chrome with remote debugging
start "" %CHROME_PATH% --remote-debugging-port=9222 --user-data-dir="%LOCALAPPDATA%\Google\Chrome\User Data"

echo.
echo Chrome started with remote debugging enabled!
echo Port: 9222
echo.
echo You can now run the worker script.
echo.
pause
