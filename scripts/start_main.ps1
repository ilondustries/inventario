# Script para iniciar servidor MAIN
Write-Host "🚀 Iniciando servidor MAIN..." -ForegroundColor Green
Write-Host "📊 Base de datos: almacen_main.db" -ForegroundColor Yellow
Write-Host "🔒 Puerto: 8001 (HTTPS)" -ForegroundColor Yellow
Write-Host "🌿 Rama: main" -ForegroundColor Yellow
Write-Host ""

# Configurar variables de entorno
$env:BRANCH = "main"
$env:PORT = "8001"
$env:ENVIRONMENT = "production"

# Cambiar al directorio backend
Set-Location "backend"

# Iniciar servidor con HTTPS
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --ssl-keyfile=./key.pem --ssl-certfile=./cert.pem --reload

Write-Host ""
Write-Host "🛑 Servidor detenido" -ForegroundColor Red 