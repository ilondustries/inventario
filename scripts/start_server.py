#!/usr/bin/env python3
"""
Script para iniciar el servidor del Sistema de Almacén
"""

import os
import sys
import socket
import subprocess
from pathlib import Path

def get_local_ip():
    """Obtiene la IP local del servidor"""
    try:
        # Conectarse a un servidor externo para obtener la IP local
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def check_python_version():
    """Verifica que Python sea 3.7 o superior"""
    if sys.version_info < (3, 7):
        print("❌ Error: Se requiere Python 3.7 o superior")
        print(f"   Versión actual: {sys.version}")
        return False
    return True

def install_requirements():
    """Instala las dependencias necesarias"""
    requirements_file = Path(__file__).parent.parent / "backend" / "requirements.txt"
    
    if not requirements_file.exists():
        print("❌ Error: No se encontró requirements.txt")
        return False
    
    print("📦 Instalando dependencias...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)])
        print("✅ Dependencias instaladas correctamente")
        return True
    except subprocess.CalledProcessError:
        print("❌ Error al instalar dependencias")
        return False

def start_server():
    """Inicia el servidor"""
    backend_dir = Path(__file__).parent.parent / "backend"
    main_file = backend_dir / "main.py"
    
    if not main_file.exists():
        print("❌ Error: No se encontró main.py")
        return False
    
    # Cambiar al directorio del backend
    os.chdir(backend_dir)
    
    # Obtener IP local
    local_ip = get_local_ip()
    
    print("🚀 Iniciando Sistema de Almacén...")
    print(f"📱 Servidor disponible en:")
    print(f"   Local: http://localhost:8000")
    print(f"   Red: http://{local_ip}:8000")
    print(f"   📋 API Docs: http://localhost:8000/docs")
    print("\nPara acceder desde tu tablet, usa la URL de 'Red'")
    print("🛑 Presiona Ctrl+C para detener el servidor")
    print("-" * 50)
    
    try:
        # Iniciar servidor con uvicorn
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n👋 Servidor detenido")
    except Exception as e:
        print(f"❌ Error al iniciar servidor: {e}")
        return False
    
    return True

def main():
    """Función principal"""
    print("Sistema de Almacén - Iniciador")
    print("=" * 40)
    
    # Verificar versión de Python
    if not check_python_version():
        sys.exit(1)
    
    # Instalar dependencias
    if not install_requirements():
        sys.exit(1)
    
    # Iniciar servidor
    start_server()

if __name__ == "__main__":
    main() 