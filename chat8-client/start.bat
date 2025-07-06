@echo off
echo Starting Chat8 Client...
echo.

cd /d "%~dp0"

echo Checking Node.js installation...
node --version >nul 2>&1
if errorlevel 1 (
    echo Error: Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

echo Building Signal library...
cd libsignal
cargo build --release
if errorlevel 1 (
    echo Warning: Failed to build Signal library. Some features may not work.
)
cd ..

echo Installing frontend dependencies...
cd frontend
npm install
if errorlevel 1 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)

echo Starting development server...
echo Client will be available at http://localhost:5173
echo Make sure the server is running at http://localhost:8000
echo.
npm run dev

pause