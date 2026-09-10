@echo off
echo Creating Python virtual environment (venv)...
python -m venv venv
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo Installing dependencies from requirements.txt...
pip install -r requirements.txt
echo.
echo Virtual environment setup complete!
pause
