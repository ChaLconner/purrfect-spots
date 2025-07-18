@echo off
echo 🚀 Installing backend dependencies...
echo.

cd /d "%~dp0"

echo 📦 Installing Python packages...
pip install -r requirements.txt

echo.
echo ✅ Installation complete!
echo.
echo 🔧 To start the server, run:
echo    python app.py
echo.
pause
