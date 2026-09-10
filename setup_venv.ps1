Write-Host "Creating Python virtual environment (venv)..." -ForegroundColor Cyan
python -m venv venv
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
.\venv\Scripts\Activate.ps1
Write-Host "Installing dependencies from requirements.txt..." -ForegroundColor Cyan
pip install -r requirements.txt
Write-Host "Virtual environment setup complete!" -ForegroundColor Green
