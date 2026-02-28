@echo off
REM Multi-LLM Risk Intelligence Platform - Setup Script for Windows

echo.
echo 🧠 Multi-LLM Risk Intelligence Platform Setup
echo =============================================
echo.

REM Check Python version
echo Checking Python version...
python --version
echo ✅ Python found
echo.

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
echo ✅ Virtual environment created
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo ✅ Virtual environment activated
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip
echo ✅ pip upgraded
echo.

REM Install requirements
echo Installing dependencies...
pip install -r requirements.txt
echo ✅ Dependencies installed
echo.

REM Copy .env.example to .env if it doesn't exist
if not exist .env (
    echo Creating .env file...
    copy .env.example .env
    echo ✅ .env file created
    echo.
    echo ⚠️  IMPORTANT: Edit .env and add your API keys:
    echo    - OPENAI_API_KEY
    echo    - GOOGLE_API_KEY
    echo.
) else (
    echo ✅ .env file already exists
    echo.
)

echo =============================================
echo ✅ Setup complete!
echo.
echo Next steps:
echo 1. Edit .env file and add your API keys
echo 2. Run: streamlit run app/main.py
echo 3. Visit: http://localhost:8501
echo.
echo For Docker deployment:
echo   docker-compose up --build
echo.
echo =============================================
pause
