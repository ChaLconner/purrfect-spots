# PowerShell script to install dependencies and start backend
Write-Host "🚀 Installing backend dependencies..." -ForegroundColor Green

# Change to script directory
Set-Location $PSScriptRoot

Write-Host "📦 Installing Python packages..." -ForegroundColor Yellow
pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Installation complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🔧 To start the server, run:" -ForegroundColor Cyan
    Write-Host "   python app.py" -ForegroundColor White
    Write-Host ""
    
    $start = Read-Host "Do you want to start the server now? (y/N)"
    if ($start -eq "y" -or $start -eq "Y") {
        Write-Host "🚀 Starting server..." -ForegroundColor Green
        python app.py
    }
} else {
    Write-Host "❌ Installation failed!" -ForegroundColor Red
}
