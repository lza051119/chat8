@echo off
echo Starting Chat8 Server...
echo.

cd /d "%~dp0"

if not exist "backend\venv" (
    echo Creating virtual environment...
    cd backend
    python -m venv venv
    cd ..
)

echo Activating virtual environment...
call backend\venv\Scripts\activate.bat

echo Installing dependencies...
cd backend
pip install -r requirements.txt

echo Initializing database...
python -m app.init_db

echo Starting server on http://localhost:8000
python -m app.main

pause