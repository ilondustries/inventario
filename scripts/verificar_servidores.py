#!/usr/bin/env python3
"""
Script para verificar qué base de datos está usando cada servidor
"""

import requests
import json
import sys
import os

# Configuración
BASE_URL_DESARROLLO = "https://localhost:8000"
BASE_URL_MAIN = "https://localhost:8001"

def verificar_servidor(url, nombre):
    """Verificar un servidor específico"""
    try:
        # Intentar obtener estadísticas
        response = requests.get(f"{url}/api/estadisticas", verify=False, timeout=5)
        
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Servidor {nombre} ({url}) está funcionando")
            print(f"   - Productos: {stats.get('total_productos', 'N/A')}")
            print(f"   - Tickets: {stats.get('total_tickets', 'N/A')}")
            print(f"   - Usuarios: {stats.get('total_usuarios', 'N/A')}")
            return True
        else:
            print(f"❌ Servidor {nombre} ({url}) respondió con código {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Servidor {nombre} ({url}) no está respondiendo")
        return False
    except Exception as e:
        print(f"❌ Error verificando {nombre}: {e}")
        return False

def verificar_base_datos():
    """Verificar las bases de datos"""
    import sqlite3
    
    print("\n=== VERIFICACIÓN DE BASES DE DATOS ===")
    
    # Verificar almacen_desarrollo.db
    try:
        conn_desarrollo = sqlite3.connect('data/almacen_desarrollo.db')
        cursor_desarrollo = conn_desarrollo.cursor()
        
        cursor_desarrollo.execute("SELECT COUNT(*) FROM productos")
        productos_desarrollo = cursor_desarrollo.fetchone()[0]
        
        cursor_desarrollo.execute("SELECT COUNT(*) FROM tickets_compra")
        tickets_desarrollo = cursor_desarrollo.fetchone()[0]
        
        cursor_desarrollo.execute("SELECT COUNT(*) FROM usuarios")
        usuarios_desarrollo = cursor_desarrollo.fetchone()[0]
        
        conn_desarrollo.close()
        
        print(f"✅ almacen_desarrollo.db:")
        print(f"   - Productos: {productos_desarrollo}")
        print(f"   - Tickets: {tickets_desarrollo}")
        print(f"   - Usuarios: {usuarios_desarrollo}")
        
    except Exception as e:
        print(f"❌ Error con almacen_desarrollo.db: {e}")
    
    # Verificar almacen_main.db
    try:
        conn_main = sqlite3.connect('data/almacen_main.db')
        cursor_main = conn_main.cursor()
        
        cursor_main.execute("SELECT COUNT(*) FROM productos")
        productos_main = cursor_main.fetchone()[0]
        
        cursor_main.execute("SELECT COUNT(*) FROM tickets_compra")
        tickets_main = cursor_main.fetchone()[0]
        
        cursor_main.execute("SELECT COUNT(*) FROM usuarios")
        usuarios_main = cursor_main.fetchone()[0]
        
        conn_main.close()
        
        print(f"\n✅ almacen_main.db:")
        print(f"   - Productos: {productos_main}")
        print(f"   - Tickets: {tickets_main}")
        print(f"   - Usuarios: {usuarios_main}")
        
    except Exception as e:
        print(f"❌ Error con almacen_main.db: {e}")

def main():
    print("=== VERIFICACIÓN DE SERVIDORES ===\n")
    
    # Verificar servidor de desarrollo
    desarrollo_ok = verificar_servidor(BASE_URL_DESARROLLO, "DESARROLLO (puerto 8000)")
    
    # Verificar servidor main
    main_ok = verificar_servidor(BASE_URL_MAIN, "MAIN (puerto 8001)")
    
    # Verificar bases de datos
    verificar_base_datos()
    
    print(f"\n=== ANÁLISIS ===")
    if desarrollo_ok and main_ok:
        print("✅ Ambos servidores están funcionando")
        print("⚠️ Si ves los mismos datos en ambos, verifica:")
        print("   1. Que cada servidor use su base de datos correcta")
        print("   2. Que las variables de entorno BRANCH estén configuradas")
        print("   3. Que los archivos de base de datos sean diferentes")
    elif desarrollo_ok:
        print("✅ Solo el servidor de desarrollo está funcionando")
    elif main_ok:
        print("✅ Solo el servidor main está funcionando")
    else:
        print("❌ Ningún servidor está funcionando")
    
    print(f"\n=== INSTRUCCIONES ===")
    print("Para iniciar servidor DESARROLLO:")
    print("   cd backend")
    print("   $env:BRANCH='desarrollo'; $env:PORT='8000'; python main.py")
    print("")
    print("Para iniciar servidor MAIN:")
    print("   cd backend")
    print("   $env:BRANCH='main'; $env:PORT='8001'; python main.py")

if __name__ == "__main__":
    main() 