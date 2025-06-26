# Sistema de Almacén - Script de Inicio
# PowerShell script para iniciar el servidor automáticamente

Write-Host "========================================" -ForegroundColor Green
Write-Host "    Sistema de Almacén Local" -ForegroundColor Yellow
Write-Host "    Iniciando servidor..." -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Cambiar al directorio del proyecto
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectPath = Split-Path -Parent $scriptPath
Set-Location $projectPath

Write-Host "Directorio de trabajo: $projectPath" -ForegroundColor Cyan

# Verificar que Python esté instalado
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python encontrado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: Python no está instalado" -ForegroundColor Red
    Write-Host "Presiona cualquier tecla para salir..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# Verificar que el script existe
$serverScript = Join-Path $scriptPath "start_server.py"
if (-not (Test-Path $serverScript)) {
    Write-Host "❌ Error: No se encontró start_server.py" -ForegroundColor Red
    Write-Host "Presiona cualquier tecla para salir..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

Write-Host "✅ Iniciando servidor..." -ForegroundColor Green
Write-Host ""

# Iniciar el servidor
try {
    python $serverScript
} catch {
    Write-Host "❌ Error al iniciar el servidor: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "Servidor detenido. Presiona cualquier tecla para reiniciar..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 