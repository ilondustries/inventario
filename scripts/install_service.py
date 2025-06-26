#!/usr/bin/env python3
"""
Script para instalar el Sistema de Almacén como servicio de Windows
Requerimientos: pywin32 (pip install pywin32)
"""

import os
import sys
import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import subprocess
from pathlib import Path

class AlmacenService(win32serviceutil.ServiceFramework):
    _svc_name_ = "SistemaAlmacen"
    _svc_display_name_ = "Sistema de Almacén Local"
    _svc_description_ = "Servidor web para gestión de inventario en red local"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.process = None

    def SvcStop(self):
        """Detener el servicio"""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        if self.process:
            self.process.terminate()

    def SvcDoRun(self):
        """Ejecutar el servicio"""
        try:
            # Cambiar al directorio del proyecto
            project_dir = Path(__file__).parent.parent
            os.chdir(project_dir)
            
            # Iniciar el servidor
            self.process = subprocess.Popen([
                sys.executable, "scripts/start_server.py"
            ])
            
            # Esperar hasta que se detenga
            self.process.wait()
            
        except Exception as e:
            with open("C:/almacen_service_error.log", "a") as f:
                f.write(f"Error en servicio: {e}\n")

def install_service():
    """Instalar el servicio"""
    try:
        # Verificar que pywin32 esté instalado
        import win32serviceutil
    except ImportError:
        print("❌ Error: pywin32 no está instalado")
        print("Instala con: pip install pywin32")
        return False
    
    try:
        win32serviceutil.InstallService(
            AlmacenService._svc_name_,
            AlmacenService._svc_display_name_,
            AlmacenService._svc_description_
        )
        print("✅ Servicio instalado correctamente")
        print("Para iniciar: net start SistemaAlmacen")
        print("Para detener: net stop SistemaAlmacen")
        return True
    except Exception as e:
        print(f"❌ Error instalando servicio: {e}")
        return False

def uninstall_service():
    """Desinstalar el servicio"""
    try:
        win32serviceutil.RemoveService(AlmacenService._svc_name_)
        print("✅ Servicio desinstalado correctamente")
        return True
    except Exception as e:
        print(f"❌ Error desinstalando servicio: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "install":
            install_service()
        elif sys.argv[1] == "uninstall":
            uninstall_service()
        else:
            win32serviceutil.HandleCommandLine(AlmacenService)
    else:
        print("Uso:")
        print("  python install_service.py install    - Instalar servicio")
        print("  python install_service.py uninstall  - Desinstalar servicio")
        print("  python install_service.py start      - Iniciar servicio")
        print("  python install_service.py stop       - Detener servicio") 