#!/usr/bin/env python3
"""
Script para verificar la configuración de cada servidor
"""

import requests
import json
import sys
import os

# Configuración
BASE_URL_DESARROLLO = "https://localhost:8000"
BASE_URL_MAIN = "https://localhost:8001"

def verificar_servidor_config(url, nombre):
    """Verificar la configuración de un servidor específico"""
    try:
        # Intentar obtener estadísticas para ver qué datos tiene
        response = requests.get(f"{url}/api/estadisticas", verify=False, timeout=5)
        
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Servidor {nombre} ({url}) está funcionando")
            print(f"   - Productos: {stats.get('total_productos', 'N/A')}")
            print(f"   - Tickets: {stats.get('total_tickets', 'N/A')}")
            print(f"   - Usuarios: {stats.get('total_usuarios', 'N/A')}")
            
            # Intentar obtener algunos tickets para ver qué datos tiene
            response_tickets = requests.get(f"{url}/api/tickets?limit=3", verify=False, timeout=5)
            if response_tickets.status_code == 200:
                tickets = response_tickets.json()
                if tickets:
                    print(f"   - Últimos tickets:")
                    for ticket in tickets[:3]:
                        print(f"     * {ticket.get('numero_ticket', 'N/A')} - {ticket.get('estado', 'N/A')}")
                else:
                    print(f"   - No hay tickets en este servidor")
            
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

def verificar_base_datos_directo():
    """Verificar las bases de datos directamente"""
    import sqlite3
    
    print("\n=== VERIFICACIÓN DIRECTA DE BASES DE DATOS ===")
    
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
        
        # Obtener algunos tickets de ejemplo
        cursor_desarrollo.execute("SELECT numero_ticket, estado FROM tickets_compra ORDER BY id DESC LIMIT 3")
        tickets_ejemplo_desarrollo = cursor_desarrollo.fetchall()
        
        conn_desarrollo.close()
        
        print(f"✅ almacen_desarrollo.db:")
        print(f"   - Productos: {productos_desarrollo}")
        print(f"   - Tickets: {tickets_desarrollo}")
        print(f"   - Usuarios: {usuarios_desarrollo}")
        if tickets_ejemplo_desarrollo:
            print(f"   - Ejemplos de tickets:")
            for ticket in tickets_ejemplo_desarrollo:
                print(f"     * {ticket[0]} - {ticket[1]}")
        
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
        
        # Obtener algunos tickets de ejemplo
        cursor_main.execute("SELECT numero_ticket, estado FROM tickets_compra ORDER BY id DESC LIMIT 3")
        tickets_ejemplo_main = cursor_main.fetchall()
        
        conn_main.close()
        
        print(f"\n✅ almacen_main.db:")
        print(f"   - Productos: {productos_main}")
        print(f"   - Tickets: {tickets_main}")
        print(f"   - Usuarios: {usuarios_main}")
        if tickets_ejemplo_main:
            print(f"   - Ejemplos de tickets:")
            for ticket in tickets_ejemplo_main:
                print(f"     * {ticket[0]} - {ticket[1]}")
        
    except Exception as e:
        print(f"❌ Error con almacen_main.db: {e}")

def main():
    print("=== VERIFICACIÓN DE CONFIGURACIÓN DE SERVIDORES ===\n")
    
    # Verificar servidor de desarrollo
    desarrollo_ok = verificar_servidor_config(BASE_URL_DESARROLLO, "DESARROLLO (puerto 8000)")
    
    # Verificar servidor main
    main_ok = verificar_servidor_config(BASE_URL_MAIN, "MAIN (puerto 8001)")
    
    # Verificar bases de datos directamente
    verificar_base_datos_directo()
    
    print(f"\n=== ANÁLISIS ===")
    if desarrollo_ok and main_ok:
        print("✅ Ambos servidores están funcionando")
        print("🔍 Comparando datos...")
        print("Si ambos servidores muestran los mismos datos, significa que:")
        print("   1. Ambos están usando la misma base de datos, O")
        print("   2. Las bases de datos tienen datos idénticos")
        print("")
        print("Para verificar que cada servidor use su base de datos correcta:")
        print("   1. Detén ambos servidores")
        print("   2. Inicia servidor DESARROLLO: $env:BRANCH='desarrollo'; $env:PORT='8000'; python main.py")
        print("   3. Inicia servidor MAIN: $env:BRANCH='main'; $env:PORT='8001'; python main.py")
    elif desarrollo_ok:
        print("✅ Solo el servidor de desarrollo está funcionando")
    elif main_ok:
        print("✅ Solo el servidor main está funcionando")
    else:
        print("❌ Ningún servidor está funcionando")

if __name__ == "__main__":
    main() 