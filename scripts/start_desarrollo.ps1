# Script para iniciar servidor de DESARROLLO
Write-Host "🚀 Iniciando servidor DESARROLLO..." -ForegroundColor Green
Write-Host "📊 Base de datos: almacen_desarrollo.db" -ForegroundColor Yellow
Write-Host "🔒 Puerto: 8000 (HTTPS)" -ForegroundColor Yellow
Write-Host "🌿 Rama: desarrollo" -ForegroundColor Yellow
Write-Host ""

# Configurar variables de entorno
$env:BRANCH = "desarrollo"
$env:PORT = "8000"
$env:ENVIRONMENT = "development"

# Cambiar al directorio backend
Set-Location "backend"

# Iniciar servidor con HTTPS
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --ssl-keyfile=./key.pem --ssl-certfile=./cert.pem --reload

Write-Host ""
Write-Host "🛑 Servidor detenido" -ForegroundColor Red 