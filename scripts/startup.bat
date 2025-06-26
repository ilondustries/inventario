@echo off
title Sistema de Almacén - Servidor
echo ========================================
echo    Sistema de Almacén Local
echo    Iniciando servidor automaticamente...
echo ========================================
echo.

cd /d "%~dp0.."
python scripts/start_server.py

echo.
echo Servidor detenido. Presiona cualquier tecla para reiniciar...
pause
goto :eof 