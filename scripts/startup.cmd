@echo off
title Sistema de Almacén - Servidor
color 0A

echo ========================================
echo    Sistema de Almacén Local
echo    Iniciando servidor automaticamente...
echo ========================================
echo.

REM Cambiar al directorio del proyecto
cd /d "%~dp0.."

REM Verificar que Python esté instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Python no está instalado
    echo Presiona cualquier tecla para salir...
    pause >nul
    exit /b 1
)

REM Verificar que el script existe
if not exist "scripts\start_server.py" (
    echo ❌ Error: No se encontró start_server.py
    echo Presiona cualquier tecla para salir...
    pause >nul
    exit /b 1
)

echo ✅ Python encontrado
echo ✅ Script encontrado
echo ✅ Iniciando servidor...
echo.

REM Iniciar el servidor
python scripts\start_server.py

echo.
echo Servidor detenido. Presiona cualquier tecla para reiniciar...
pause >nul
goto :eof 